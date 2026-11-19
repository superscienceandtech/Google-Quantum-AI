from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
import math
from math import prod
from typing import Any, Mapping, TypeGuard


class ParameterKind(str, Enum):
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    CATEGORICAL = "CATEGORICAL"
    FIXED = "FIXED"


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("Value must be JSON serializable without NaN or infinity") from exc


def _is_json_scalar(value: Any) -> bool:
    return value is None or type(value) in (str, bool, int) or (
        type(value) is float and math.isfinite(value)
    )


def _is_integer(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> TypeGuard[int | float]:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


@dataclass(frozen=True)
class ParameterDefinition:
    name: str
    kind: ParameterKind
    minimum: int | float | None = None
    maximum: int | float | None = None
    step: int | float | None = None
    choices: tuple[Any, ...] = ()
    fixed_value: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name or self.name.strip() != self.name:
            raise ValueError("Parameter name must be a non-empty trimmed string")
        try:
            kind = self.kind if isinstance(self.kind, ParameterKind) else ParameterKind(self.kind)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Unsupported parameter kind: {self.kind}") from exc
        object.__setattr__(self, "kind", kind)
        if not isinstance(self.choices, tuple):
            object.__setattr__(self, "choices", tuple(self.choices))

        if kind == ParameterKind.INTEGER:
            minimum = self.minimum
            maximum = self.maximum
            step = self.step
            if not _is_integer(minimum) or not _is_integer(maximum):
                raise ValueError(f"{self.name}: integer bounds are required")
            if minimum > maximum:
                raise ValueError(f"{self.name}: minimum exceeds maximum")
            if not _is_integer(step) or step <= 0:
                raise ValueError(f"{self.name}: integer step must be positive")
            self._reject_unused(choices=bool(self.choices), fixed=self.fixed_value is not None)
        elif kind == ParameterKind.FLOAT:
            minimum = self.minimum
            maximum = self.maximum
            step = self.step
            if not _is_finite_number(minimum) or not _is_finite_number(maximum):
                raise ValueError(f"{self.name}: finite float bounds are required")
            if minimum > maximum:
                raise ValueError(f"{self.name}: minimum exceeds maximum")
            if step is not None:
                if not _is_finite_number(step) or step <= 0:
                    raise ValueError(f"{self.name}: float step must be positive")
                object.__setattr__(self, "step", float(step))
            object.__setattr__(self, "minimum", float(minimum))
            object.__setattr__(self, "maximum", float(maximum))
            self._reject_unused(choices=bool(self.choices), fixed=self.fixed_value is not None)
        elif kind == ParameterKind.CATEGORICAL:
            if not self.choices:
                raise ValueError(f"{self.name}: categorical choices cannot be empty")
            if any(not _is_json_scalar(choice) for choice in self.choices):
                raise ValueError(f"{self.name}: choices must be finite JSON scalars")
            encoded = [canonical_json([type(choice).__name__, choice]) for choice in self.choices]
            if len(set(encoded)) != len(encoded):
                raise ValueError(f"{self.name}: categorical choices must be unique")
            self._reject_unused(
                bounds=self.minimum is not None or self.maximum is not None,
                step=self.step is not None,
                fixed=self.fixed_value is not None,
            )
        else:
            if not _is_json_scalar(self.fixed_value):
                raise ValueError(f"{self.name}: fixed value must be a finite JSON scalar")
            self._reject_unused(
                bounds=self.minimum is not None or self.maximum is not None,
                step=self.step is not None,
                choices=bool(self.choices),
            )

    def _reject_unused(
        self,
        *,
        bounds: bool = False,
        step: bool = False,
        choices: bool = False,
        fixed: bool = False,
    ) -> None:
        if bounds:
            raise ValueError(f"{self.name}: bounds are not valid for {self.kind.value}")
        if step:
            raise ValueError(f"{self.name}: step is not valid for {self.kind.value}")
        if choices:
            raise ValueError(f"{self.name}: choices are not valid for {self.kind.value}")
        if fixed:
            raise ValueError(f"{self.name}: fixed_value is not valid for {self.kind.value}")

    def validate_value(self, value: Any) -> Any:
        if self.kind == ParameterKind.INTEGER:
            if not _is_integer(value):
                raise ValueError(f"{self.name} must be an integer")
            minimum = self.minimum
            maximum = self.maximum
            step = self.step
            if not _is_integer(minimum) or not _is_integer(maximum) or not _is_integer(step):
                raise ValueError(f"{self.name} has invalid integer bounds")
            if value < minimum or value > maximum:
                raise ValueError(f"{self.name} is outside declared bounds")
            if (value - minimum) % step != 0:
                raise ValueError(f"{self.name} does not align with declared step")
            return value

        if self.kind == ParameterKind.FLOAT:
            if not _is_finite_number(value):
                raise ValueError(f"{self.name} must be a finite number")
            normalized = float(value)
            minimum = self.minimum
            maximum = self.maximum
            if not _is_finite_number(minimum) or not _is_finite_number(maximum):
                raise ValueError(f"{self.name} has invalid float bounds")
            if normalized < minimum or normalized > maximum:
                raise ValueError(f"{self.name} is outside declared bounds")
            if self.step is not None:
                offset = (
                    Decimal(str(normalized)) - Decimal(str(minimum))
                ) / Decimal(str(self.step))
                if offset != offset.to_integral_value():
                    raise ValueError(f"{self.name} does not align with declared step")
            return normalized

        if self.kind == ParameterKind.CATEGORICAL:
            if not any(
                type(value) is type(choice) and value == choice
                for choice in self.choices
            ):
                raise ValueError(f"{self.name} is not an allowed categorical value")
            return value

        if type(value) is not type(self.fixed_value) or value != self.fixed_value:
            raise ValueError(f"{self.name} must equal its fixed value")
        return value

    def grid_values(self) -> tuple[Any, ...]:
        if self.kind == ParameterKind.INTEGER:
            minimum, maximum, step = self.integer_bounds()
            return tuple(range(minimum, maximum + 1, step))
        if self.kind == ParameterKind.FLOAT:
            minimum, maximum, step = self.float_bounds()
            if step is None:
                if minimum == maximum:
                    return (minimum,)
                raise ValueError(f"{self.name}: continuous floats have no grid values")
            low = Decimal(str(minimum))
            high = Decimal(str(maximum))
            decimal_step = Decimal(str(step))
            count = int((high - low) // decimal_step) + 1
            return tuple(float(low + decimal_step * index) for index in range(count))
        if self.kind == ParameterKind.CATEGORICAL:
            return self.choices
        return (self.fixed_value,)

    def integer_bounds(self) -> tuple[int, int, int]:
        if (
            self.kind != ParameterKind.INTEGER
            or not _is_integer(self.minimum)
            or not _is_integer(self.maximum)
            or not _is_integer(self.step)
        ):
            raise ValueError(f"{self.name} does not define integer bounds")
        return self.minimum, self.maximum, self.step

    def float_bounds(self) -> tuple[float, float, float | None]:
        if (
            self.kind != ParameterKind.FLOAT
            or not _is_finite_number(self.minimum)
            or not _is_finite_number(self.maximum)
        ):
            raise ValueError(f"{self.name} does not define float bounds")
        minimum = float(self.minimum)
        maximum = float(self.maximum)
        step = float(self.step) if self.step is not None else None
        return minimum, maximum, step

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"name": self.name, "kind": self.kind.value}
        if self.kind in (ParameterKind.INTEGER, ParameterKind.FLOAT):
            data.update(
                {
                    "minimum": self.minimum,
                    "maximum": self.maximum,
                    "step": self.step,
                }
            )
        elif self.kind == ParameterKind.CATEGORICAL:
            data["choices"] = list(self.choices)
        else:
            data["fixed_value"] = self.fixed_value
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ParameterDefinition":
        return cls(**dict(data))


@dataclass(frozen=True)
class SearchSpace:
    parameters: tuple[ParameterDefinition, ...]
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if not isinstance(self.parameters, tuple):
            object.__setattr__(self, "parameters", tuple(self.parameters))
        if not self.parameters:
            raise ValueError("Search space must contain at least one parameter")
        if not all(isinstance(item, ParameterDefinition) for item in self.parameters):
            raise ValueError("Search-space entries must be ParameterDefinition objects")
        names = [item.name for item in self.parameters]
        if len(set(names)) != len(names):
            raise ValueError("Search-space parameter names must be unique")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ValueError("schema_version is required")

    def validate(self, values: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(values, Mapping):
            raise ValueError("Parameter values must be a mapping")
        expected = {item.name for item in self.parameters}
        missing = expected - set(values)
        unknown = set(values) - expected
        if missing:
            raise ValueError(f"Missing parameters: {sorted(missing)}")
        if unknown:
            raise ValueError(f"Unknown parameters: {sorted(unknown)}")
        return {
            definition.name: definition.validate_value(values[definition.name])
            for definition in self.parameters
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "parameters": [parameter.to_dict() for parameter in self.parameters],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SearchSpace":
        return cls(
            parameters=tuple(
                ParameterDefinition.from_dict(item) for item in data["parameters"]
            ),
            schema_version=data["schema_version"],
        )

    @property
    def search_space_id(self) -> str:
        digest = hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()
        return f"search-space:{digest}"

    @property
    def finite_configuration_count(self) -> int | None:
        if any(
            parameter.kind == ParameterKind.FLOAT
            and parameter.step is None
            and parameter.minimum != parameter.maximum
            for parameter in self.parameters
        ):
            return None
        return prod(len(parameter.grid_values()) for parameter in self.parameters)
