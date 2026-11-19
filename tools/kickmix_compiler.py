"""Bounded KMX v2 parser, validator, deterministic writer, and local CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from tools.participant_optimizer import optimize_adjacent_involutions


KMX_INPUT_BYTE_LIMIT = 16 * 1024 * 1024
MAX_COMPETITION_QUBIT_OR_BIT_ID = (1 << 30) // 1536
MAX_UPSTREAM_QUBIT_OR_BIT_ID = 500_000_000
MAX_LOCAL_REGISTERS = 10_000
_ID_PATTERN = re.compile(r"([qbr])([0-9]+)\Z")
_EXPONENT_PATTERN = re.compile(r"[+-]?[0-9]+\.[0-9]+\Z")
_OPCODE_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*\Z")


class WireKind(str, Enum):
    QUBIT = "q"
    BIT = "b"
    REGISTER = "r"


@dataclass(frozen=True)
class Wire:
    kind: WireKind
    index: int

    def __post_init__(self) -> None:
        if not isinstance(self.kind, WireKind):
            raise ValueError("wire kind must be a WireKind")
        if type(self.index) is not int or self.index < 0:
            raise ValueError("wire index must be a non-negative integer")
        if self.kind is WireKind.REGISTER:
            if self.index >= MAX_LOCAL_REGISTERS:
                raise ValueError(
                    f"register ID must be less than the local limit "
                    f"{MAX_LOCAL_REGISTERS}"
                )
        elif self.index >= MAX_UPSTREAM_QUBIT_OR_BIT_ID:
            raise ValueError(
                "qubit and bit IDs must be less than the pinned upstream limit "
                f"{MAX_UPSTREAM_QUBIT_OR_BIT_ID}"
            )

    def to_token(self) -> str:
        return f"{self.kind.value}{self.index}"


_FIXED_OPERANDS = {
    "X": (WireKind.QUBIT,),
    "CX": (WireKind.QUBIT, WireKind.QUBIT),
    "CCX": (WireKind.QUBIT, WireKind.QUBIT, WireKind.QUBIT),
    "Z": (WireKind.QUBIT,),
    "CZ": (WireKind.QUBIT, WireKind.QUBIT),
    "CCZ": (WireKind.QUBIT, WireKind.QUBIT, WireKind.QUBIT),
    "Z_POW": (WireKind.QUBIT,),
    "NEG": (),
    "SWAP": (WireKind.QUBIT, WireKind.QUBIT),
    "CSWAP": (WireKind.QUBIT, WireKind.QUBIT, WireKind.QUBIT),
    "R": (WireKind.QUBIT,),
    "HMR": (WireKind.QUBIT, WireKind.BIT),
    "BIT_INVERT": (WireKind.BIT,),
    "BIT_STORE0": (WireKind.BIT,),
    "BIT_STORE1": (WireKind.BIT,),
    "PUSH_CONDITION": (),
    "POP_CONDITION": (),
    "INFO_TAG": (),
}

_ALLOWED_OPCODES = frozenset(
    {
        *_FIXED_OPERANDS,
        "REGISTER",
        "APPEND_TO_REGISTER",
        "DEBUG_PRINT",
    }
)


def _validate_text(value: str, field_name: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError(f"{field_name} must contain ASCII characters only") from error


@dataclass(frozen=True)
class Instruction:
    opcode: str
    operands: Tuple[Wire, ...] = ()
    condition: Optional[int] = None
    exponent: Optional[str] = None
    text: Optional[str] = None

    def __post_init__(self) -> None:
        if type(self.opcode) is not str or not _OPCODE_PATTERN.fullmatch(self.opcode):
            raise ValueError("opcode must be an uppercase KMX instruction name")
        if self.opcode not in _ALLOWED_OPCODES:
            raise ValueError(f"unsupported KMX instruction: {self.opcode}")
        if type(self.operands) is not tuple or any(
            not isinstance(wire, Wire) for wire in self.operands
        ):
            raise ValueError("operands must be a tuple of Wire values")
        if self.condition is not None:
            Wire(WireKind.BIT, self.condition)
        if self.exponent is not None:
            if self.opcode != "Z_POW" or type(self.exponent) is not str:
                raise ValueError("only Z_POW may have a decimal exponent")
            if not _EXPONENT_PATTERN.fullmatch(self.exponent):
                raise ValueError("Z_POW exponent must be decimal without an exponent")
            try:
                if not Decimal(self.exponent).is_finite():
                    raise ValueError("Z_POW exponent must be finite")
            except InvalidOperation as error:
                raise ValueError("Z_POW exponent is not a valid decimal") from error
        if self.text is not None:
            if self.opcode not in {"REGISTER", "INFO_TAG"}:
                raise ValueError("quoted text is only supported by REGISTER and INFO_TAG")
            _validate_text(self.text, "quoted text")

        if self.opcode == "REGISTER":
            expected = (WireKind.REGISTER,)
            if self.condition is not None or self.exponent is not None:
                raise ValueError("REGISTER does not accept a condition or exponent")
        elif self.opcode == "APPEND_TO_REGISTER":
            expected = None
            if (
                len(self.operands) != 2
                or self.operands[0].kind not in {WireKind.QUBIT, WireKind.BIT}
                or self.operands[1].kind is not WireKind.REGISTER
                or self.condition is not None
                or self.exponent is not None
                or self.text is not None
            ):
                raise ValueError("APPEND_TO_REGISTER requires a qubit/bit and register")
        elif self.opcode == "DEBUG_PRINT":
            if (
                any(wire.kind is WireKind.REGISTER and wire.index >= MAX_LOCAL_REGISTERS
                    for wire in self.operands)
                or self.exponent is not None
                or self.text is not None
            ):
                raise ValueError("DEBUG_PRINT accepts only wire operands and a condition")
            expected = None
        elif self.opcode == "INFO_TAG":
            expected = ()
            if self.text is None or self.condition is not None or self.exponent is not None:
                raise ValueError("INFO_TAG requires quoted text and accepts no condition")
        else:
            expected = _FIXED_OPERANDS[self.opcode]
            if self.opcode == "Z_POW":
                if self.exponent is None:
                    raise ValueError("Z_POW requires an exponent")
            elif self.exponent is not None:
                raise ValueError(f"{self.opcode} does not accept an exponent")
            if self.opcode == "PUSH_CONDITION":
                if self.condition is None:
                    raise ValueError("PUSH_CONDITION requires a condition bit")
            elif self.opcode == "POP_CONDITION" and self.condition is not None:
                raise ValueError("POP_CONDITION does not accept a condition")

        if expected is not None and tuple(wire.kind for wire in self.operands) != expected:
            raise ValueError(
                f"{self.opcode} expects operands of kinds "
                f"{', '.join(kind.value for kind in expected) or '(none)'}"
            )
        if self.opcode not in {"REGISTER", "APPEND_TO_REGISTER", "INFO_TAG"}:
            if self.text is not None:
                raise ValueError(f"{self.opcode} does not accept quoted text")


@dataclass(frozen=True)
class Circuit:
    instructions: Tuple[Instruction, ...]

    def __post_init__(self) -> None:
        if type(self.instructions) is not tuple or any(
            not isinstance(instruction, Instruction) for instruction in self.instructions
        ):
            raise ValueError("instructions must be a tuple of Instruction values")
        for instruction in self.instructions:
            if instruction.opcode in {"CX", "CZ", "SWAP", "CCX", "CCZ", "CSWAP"}:
                qubit_ids = tuple(wire.index for wire in instruction.operands)
                if len(set(qubit_ids)) != len(qubit_ids):
                    raise ValueError(
                        f"{instruction.opcode} cannot repeat a qubit operand"
                    )
        _validate_register_metadata(self.instructions)


def _validate_register_metadata(instructions: Tuple[Instruction, ...]) -> int:
    max_register = -1
    names: dict[int, Optional[str]] = {}
    for instruction in instructions:
        if instruction.opcode == "REGISTER":
            register_id = instruction.operands[0].index
            max_register = max(max_register, register_id)
            names[register_id] = instruction.text
        elif instruction.opcode == "APPEND_TO_REGISTER":
            register_id = instruction.operands[1].index
            max_register = max(max_register, register_id)

    if max_register >= MAX_LOCAL_REGISTERS:
        raise ValueError(f"register count exceeds the local limit {MAX_LOCAL_REGISTERS}")
    named_registers: dict[str, int] = {}
    for register_id, name in names.items():
        if name:
            previous_id = named_registers.get(name)
            if previous_id is not None and previous_id != register_id:
                raise ValueError(f"duplicate register name: {name}")
            named_registers[name] = register_id
    return max_register + 1


def _validate_visible_metric_constraints(circuit: Circuit) -> None:
    register_names: dict[int, Optional[str]] = {}
    max_register = -1
    for instruction in circuit.instructions:
        if (
            instruction.condition is not None
            and instruction.condition >= MAX_COMPETITION_QUBIT_OR_BIT_ID
        ):
            raise KmxSyntaxError(
                "qubit and bit IDs exceed the visible metric limit "
                f"{MAX_COMPETITION_QUBIT_OR_BIT_ID}"
            )
        for wire in instruction.operands:
            if wire.kind in {WireKind.QUBIT, WireKind.BIT}:
                if wire.index >= MAX_COMPETITION_QUBIT_OR_BIT_ID:
                    raise KmxSyntaxError(
                        "qubit and bit IDs exceed the visible metric limit "
                        f"{MAX_COMPETITION_QUBIT_OR_BIT_ID}"
                    )
        if instruction.opcode == "REGISTER":
            register_id = instruction.operands[0].index
            max_register = max(max_register, register_id)
            register_names[register_id] = instruction.text
        elif instruction.opcode == "APPEND_TO_REGISTER":
            register_id = instruction.operands[1].index
            max_register = max(max_register, register_id)

    unnamed = [
        register_id
        for register_id in range(max_register + 1)
        if register_names.get(register_id) is None
    ]
    if unnamed:
        raise KmxSyntaxError(
            "every register must have a string name for the visible metric; "
            f"unnamed register IDs include {unnamed[:8]}"
        )


@dataclass(frozen=True)
class ResourceSummary:
    instruction_count: int
    qubit_count: int
    bit_count: int
    register_count: int
    opcode_counts: Tuple[Tuple[str, int], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "instruction_count": self.instruction_count,
            "qubit_count": self.qubit_count,
            "bit_count": self.bit_count,
            "register_count": self.register_count,
            "opcode_counts": dict(self.opcode_counts),
        }


@dataclass(frozen=True)
class CompilationOutcome:
    output_text: str
    input_sha256: str
    output_sha256: str
    before: ResourceSummary
    after: ResourceSummary
    canceled_pairs: int

    def to_dict(self) -> dict[str, object]:
        return {
            "input_sha256": self.input_sha256,
            "output_sha256": self.output_sha256,
            "canceled_pairs": self.canceled_pairs,
            "resources_before": self.before.to_dict(),
            "resources_after": self.after.to_dict(),
            "compiler": "local-kmx-v2-core",
            "compiler_version": "1",
        }


class KmxSyntaxError(ValueError):
    def __init__(self, message: str, line_number: Optional[int] = None) -> None:
        self.line_number = line_number
        prefix = f"line {line_number}: " if line_number is not None else ""
        super().__init__(prefix + message)


class _OutputPublicationUncertain(OSError):
    pass


@dataclass(frozen=True)
class _Token:
    value: str
    quoted: bool = False


def _lex_line(line: str, line_number: int) -> Tuple[_Token, ...]:
    tokens = []
    position = 0
    while position < len(line):
        while position < len(line) and line[position] in " \t":
            position += 1
        if position >= len(line) or line[position] == "#":
            break
        if line[position] == '"':
            position += 1
            characters = []
            while position < len(line) and line[position] != '"':
                character = line[position]
                if ord(character) > 127:
                    raise KmxSyntaxError(
                        "non-ASCII characters are only allowed in comments", line_number
                    )
                if character == "#":
                    raise KmxSyntaxError(
                        "a pound sign in quoted text must be escaped as \\P", line_number
                    )
                if character == "\\":
                    position += 1
                    if position >= len(line):
                        raise KmxSyntaxError("incomplete quoted-text escape", line_number)
                    escapes = {
                        "B": "\\",
                        "Q": '"',
                        "P": "#",
                        "n": "\n",
                        "r": "\r",
                    }
                    escaped = escapes.get(line[position])
                    if escaped is None:
                        raise KmxSyntaxError("unknown quoted-text escape", line_number)
                    characters.append(escaped)
                else:
                    characters.append(character)
                position += 1
            if position >= len(line):
                raise KmxSyntaxError("unterminated quoted text", line_number)
            position += 1
            if position < len(line) and line[position] not in " \t#":
                raise KmxSyntaxError("quoted text must be a complete token", line_number)
            tokens.append(_Token("".join(characters), True))
            continue

        start = position
        while position < len(line) and line[position] not in " \t#":
            if line[position] == '"':
                raise KmxSyntaxError("quoted text must begin at a token boundary", line_number)
            position += 1
        tokens.append(_Token(line[start:position]))
        if position < len(line) and line[position] == "#":
            break
    return tuple(tokens)


def _parse_wire(token: _Token, line_number: int) -> Wire:
    if token.quoted:
        raise KmxSyntaxError("wire IDs must be unquoted", line_number)
    match = _ID_PATTERN.fullmatch(token.value)
    if match is None:
        raise KmxSyntaxError(f"invalid wire ID: {token.value!r}", line_number)
    prefix, digits = match.groups()
    try:
        index = int(digits, 10)
        kind = WireKind(prefix)
        return Wire(kind, index)
    except (ValueError, OverflowError) as error:
        raise KmxSyntaxError(str(error), line_number) from error


def _parse_exponent(token: _Token, line_number: int) -> str:
    if token.quoted or not _EXPONENT_PATTERN.fullmatch(token.value):
        raise KmxSyntaxError(
            "Z_POW exponent must be decimal without scientific notation", line_number
        )
    try:
        if not Decimal(token.value).is_finite():
            raise KmxSyntaxError("Z_POW exponent must be finite", line_number)
    except InvalidOperation as error:
        raise KmxSyntaxError("Z_POW exponent is not a valid decimal", line_number) from error
    return token.value


def _parse_instruction(tokens: Tuple[_Token, ...], line_number: int) -> Instruction:
    opcode_token, *rest = tokens
    if opcode_token.quoted or not _OPCODE_PATTERN.fullmatch(opcode_token.value):
        raise KmxSyntaxError("invalid instruction name", line_number)
    opcode = opcode_token.value
    if opcode not in _ALLOWED_OPCODES:
        raise KmxSyntaxError(f"unsupported KMX instruction: {opcode}", line_number)

    if opcode == "INFO_TAG":
        if len(rest) != 1 or not rest[0].quoted:
            raise KmxSyntaxError("INFO_TAG requires exactly one quoted text value", line_number)
        return Instruction(opcode, text=rest[0].value)

    if opcode == "REGISTER":
        if len(rest) not in (1, 2) or (len(rest) == 2 and not rest[1].quoted):
            raise KmxSyntaxError(
                "REGISTER requires a register ID and optional quoted name", line_number
            )
        register = _parse_wire(rest[0], line_number)
        if register.kind is not WireKind.REGISTER:
            raise KmxSyntaxError("REGISTER requires a register ID", line_number)
        return Instruction(
            opcode, (register,), text=rest[1].value if len(rest) == 2 else None
        )

    if opcode == "APPEND_TO_REGISTER":
        if len(rest) != 2:
            raise KmxSyntaxError("APPEND_TO_REGISTER requires a wire and register ID", line_number)
        wire = _parse_wire(rest[0], line_number)
        register = _parse_wire(rest[1], line_number)
        if wire.kind is WireKind.REGISTER or register.kind is not WireKind.REGISTER:
            raise KmxSyntaxError(
                "APPEND_TO_REGISTER requires a qubit/bit followed by a register ID",
                line_number,
            )
        return Instruction(opcode, (wire, register))

    condition: Optional[int] = None
    if len(rest) >= 2 and not rest[-2].quoted and rest[-2].value == "if":
        condition_wire = _parse_wire(rest[-1], line_number)
        if condition_wire.kind is not WireKind.BIT:
            raise KmxSyntaxError("condition must be a bit ID", line_number)
        condition = condition_wire.index
        rest = rest[:-2]
    elif any(not token.quoted and token.value == "if" for token in rest):
        raise KmxSyntaxError("condition must be the final 'if bN' pair", line_number)

    if opcode == "DEBUG_PRINT":
        wires = tuple(_parse_wire(token, line_number) for token in rest)
        return Instruction(opcode, wires, condition=condition)

    if opcode == "PUSH_CONDITION" and condition is None:
        raise KmxSyntaxError("PUSH_CONDITION requires 'if bN'", line_number)
    if opcode == "Z_POW":
        if len(rest) != 2:
            raise KmxSyntaxError("Z_POW requires one qubit and one exponent", line_number)
        wire = _parse_wire(rest[0], line_number)
        exponent = _parse_exponent(rest[1], line_number)
        return Instruction(opcode, (wire,), condition=condition, exponent=exponent)

    wires = tuple(_parse_wire(token, line_number) for token in rest)
    try:
        return Instruction(opcode, wires, condition=condition)
    except ValueError as error:
        raise KmxSyntaxError(str(error), line_number) from error


def parse_kmx(text: str) -> Circuit:
    if type(text) is not str:
        raise TypeError("KMX input must be text")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise KmxSyntaxError("KMX input is not valid UTF-8 text") from error
    if len(encoded) > KMX_INPUT_BYTE_LIMIT:
        raise KmxSyntaxError(
            f"KMX input exceeds the local {KMX_INPUT_BYTE_LIMIT}-byte limit"
        )

    instructions = []
    for line_number, line in enumerate(re.split(r"\r\n|\n|\r", text), start=1):
        tokens = _lex_line(line, line_number)
        if tokens:
            try:
                instructions.append(_parse_instruction(tokens, line_number))
            except KmxSyntaxError:
                raise
            except ValueError as error:
                raise KmxSyntaxError(str(error), line_number) from error
    try:
        return Circuit(tuple(instructions))
    except ValueError as error:
        raise KmxSyntaxError(str(error)) from error


def _quote_text(value: str) -> str:
    _validate_text(value, "quoted text")
    escaped = (
        value.replace("\\", "\\B")
        .replace('"', "\\Q")
        .replace("#", "\\P")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def _instruction_to_line(instruction: Instruction) -> str:
    opcode = instruction.opcode
    if opcode == "INFO_TAG":
        return f"INFO_TAG {_quote_text(instruction.text or '')}"
    if opcode == "REGISTER":
        line = f"REGISTER {instruction.operands[0].to_token()}"
        if instruction.text is not None:
            line += f" {_quote_text(instruction.text)}"
        return line
    parts = [opcode]
    parts.extend(wire.to_token() for wire in instruction.operands)
    if instruction.exponent is not None:
        parts.append(instruction.exponent)
    if instruction.condition is not None:
        parts.extend(("if", f"b{instruction.condition}"))
    return " ".join(parts)


def serialize_kmx(circuit: Circuit) -> str:
    if not isinstance(circuit, Circuit):
        raise TypeError("circuit must be a Circuit")
    if not circuit.instructions:
        return ""
    return "\n".join(_instruction_to_line(item) for item in circuit.instructions) + "\n"


def summarize_resources(circuit: Circuit) -> ResourceSummary:
    counts: dict[str, int] = {}
    max_qubit = -1
    max_bit = -1
    register_count = 0
    for instruction in circuit.instructions:
        counts[instruction.opcode] = counts.get(instruction.opcode, 0) + 1
        if instruction.opcode == "REGISTER":
            register_count = max(register_count, instruction.operands[0].index + 1)
        elif instruction.opcode == "APPEND_TO_REGISTER":
            register_count = max(register_count, instruction.operands[1].index + 1)
        if instruction.condition is not None:
            max_bit = max(max_bit, instruction.condition)
        for wire in instruction.operands:
            if wire.kind is WireKind.QUBIT:
                max_qubit = max(max_qubit, wire.index)
            elif wire.kind is WireKind.BIT:
                max_bit = max(max_bit, wire.index)
    return ResourceSummary(
        instruction_count=len(circuit.instructions),
        qubit_count=max_qubit + 1,
        bit_count=max_bit + 1,
        register_count=register_count,
        opcode_counts=tuple(sorted(counts.items())),
    )


def compile_kmx(text: str, *, optimize: bool = True) -> CompilationOutcome:
    source_circuit = parse_kmx(text)
    _validate_visible_metric_constraints(source_circuit)
    source_bytes = text.encode("utf-8")
    before = summarize_resources(source_circuit)
    if optimize:
        optimized, canceled_pairs = optimize_adjacent_involutions(source_circuit)
    else:
        optimized, canceled_pairs = source_circuit, 0
    output_text = serialize_kmx(optimized)
    output_bytes = output_text.encode("ascii")
    return CompilationOutcome(
        output_text=output_text,
        input_sha256=hashlib.sha256(source_bytes).hexdigest(),
        output_sha256=hashlib.sha256(output_bytes).hexdigest(),
        before=before,
        after=summarize_resources(optimized),
        canceled_pairs=canceled_pairs,
    )


def _read_kmx_path(path: Path) -> str:
    if not hasattr(os, "O_NOFOLLOW"):
        raise OSError("safe no-follow input opening is unavailable on this platform")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("input must be a regular file")
        initial_identity = (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        )
        if metadata.st_size > KMX_INPUT_BYTE_LIMIT:
            raise ValueError(
                f"input exceeds the local {KMX_INPUT_BYTE_LIMIT}-byte limit"
            )
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, KMX_INPUT_BYTE_LIMIT + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > KMX_INPUT_BYTE_LIMIT:
                raise ValueError(
                    f"input exceeds the local {KMX_INPUT_BYTE_LIMIT}-byte limit"
                )
            chunks.append(chunk)
        final_metadata = os.fstat(descriptor)
        final_identity = (
            final_metadata.st_dev,
            final_metadata.st_ino,
            final_metadata.st_size,
            final_metadata.st_mtime_ns,
            final_metadata.st_ctime_ns,
        )
        if final_identity != initial_identity:
            raise ValueError("input changed while it was being read")
        return b"".join(chunks).decode("utf-8", errors="strict")
    finally:
        os.close(descriptor)


def _write_exclusive(path: Path, content: bytes) -> None:
    if not path.name or path.name in {".", ".."}:
        raise ValueError("output must name a file")
    temporary_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent or Path(".")
    )
    published = False
    temporary_exists = True
    try:
        with os.fdopen(temporary_descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary_name, path)
        published = True
        os.unlink(temporary_name)
        temporary_exists = False
        directory_descriptor = os.open(
            path.parent or Path("."),
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as error:
        if published:
            raise _OutputPublicationUncertain(
                f"output may already be published; verify it before retrying: {error}"
            ) from error
        raise
    finally:
        if temporary_exists:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            except OSError as error:
                if published:
                    raise _OutputPublicationUncertain(
                        f"output may already be published; temporary cleanup failed: {error}"
                    ) from error
                raise


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate and optimize a KMX v2 circuit into deterministic KMX text."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="validate and serialize without applying local optimization",
    )
    arguments = parser.parse_args(argv)
    try:
        source = _read_kmx_path(arguments.input)
        outcome = compile_kmx(source, optimize=not arguments.no_optimize)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"compilation failed: {error}", file=sys.stderr)
        return 2

    try:
        _write_exclusive(arguments.output, outcome.output_text.encode("ascii"))
    except (OSError, ValueError) as error:
        print(f"output publication failed: {error}", file=sys.stderr)
        return 3

    print(json.dumps(outcome.to_dict(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.modules.setdefault("tools.kickmix_compiler", sys.modules[__name__])
    raise SystemExit(main())
