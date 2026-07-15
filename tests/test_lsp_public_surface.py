from __future__ import annotations

from ulam.lean import lsp


def test_lsp_public_symbols_are_exported() -> None:
    for name in lsp.__all__:
        assert hasattr(lsp, name), f"lsp.py should export {name}"


def test_public_aliases_match_private_implementations() -> None:
    assert lsp.format_diagnostics is lsp._format_diagnostics
    assert lsp.lean_lsp_cmd is lsp._lean_lsp_cmd
    assert lsp.LSPClient is lsp._LSPClient
    assert lsp.MessageReader is lsp._MessageReader
    assert lsp.normalize_diagnostic is lsp._normalize_diagnostic
    assert lsp.read_stderr is lsp._read_stderr
    assert lsp.terminate_process is lsp._terminate_process


def test_lsp_runner_imports_public_names_not_private() -> None:
    import ast
    import inspect

    from ulam.lean import lsp_runner

    source = inspect.getsource(lsp_runner)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "lsp":
            for alias in node.names:
                name = alias.name
                assert not name.startswith("_"), (
                    f"lsp_runner.py should import public name, not private {name!r}"
                )
