import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.kickmix_compiler import (
    MAX_COMPETITION_QUBIT_OR_BIT_ID,
    MAX_UPSTREAM_QUBIT_OR_BIT_ID,
    Circuit,
    KmxSyntaxError,
    Wire,
    WireKind,
    compile_kmx,
    main,
    parse_kmx,
    serialize_kmx,
    summarize_resources,
)
from tools.participant_optimizer import cancel_adjacent_involutions


def simulate_reversible_phase(circuit, qubit_state, bit_state):
    qubits = list(qubit_state)
    bits = list(bit_state)
    phase = 0
    condition_stack = []

    for instruction in circuit.instructions:
        opcode = instruction.opcode
        if opcode == "PUSH_CONDITION":
            condition_stack.append(bool(bits[instruction.condition]))
            continue
        if opcode == "POP_CONDITION":
            if condition_stack:
                condition_stack.pop()
            continue
        if opcode in {"REGISTER", "APPEND_TO_REGISTER", "INFO_TAG", "DEBUG_PRINT"}:
            continue
        if not all(condition_stack):
            continue
        if instruction.condition is not None and not bits[instruction.condition]:
            continue
        qubits_used = [wire.index for wire in instruction.operands if wire.kind is WireKind.QUBIT]
        if opcode == "X":
            qubits[qubits_used[0]] ^= 1
        elif opcode == "CX":
            control, target = qubits_used
            qubits[target] ^= qubits[control]
        elif opcode == "CCX":
            control_a, control_b, target = qubits_used
            qubits[target] ^= qubits[control_a] & qubits[control_b]
        elif opcode == "Z":
            phase ^= qubits[qubits_used[0]]
        elif opcode == "CZ":
            phase ^= qubits[qubits_used[0]] & qubits[qubits_used[1]]
        elif opcode == "CCZ":
            phase ^= qubits[qubits_used[0]] & qubits[qubits_used[1]] & qubits[qubits_used[2]]
        elif opcode == "NEG":
            phase ^= 1
        elif opcode == "SWAP":
            left, right = qubits_used
            qubits[left], qubits[right] = qubits[right], qubits[left]
        elif opcode == "CSWAP":
            control, left, right = qubits_used
            if qubits[control]:
                qubits[left], qubits[right] = qubits[right], qubits[left]
        elif opcode == "BIT_INVERT":
            target = instruction.operands[0].index
            bits[target] ^= 1
        elif opcode == "BIT_STORE0":
            bits[instruction.operands[0].index] = 0
        elif opcode == "BIT_STORE1":
            bits[instruction.operands[0].index] = 1
    return tuple(qubits), tuple(bits), phase


