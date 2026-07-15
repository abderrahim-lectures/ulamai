# Architecture

This document explains how `ulam` (package `ulam`, distributed as `ulam-prover`)
works internally: what it does, how the pieces fit together, and where to
look when extending it.

## What it does

`ulam` is a CLI that produces machine-checked Lean 4 proofs by looping an LLM
against the Lean compiler:

1. An LLM proposes a next proof step (a tactic, or a full draft).
2. Lean verifies the step (typecheck / tactic execution).
3. Errors feed back into the LLM as repair context; the search backtracks or
   retries until the goal is closed or the run gives up.

It also has a **LaTeX → Lean formalization** pipeline (`formalize`) and an
**informal (LaTeX) proof drafting** pipeline (`prove --output-format tex`)
that composes a natural-language proof draft via a planner/worker/judge loop,
reusing the same LLM/search machinery. There is currently **no reverse
direction** — nothing in this codebase turns an existing Lean file back into
human-readable LaTeX/prose.

## Entry points

- Installed console script: `ulam = "ulam.cli:main"` ([pyproject.toml](pyproject.toml)).
- Module entry point: `python3 -m ulam` ([ulam/__main__.py](ulam/__main__.py)).
- Standalone (no install): [ulam.sh](ulam.sh) — runs `python -m ulam` against
  the repo's `uv`-managed `.venv/`, so it can be symlinked onto `$PATH`
  (e.g. `~/.local/bin/ulam`) without `pip install -e .`.
- No-args invocation launches the interactive menu ([ulam/menu.py](ulam/menu.py))
  instead of printing `--help`.

## Package layout (`ulam/`)

```
cli.py          argparse wiring for all subcommands + their handlers (largest file)
menu.py         interactive TUI: configure providers/settings, launch prove/formalize
config.py       load/save .ulam/config.json
state.py        proof-state representation
trace.py        JSONL run tracing (run.jsonl)
types.py        shared dataclasses (ProofState, TacticResult, ...)

auth/           login flows for subscription CLIs (codex, claude, gemini)
llm/            LLM adapters — the "propose a next tactic" side
lean/           Lean backends — the "verify a tactic" side
retrieve/       premise/lemma retrieval for prompting
search/         best-first search driving the propose/verify loop
formalize/      LaTeX -> Lean pipeline (statement/draft/prove/repair, LLM judges)
```

### `ulam/llm/` — LLM adapters

All adapters implement `LLMClient` ([base.py](ulam/llm/base.py)):

```python
class LLMClient(ABC):
    def propose(self, state: ProofState, retrieved, k, instruction=None,
                context=None, mode="tactic") -> list[str]: ...
    def repair(self, state, retrieved, failed_tactic, error, k, ...) -> list[str]: ...
```

`propose()` is intentionally shaped around `ProofState` (a Lean goal), not a
raw prompt string — every adapter builds its own request payload but shares:

- **[http.py](ulam/llm/http.py)** — `urlopen_read`, `extract_openai_content`,
  `extract_anthropic_content`, `extract_ollama_content`,
  `ollama_chat_endpoints`, `ensure_cmd`. These are the genuinely
  provider-agnostic bits (HTTP GET/parse response JSON/check a CLI is on
  `$PATH`) and are shared by every adapter below **and** by
  `formalize/llm.py`, so there's exactly one implementation of each, not one
  per call site.
- API-key backends: `openai_compat.py`, `anthropic.py`, `gemini.py`,
  `ollama.py` — build a provider-specific payload/endpoint, call
  `http.urlopen_read`, parse with the matching `http.extract_*_content`.
- Subscription-CLI backends: `cli_codex.py`, `cli_claude.py`,
  `cli_gemini.py` — shell out to `codex`/`claude`/`gemini` via
  [cli_utils.py](ulam/llm/cli_utils.py); `_ensure_cmd` replaced with
  `http.ensure_cmd`.
- `mock.py` — no-network adapter for tests/smoke runs.
- `runtime.py` — `run_with_runtime_controls`: wraps a blocking call with a
  timeout + heartbeat in a worker thread; every adapter's HTTP/CLI call goes
  through this.
- `prompt.py` — builds the system/user prompt from a `ProofState` and parses
  tactic candidates back out of the LLM's response.

### `ulam/lean/` — Lean backends

All backends implement `LeanRunner` ([base.py](ulam/lean/base.py)):
`start()` / `apply(tactic)` / `close()`.

- `dojo.py` — LeanDojo/Pantograph: stateful tactic execution with real goal
  tracking. Requires `lean-dojo-v2` and `PyPantograph`
  (`git+https://github.com/stanford-centaur/PyPantograph`) — note this is
  *not* the unrelated `pantograph` package on PyPI, which is a Jupyter
  drawing-widget library that happens to share the name.
- `lsp.py` — talks to the Lean language server (`lake serve` /
  `lean --server`) for diagnostics; owns the LSP client/protocol plumbing
  (`LSPClient`, `MessageReader`, `format_diagnostics`, `lean_lsp_cmd`,
  `normalize_diagnostic`, `read_stderr`, `terminate_process` — all exported
  publicly via `__all__` for reuse by other backends, rather than other
  files reaching into underscore-prefixed internals).
- `lsp_runner.py` — a `LeanRunner` built on top of `lsp.py`'s public
  surface (see above) for script-style tactic checking without Pantograph.
