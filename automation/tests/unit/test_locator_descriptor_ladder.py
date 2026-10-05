"""Unit tests for the locator ladder in `pages/locator_descriptor.py`.

Pure Python — the Playwright scope is a recording stub, no browser starts.
"""

import pytest
from pages.locator_descriptor import LocatorDescriptor, OptionalLocatorDescriptor, ScopedLocator


class _Scope:
    """Records the Playwright locator factory call it receives."""

    def __getattr__(self, method):
        def call(*args, **kwargs):
            return (method, args, kwargs)

        return call


class _Page:
    def __init__(self):
        self.page = _Scope()


class TestValidDeclarations:
    @pytest.mark.parametrize(
        ("kwargs", "kind", "expected"),
        [
            ({"testid": "agent-form-save-button"}, "testid", ("get_by_test_id", ("agent-form-save-button",), {})),
            (
                {"role": "button", "name": "Save", "suggested_testid": "agent-form-save-button"},
                "role",
                ("get_by_role", ("button",), {"name": "Save"}),
            ),
            (
                {"role": "tab", "name": "Configuration", "exact": True, "suggested_testid": "agent-config-tab"},
                "role",
                ("get_by_role", ("tab",), {"name": "Configuration", "exact": True}),
            ),
            (
                {"label": "Name", "suggested_testid": "agent-form-name-input"},
                "label",
                ("get_by_label", ("Name",), {}),
            ),
            (
                {"css": "#agent-name", "suggested_testid": "agent-form-name-input"},
                "css",
                ("locator", ("#agent-name",), {}),
            ),
            (
                {"xpath": "//button[@aria-label='Delete']", "suggested_testid": "agent-delete-button"},
                "xpath",
                ("locator", ("xpath=//button[@aria-label='Delete']",), {}),
            ),
        ],
    )
    def test_kind_and_resolution(self, kwargs, kind, expected):
        class P(_Page):
            field = LocatorDescriptor(description="d", **kwargs)

        assert P.field.kind == kind
        assert P.field.is_testid is (kind == "testid")
        assert P().field == expected

    def test_legacy_locator_still_imports(self):
        class P(_Page):
            field = LocatorDescriptor(locator='[aria-label="Delete"]')

        assert P.field.kind == "locator"
        assert P().field == ("locator", ('[aria-label="Delete"]',), {})

    def test_legacy_fallback_only(self):
        class P(_Page):
            field = LocatorDescriptor(fallback=lambda page: ("fallback", page))

        assert P.field.kind == "fallback"
        assert P().field[0] == "fallback"

    def test_testid_plus_dead_fallback_resolves_by_testid(self):
        class P(_Page):
            field = LocatorDescriptor(testid="x-button", fallback=lambda page: "never")

        assert P().field == ("get_by_test_id", ("x-button",), {})

    def test_descriptor_is_read_only(self):
        class P(_Page):
            field = LocatorDescriptor(testid="x-button")

        with pytest.raises(AttributeError):
            P().field = "other"

    def test_optional_descriptor_returns_locator(self):
        class P(_Page):
            field = OptionalLocatorDescriptor(testid="x-button")

        assert P().field == ("get_by_test_id", ("x-button",), {})


class TestRejectedDeclarations:
    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({}, "No locator provided"),
            ({"testid": "a-b", "css": "#a", "suggested_testid": "a-b"}, "exactly one locator kind"),
            ({"testid": "a-b", "locator": "#a"}, "cannot be combined"),
            ({"name": "Save"}, "only valid together with role"),
            ({"testid": "a-b", "exact": True}, "exact= is only valid"),
            ({"role": "button", "name": "Save"}, "must carry suggested_testid"),
            ({"css": "#a"}, "must carry suggested_testid"),
            ({"testid": "a-b", "suggested_testid": "a-b"}, "only for non-testid"),
            ({"css": "#a", "suggested_testid": "Agent_Save"}, "kebab-case"),
            ({"css": "li:nth-child(2)", "suggested_testid": "a-b"}, "Positional CSS"),
            ({"css": "li:first-child", "suggested_testid": "a-b"}, "Positional CSS"),
            ({"css": "li >> nth=0", "suggested_testid": "a-b"}, "Positional CSS"),
            ({"css": '[data-testid="a-b"]', "suggested_testid": "a-b"}, "Use testid="),
            ({"css": "text=Save", "suggested_testid": "a-b"}, "plain CSS"),
            ({"xpath": "//ul/li[2]", "suggested_testid": "a-b"}, "Positional or absolute"),
            ({"xpath": "(//button)[last()]", "suggested_testid": "a-b"}, "Positional or absolute"),
            ({"xpath": "/html/body/div", "suggested_testid": "a-b"}, "Positional or absolute"),
        ],
    )
    def test_policy_violation_raises(self, kwargs, message):
        with pytest.raises(ValueError, match=message):
            LocatorDescriptor(**kwargs)

    def test_scoped_locator_rejects_legacy(self):
        with pytest.raises(ValueError, match="does not accept legacy"):
            ScopedLocator(locator="#a")
        with pytest.raises(ValueError, match="does not accept legacy"):
            ScopedLocator(fallback=lambda page: page)


class TestScopedLocator:
    def test_resolves_within_parent(self):
        spec = ScopedLocator(role="button", name="More actions", suggested_testid="entity-card-menu-button")
        assert spec.within(_Scope()) == ("get_by_role", ("button",), {"name": "More actions"})

    def test_template_args_fill_placeholders(self):
        spec = ScopedLocator(role="option", name="{}", suggested_testid="agent-tag-option-{}")
        assert spec.within(_Scope(), "smoke") == ("get_by_role", ("option",), {"name": "smoke"})

    def test_testid_template(self):
        spec = ScopedLocator(testid="skill-tag-option-{}")
        assert spec.within(_Scope(), "beta") == ("get_by_test_id", ("skill-tag-option-beta",), {})

    def test_braces_untouched_without_args(self):
        spec = ScopedLocator(css="a[href$='{}']", suggested_testid="nav-link")
        assert spec.within(_Scope()) == ("locator", ("a[href$='{}']",), {})


def test_every_page_object_declaration_passes_validation():
    """Importing every page object runs `_validate()` on all class-level declarations."""
    import importlib
    from pathlib import Path

    pages = Path(__file__).resolve().parents[2] / "pages"
    failures = []
    for path in sorted(pages.glob("*.py")):
        if path.name == "__init__.py":
            continue
        try:
            importlib.import_module(f"pages.{path.stem}")
        except Exception as exc:  # noqa: BLE001 — report every failing module at once
            failures.append(f"{path.name}: {exc}")
    assert not failures, "\n".join(failures)