class KickmixCompilerTests(unittest.TestCase):
    def test_round_trip_all_supported_instruction_families(self):
        source = (
            '# Unicode in comments is permitted: \u03bb\n'
            'REGISTER r0 "state\\Pmain"\n'
            "APPEND_TO_REGISTER q0 r0\n"
            'REGISTER r1 "classical"\n'
            "APPEND_TO_REGISTER b0 r1\n"
            "X q0 if b0\n"
            "CX q0 q1\n"
            "CCX q0 q1 q2\n"
            "Z q2\n"
            "CZ q0 q1\n"
            "CCZ q0 q1 q2\n"
            "Z_POW q2 0.500000000000000000000000000000000000005\n"
            "NEG if b0\n"
            "SWAP q0 q1\n"
            "CSWAP q0 q1 q2\n"
            "R q0\n"
            "HMR q0 b1 if b0\n"
            "BIT_INVERT b0\n"
            "BIT_STORE0 b1 if b0\n"
            "BIT_STORE1 b1\n"
            "PUSH_CONDITION if b0\n"
            "POP_CONDITION\n"
            'INFO_TAG "tag\\Qquoted\\Bslash\\Pmark\\nline"\n'
            "DEBUG_PRINT q0 b0 r0 if b1\n"
            "DEBUG_PRINT\n"
        )

        circuit = parse_kmx(source)
        canonical = serialize_kmx(circuit)
        self.assertEqual(parse_kmx(canonical), circuit)
        self.assertIn('REGISTER r0 "state\\Pmain"\n', canonical)
        self.assertIn(
            'INFO_TAG "tag\\Qquoted\\Bslash\\Pmark\\nline"\n', canonical
        )
        self.assertIn(
            "Z_POW q2 0.500000000000000000000000000000000000005\n", canonical
        )
        self.assertNotIn("\u03bb", canonical)

    def test_comments_and_line_endings_are_nonsemantic(self):
        circuit = parse_kmx("X q0 # first\r\n\n\tZ q1\r")
        self.assertEqual(
            serialize_kmx(circuit),
            "X q0\nZ q1\n",
        )

    def test_rejects_bad_syntax_and_unsupported_instructions_with_line(self):
        for source in (
            "UNKNOWN q0\n",
            "CX q0\n",
            "HMR q0 q1\n",
            "Z_POW q0 1e-3\n",
            'INFO_TAG "a#b"\n',
            'INFO_TAG "bad\\xescape"\n',
            "X q0 if q1\n",
            "PUSH_CONDITION b0\n",
            "POP_CONDITION if b0\n",
        ):
            with self.subTest(source=source), self.assertRaises(KmxSyntaxError):
                parse_kmx(source)

        with self.assertRaisesRegex(KmxSyntaxError, "line 2"):
            parse_kmx("# comment\nCX q0\n")

    def test_registers_support_sparse_ids_unnamed_entries_and_upstream_overwrite(self):
        source = (
            "APPEND_TO_REGISTER q0 r2\n"
            "REGISTER r2\n"
            'REGISTER r2 "state"\n'
            'REGISTER r4 "other"\n'
        )
        circuit = parse_kmx(source)
        self.assertEqual(serialize_kmx(circuit), source)
        self.assertEqual(summarize_resources(circuit).register_count, 5)
        with self.assertRaisesRegex(KmxSyntaxError, "every register"):
            compile_kmx(source)

    def test_register_names_must_be_unique_when_nonempty(self):
        with self.assertRaisesRegex(KmxSyntaxError, "duplicate register name"):
            parse_kmx('REGISTER r0 "state"\nREGISTER r1 "state"\n')

    def test_metric_profile_uses_final_name_for_redeclared_register(self):
        source = 'REGISTER r0 "before"\nREGISTER r0 "after"\nX q0\n'
        self.assertEqual(compile_kmx(source, optimize=False).output_text, source)

        self.assertEqual(
            Wire(WireKind.QUBIT, MAX_COMPETITION_QUBIT_OR_BIT_ID).index,
            MAX_COMPETITION_QUBIT_OR_BIT_ID,
        )
        self.assertEqual(
            parse_kmx(f"X q{MAX_COMPETITION_QUBIT_OR_BIT_ID}\n").instructions[0].operands[0].index,
            MAX_COMPETITION_QUBIT_OR_BIT_ID,
        )
        with self.assertRaises(KmxSyntaxError):
            compile_kmx(f"X q{MAX_COMPETITION_QUBIT_OR_BIT_ID}\n")
        with self.assertRaises(KmxSyntaxError):
            compile_kmx(f"X q0 if b{MAX_COMPETITION_QUBIT_OR_BIT_ID}\n")
        with self.assertRaises(ValueError):
            Wire(WireKind.QUBIT, MAX_UPSTREAM_QUBIT_OR_BIT_ID)

    def test_resource_summary_counts_typed_ids_and_metadata(self):
        circuit = parse_kmx(
            'REGISTER r0 "state"\n'
            "APPEND_TO_REGISTER q3 r0\n"
            "X q7 if b4\n"
            "DEBUG_PRINT r0\n"
        )

        summary = summarize_resources(circuit)
        self.assertEqual(summary.qubit_count, 8)
        self.assertEqual(summary.bit_count, 5)
        self.assertEqual(summary.register_count, 1)
        self.assertEqual(summary.instruction_count, 4)
        self.assertEqual(dict(summary.opcode_counts)["X"], 1)
        self.assertEqual(summarize_resources(parse_kmx("DEBUG_PRINT r7\n")).register_count, 0)

    def test_optimizer_preserves_semantics_exhaustively_on_supported_subset(self):
        source = (
            "X q0\nX q0\n"
            "CX q0 q1 if b0\nCX q0 q1 if b0\n"
            "CCX q0 q1 q2\nCCX q0 q1 q2\n"
            "Z q2\nZ q2\n"
            "CZ q0 q2 if b1\nCZ q0 q2 if b1\n"
            "CCZ q0 q1 q2\nCCZ q0 q1 q2\n"
            "SWAP q0 q1\nSWAP q0 q1\n"
            "CSWAP q0 q1 q2 if b1\nCSWAP q0 q1 q2 if b1\n"
            "NEG if b0\nNEG if b0\n"
            "BIT_INVERT b1 if b0\nBIT_INVERT b1 if b0\n"
            "BIT_INVERT b0 if b0\nBIT_INVERT b0 if b0\n"
        )
        original = parse_kmx(source)
        result = cancel_adjacent_involutions(original)

        self.assertEqual(result.canceled_pairs, 10)
        self.assertEqual(len(result.circuit.instructions), 2)
        for qubit_value in range(8):
            qubits = tuple((qubit_value >> bit) & 1 for bit in range(3))
            for classical_value in range(4):
                bits = tuple((classical_value >> bit) & 1 for bit in range(2))
                self.assertEqual(
                    simulate_reversible_phase(original, qubits, bits),
                    simulate_reversible_phase(result.circuit, qubits, bits),
                )

    def test_optimizer_does_not_cancel_self_conditioned_bit_invert(self):
        circuit = parse_kmx("BIT_INVERT b0 if b0\nBIT_INVERT b0 if b0\n")
        result = cancel_adjacent_involutions(circuit)
        self.assertEqual(result.canceled_pairs, 0)
        self.assertEqual(len(result.circuit.instructions), 2)
        self.assertNotEqual(
            simulate_reversible_phase(circuit, (), (1,)),
            simulate_reversible_phase(Circuit(()), (), (1,)),
        )

    def test_optimizer_does_not_cancel_across_metadata(self):
        circuit = parse_kmx(
            'REGISTER r0 "state"\n'
            "X q0\n"
            'INFO_TAG "boundary"\n'
            "X q0\n"
            'INFO_TAG "condition-boundary"\n'
            "X q0\n"
            "PUSH_CONDITION if b0\n"
            "POP_CONDITION\n"
            "X q0\n"
        )
        result = cancel_adjacent_involutions(circuit)
        self.assertEqual(result.canceled_pairs, 0)
        self.assertEqual(len(result.circuit.instructions), len(circuit.instructions))

    def test_parser_rejects_repeated_multi_qubit_operands(self):
        for source in ("CX q1 q1\n", "CCX q0 q1 q0\n", "CSWAP q0 q1 q1\n"):
            with self.subTest(source=source), self.assertRaisesRegex(
                KmxSyntaxError, "cannot repeat a qubit operand"
            ):
                parse_kmx(source)

    def test_optimizer_respects_condition_stack_snapshot_semantics(self):
        circuit = parse_kmx(
            "PUSH_CONDITION if b0\n"
            "BIT_STORE0 b0\n"
            "X q0\n"
            "POP_CONDITION\n"
            "POP_CONDITION\n"
        )
        for initial_bit in (0, 1):
            self.assertEqual(
                simulate_reversible_phase(circuit, (0,), (initial_bit,)),
                ((initial_bit,), (0,), 0),
            )

        nested = parse_kmx(
            "PUSH_CONDITION if b0\n"
            "PUSH_CONDITION if b1\n"
            "X q0 if b2\n"
            "POP_CONDITION\n"
            "POP_CONDITION\n"
        )
        optimized_nested = cancel_adjacent_involutions(nested)
        self.assertEqual(optimized_nested.canceled_pairs, 0)
        for classical_value in range(8):
            bits = tuple((classical_value >> bit) & 1 for bit in range(3))
            for initial_qubit in (0, 1):
                expected = initial_qubit ^ (bits[0] & bits[1] & bits[2])
                self.assertEqual(
                    simulate_reversible_phase(nested, (initial_qubit,), bits),
                    simulate_reversible_phase(
                        optimized_nested.circuit, (initial_qubit,), bits
                    ),
                )
                self.assertEqual(
                    simulate_reversible_phase(nested, (initial_qubit,), bits)[0],
                    (expected,),
                )

        cancelable = parse_kmx(
            "PUSH_CONDITION if b0\n"
            "X q0\n"
            "X q0\n"
            "POP_CONDITION\n"
        )
        optimized = cancel_adjacent_involutions(cancelable)
        self.assertEqual(optimized.canceled_pairs, 1)
        for initial_bit in (0, 1):
            for initial_qubit in (0, 1):
                self.assertEqual(
                    simulate_reversible_phase(cancelable, (initial_qubit,), (initial_bit,)),
                    simulate_reversible_phase(
                        optimized.circuit, (initial_qubit,), (initial_bit,)
                    ),
                )

    def test_optimizer_never_cancels_reset_or_measurement_boundaries(self):
        circuit = parse_kmx(
            "R q0\n"
            "R q0\n"
            "HMR q0 b0\n"
            "HMR q0 b0\n"
        )
        result = cancel_adjacent_involutions(circuit)
        self.assertEqual(result.canceled_pairs, 0)
        self.assertEqual(result.circuit, circuit)

    def test_compile_is_deterministic_and_reports_provenance(self):
        source = 'REGISTER r0 "state"\nAPPEND_TO_REGISTER q0 r0\nX q0\nX q0\n'
        first = compile_kmx(source)
        second = compile_kmx(source)
        self.assertEqual(first, second)
        self.assertEqual(first.canceled_pairs, 1)
        self.assertEqual(first.after.instruction_count, 2)
        self.assertEqual(
            first.output_sha256,
            __import__("hashlib").sha256(first.output_text.encode("ascii")).hexdigest(),
        )
        self.assertEqual(
            compile_kmx(source, optimize=False).output_text,
            source,
        )

    def test_compile_kmx_rejects_non_text_with_type_error(self):
        with self.assertRaises(TypeError):
            compile_kmx(None)

    def test_cli_writes_exclusively_and_emits_machine_readable_provenance(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.kmx"
            output = root / "output.kmx"
            source.write_text("X q0\nX q0\n", encoding="ascii")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main([str(source), str(output)])
            self.assertEqual(status, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(output.read_text(encoding="ascii"), "")
            self.assertEqual(json.loads(stdout.getvalue())["canceled_pairs"], 1)

            output.write_text("preserve", encoding="ascii")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                status = main([str(source), str(output)])
            self.assertEqual(status, 3)
            self.assertEqual(output.read_text(encoding="ascii"), "preserve")

    def test_module_cli_compiles_with_the_canonical_circuit_type(self):
        source_text = 'REGISTER r0 "state"\nX q0\n'
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.kmx"
            output = root / "output.kmx"
            source.write_text(source_text, encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tools.kickmix_compiler",
                    str(source),
                    str(output),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                check=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True,
            )
            record = json.loads(completed.stdout)
            self.assertEqual(output.read_text(encoding="utf-8"), source_text)
            self.assertEqual(record["canceled_pairs"], 0)

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "no-follow file open is required")
    def test_cli_rejects_symlink_input(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.kmx"
            link = root / "link.kmx"
            output = root / "output.kmx"
            source.write_text("X q0\n", encoding="ascii")
            link.symlink_to(source)

            with contextlib.redirect_stderr(io.StringIO()):
                status = main([str(link), str(output)])
            self.assertEqual(status, 2)
            self.assertFalse(output.exists())

    def test_cli_reports_output_that_was_published_before_directory_sync_failure(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "input.kmx"
            output = root / "output.kmx"
            source.write_text("X q0\n", encoding="ascii")
            real_fsync = os.fsync
            calls = 0

            def fail_directory_sync(descriptor):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected directory sync failure")
                return real_fsync(descriptor)

            stderr = io.StringIO()
            with patch("tools.kickmix_compiler.os.fsync", side_effect=fail_directory_sync):
                with contextlib.redirect_stderr(stderr):
                    status = main([str(source), str(output)])

            self.assertEqual(status, 3)
            self.assertIn("output may already be published", stderr.getvalue())
            self.assertEqual(output.read_text(encoding="ascii"), "X q0\n")


if __name__ == "__main__":
    unittest.main()
