#!/usr/bin/env bash
# Point a freshly `lake init`/`lake new`'d project's .lake/packages at a
# shared, machine-wide Mathlib+deps cache instead of re-downloading them.
#
# Why this script exists instead of relying on Lake's own cache: Lake does
# have a real built-in shared cache dir (`lake env` -> LAKE_CACHE_DIR,
# defaults to <toolchain>/lake/cache, auto-shared across every project on
# that toolchain) -- but that's for `lake cache get`'s Reservoir-based
# package downloads. Mathlib instead ships its own downloader
# (`lake exe cache get`, run automatically by `lake build`) which pulls
# prebuilt .olean files straight from Mathlib's own Azure blob storage into
# the project-LOCAL .lake/build, bypassing LAKE_CACHE_DIR entirely. There is
# no standard shared location for that path, so this symlinks .lake/packages
# (the built package checkouts) at a fixed spot under $HOME/.cache instead.
#
# Usage: run from inside the Lean project root, after `lake init <name> math`
# but before `lake build` (or `lake exe cache get`):
#   scripts/link_shared_mathlib_cache.sh
#
# Only safe to use across projects pinned to the SAME Mathlib toolchain
# (checked below via lean-toolchain) -- packages built against a different
# Lean/Mathlib version are not binary-compatible.
set -euo pipefail

if [[ ! -f lean-toolchain ]]; then
    echo "error: no lean-toolchain file in $(pwd) -- run this from a Lean project root" >&2
    exit 1
fi

toolchain="$(cat lean-toolchain | tr -d '[:space:]')"
version="${toolchain##*:}"
cache_root="${ULAM_LAKE_CACHE_DIR:-$HOME/.cache/lake}"
shared="$cache_root/packages-$version"

mkdir -p ".lake"
if [[ -e ".lake/packages" && ! -L ".lake/packages" ]]; then
    if [[ -d ".lake/packages" ]] && [[ -z "$(ls -A .lake/packages)" ]]; then
        rmdir ".lake/packages"
    else
        echo "error: .lake/packages already exists and is not empty/not a symlink -- refusing to overwrite" >&2
        exit 1
    fi
fi

if [[ -d "$shared" ]]; then
    echo "Reusing shared package cache: $shared"
else
    echo "No shared cache yet for toolchain $version at $shared"
    echo "It will be created here after this project's first successful build:"
    echo "  mkdir -p \"$cache_root\" && mv .lake/packages \"$shared\" && ln -s \"$shared\" .lake/packages"
    exit 0
fi

ln -sfn "$shared" ".lake/packages"
echo "Linked .lake/packages -> $shared"
