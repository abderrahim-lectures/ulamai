from __future__ import annotations

import argparse

from ulam.cli import (
    _resolve_allow_axioms,
    _resolve_bool_setting,
    _resolve_enum_setting,
    _resolve_float_setting,
    _resolve_formalize_llm_check,
    _resolve_formalize_llm_check_timing,
    _resolve_formalize_max_rounds,
    _resolve_int_setting,
    _resolve_llm_edit_scope,
    _resolve_tex_rounds,
    _resolve_typecheck_timeout,
)


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_resolve_bool_setting_explicit_flag_wins() -> None:
    assert _resolve_bool_setting(_ns(flag=False), "flag", "sec", "key", True, {"sec": {"key": True}}) is False


def test_resolve_bool_setting_falls_back_to_config() -> None:
    assert _resolve_bool_setting(_ns(), "flag", "sec", "key", True, {"sec": {"key": False}}) is False


def test_resolve_bool_setting_falls_back_to_default() -> None:
    assert _resolve_bool_setting(_ns(), "flag", "sec", "key", True, {}) is True


def test_resolve_int_setting_clamps_minimum_and_maximum() -> None:
    assert _resolve_int_setting(_ns(n=0), "n", "sec", "key", 5, {}, minimum=1, maximum=10) == 1
    assert _resolve_int_setting(_ns(n=99), "n", "sec", "key", 5, {}, minimum=1, maximum=10) == 10
    assert _resolve_int_setting(_ns(n=7), "n", "sec", "key", 5, {}, minimum=1, maximum=10) == 7


def test_resolve_int_setting_invalid_explicit_falls_back_to_clamped_default() -> None:
    assert _resolve_int_setting(_ns(n="not-an-int"), "n", "sec", "key", 5, {}, minimum=1) == 5


def test_resolve_float_setting_clamps_minimum() -> None:
    assert _resolve_float_setting(_ns(t=2.0), "t", "sec", "key", 60.0, {}, minimum=5.0) == 5.0
    assert _resolve_float_setting(_ns(t=30.0), "t", "sec", "key", 60.0, {}, minimum=5.0) == 30.0


def test_resolve_enum_setting_invalid_explicit_falls_back_to_config() -> None:
    result = _resolve_enum_setting(
        _ns(mode="bogus"), "mode", "sec", "key", {"a", "b"}, "a", {"sec": {"key": "b"}}
    )
    assert result == "b"


def test_resolve_enum_setting_invalid_config_falls_back_to_default() -> None:
    result = _resolve_enum_setting(
        _ns(mode=None), "mode", "sec", "key", {"a", "b"}, "a", {"sec": {"key": "bogus"}}
    )
    assert result == "a"


def test_resolve_allow_axioms_matches_prove_section() -> None:
    assert _resolve_allow_axioms(_ns(allow_axioms=None), {"prove": {"allow_axioms": False}}) is False
    assert _resolve_allow_axioms(_ns(allow_axioms=None), {}) is True


def test_resolve_typecheck_timeout_enforces_minimum_of_5() -> None:
    assert _resolve_typecheck_timeout(_ns(typecheck_timeout=1), {}) == 5.0
    assert _resolve_typecheck_timeout(_ns(typecheck_timeout=None), {"prove": {"typecheck_timeout_s": 42}}) == 42.0


def test_resolve_llm_edit_scope_only_accepts_known_values() -> None:
    assert _resolve_llm_edit_scope(_ns(llm_edit_scope="errors_only"), {}) == "errors_only"
    assert _resolve_llm_edit_scope(_ns(llm_edit_scope="nonsense"), {}) == "full"


def test_resolve_tex_rounds_minimum_is_1() -> None:
    assert _resolve_tex_rounds(_ns(tex_rounds=0), {}) == 1
    assert _resolve_tex_rounds(_ns(tex_rounds=None), {"prove": {"tex_rounds": 9}}) == 9


def test_resolve_formalize_max_rounds_default_and_config() -> None:
    assert _resolve_formalize_max_rounds(_ns(max_rounds=None), {}) == 5
    assert _resolve_formalize_max_rounds(_ns(max_rounds=None), {"formalize": {"max_rounds": 3}}) == 3


def test_resolve_formalize_llm_check_timing_only_accepts_known_values() -> None:
    assert _resolve_formalize_llm_check_timing(_ns(llm_check_timing="mid+end"), {}) == "mid+end"
    assert _resolve_formalize_llm_check_timing(_ns(llm_check_timing="bogus"), {}) == "end"


def test_resolve_formalize_llm_check_bool() -> None:
    assert _resolve_formalize_llm_check(_ns(llm_check=None), {"formalize": {"llm_check": False}}) is False
