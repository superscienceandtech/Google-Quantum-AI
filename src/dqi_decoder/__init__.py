"""Research-only DQI mathematics; this package is not an official verifier adapter."""

from .field import (
    FIELD_DEGREE,
    FIELD_MODULUS_POLYNOMIAL,
    FIELD_SIZE,
    add,
    inverse,
    multiply,
    power,
    validate_element,
)
from .decoder import (
    DQI_MAX_CORRECTABLE_ERRORS,
    DecodedError,
    InvalidSyndrome,
    NoDecodingSolution,
    decode_error,
)
from .syndrome import (
    DQI_ERROR_SYMBOL_COUNT,
    DQI_SYNDROME_COUNT,
    compute_dqi_syndrome,
)

__all__ = [
    "DQI_ERROR_SYMBOL_COUNT",
    "DQI_MAX_CORRECTABLE_ERRORS",
    "DQI_SYNDROME_COUNT",
    "DecodedError",
    "FIELD_DEGREE",
    "FIELD_MODULUS_POLYNOMIAL",
    "FIELD_SIZE",
    "InvalidSyndrome",
    "NoDecodingSolution",
    "add",
    "compute_dqi_syndrome",
    "decode_error",
    "inverse",
    "multiply",
    "power",
    "validate_element",
]
