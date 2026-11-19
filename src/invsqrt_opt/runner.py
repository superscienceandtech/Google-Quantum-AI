from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
import uuid
from typing import Any, Mapping

from .backend import (
    BackendExecutionResult,
    BackendOperation,
    BuiltCircuit,
    ExperimentBackend,
    OperationStatus,
    UnavailableBackend,
)
from .configurations import CandidateConfiguration
from .contract import OFFICIAL_INVSQRT_SPEC
from .execution import ExecutionLifecycle, ExecutionStatus
from .models import (
    Candidate,
    CandidateState,
    ExperimentConfig,
    ExperimentStatus,
    MeasurementStatus,
    MetricProvenance,
    ResourceMetrics,
    VerificationStatus as CandidateVerificationStatus,
)
from .records import ExperimentRecord, ExperimentStore
from .score import ScoreResult, calculate_official_score, calculate_score
from .search_space import SearchSpace
from .strategies import GenerationBatch, SearchStrategy
from .verifier import (
    ArtifactStatus,
    ExecutionStatus as VerifierExecutionStatus,
    OfficialVerifierAdapter,
    UnavailableVerifierAdapter,
    VerificationLevel,
    VerificationRequest,
    VerificationResult,
    VerificationStatus as OfficialVerificationStatus,
)


@dataclass(frozen=True)
class ExperimentOutcome:
    configuration: CandidateConfiguration
    execution_status: ExecutionStatus
    state_history: tuple[ExecutionStatus, ...]
    backend_result: BackendExecutionResult
    experiment_record: ExperimentRecord
    persistence_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_id": self.configuration.configuration_id,
            "execution_status": self.execution_status.value,
            "state_history": [status.value for status in self.state_history],
            "backend_result": self.backend_result.to_dict(),
            "experiment_record": self.experiment_record.to_dict(),
            "persistence_error": self.persistence_error,
        }


@dataclass(frozen=True)
class ExperimentRunSummary:
    run_id: str
    started_at: str
    completed_at: str
    generation: GenerationBatch
    outcomes: tuple[ExperimentOutcome, ...]
    interrupted: bool
    summary_persistence_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "requested_count": self.generation.requested_count,
            "generated_count": self.generation.generated_count,
            "total_possible": self.generation.total_possible,
            "limit_applied": self.generation.limit_applied,
            "space_exhausted": self.generation.space_exhausted,
            "generation_complete": self.generation.complete,
            "interrupted": self.interrupted,
            "outcomes": [outcome.to_dict() for outcome in self.outcomes],
            "summary_persistence_error": self.summary_persistence_error,
        }


