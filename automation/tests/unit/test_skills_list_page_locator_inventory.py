"""Static-analysis regression test for SkillsListPage's `LocatorDescriptor`
inventory (ELITEA-2428 review round 1).

Guards against the dead-code shape a fresh-session reviewer flagged on this
PR's first round: a page-wide `LocatorDescriptor` field (`entity_card_icon`)
defined once but never invoked (`self.entity_card_icon` / `list_page.entity_
card_icon`) anywhere in `automation/`, because the actual per-card lookup
(`card_icon_locator()`) re-derives the same `entity-card-icon` testid as a
raw scoped-selector string constant (`CARD_ICON_SELECTOR`) instead of ever
calling the field. Root pattern is older tech debt in `AgentsListPage`
(untouched here) — see
`.agents/memory/qa-engineer/entity_card_icon_field_is_dead_code_pattern.md`.

Pure source inspection, no browser/Playwright infra — same style as the
rest of `tests/unit/` (see `tests/unit/conftest.py`).
"""

import re
from pathlib import Path

AUTOMATION_ROOT = Path(__file__).resolve().parents[2]
PAGE_OBJECT_FILE = AUTOMATION_ROOT / "pages" / "skills_list_page.py"

_FIELD_DEF_RE = re.compile(r"^\s*(\w+)\s*=\s*LocatorDescriptor\(", re.MULTILINE)


def _locator_descriptor_field_names(source: str) -> list[str]:
    return _FIELD_DEF_RE.findall(source)


def test_skills_list_page_has_no_unreferenced_locator_descriptor_fields():
    """Every `LocatorDescriptor` field `SkillsListPage` defines must be used
    somewhere under `automation/` (a page-object method or a test) via
    `self.<field>` / `<page_var>.<field>` — otherwise it's dead weight that
    silently inflates the testid-coverage metric without ever exercising
    anything (`.agents/testing.md` § Locator policy — coverage rationale)."""
    source = PAGE_OBJECT_FILE.read_text(encoding="utf-8")
    field_names = _locator_descriptor_field_names(source)
    assert field_names, "expected at least one LocatorDescriptor field to check"

    unreferenced = []
    for field in field_names:
        usage_re = re.compile(rf"\.{re.escape(field)}\b")
        hits = 0
        for py_file in AUTOMATION_ROOT.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue
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