- `cli_check.py` — plain `lake env lean` typecheck, no incremental state.
- `mock.py` — no-Lean smoke-testing backend.

### `ulam/retrieve/` — premise selection

`base.py` interface, `embeddings.py` (embedding similarity), `indexed.py`
(local token-overlap index, built via `ulam index build`).

### `ulam/search/best_first.py`

Drives the propose → verify → repair loop: best-first/beam search over
`ProofState`s with a transposition table to avoid re-exploring equivalent
states, calling into `llm/` for candidates and `lean/` for verification.

### `ulam/formalize/` — LaTeX → Lean

- `engine.py` (`FormalizationEngine`) — orchestrates segmenting a `.tex`
  document, drafting Lean declarations, running proof search per
  declaration, equivalence/semantic auditing, and writing artifacts.
  `_make_llm_client` here correctly builds a real `ulam/llm/` `LLMClient`
  for the tactic-search side of formalization.
- `llm.py` (`FormalizationLLM`) — a **separate, second** LLM client used for
  the non-tactic prompts formalization needs (draft/repair/judge/plan, all
  raw prompt → text/JSON, not `ProofState`-shaped). It cannot reuse
  `LLMClient.propose()` because the request shape is fundamentally
  different — but it now reuses the same low-level `llm/http.py` helpers as
  the `LLMClient` adapters instead of re-implementing HTTP/parsing itself
  (previously ~150 lines of duplicated, drifting request/parsing code; see
  git history on `formalize/llm.py` for the before/after).
- `segment.py` / `segmentation.py` — split long `.tex` documents into
  per-statement chunks.

## Config resolution (`cli.py`)

CLI flags and `.ulam/config.json` both feed into per-setting "resolver"
functions of the shape *explicit CLI flag wins, else config value, else
default*. Rather than ~40 hand-written copies of that logic, `cli.py` now
has four generic primitives:

```python
_resolve_bool_setting(args, attr, section, key, default, config=None)
_resolve_int_setting(args, attr, section, key, default, config=None, minimum=None, maximum=None)
_resolve_float_setting(args, attr, section, key, default, config=None, minimum=None)
_resolve_enum_setting(args, attr, section, key, choices, default, config=None)
```

Each `_resolve_<setting>()` function (`_resolve_allow_axioms`,
`_resolve_tex_rounds`, `_resolve_formalize_llm_check`, ...) is a one-line
wrapper calling the matching primitive with its section/key/default — new
settings that fit this shape should follow the same pattern rather than
hand-rolling the explicit/config/default branching again. Settings with
genuinely different resolution logic (e.g. `_resolve_formalize_max_repairs`,
which falls back to a *different resolved setting* rather than a static
default) are left as their own functions.

`menu.py` (the interactive TUI) imports `_normalize_proof_profile` and
`run_prove` from `cli.py` directly rather than re-deriving them.

## Data flow (proving)

```
cli.py (parse args)
  -> load .ulam/config.json (config.py)
  -> build LLMClient (llm/*.py) + LeanRunner (lean/*.py)
  -> search/best_first.py loop:
       retrieve/*.py  -> relevant premises
       llm/*.py       -> candidate tactic(s)
       lean/*.py      -> verify candidate
       (repeat / backtrack on failure)
  -> state.py / trace.py -> run.jsonl
```

## Data flow (formalizing)

```
cli.py run_formalize
  -> formalize/engine.py FormalizationEngine.run()
       formalize/segment*.py -> per-statement chunks of the .tex
       formalize/llm.py      -> draft/repair/judge prompts (raw text/JSON)
       engine._make_llm_client -> real LLMClient for per-declaration proof search
       search/best_first.py (reused) -> proof search per declaration
       lean/*.py -> typecheck/verify
  -> Lean file + artifacts written to disk
```

## Testing / benchmarking

- `tests/` — unit tests for extracted helpers (bench-compare gating,
  guardrail/inference profiles, LLM strategy pivoting, LSP runner helpers,
  menu helpers, TeX-proving helpers, search planner helpers). Run with
  `.venv/bin/python -m pytest tests/ -q`.
- `bench/` — JSONL benchmark suites (miniF2F-derived, a regression suite),
  run via `ulam bench --suite ...`, validated via `ulam bench-validate`,
  compared via `ulam bench-compare` (used for CI non-regression gating).

## Known structural debt (not yet addressed)

- `cli.py` is ~10k lines with several very large functions (`main`,
  `run_prove_tex`, `run_bench`); most of `main()`'s subcommand wiring and
  `run_prove_tex`/`run_bench` bodies aren't covered by `tests/` end-to-end.
- `menu.py`'s `_build_args_from_config` independently constructs the
  `argparse.Namespace`-equivalent dict handed to `run_prove`/`run_prove_tex`,
  rather than going through the same resolver primitives `cli.py` uses —
  left alone in this pass because unifying it safely requires more surgery
  than a mechanical dedup (menu.py builds args *before* the CLI parses any,
  cli.py resolves settings *from* parsed args).
- `formalize/engine.py`/`llm.py` remain very large single files
  (~93KB/~65KB) — splitting them by concern (segmentation vs. drafting vs.
  proof-search vs. semantic auditing) would help but wasn't done here to
  keep this pass's blast radius limited to verifiable, mechanical
  deduplication.