class ExperimentRunner:
    def __init__(
        self,
        backend: ExperimentBackend | None,
        store: ExperimentStore,
        verifier: OfficialVerifierAdapter | None = None,
    ) -> None:
        self.backend = backend or UnavailableBackend()
        self.store = store
        self.verifier = verifier or UnavailableVerifierAdapter()
        if not isinstance(self.backend.backend_id, str) or not self.backend.backend_id.strip():
            raise ValueError("backend_id is required")
        if (
            not isinstance(self.backend.backend_version, str)
            or not self.backend.backend_version.strip()
        ):
            raise ValueError("backend_version is required")

    def run(
        self,
        search_space: SearchSpace,
        strategy: SearchStrategy,
        *,
        git_commit: str,
        software_version: str,
        dependency_metadata: Mapping[str, str],
        seed: int | None = None,
        sample_count: int | None = None,
        max_experiments: int | None = None,
        run_id: str | None = None,
        authorization_reference: str | None = None,
    ) -> ExperimentRunSummary:
        if not isinstance(git_commit, str) or not git_commit.strip():
            raise ValueError("git_commit is required for experiment provenance")
        if not isinstance(software_version, str) or not software_version.strip():
            raise ValueError("software_version is required")
        if not isinstance(dependency_metadata, Mapping) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in dependency_metadata.items()
        ):
            raise ValueError("dependency_metadata must map strings to strings")
        if authorization_reference is not None and (
            not isinstance(authorization_reference, str)
            or not authorization_reference.strip()
        ):
            raise ValueError("authorization_reference must be a non-empty string")
        effective_run_id = run_id or str(uuid.uuid4())
        if not isinstance(effective_run_id, str) or not effective_run_id.strip():
            raise ValueError("run_id must be a non-empty string")

        started_at = datetime.now(timezone.utc).isoformat()
        generation = strategy.generate(
            search_space,
            benchmark_id=OFFICIAL_INVSQRT_SPEC.benchmark_id,
            seed=seed,
            max_configurations=max_experiments,
            sample_count=sample_count,
        )
        if not isinstance(generation, GenerationBatch):
            raise ValueError("Search strategy returned an invalid generation batch")
        if (
            generation.strategy_id != strategy.strategy_id
            or generation.strategy_version != strategy.version
        ):
            raise ValueError("Generation batch strategy provenance does not match")
        outcomes: list[ExperimentOutcome] = []
        seen_fingerprints: set[str] = set()
        interrupted = False
        try:
            for index, configuration in enumerate(generation.configurations):
                if configuration.fingerprint in seen_fingerprints:
                    outcome = self._duplicate_outcome(
                        configuration,
                        search_space,
                        generation,
                        effective_run_id,
                        index,
                        git_commit,
                        software_version,
                        dependency_metadata,
                    )
                else:
                    seen_fingerprints.add(configuration.fingerprint)
                    outcome = self._execute_one(
                        configuration,
                        search_space,
                        generation,
                        effective_run_id,
                        index,
                        git_commit,
                        software_version,
                        dependency_metadata,
                        authorization_reference,
                    )
                outcomes.append(outcome)
        except KeyboardInterrupt:
            interrupted = True

        completed_at = datetime.now(timezone.utc).isoformat()
        summary = ExperimentRunSummary(
            run_id=effective_run_id,
            started_at=started_at,
            completed_at=completed_at,
            generation=generation,
            outcomes=tuple(outcomes),
            interrupted=interrupted,
        )
        summary_record = ExperimentRecord(
            experiment_id=f"{effective_run_id}:summary",
            candidate_id=effective_run_id,
            git_commit=git_commit,
            candidate_state=CandidateState.CREATED,
            verification_status=CandidateVerificationStatus.NOT_RUN,
            score_result=None,
            search_space=search_space.to_dict(),
            search_strategy={
                "strategy_id": generation.strategy_id,
                "version": generation.strategy_version,
                "seed": generation.seed,
            },
            backend_execution={
                "record_type": "RUN_SUMMARY",
                "interrupted": interrupted,
                "started_at": started_at,
                "completed_at": completed_at,
                "requested_count": generation.requested_count,
                "generated_count": generation.generated_count,
                "limit_applied": generation.limit_applied,
                "space_exhausted": generation.space_exhausted,
                "generation_complete": generation.complete,
                "completed_outcomes": len(outcomes),
                "outcome_statuses": [
                    outcome.execution_status.value for outcome in outcomes
                ],
                "configuration_ids": [
                    outcome.configuration.configuration_id for outcome in outcomes
                ],
            },
            experiment_provenance={
                "software_version": software_version,
                "dependency_metadata": dict(dependency_metadata),
                "backend_id": self.backend.backend_id,
                "backend_version": self.backend.backend_version,
            },
            record_type="RUN_SUMMARY",
        )
        summary_error = self._persist(summary_record)
        return ExperimentRunSummary(
            run_id=summary.run_id,
            started_at=summary.started_at,
            completed_at=summary.completed_at,
            generation=summary.generation,
            outcomes=summary.outcomes,
            interrupted=summary.interrupted,
            summary_persistence_error=summary_error,
        )

    def _execute_one(
        self,
        configuration: CandidateConfiguration,
        search_space: SearchSpace,
        generation: GenerationBatch,
        run_id: str,
        index: int,
        git_commit: str,
        software_version: str,
        dependency_metadata: Mapping[str, str],
        authorization_reference: str | None,
    ) -> ExperimentOutcome:
        lifecycle = ExecutionLifecycle()
        started = time.perf_counter()
        operations: dict[str, BackendOperation] = {}
        resource_metrics: ResourceMetrics | None = None
        circuit: BuiltCircuit | None = None
        verification_result: VerificationResult | None = None
        error: str | None = None
        try:
            if configuration.benchmark_id != OFFICIAL_INVSQRT_SPEC.benchmark_id:
                raise ValueError("Configuration benchmark ID does not match INVSQRT")
            if configuration.strategy_id != generation.strategy_id:
                raise ValueError("Configuration strategy ID does not match search batch")
            if configuration.seed != generation.seed:
                raise ValueError("Configuration seed does not match search batch")
            configuration.validate_against(search_space)
        except (TypeError, ValueError) as exc:
            lifecycle.transition(ExecutionStatus.CONFIGURATION_INVALID)
            error = str(exc)
            return self._finish(
                configuration,
                search_space,
                generation,
                run_id,
                index,
                git_commit,
                software_version,
                dependency_metadata,
                lifecycle,
                operations,
                resource_metrics,
                circuit,
                verification_result,
                started,
                error,
            )

        lifecycle.transition(ExecutionStatus.CONFIGURATION_VALID)
        try:
            backend_available = self.backend.available
        except Exception as exc:
            backend_available = False
            error = f"Backend availability check failed: {type(exc).__name__}: {exc}"
        if not isinstance(backend_available, bool):
            backend_available = False
            error = "Backend availability must be a boolean"
        if not backend_available:
            lifecycle.transition(ExecutionStatus.BACKEND_UNAVAILABLE)
            for name in (
                "configuration_validation",
                "circuit_construction",
                "resource_measurement",
                "compilation",
                "official_verification",
            ):
                operations[name] = BackendOperation(
                    OperationStatus.UNAVAILABLE,
                    error=error or "Backend unavailable",
                )
            return self._finish(
                configuration,
                search_space,
                generation,
                run_id,
                index,
                git_commit,
                software_version,
                dependency_metadata,
                lifecycle,
                operations,
                resource_metrics,
                circuit,
                verification_result,
                started,
                error,
            )

        lifecycle.transition(ExecutionStatus.EXECUTION_PENDING)
        lifecycle.transition(ExecutionStatus.EXECUTION_RUNNING)
        validation = self._call_backend(
            "configuration_validation",
            lambda: self.backend.validate_configuration(configuration, search_space),
        )
        operations["configuration_validation"] = validation
        if validation.status != OperationStatus.SUCCEEDED:
            error = validation.error or "Backend rejected the configuration"
        else:
            construction = self._call_backend(
                "circuit_construction",
                lambda: self.backend.construct_circuit(configuration),
            )
            operations["circuit_construction"] = construction
            if construction.status == OperationStatus.SUCCEEDED:
                if isinstance(construction.value, BuiltCircuit):
                    circuit = construction.value
                    if circuit.metadata is not None:
                        if circuit.metadata.candidate_id != configuration.configuration_id:
                            error = "Circuit metadata candidate ID does not match configuration"
                        else:
                            metadata_errors = circuit.metadata.validate_metadata()
                            if metadata_errors:
                                error = "Circuit metadata validation failed: " + "; ".join(
                                    metadata_errors
                                )
                else:
                    operations["circuit_construction"] = BackendOperation(
                        OperationStatus.FAILED,
                        error="Successful circuit construction returned no BuiltCircuit",
                    )
                    error = operations["circuit_construction"].error
            elif construction.status == OperationStatus.FAILED:
                error = construction.error

            if circuit is not None:
                measurement = self._call_backend(
                    "resource_measurement",
                    lambda: self.backend.measure_resources(configuration, circuit),
                )
                if measurement.status == OperationStatus.SUCCEEDED:
                    if isinstance(measurement.value, ResourceMetrics):
                        resource_metrics = measurement.value
                    else:
                        measurement = BackendOperation(
                            OperationStatus.FAILED,
                            error="Resource measurement returned no ResourceMetrics",
                        )
                if measurement.status == OperationStatus.FAILED and error is None:
                    error = measurement.error
                operations["resource_measurement"] = measurement

                compilation = self._call_backend(
                    "compilation",
                    lambda: self.backend.compile_circuit(configuration, circuit),
                )
                operations["compilation"] = compilation
                if (
                    compilation.status == OperationStatus.FAILED
                    and error is None
                ):
                    error = compilation.error
            else:
                operations["resource_measurement"] = BackendOperation(
                    OperationStatus.NOT_STARTED,
                    error="Circuit construction did not produce an artifact",
                )
                operations["compilation"] = BackendOperation(
                    OperationStatus.NOT_STARTED,
                    error="Circuit construction did not produce an artifact",
                )

        if error is None and resource_metrics is not None:
            try:
                self._score_for_metrics(resource_metrics)
            except ValueError as exc:
                error = f"Resource metrics could not be scored: {exc}"

        if error is None and authorization_reference:
            lifecycle.transition(ExecutionStatus.VERIFICATION_PENDING)
            verification_result, verification_operation = self._verify(
                configuration,
                circuit,
                git_commit,
                dependency_metadata,
                authorization_reference,
                run_id,
                index,
            )
            operations["official_verification"] = verification_operation
        else:
            operations["official_verification"] = BackendOperation(
                OperationStatus.NOT_STARTED,
                error=(
                    "No authorization reference supplied"
                    if not authorization_reference
                    else "Circuit artifact unavailable"
                ),
            )

        status = self._final_status(
            error,
            operations,
            resource_metrics,
            circuit,
            verification_result,
            authorization_reference,
        )
        lifecycle.transition(status)
        return self._finish(
            configuration,
            search_space,
            generation,
            run_id,
            index,
            git_commit,
            software_version,
            dependency_metadata,
            lifecycle,
            operations,
            resource_metrics,
            circuit,
            verification_result,
            started,
            error,
        )

    @staticmethod
    def _call_backend(name: str, operation: Any) -> BackendOperation:
        try:
            result = operation()
        except Exception as exc:
            return BackendOperation(
                OperationStatus.FAILED,
                error=f"{name} raised {type(exc).__name__}: {exc}",
            )
        if not isinstance(result, BackendOperation):
            return BackendOperation(
                OperationStatus.FAILED,
                error=f"{name} returned an invalid backend operation result",
            )
        return result

    def _verify(
        self,
        configuration: CandidateConfiguration,
        circuit: BuiltCircuit | None,
        git_commit: str,
        dependency_metadata: Mapping[str, str],
        authorization_reference: str,
        run_id: str,
        index: int,
    ) -> tuple[VerificationResult | None, BackendOperation]:
        if circuit is None:
            return None, BackendOperation(
                OperationStatus.UNAVAILABLE,
                error="No circuit artifact is available for verification",
            )
        try:
            availability = self.verifier.discover()
        except Exception as exc:
            return None, BackendOperation(
                OperationStatus.FAILED,
                error=f"Verifier discovery failed: {type(exc).__name__}: {exc}",
            )

        verifier_id = availability.verifier_id or "official-invsqrt-verifier"
        request = VerificationRequest(
            request_id=f"{run_id}:{index}:verification",
            candidate_id=configuration.configuration_id,
            candidate_artifact=circuit.artifact_reference,
            specification_version=OFFICIAL_INVSQRT_SPEC.contract_version,
            verifier_id=verifier_id,
            git_commit=git_commit,
            environment_metadata=dict(dependency_metadata),
            requested_level=VerificationLevel.OFFICIAL,
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            authorization_reference=authorization_reference,
        )
        if (
            availability.status != ArtifactStatus.AVAILABLE
            or not availability.source_checksum
        ):
            result = VerificationResult(
                request_id=request.request_id,
                candidate_id=request.candidate_id,
                verifier_id=request.verifier_id,
                verifier_source_checksum=None,
                execution_status=VerifierExecutionStatus.NOT_STARTED,
                verification_status=OfficialVerificationStatus.VERIFIER_UNAVAILABLE,
                exit_code=None,
                evidence_references=(),
                error_details=availability.detail or "Official verifier unavailable",
                provenance_complete=False,
            )
            return result, BackendOperation(
                OperationStatus.UNAVAILABLE,
                value=result,
                error=result.error_details,
            )

        try:
            request_errors = self.verifier.validate_request(request)
        except Exception as exc:
            request_errors = (
                f"Verifier request validation failed: {type(exc).__name__}: {exc}",
            )
        if request_errors:
            result = VerificationResult(
                request_id=request.request_id,
                candidate_id=request.candidate_id,
                verifier_id=request.verifier_id,
                verifier_source_checksum=availability.source_checksum,
                execution_status=VerifierExecutionStatus.NOT_STARTED,
                verification_status=OfficialVerificationStatus.NOT_CHECKED,
                exit_code=None,
                evidence_references=(),
                error_details="; ".join(request_errors),
                provenance_complete=False,
            )
            return result, BackendOperation(
                OperationStatus.UNAVAILABLE,
                value=result,
                error=result.error_details,
            )

        try:
            result = self.verifier.execute(request)
        except Exception as exc:
            result = VerificationResult(
                request_id=request.request_id,
                candidate_id=request.candidate_id,
                verifier_id=request.verifier_id,
                verifier_source_checksum=availability.source_checksum,
                execution_status=VerifierExecutionStatus.FAILED,
                verification_status=OfficialVerificationStatus.EXECUTION_FAILED,
                exit_code=None,
                evidence_references=(),
                error_details=f"Verifier execution failed: {type(exc).__name__}: {exc}",
                provenance_complete=False,
            )
            return result, BackendOperation(
                OperationStatus.FAILED,
                value=result,
                error=result.error_details,
            )

        if not isinstance(result, VerificationResult):
            return None, BackendOperation(
                OperationStatus.FAILED,
                error="Verifier returned an invalid result type",
            )

        mismatches = []
        if result.request_id != request.request_id:
            mismatches.append("request ID mismatch")
        if result.candidate_id != request.candidate_id:
            mismatches.append("candidate ID mismatch")
        if result.verifier_id != request.verifier_id:
            mismatches.append("verifier ID mismatch")
        if result.verifier_source_checksum != availability.source_checksum:
            mismatches.append("verifier checksum mismatch")
        if result.verification_status == OfficialVerificationStatus.PASSED and (
            result.execution_status != VerifierExecutionStatus.EXECUTED
            or result.exit_code != 0
            or not result.evidence_references
            or not result.provenance_complete
        ):
            mismatches.append("incomplete official-pass evidence")

        if mismatches:
            result = VerificationResult(
                request_id=request.request_id,
                candidate_id=request.candidate_id,
                verifier_id=request.verifier_id,
                verifier_source_checksum=availability.source_checksum,
                execution_status=result.execution_status,
                verification_status=OfficialVerificationStatus.RESULT_UNKNOWN,
                exit_code=result.exit_code,
                evidence_references=result.evidence_references,
                stdout_reference=result.stdout_reference,
                stderr_reference=result.stderr_reference,
                execution_start=result.execution_start,
                execution_end=result.execution_end,
                resource_metrics=result.resource_metrics,
                error_details="Verifier result rejected: " + "; ".join(mismatches),
                provenance_complete=False,
            )
        return result, BackendOperation(
            OperationStatus.SUCCEEDED,
            value=result,
            error=result.error_details,
            evidence_references=result.evidence_references,
        )

    @staticmethod
    def _final_status(
        error: str | None,
        operations: Mapping[str, BackendOperation],
        metrics: ResourceMetrics | None,
        circuit: BuiltCircuit | None,
        verification_result: VerificationResult | None,
        authorization_reference: str | None,
    ) -> ExecutionStatus:
        if error or any(
            item.status == OperationStatus.FAILED
            for item in operations.values()
        ):
            return ExecutionStatus.EXECUTION_FAILED
        if circuit is None or circuit.metadata is None:
            return ExecutionStatus.CIRCUIT_METADATA_UNAVAILABLE
        if metrics is None or not metrics.is_complete:
            return ExecutionStatus.RESOURCE_METRICS_UNAVAILABLE
        if operations.get("compilation", BackendOperation(OperationStatus.NOT_STARTED)).status in (
            OperationStatus.NOT_STARTED,
            OperationStatus.UNAVAILABLE,
        ):
            return ExecutionStatus.COMPILATION_UNAVAILABLE
        if not authorization_reference:
            return ExecutionStatus.EXECUTION_SUCCEEDED
        if verification_result is None:
            return ExecutionStatus.VERIFICATION_UNAVAILABLE
        if (
            verification_result.verification_status
            == OfficialVerificationStatus.PASSED
        ):
            return ExecutionStatus.OFFICIAL_VERIFICATION_PASSED
        if (
            verification_result.verification_status
            == OfficialVerificationStatus.REJECTED
        ):
            return ExecutionStatus.OFFICIAL_VERIFICATION_REJECTED
        if (
            verification_result.verification_status
            == OfficialVerificationStatus.EXECUTION_FAILED
        ):
            return ExecutionStatus.EXECUTION_FAILED
        if (
            verification_result.verification_status
            in (
                OfficialVerificationStatus.VERIFIER_UNAVAILABLE,
                OfficialVerificationStatus.NOT_CHECKED,
            )
        ):
            return ExecutionStatus.VERIFICATION_UNAVAILABLE
        return ExecutionStatus.RESULT_UNKNOWN

    @staticmethod
    def _score_for_metrics(metrics: ResourceMetrics) -> ScoreResult | None:
        if not metrics.is_complete:
            return None
        if (
            metrics.provenance == MetricProvenance.OFFICIAL
            and metrics.measurement_status == MeasurementStatus.MEASURED
        ):
            return calculate_official_score(metrics)
        if metrics.provenance == MetricProvenance.ESTIMATE:
            return calculate_score(metrics)
        return None

    def _finish(
        self,
        configuration: CandidateConfiguration,
        search_space: SearchSpace,
        generation: GenerationBatch,
        run_id: str,
        index: int,
        git_commit: str,
        software_version: str,
        dependency_metadata: Mapping[str, str],
        lifecycle: ExecutionLifecycle,
        operations: Mapping[str, BackendOperation],
        resource_metrics: ResourceMetrics | None,
        circuit: BuiltCircuit | None,
        verification_result: VerificationResult | None,
        started: float,
        error: str | None,
        *,
        duplicate_of: str | None = None,
    ) -> ExperimentOutcome:
        try:
            score_result = (
                self._score_for_metrics(resource_metrics)
                if resource_metrics is not None
                else None
            )
        except ValueError as exc:
            score_result = None
            error = error or f"Resource metrics could not be scored: {exc}"

        p002_verification_status = CandidateVerificationStatus.NOT_RUN
        candidate_state = CandidateState.CREATED
        if verification_result is not None:
            if verification_result.verification_status == OfficialVerificationStatus.PASSED:
                p002_verification_status = CandidateVerificationStatus.PASSED
                candidate = Candidate(
                    candidate_id=configuration.configuration_id,
                    candidate_version=configuration.schema_version,
                    optimization_strategy=configuration.strategy_id,
                    configuration=configuration.parameters,
                    circuit_artifact=(
                        circuit.artifact_reference if circuit is not None else None
                    ),
                    resource_metrics=resource_metrics,
                )
                promoted = candidate.promote_from_verification_result(
                    verification_result
                )
                candidate_state = promoted.state
            elif verification_result.verification_status in (
                OfficialVerificationStatus.REJECTED,
                OfficialVerificationStatus.EXECUTION_FAILED,
            ):
                p002_verification_status = CandidateVerificationStatus.FAILED
                candidate_state = CandidateState.REJECTED

        experiment_id = f"{run_id}:{index:06d}"
        execution_completed_at = datetime.now(timezone.utc).isoformat()
        config_record = ExperimentConfig(
            experiment_id=experiment_id,
            candidate_id=configuration.configuration_id,
            strategy_name=configuration.strategy_id,
            parameter_configuration=dict(configuration.parameters),
            random_seed=configuration.seed,
            software_version=software_version,
            dependency_metadata=dict(dependency_metadata),
            git_commit=git_commit,
            creation_timestamp=configuration.created_at,
            execution_status=(
                ExperimentStatus.SUCCEEDED
                if lifecycle.current
                in (
                    ExecutionStatus.EXECUTION_SUCCEEDED,
                    ExecutionStatus.OFFICIAL_VERIFICATION_PASSED,
                )
                else ExperimentStatus.FAILED
            ),
            evidence_references=(
                verification_result.evidence_references
                if verification_result is not None
                else ()
            ),
        )
        backend_result = BackendExecutionResult(
            configuration_id=configuration.configuration_id,
            backend_id=self.backend.backend_id,
            backend_version=self.backend.backend_version,
            execution_status=lifecycle.current,
            operations=dict(operations),
            resource_metrics=resource_metrics,
            circuit_metadata=circuit.metadata if circuit is not None else None,
            runtime_seconds=max(0.0, time.perf_counter() - started),
            verification_result=(
                verification_result.to_dict()
                if verification_result is not None
                else None
            ),
            error=error,
            evidence_references=tuple(
                reference
                for operation in operations.values()
                for reference in operation.evidence_references
            ),
        )
        provenance = {
            "run_id": run_id,
            "experiment_config": config_record.to_dict(),
            "configuration_fingerprint": configuration.fingerprint,
            "search_strategy": {
                "strategy_id": generation.strategy_id,
                "version": generation.strategy_version,
                "seed": generation.seed,
            },
            "git_commit": git_commit,
            "software_version": software_version,
            "dependency_metadata": dict(dependency_metadata),
            "created_at": configuration.created_at,
            "execution_completed_at": execution_completed_at,
            "execution_state_history": [
                status.value for status in lifecycle.history
            ],
        }
        if duplicate_of is not None:
            provenance["duplicate_of"] = duplicate_of
        record = ExperimentRecord(
            experiment_id=experiment_id,
            candidate_id=configuration.configuration_id,
            git_commit=git_commit,
            candidate_state=candidate_state,
            verification_status=p002_verification_status,
            score_result=score_result,
            evidence_references=(
                verification_result.evidence_references
                if verification_result is not None
                else ()
            ),
            verification_result=(
                verification_result.to_dict()
                if verification_result is not None
                else None
            ),
            search_configuration=configuration.to_dict(),
            search_space=search_space.to_dict(),
            search_strategy={
                "strategy_id": generation.strategy_id,
                "version": generation.strategy_version,
                "seed": generation.seed,
                "requested_count": generation.requested_count,
                "generated_count": generation.generated_count,
                "limit_applied": generation.limit_applied,
                "space_exhausted": generation.space_exhausted,
                "generation_complete": generation.complete,
            },
            resource_metrics=(
                resource_metrics.to_dict() if resource_metrics is not None else None
            ),
            backend_execution=backend_result.to_dict(),
            experiment_provenance=provenance,
        )
        persistence_error = self._persist(record)
        return ExperimentOutcome(
            configuration=configuration,
            execution_status=lifecycle.current,
            state_history=tuple(lifecycle.history),
            backend_result=backend_result,
            experiment_record=record,
            persistence_error=persistence_error,
        )

    def _duplicate_outcome(
        self,
        configuration: CandidateConfiguration,
        search_space: SearchSpace,
        generation: GenerationBatch,
        run_id: str,
        index: int,
        git_commit: str,
        software_version: str,
        dependency_metadata: Mapping[str, str],
    ) -> ExperimentOutcome:
        lifecycle = ExecutionLifecycle()
        lifecycle.transition(ExecutionStatus.CONFIGURATION_VALID)
        lifecycle.transition(ExecutionStatus.DUPLICATE_CONFIGURATION)
        operations = {
            name: BackendOperation(
                OperationStatus.NOT_STARTED,
                error="Duplicate configuration was not executed",
            )
            for name in (
                "configuration_validation",
                "circuit_construction",
                "resource_measurement",
                "compilation",
                "official_verification",
            )
        }
        return self._finish(
            configuration,
            search_space,
            generation,
            run_id,
            index,
            git_commit,
            software_version,
            dependency_metadata,
            lifecycle,
            operations,
            None,
            None,
            None,
            time.perf_counter(),
            "Duplicate configuration was not executed",
            duplicate_of="earlier configuration in this run",
        )

    def _persist(self, record: ExperimentRecord) -> str | None:
        try:
            self.store.append(record)
        except (OSError, ValueError) as exc:
            return f"{type(exc).__name__}: {exc}"
        return None
