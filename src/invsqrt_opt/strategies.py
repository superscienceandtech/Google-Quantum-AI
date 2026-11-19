from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import random
from typing import Protocol

from .configurations import CandidateConfiguration
from .search_space import ParameterKind, SearchSpace


@dataclass(frozen=True)
class GenerationBatch:
    strategy_id: str
    seed: int | None
    configurations: tuple[CandidateConfiguration, ...]
    requested_count: int
    generated_count: int
    total_possible: int | None
    limit_applied: bool
    space_exhausted: bool
    strategy_version: str = "1"

    def __post_init__(self) -> None:
        for name in ("requested_count", "generated_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not isinstance(self.strategy_id, str) or not self.strategy_id.strip():
            raise ValueError("strategy_id is required")
        if self.generated_count != len(self.configurations):
            raise ValueError("generated_count must match configuration count")
        if self.total_possible is not None and (
            isinstance(self.total_possible, bool)
            or not isinstance(self.total_possible, int)
            or self.total_possible < 0
        ):
            raise ValueError("total_possible must be a non-negative integer")
        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ValueError("seed must be an integer or None")
        if not isinstance(self.strategy_version, str) or not self.strategy_version.strip():
            raise ValueError("strategy_version is required")

    @property
    def complete(self) -> bool:
        return (
            self.generated_count >= self.requested_count
            or self.space_exhausted
            or self.limit_applied
        )


class SearchStrategy(Protocol):
    strategy_id: str
    version: str

    def generate(
        self,
        search_space: SearchSpace,
        *,
        benchmark_id: str,
        seed: int | None = None,
        max_configurations: int | None = None,
        sample_count: int | None = None,
    ) -> GenerationBatch:
        ...


def _validate_limit(limit: int | None) -> None:
    if limit is not None and (
        isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0
    ):
        raise ValueError("max_configurations must be a positive integer")


class GridSearch:
    strategy_id = "grid-search"
    version = "1"

    def generate(
        self,
        search_space: SearchSpace,
        *,
        benchmark_id: str,
        seed: int | None = None,
        max_configurations: int | None = None,
        sample_count: int | None = None,
    ) -> GenerationBatch:
        if sample_count is not None:
            raise ValueError("sample_count is not used by grid search")
        _validate_limit(max_configurations)
        values = [parameter.grid_values() for parameter in search_space.parameters]
        total = 1
        for choices in values:
            total *= len(choices)
        generated_limit = min(total, max_configurations or total)
        configurations: list[CandidateConfiguration] = []
        for parameter_values in product(*values):
            if len(configurations) >= generated_limit:
                break
            parameters = {
                definition.name: value
                for definition, value in zip(search_space.parameters, parameter_values)
            }
            configurations.append(
                CandidateConfiguration.create(
                    parameters,
                    search_space,
                    self.strategy_id,
                    seed=seed,
                    benchmark_id=benchmark_id,
                )
            )
        return GenerationBatch(
            strategy_id=self.strategy_id,
            seed=seed,
            configurations=tuple(configurations),
            requested_count=total,
            generated_count=len(configurations),
            total_possible=total,
            limit_applied=len(configurations) < total,
            space_exhausted=len(configurations) == total,
            strategy_version=self.version,
        )


class RandomSearch:
    strategy_id = "random-search"
    version = "1"

    def generate(
        self,
        search_space: SearchSpace,
        *,
        benchmark_id: str,
        seed: int | None = None,
        max_configurations: int | None = None,
        sample_count: int | None = None,
    ) -> GenerationBatch:
        _validate_limit(max_configurations)
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("Random search requires an explicit integer seed")
        if sample_count is None or (
            isinstance(sample_count, bool)
            or not isinstance(sample_count, int)
            or sample_count <= 0
        ):
            raise ValueError("sample_count must be a positive integer")

        requested = sample_count
        target = min(sample_count, max_configurations or sample_count)
        limit_applied = target < sample_count
        total = search_space.finite_configuration_count
        if total is not None:
            target = min(target, total)
        rng = random.Random(seed)
        configurations: list[CandidateConfiguration] = []

        if total is not None:
            indices = self._sample_unique_indices(rng, total, target)
            for index in indices:
                parameters = self._parameters_at(search_space, index)
                configurations.append(
                    CandidateConfiguration.create(
                        parameters,
                        search_space,
                        self.strategy_id,
                        seed=seed,
                        benchmark_id=benchmark_id,
                    )
                )
        else:
            seen: set[str] = set()
            attempts = 0
            maximum_attempts = max(100, target * 100)
            while len(configurations) < target and attempts < maximum_attempts:
                attempts += 1
                parameters = self._random_parameters(search_space, rng)
                configuration = CandidateConfiguration.create(
                    parameters,
                    search_space,
                    self.strategy_id,
                    seed=seed,
                    benchmark_id=benchmark_id,
                )
                if configuration.fingerprint not in seen:
                    seen.add(configuration.fingerprint)
                    configurations.append(configuration)

        exhausted = total is not None and len(configurations) >= total
        return GenerationBatch(
            strategy_id=self.strategy_id,
            seed=seed,
            configurations=tuple(configurations),
            requested_count=requested,
            generated_count=len(configurations),
            total_possible=total,
            limit_applied=limit_applied,
            space_exhausted=exhausted,
            strategy_version=self.version,
        )

    @staticmethod
    def _sample_unique_indices(
        rng: random.Random,
        population: int,
        count: int,
    ) -> tuple[int, ...]:
        selected: set[int] = set()
        ordered: list[int] = []
        for boundary in range(population - count, population):
            choice = rng.randrange(boundary + 1)
            value = boundary if choice in selected else choice
            selected.add(value)
            ordered.append(value)
        rng.shuffle(ordered)
        return tuple(ordered)

    @staticmethod
    def _parameters_at(search_space: SearchSpace, index: int) -> dict[str, object]:
        dimensions = [
            parameter.grid_values() for parameter in search_space.parameters
        ]
        values: list[object] = [None] * len(dimensions)
        remaining = index
        for position in range(len(dimensions) - 1, -1, -1):
            dimension = dimensions[position]
            remaining, offset = divmod(remaining, len(dimension))
            values[position] = dimension[offset]
        return {
            parameter.name: values[position]
            for position, parameter in enumerate(search_space.parameters)
        }

    @staticmethod
    def _random_parameters(
        search_space: SearchSpace,
        rng: random.Random,
    ) -> dict[str, object]:
        values: dict[str, object] = {}
        for parameter in search_space.parameters:
            if parameter.kind == ParameterKind.INTEGER:
                minimum, maximum, step = parameter.integer_bounds()
                count = (maximum - minimum) // step + 1
                values[parameter.name] = minimum + rng.randrange(count) * step
            elif parameter.kind == ParameterKind.FLOAT:
                minimum, maximum, step = parameter.float_bounds()
                if step is not None or minimum == maximum:
                    choices = parameter.grid_values()
                    values[parameter.name] = choices[rng.randrange(len(choices))]
                else:
                    values[parameter.name] = rng.uniform(minimum, maximum)
            elif parameter.kind == ParameterKind.CATEGORICAL:
                values[parameter.name] = parameter.choices[
                    rng.randrange(len(parameter.choices))
                ]
            else:
                values[parameter.name] = parameter.fixed_value
        return values
