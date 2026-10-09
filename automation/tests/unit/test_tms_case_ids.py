"""Unit tests for `utils/tms_case_ids.py` — the `@pytest.mark.tms(...)` plugin.

Pure Python: the pytest `Item` is a stub shaped exactly like the attributes
allure-pytest's own `allure_name` reads (`name`, `obj`, `funcargs`, `callspec`),
and `allure.dynamic.title` is monkeypatched to record instead of writing to a
report. No browser, no Allure run directory.

The point under test is the 2026-10 change: the case-id prefix lands on the
**effective** title — the pytest function name when the test declares no
`@allure.title`, the declared title when it does.
"""

import allure
import pytest
from utils.tms_case_ids import _apply_title, effective_title, format_title, tms_case_ids


class _Marker:
    """Stands in for a pytest `Mark` — only `.args` is read."""

    def __init__(self, *args):
        self.args = args


class _CallSpec:
    def __init__(self, params, id_):
        self.params = params
        self.id = id_


class _Item:
    """Minimal stub of a pytest `Function` item.

    Carries exactly the attributes read by `allure_pytest.utils.allure_name`
    (`name`, `obj`, `funcargs`) plus `iter_markers`, and `callspec` only when
    parametrized — mirroring real pytest, where unparametrized items have no
    `callspec` at all.
    """

    def __init__(self, name, *, title=None, markers=(), funcargs=None, params=None, param_id=None):
        self.name = name
        self.funcargs = funcargs or {}
        self._markers = list(markers)

        def test_function():
            pass

        if title is not None:
            test_function.__allure_display_name__ = title
        self.obj = test_function

        if params is not None or param_id is not None:
            self.callspec = _CallSpec(params or {}, param_id)

    def iter_markers(self, name):
        return [m for m in self._markers if name == "tms"]


@pytest.fixture
def applied_titles(monkeypatch):
    """Record what `_apply_title` hands to `allure.dynamic.title`."""
    recorded = []
    monkeypatch.setattr(allure.dynamic, "title", recorded.append)
    return recorded


class TestEffectiveTitle:
    def test_falls_back_to_the_pytest_item_name(self):
        item = _Item("test_delete_pipeline_version_falls_back_to_base[chromium]")
        assert effective_title(item) == "test_delete_pipeline_version_falls_back_to_base[chromium]"

    def test_prefers_an_explicit_allure_title(self):
        item = _Item(
            "test_no_access_permission_blocks_all_api_operations",
            title="No Access: All API operations return 403 Forbidden",
        )
        assert effective_title(item) == "No Access: All API operations return 403 Forbidden"

    def test_substitutes_placeholders_from_parametrize_values(self):
        item = _Item(
            "test_invalid_bucket_name[name-with-space]",
            title="Invalid bucket name format is rejected: {invalid_name!r}",
            funcargs={"invalid_name": "name with space"},
            params={"invalid_name": "name with space"},
            param_id="name-with-space",
        )
        assert effective_title(item) == "Invalid bucket name format is rejected: 'name with space'"


class TestCaseIds:
    def test_collects_and_sorts_every_declared_id(self):
        item = _Item("test_x", markers=[_Marker("ELITEA-2461"), _Marker("ELITEA-2149")])
        assert tms_case_ids(item) == ["ELITEA-2149", "ELITEA-2461"]

    def test_deduplicates_ids_declared_at_several_scopes(self):
        item = _Item("test_x", markers=[_Marker("ELITEA-2003"), _Marker("ELITEA-2003")])
        assert tms_case_ids(item) == ["ELITEA-2003"]

    def test_no_marker_means_no_ids(self):
        assert tms_case_ids(_Item("test_x")) == []


class TestAppliedTitle:
    """The behaviour the asymmetry report was about — both shapes get the id."""

    def test_prefixes_the_function_name_when_no_allure_title_is_set(self, applied_titles):
        item = _Item(
            "test_delete_pipeline_version_falls_back_to_base",
            markers=[_Marker("ELITEA-2003")],
        )
        _apply_title(item)
        assert applied_titles == ["[ELITEA-2003] test_delete_pipeline_version_falls_back_to_base"]

    def test_prefixes_an_explicit_allure_title_too(self, applied_titles):
        item = _Item(
            "test_no_access_permission_blocks_all_api_operations",
            title="No Access: All API operations return 403 Forbidden",
            markers=[_Marker("ELITEA-2493")],
        )
        _apply_title(item)
        assert applied_titles == ["[ELITEA-2493] No Access: All API operations return 403 Forbidden"]

    def test_prefixes_several_ids_space_separated(self, applied_titles):
        item = _Item(
            "test_covers_two_cases",
            title="One test, two cases",
            markers=[_Marker("ELITEA-2149", "ELITEA-2461")],
        )
        _apply_title(item)
        assert applied_titles == ["[ELITEA-2149 ELITEA-2461] One test, two cases"]

    def test_leaves_an_unmarked_test_untouched(self, applied_titles):
        _apply_title(_Item("test_framework_helper", title="A helper with no TMS case"))
        assert applied_titles == []

    def test_is_idempotent_across_the_call_and_teardown_hooks(self, applied_titles):
        """Both `runtest_call` and `runtest_teardown` apply the title.

        `allure.dynamic.title` only assigns the report's `test_result.name`,
        while `effective_title` re-reads the untouched source (the decorator
        attribute / `item.name`) — so the second application recomputes the
        same string rather than prefixing the prefix.
        """
        item = _Item("test_x", title="A titled test", markers=[_Marker("ELITEA-1")])
        _apply_title(item)
        _apply_title(item)
        assert applied_titles == ["[ELITEA-1] A titled test"] * 2


class TestFormatTitle:
    def test_renders_the_bracketed_prefix(self):
        assert format_title(["ELITEA-1", "ELITEA-2"], "test_x") == "[ELITEA-1 ELITEA-2] test_x"
