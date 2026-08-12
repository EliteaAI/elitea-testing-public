"""Static-analysis regression test for SkillsListPage's `LocatorDescriptor`
inventory (ELITEA-2428 review round 1; scoping fix round 2).

Guards against the dead-code shape a fresh-session reviewer flagged on this
PR's first round: a page-wide `LocatorDescriptor` field (`entity_card_icon`)
defined once but never invoked (`self.entity_card_icon` / `list_page.entity_
card_icon`) anywhere in `automation/`, because the actual per-card lookup
(`card_icon_locator()`) re-derives the same `entity-card-icon` testid as a
raw scoped-selector string constant (`CARD_ICON_SELECTOR`) instead of ever
calling the field. Root pattern is older tech debt in `AgentsListPage`
(untouched here) — see
`.agents/memory/qa-engineer/entity_card_icon_field_is_dead_code_pattern.md`.

**Round 2 fix — scoping.** Round 1's guard scanned every `.py` file under
`automation/` for a bare ``\\.{field}\\b`` match, with no check that the file
had anything to do with `SkillsListPage`. That let a since-removed,
genuinely unreferenced `table_view_button` field on `SkillsListPage` pass
the guard undetected: `AgentsListPage` defines its OWN `card_view_button` /
`table_view_button` fields and uses them internally
(`self.table_view_button.click(...)`, `self.table_view_button.get_attribute
(...)` in `agents_list_page.py`), and those string-identical hits were
counted as "SkillsListPage.table_view_button is referenced" even though
no file ever wrote `<skills_list_page_var>.table_view_button`. The fix
(`_files_referencing_skills_list_page()`) restricts the reference search to
files that actually import/use `SkillsListPage` — plus the page object's
own source, so internal `self.<field>` usages inside `SkillsListPage`'s own
methods still count.

Pure source inspection, no browser/Playwright infra — same style as the
rest of `tests/unit/` (see `tests/unit/conftest.py`).
"""

import re
from pathlib import Path

AUTOMATION_ROOT = Path(__file__).resolve().parents[2]
PAGE_OBJECT_FILE = AUTOMATION_ROOT / "pages" / "skills_list_page.py"
CLASS_NAME = "SkillsListPage"

_FIELD_DEF_RE = re.compile(r"^\s*(\w+)\s*=\s*LocatorDescriptor\(", re.MULTILINE)


def _locator_descriptor_field_names(source: str) -> list[str]:
    return _FIELD_DEF_RE.findall(source)


def _files_referencing_skills_list_page() -> list[Path]:
    """Files in scope for dead-code reference counting.

    Always includes the page object's own source (so `self.<field>` usages
    inside `SkillsListPage`'s own methods count), plus every other file
    under `automation/` whose text mentions `SkillsListPage` at all (an
    import line or a direct instantiation) — i.e. a file that could
    plausibly hold a real `<skills_list_page_var>.<field>` reference.

    Deliberately excludes every file that never mentions `SkillsListPage`:
    those can only contribute same-named-field false positives from an
    unrelated class (the `AgentsListPage.card_view_button` /
    `.table_view_button` collision this fix closes).
    """
    files = [PAGE_OBJECT_FILE]
    for py_file in AUTOMATION_ROOT.rglob("*.py"):
        if py_file == PAGE_OBJECT_FILE or "__pycache__" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        if CLASS_NAME in text:
            files.append(py_file)
    return files


def test_skills_list_page_has_no_unreferenced_locator_descriptor_fields():
    """Every `LocatorDescriptor` field `SkillsListPage` defines must be used
    somewhere under `automation/` (a page-object method or a test) via
    `self.<field>` / `<page_var>.<field>` — otherwise it's dead weight that
    silently inflates the testid-coverage metric without ever exercising
    anything (`.agents/testing.md` § Locator policy — coverage rationale).

    Scoped to files that actually reference `SkillsListPage` (see
    `_files_referencing_skills_list_page`) — an unscoped grep over the whole
    tree would count another page object's same-named field usage (e.g.
    `AgentsListPage.table_view_button`) as if it referenced this class's
    field of the same name, which is exactly the bug that let an earlier,
    genuinely unreferenced `table_view_button` field ship past round 1's
    version of this guard."""
    source = PAGE_OBJECT_FILE.read_text(encoding="utf-8")
    field_names = _locator_descriptor_field_names(source)
    assert field_names, "expected at least one LocatorDescriptor field to check"

    scoped_files = _files_referencing_skills_list_page()

    unreferenced = []
    for field in field_names:
        usage_re = re.compile(rf"\.{re.escape(field)}\b")
        hits = 0
        for py_file in scoped_files:
            text = py_file.read_text(encoding="utf-8")
            for match in usage_re.finditer(text):
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.end())
                line = text[line_start:line_end if line_end != -1 else None]
                if "LocatorDescriptor(" in line:
                    continue  # skip the field's own definition line
                hits += 1
        if hits == 0:
            unreferenced.append(field)

    assert not unreferenced, (
        "SkillsListPage LocatorDescriptor field(s) defined but never "
        f"referenced anywhere in automation/: {unreferenced} — dead code "
        "(see entity_card_icon_field_is_dead_code_pattern.md)"
    )


def test_entity_card_icon_not_reintroduced_as_page_wide_locator():
    """Regression pin for the specific finding: `entity_card_icon` must not
    come back as an unscoped, page-wide `LocatorDescriptor` field on
    `SkillsListPage` — the scoped `CARD_ICON_SELECTOR` constant +
    `card_icon_locator()` helper is the only sanctioned shape for this
    testid on this page (one instance per visible card, always addressed
    scoped to a specific card)."""
    source = PAGE_OBJECT_FILE.read_text(encoding="utf-8")
    assert "entity_card_icon = LocatorDescriptor(" not in source, (
        "entity_card_icon reappeared as an unscoped page-wide field — "
        "it was removed as dead code in ELITEA-2428 round 1; use "
        "CARD_ICON_SELECTOR + card_icon_locator() instead"
    )
    assert 'CARD_ICON_SELECTOR = \'[data-testid="entity-card-icon"]\'' in source


def test_table_view_button_not_reintroduced_as_unreferenced_field():
    """Regression pin for the round-2 finding: `table_view_button` must not
    come back on `SkillsListPage` unless a test actually exercises table
    view on this page. This case only ever asserts card view (default,
    never toggled away), so the field has no genuine caller — reintroducing
    it would be exactly the unreferenced-field shape
    `test_skills_list_page_has_no_unreferenced_locator_descriptor_fields`
    exists to catch, and this pin fails fast even if that guard's scoping
    ever regresses."""
    source = PAGE_OBJECT_FILE.read_text(encoding="utf-8")
    assert "table_view_button = LocatorDescriptor(" not in source, (
        "table_view_button reappeared on SkillsListPage but ELITEA-2428's "
        "test never switches to table view — either wire a real caller for "
        "it on this page or leave it out (a future case that exercises "
        "table view should add it then, with its own reference)"
    )
