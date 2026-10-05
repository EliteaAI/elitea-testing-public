"""Unit tests for `scripts/locator_inventory.py` — scan, debt metric and ledger state machine."""

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "locator_inventory.py"
_spec = importlib.util.spec_from_file_location("locator_inventory", SCRIPT)
inv_mod = importlib.util.module_from_spec(_spec)
sys.modules["locator_inventory"] = inv_mod  # dataclasses resolve their module via sys.modules
_spec.loader.exec_module(inv_mod)

PAGE_SRC = textwrap.dedent(
    """
    from .locator_descriptor import LocatorDescriptor, ScopedLocator

    class DemoPage:
        save = LocatorDescriptor(testid="demo-save-button")
        name = LocatorDescriptor(label="Name", suggested_testid="demo-name-input")
        menu = LocatorDescriptor(role="button", name="Menu", suggested_testid="demo-menu-button")
        legacy = LocatorDescriptor(fallback=lambda page: page.locator("#x"))
        ROW_DELETE = '[data-testid="demo-row-delete-button"]'
        ROW_EDIT = ScopedLocator(css="button.edit", suggested_testid="demo-row-edit-button")
        OLD_SELECTOR = "div.old"

        def raw(self):
            return self.page.locator("button.raw")

        def scoped_ok(self, row):
            return row.locator(self.ROW_DELETE)

        def literal_ok(self, row):
            return row.locator('[data-testid="demo-x"]')
    """
)


@pytest.fixture
def pages_dir(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "demo_page.py").write_text(PAGE_SRC, encoding="utf-8")
    return pages


def test_scan_counts_declarations_and_unmanaged(pages_dir):
    inv = inv_mod.scan(pages_dir)
    kinds = {d.attr: d.kind for d in inv.declarations}
    assert kinds == {
        "save": "testid",
        "name": "label",
        "menu": "role",
        "legacy": "fallback",
        "ROW_DELETE": "testid",
        "ROW_EDIT": "css",
    }
    hints = {d.attr: d.suggested_testid for d in inv.declarations}
    assert hints["menu"] == "demo-menu-button"
    unmanaged = {u.where for u in inv.unmanaged}
    assert unmanaged == {"raw", "OLD_SELECTOR"}


def test_metric(pages_dir):
    m = inv_mod.scan(pages_dir).metric()
    assert m["declared_total"] == 6
    assert m["declared_testid"] == 2
    assert m["declared_non_testid"] == 4
    assert m["non_testid_with_hint"] == 3
    assert m["non_testid_without_hint"] == 1
    assert m["locator_debt"] == pytest.approx(4 / 6, abs=1e-4)
    assert m["unmanaged_handles"] == 2


def test_ledger_lifecycle(pages_dir):
    ledger = {"schema": 1, "entries": {}}
    changes = inv_mod.sync_ledger(inv_mod.scan(pages_dir), ledger)
    assert len(changes["added"]) == 4
    eid = "pages/demo_page.py::DemoPage.menu"
    assert ledger["entries"][eid]["state"] == "raw"

    with pytest.raises(SystemExit, match="illegal transition"):
        inv_mod.mark(ledger, eid, "migrated", "x")
    with pytest.raises(SystemExit, match="evidence"):
        inv_mod.mark(ledger, eid, "testid-proposed", "")

    inv_mod.mark(ledger, eid, "testid-proposed", "EliteaAI/EliteaUI@abc1234")
    q = inv_mod.queue(ledger, 10)
    assert [r["id"] for r in q["awaiting_deploy"]] == [eid]
    assert eid not in [r["id"] for r in q["phase_b_add_testid"]]
    assert [r["id"] for r in q["needs_hint"]] == ["pages/demo_page.py::DemoPage.legacy"]

    inv_mod.mark(ledger, eid, "on-dev", "dev build 2026-10-05")
    assert [r["id"] for r in inv_mod.queue(ledger, 10)["phase_a_swap"]] == [eid]

    # The migrator swaps the declaration to testid=; the next sync records it as migrated.
    swapped = PAGE_SRC.replace(
        'menu = LocatorDescriptor(role="button", name="Menu", suggested_testid="demo-menu-button")',
        'menu = LocatorDescriptor(testid="demo-menu-button")',
    )
    (pages_dir / "demo_page.py").write_text(swapped, encoding="utf-8")
    changes = inv_mod.sync_ledger(inv_mod.scan(pages_dir), ledger)
    assert changes["migrated"] == [eid]
    assert ledger["entries"][eid]["state"] == "migrated"
    assert ledger["metric"]["declared_non_testid"] == 3


def test_sync_marks_deleted_declarations_removed(pages_dir):
    ledger = {"schema": 1, "entries": {}}
    inv_mod.sync_ledger(inv_mod.scan(pages_dir), ledger)
    (pages_dir / "demo_page.py").write_text(PAGE_SRC.replace("    legacy = ", "    # legacy = "), encoding="utf-8")
    changes = inv_mod.sync_ledger(inv_mod.scan(pages_dir), ledger)
    assert changes["removed"] == ["pages/demo_page.py::DemoPage.legacy"]


def test_real_pages_scan_runs():
    inv = inv_mod.scan(inv_mod.DEFAULT_PAGES)
    assert inv.metric()["declared_total"] > 0
