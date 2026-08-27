"""Unit tests pinning the two review findings on
``tests.ui.admin.test_secrets_search_filter`` (ELITEA-2334, PR review round 1).

1. **The case-insensitivity step could degrade to a tautology.** ``_pick_probe``
   derives the search term from a rendered name prefix. Nothing required that
   prefix to contain a *cased* character, so against live data holding a secret
   named e.g. ``2fa_token`` or ``_internal_key`` it could return ``"2"`` /
   ``"_"`` — for which ``probe.upper() == probe.lower() == probe``. Case step 4
   would then type the byte-identical term step 3 already asserted on and pass
   while proving nothing about case handling: a product that had dropped the
   ``toLowerCase()`` on either side of ``SecretsContent.jsx``'s filter would
   still be green. The fix makes the cased character part of the derivation
   contract, and fails loudly with a named reason when the live data cannot
   supply one.

2. **The AFS Coverage-Map row for case step 5 claimed an assertion the code did
   not make.** ``l3_secrets-search-filters-by-name_ELITEA-2334.md`` lists
   ``Asserted where: value == ""; total == total_all; page-1 set restored`` — the
   spec asserted only the first two. "All secrets are shown again" was therefore
   proved by a *count*, which a filter that restored the wrong ten rows would
   satisfy. The fix captures the unfiltered page-1 slice up front and compares
   the restored set against it.

These are unit tests rather than a second live run because both defects are in
term-derivation / assertion presence, neither of which needs a browser: the
tautology reproduces deterministically from a synthetic name list, and the
missing assertion is a property of the spec's own source.
"""

import inspect

import pytest

# Import the MODULE, never `from ... import TestSecretsSearchFilter`: a `Test*`
# class bound into this module's namespace is collected by pytest here too, and
# the whole live UI spec would run a second time under `tests/unit/`.
import tests.ui.admin.test_secrets_search_filter as spec

_has_cased_character = spec._has_cased_character
_matches = spec._matches
_pick_probe = spec._pick_probe

# Names whose FIRST usable prefix is caseless: "2" filters {2fa_token, 2fb_token}
# out of three names — a proper, non-empty, single-page subset, so the
# pre-fix `_pick_probe` returned it and step 4 became a no-op.
_DIGIT_LED_NAMES = ["2fa_token", "2fb_token", "3xx_token"]

# No prefix of any name carries a cased character at all — the derivation
# genuinely cannot satisfy the case, and must say so instead of silently
# handing back a useless probe.
_CASELESS_NAMES = ["123", "124", "125"]


def test_has_cased_character_rejects_digits_and_punctuation():
    assert not _has_cased_character("2")
    assert not _has_cased_character("_")
    assert not _has_cased_character("2-4_9")
    assert _has_cased_character("a")
    assert _has_cased_character("2f")
    assert _has_cased_character("PGVECTOR")


def test_pick_probe_never_returns_a_caseless_probe():
    """The regression: pre-fix this returned ``"2"``."""
    probe = _pick_probe(_DIGIT_LED_NAMES)

    assert _has_cased_character(probe), (
        f"_pick_probe returned {probe!r}, which has no cased character — "
        "case step 4 would re-assert step 3 instead of exercising case-insensitivity"
    )
    assert probe.upper() != probe and probe.upper() != probe.lower()


def test_pick_probe_still_filters_to_a_proper_non_empty_subset():
    """The cased-character guard must not cost the probe its original property."""
    probe = _pick_probe(_DIGIT_LED_NAMES)
    hits = _matches(_DIGIT_LED_NAMES, probe)

    assert 0 < len(hits) < len(_DIGIT_LED_NAMES), (
        f"Probe {probe!r} matched {hits} — expected a proper, non-empty subset of "
        f"{_DIGIT_LED_NAMES}"
    )


def test_pick_probe_fails_loudly_when_no_cased_probe_exists():
    with pytest.raises(AssertionError, match="cased character"):
        _pick_probe(_CASELESS_NAMES)


def test_step_4_guards_the_probe_before_typing_the_case_variants():
    """The in-spec guard, so a future edit to `_pick_probe` cannot silently
    re-introduce the tautology at the call site."""
    source = inspect.getsource(
        spec.TestSecretsSearchFilter.test_search_field_filters_secrets_by_name
    )

    assert "assert _has_cased_character(probe)" in source, (
        "Step 4 must assert the probe carries a cased character before typing "
        "probe.upper()/probe.lower()"
    )


def test_step_5_asserts_the_page_1_set_is_restored_not_merely_its_count():
    """Backs the AFS Coverage-Map claim `page-1 set restored` for case step 5."""
    source = inspect.getsource(
        spec.TestSecretsSearchFilter.test_search_field_filters_secrets_by_name
    )

    assert "page1_names = secrets_page.get_row_names()" in source, (
        "Step 1 must capture the unfiltered page-1 name set for step 5 to compare against"
    )
    assert "set(secrets_page.get_row_names()) == set(page1_names)" in source, (
        "Step 5 must assert the restored page-1 NAME SET, not only the row count and "
        "the pagination total — the AFS Coverage Map claims that assertion exists"
    )
