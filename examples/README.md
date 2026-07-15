# Examples

This folder contains runnable example inputs for the main UlamAI workflows,
organized by the subcommand that consumes them. For the full tutorial, see
[`../docs/tutorial.md`](../docs/tutorial.md) (or the Colab notebook
[`../docs/tutorial.ipynb`](../docs/tutorial.ipynb)).

## Start Here

1. Read [`../docs/tutorial.md`](../docs/tutorial.md) (full guide).
2. If you prefer notebooks, open [`../docs/tutorial.ipynb`](../docs/tutorial.ipynb) in Colab.
3. Run the quick-start commands below.

## Files

- `prove/smoke.lean`: minimal Lean proving smoke test.
- `prove/infinite_primes.txt`: statement-only input for `prove --output-format tex`.
- `formalize/identity_toy.tex`: small formalization example (commutativity of addition).
- `formalize/polish_olympiad_statement.tex`: olympiad statement-only formalization input.
- `formalize/polish_olympiad_proof.tex`: same olympiad theorem with a full informal proof narrative (recommended formalization input).
- `formalize/stress/{category_theory,groups,rings,modules,algebras}/hard_true.tex`: genuinely correct but hard theorems (Yoneda lemma, Sylow's first theorem, PID⟹UFD, structure theorem for f.g. modules over a PID, Wedderburn's theorem) — stress tests / aspirational benchmarks, expected to be difficult for the current pipeline.
- `formalize/stress/{category_theory,groups,rings,modules,algebras}/false.tex`: deliberately **false** statements, each with a plausible-looking but flawed proof — soundness tests. **The files themselves do not say the statement is false** (that would give the LLM the answer and defeat the test); a correct pipeline must fail/refuse these on its own rather than produce a bogus Lean proof. What's actually wrong with each one:
  - `category_theory/false.tex`: not every functor has a left adjoint (e.g. the forgetful functor `Field -> Set` has none, since `Field` has no initial object).
  - `groups/false.tex`: the converse of Lagrange's theorem is false (e.g. `A4`, order 12, has no subgroup of order 6).
  - `rings/false.tex`: not every integral domain is a UFD (e.g. `Z[sqrt(-5)]`, via `6 = 2*3 = (1+sqrt(-5))(1-sqrt(-5))`).
  - `modules/false.tex`: not every module over a PID is free (e.g. `Z/2Z` as a `Z`-module).
  - `algebras/false.tex`: not every finite-dimensional algebra is semisimple (e.g. `k[x]/(x^2)` has nonzero nilpotent radical `(x)`).

## Recommended Defaults

- LLM provider: `codex_cli` (recommended).
- Prove mode for Lean files: `llm`.
- Output format for informal proving: `tex`.

## Quick Commands

Smoke prove:

```bash
python3 -m ulam prove examples/prove/smoke.lean --theorem irrational_sqrt_two_smoke
```

Prove to TeX (infinitely many primes):

```bash
python3 -m ulam prove --theorem infinitely_many_primes --output-format tex \
  --statement "$(cat examples/prove/infinite_primes.txt)" \
  --llm codex_cli --tex-rounds 3 --tex-worker-drafts 2 --tex-judge-repairs 2 \
  --tex-replan-passes 2 --tex-artifacts-dir runs/prove_tex
```

Formalize olympiad statement-only file:

```bash
python3 -m ulam formalize examples/formalize/polish_olympiad_statement.tex \
  --out examples/formalize/polish_olympiad_statement.lean \
  --proof-backend llm --lean-backend dojo
```

Formalize olympiad full-proof file (recommended):

```bash
python3 -m ulam formalize examples/formalize/polish_olympiad_proof.tex \
  --out examples/formalize/polish_olympiad_proof.lean \
  --proof-backend llm --lean-backend dojo
```
