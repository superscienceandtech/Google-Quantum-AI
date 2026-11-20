from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Any

from .evidence import AuthorityClass


class VerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_RUN = "NOT_RUN"
    NOT_VERIFIED = "NOT_VERIFIED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True)
class ValidationResult:
    status: VerificationStatus
    name: str
    authority: str
    message: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()
    evidence_manifest: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Validation name must not be empty")
        if not self.authority:
            raise ValueError("Authority classification must not be empty")
        allowed_authorities = {item.value for item in AuthorityClass}
        if self.authority not in allowed_authorities:
            raise ValueError(f"Unknown authority classification: {self.authority}")

        normalized_status = (
            self.status
            if isinstance(self.status, VerificationStatus)
            else VerificationStatus(self.status)
        )
        object.__setattr__(self, "status", normalized_status)

        if not isinstance(self.evidence_refs, tuple):
            raise ValueError("Evidence references must be a tuple")
        normalized_refs = tuple(
            reference.strip() if isinstance(reference, str) else ""
            for reference in self.evidence_refs
        )
        if any(
            not reference
            or len(reference) > 128
            or any(character.isspace() for character in reference)
            for reference in normalized_refs
        ):
            raise ValueError("Evidence references must be non-empty, unspaced identifiers")
        if len(set(normalized_refs)) != len(normalized_refs):
            raise ValueError("Duplicate evidence references are not allowed")
        object.__setattr__(self, "evidence_refs", normalized_refs)

        is_official_pass = (
            normalized_status == VerificationStatus.PASS
            and self.authority == AuthorityClass.OFFICIAL_COMPETITION_VERIFIER.value
        )
        if is_official_pass and not self.evidence_refs:
            raise ValueError(
                "OFFICIAL_COMPETITION_VERIFIER PASS requires evidence references"
            )
        if is_official_pass and self.evidence_manifest is not None:
            recorded_ids = set(self.evidence_manifest)
            missing = set(normalized_refs) - recorded_ids
            if missing:
                raise ValueError(
                    "Official PASS references missing evidence records: "
                    + ", ".join(sorted(missing))
                )
