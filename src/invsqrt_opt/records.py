from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Iterable, Mapping, Any

from .models import (
    CandidateState,
    MetricProvenance,
    VerificationStatus,
)
from .score import ScoreResult


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    candidate_id: str
    git_commit: str
    candidate_state: CandidateState
    verification_status: VerificationStatus
    score_result: ScoreResult | None
    evidence_references: tuple[str, ...] = ()
    verification_result: Mapping[str, Any] | None = None
    search_configuration: Mapping[str, Any] | None = None
    search_space: Mapping[str, Any] | None = None
    search_strategy: Mapping[str, Any] | None = None
    resource_metrics: Mapping[str, Any] | None = None
    backend_execution: Mapping[str, Any] | None = None
    experiment_provenance: Mapping[str, Any] | None = None
    record_type: str = "CANDIDATE"

    def __post_init__(self) -> None:
        for name in ("experiment_id", "candidate_id", "git_commit"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if not isinstance(self.candidate_state, CandidateState):
            self_candidate_state = CandidateState(self.candidate_state)
            object.__setattr__(self, "candidate_state", self_candidate_state)
        if not isinstance(self.verification_status, VerificationStatus):
            verification_status = VerificationStatus(self.verification_status)
            object.__setattr__(self, "verification_status", verification_status)
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )
        for name in (
            "verification_result",
            "search_configuration",
            "search_space",
            "search_strategy",
            "resource_metrics",
            "backend_execution",
            "experiment_provenance",
        ):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, Mapping):
                    raise ValueError(f"{name} must be a mapping")
                object.__setattr__(self, name, dict(value))
        if self.record_type not in ("CANDIDATE", "RUN_SUMMARY"):
            raise ValueError("record_type must be CANDIDATE or RUN_SUMMARY")

    @property
    def is_officially_eligible(self) -> bool:
        if self.record_type != "CANDIDATE" or not (
            self.candidate_state == CandidateState.OFFICIAL_VERIFIER_VALIDATED
            and self.verification_status == VerificationStatus.PASSED
            and self.score_result is not None
            and self.score_result.provenance == MetricProvenance.OFFICIAL
            and bool(self.evidence_references)
        ):
            return False
        if self.verification_result is None:
            return False
        return (
            self.verification_result.get("execution_status") == "EXECUTED"
            and self.verification_result.get("verification_status") == "PASSED"
            and self.verification_result.get("exit_code") == 0
            and bool(self.verification_result.get("verifier_source_checksum"))
            and bool(self.verification_result.get("provenance_complete"))
            and bool(self.verification_result.get("evidence_references"))
            and self.verification_result.get("candidate_id") == self.candidate_id
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "experiment_id": self.experiment_id,
            "candidate_id": self.candidate_id,
            "git_commit": self.git_commit,
            "candidate_state": self.candidate_state.value,
            "verification_status": self.verification_status.value,
            "cost_c": (
                self.score_result.cost_c if self.score_result is not None else None
            ),
            "score": self.score_result.score if self.score_result is not None else None,
            "metric_provenance": (
                self.score_result.provenance.value
                if self.score_result is not None
                else None
            ),
            "evidence_references": list(self.evidence_references),
            "verification_result": (
                dict(self.verification_result)
                if self.verification_result is not None
                else None
            ),
            "record_type": self.record_type,
        }
        for name in (
            "search_configuration",
            "search_space",
            "search_strategy",
            "resource_metrics",
            "backend_execution",
            "experiment_provenance",
        ):
            value = getattr(self, name)
            if value is not None:
                data[name] = dict(value)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExperimentRecord":
        required = {
            "experiment_id",
            "candidate_id",
            "git_commit",
            "candidate_state",
            "verification_status",
        }
        missing = required - set(data)
        if missing:
            raise ValueError(f"Missing experiment record fields: {sorted(missing)}")
        score_result = None
        if data.get("score") is not None and data.get("cost_c") is not None:
            if data.get("metric_provenance") is None:
                raise ValueError("metric_provenance is required when a score exists")
            score_result = ScoreResult(
                cost_c=float(data["cost_c"]),
                score=float(data["score"]),
                provenance=MetricProvenance(data["metric_provenance"]),
            )
        return cls(
            experiment_id=data["experiment_id"],
            candidate_id=data["candidate_id"],
            git_commit=data["git_commit"],
            candidate_state=CandidateState(data["candidate_state"]),
            verification_status=VerificationStatus(data["verification_status"]),
            score_result=score_result,
            evidence_references=tuple(data.get("evidence_references", [])),
            verification_result=(
                dict(data["verification_result"])
                if data.get("verification_result") is not None
                else None
            ),
            search_configuration=(
                dict(data["search_configuration"])
                if data.get("search_configuration") is not None
                else None
            ),
            search_space=(
                dict(data["search_space"])
                if data.get("search_space") is not None
                else None
            ),
            search_strategy=(
                dict(data["search_strategy"])
                if data.get("search_strategy") is not None
                else None
            ),
            resource_metrics=(
                dict(data["resource_metrics"])
                if data.get("resource_metrics") is not None
                else None
            ),
            backend_execution=(
                dict(data["backend_execution"])
                if data.get("backend_execution") is not None
                else None
            ),
            experiment_provenance=(
                dict(data["experiment_provenance"])
                if data.get("experiment_provenance") is not None
                else None
            ),
            record_type=data.get("record_type", "CANDIDATE"),
        )


class ExperimentStore:
    def __init__(self, path: str | Path) -> None:
        requested_path = Path(path).expanduser()
        if requested_path.is_symlink():
            raise ValueError("Experiment storage path cannot be a symbolic link")
        if requested_path.exists() and not requested_path.is_file():
            raise ValueError("Experiment storage path must be a regular file")
        resolved_path = requested_path.resolve()
        repository_root = Path(__file__).resolve().parents[2]
        protected_paths = (
            repository_root / ".git",
            repository_root / "external",
            repository_root / "results" / "raw",
        )
        for protected in protected_paths:
            protected_path = protected.resolve()
            if (
                resolved_path == protected_path
                or resolved_path.is_relative_to(protected_path)
            ):
                raise ValueError(
                    "Experiment storage cannot target Git metadata or protected "
                    "official artifacts/baseline evidence"
                )
        self.path = resolved_path

    def append(self, record: ExperimentRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for existing in self.load():
            if existing.experiment_id == record.experiment_id:
                raise ValueError(
                    f"Experiment ID already exists: {record.experiment_id}"
                )
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    def load(self) -> list[ExperimentRecord]:
        if not self.path.exists():
            return []
        records: list[ExperimentRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(
                        ExperimentRecord.from_dict(json.loads(line))
                    )
                except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid experiment record at {self.path}:{line_number}"
                    ) from exc
        return records

    @staticmethod
    def compare(records: Iterable[ExperimentRecord]) -> list[ExperimentRecord]:
        return sorted(
            (
                record
                for record in records
                if record.record_type == "CANDIDATE"
                and record.is_officially_eligible
                and record.score_result is not None
            ),
            key=lambda record: (
                record.score_result.score
                if record.score_result is not None
                else float("inf")
            ),
        )

    @staticmethod
    def best(records: Iterable[ExperimentRecord]) -> ExperimentRecord | None:
        eligible = ExperimentStore.compare(records)
        return eligible[0] if eligible else None
