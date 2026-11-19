from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from types import MappingProxyType
from typing import Any, Mapping

from .contract import OFFICIAL_INVSQRT_SPEC
from .search_space import SearchSpace, canonical_json


@dataclass(frozen=True)
class CandidateConfiguration:
    configuration_id: str
    benchmark_id: str
    parameters: Mapping[str, Any]
    search_space_id: str
    strategy_id: str
    seed: int | None
    created_at: str
    creation_metadata: Mapping[str, str]
    fingerprint: str
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if not isinstance(self.benchmark_id, str) or not self.benchmark_id.strip():
            raise ValueError("benchmark_id is required")
        if not isinstance(self.search_space_id, str) or not self.search_space_id.strip():
            raise ValueError("search_space_id is required")
        if not isinstance(self.strategy_id, str) or not self.strategy_id.strip():
            raise ValueError("strategy_id is required")
        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ValueError("seed must be an integer or None")
        if not isinstance(self.schema_version, str) or self.schema_version != "1":
            raise ValueError("Unsupported candidate configuration schema version")
        try:
            datetime.fromisoformat(self.created_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("created_at must be an ISO-8601 timestamp") from exc
        if not isinstance(self.parameters, Mapping):
            raise ValueError("parameters must be a mapping")
        if not isinstance(self.creation_metadata, Mapping) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in self.creation_metadata.items()
        ):
            raise ValueError("creation_metadata must map strings to strings")

        frozen_parameters = dict(self.parameters)
        canonical_json(frozen_parameters)
        object.__setattr__(
            self, "parameters", MappingProxyType(frozen_parameters)
        )
        object.__setattr__(
            self,
            "creation_metadata",
            MappingProxyType(dict(self.creation_metadata)),
        )
        expected_fingerprint = self._fingerprint(
            self.benchmark_id,
            frozen_parameters,
            self.search_space_id,
            self.strategy_id,
            self.seed,
            self.schema_version,
        )
        if self.fingerprint != expected_fingerprint:
            raise ValueError("Configuration fingerprint does not match its values")
        if self.configuration_id != f"candidate-config:{expected_fingerprint}":
            raise ValueError("Configuration ID does not match its fingerprint")

    @staticmethod
    def _fingerprint(
        benchmark_id: str,
        parameters: Mapping[str, Any],
        search_space_id: str,
        strategy_id: str,
        seed: int | None,
        schema_version: str,
    ) -> str:
        payload = {
            "benchmark_id": benchmark_id,
            "parameters": dict(parameters),
            "search_space_id": search_space_id,
            "strategy_id": strategy_id,
            "seed": seed,
            "schema_version": schema_version,
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        parameters: Mapping[str, Any],
        search_space: SearchSpace,
        strategy_id: str,
        *,
        seed: int | None = None,
        benchmark_id: str = OFFICIAL_INVSQRT_SPEC.benchmark_id,
        created_at: str | None = None,
        creation_metadata: Mapping[str, str] | None = None,
    ) -> "CandidateConfiguration":
        validated_parameters = search_space.validate(parameters)
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        metadata = dict(creation_metadata or {})
        fingerprint = cls._fingerprint(
            benchmark_id,
            validated_parameters,
            search_space.search_space_id,
            strategy_id,
            seed,
            "1",
        )
        return cls(
            configuration_id=f"candidate-config:{fingerprint}",
            benchmark_id=benchmark_id,
            parameters=validated_parameters,
            search_space_id=search_space.search_space_id,
            strategy_id=strategy_id,
            seed=seed,
            created_at=timestamp,
            creation_metadata=metadata,
            fingerprint=fingerprint,
        )

    def validate_against(self, search_space: SearchSpace) -> None:
        if self.search_space_id != search_space.search_space_id:
            raise ValueError("Configuration belongs to a different search space")
        search_space.validate(self.parameters)

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_id": self.configuration_id,
            "benchmark_id": self.benchmark_id,
            "parameters": dict(self.parameters),
            "search_space_id": self.search_space_id,
            "strategy_id": self.strategy_id,
            "seed": self.seed,
            "created_at": self.created_at,
            "creation_metadata": dict(self.creation_metadata),
            "fingerprint": self.fingerprint,
            "schema_version": self.schema_version,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateConfiguration":
        return cls(**dict(data))

    @classmethod
    def from_json(cls, text: str) -> "CandidateConfiguration":
        return cls.from_dict(json.loads(text))
