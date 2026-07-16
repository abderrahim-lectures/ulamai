from __future__ import annotations

from ulam.formalize.engine import _normalize_imports, _normalize_lean_output


def test_normalize_imports_keeps_multiple_modules_on_separate_lines() -> None:
    raw = "import Mathlib\nimport Mathlib.Data.Nat.Basic\n\ntheorem foo : True := trivial\n"
    out = _normalize_imports(raw)
    assert "import Mathlib Mathlib.Data.Nat.Basic" not in out
    assert "import Mathlib\nimport Mathlib.Data.Nat.Basic" in out


def test_normalize_imports_dedupes_and_always_includes_mathlib() -> None:
    raw = "import Mathlib\nimport Mathlib\nimport Mathlib.Algebra.Group.Basic\n\ntheorem foo : True := trivial\n"
    out = _normalize_imports(raw)
    assert out.count("import Mathlib\n") == 1
    assert "import Mathlib.Algebra.Group.Basic" in out


def test_normalize_imports_inserts_mathlib_when_missing() -> None:
    raw = "import Mathlib.Data.Nat.Basic\n\ntheorem foo : True := trivial\n"
    out = _normalize_imports(raw)
    lines = out.splitlines()
    assert lines[0] == "import Mathlib"
    assert "import Mathlib.Data.Nat.Basic" in lines


def test_normalize_imports_empty_input_defaults_to_mathlib() -> None:
    assert _normalize_imports("") == "import Mathlib\n"


def test_normalize_lean_output_produces_parseable_multi_import_header() -> None:
    raw = (
        "```lean\n"
        "import Mathlib\n"
        "import Mathlib.Data.Nat.Basic\n\n"
        "theorem add_comm_toy (m n : Nat) : m + n = n + m := by\n"
        "  sorry\n"
        "```\n"
    )
    out = _normalize_lean_output(raw)
    header_lines = [l for l in out.splitlines() if l.startswith("import ")]
    # Each import statement must be on its own line -- Lean 4 has no
    # space-separated multi-module import syntax.
    assert header_lines == ["import Mathlib", "import Mathlib.Data.Nat.Basic"]
