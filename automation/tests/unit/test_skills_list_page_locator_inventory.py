"""Static-analysis regression test for SkillsListPage's `LocatorDescriptor`
inventory (ELITEA-2428 review round 1; scoping fixes round 2 and round 3).

Guards against the dead-code shape a fresh-session reviewer flagged on this
PR's first round: a page-wide `LocatorDescriptor` field (`entity_card_icon`)
defined once but never invoked (`self.entity_card_icon` / `list_page.entity_
card_icon`) anywhere in `automation/`, because the actual per-card lookup
(`card_icon_locator()`) re-derives the same `entity-card-icon` testid as a
raw scoped-selector string constant (`CARD_ICON_SELECTOR`) instead of ever
calling the field. Root pattern is older tech debt in `AgentsListPage`
(untouched here) — see
`.agents/memory/qa-engineer/entity_card_icon_field_is_dead_code_pattern.md`.

**Round 2 fix — scoping (still incomplete).** Round 1's guard scanned every
`.py` file under `automation/` for a bare ``\\.{field}\\b`` match, with no
check that the file had anything to do with `SkillsListPage`. That let a
since-removed, genuinely unreferenced `table_view_button` field on
`SkillsListPage` pass the guard undetected: `AgentsListPage` defines its OWN
`card_view_button` / `table_view_button` fields and uses them internally,
and those string-identical hits were counted as
"SkillsListPage.table_view_button is referenced". Round 2 narrowed the file
set to "files whose text contains the bare substring `SkillsListPage`" —
but a *bare substring* match is itself collidable: `automation/pages/
agents_list_page.py` mentions `SkillsListPage` only in a comment
(`# CredentialsListPage/SkillsListPage/McpListPage; ...`), which pulled the
*entire* `AgentsListPage` file — and its own same-named fields — back into
scope. Several other page objects (`pipelines_list_page.py`,
`credentials_list_page.py`, `chat_page.py`, `artifacts_page.py`,
`notification_center_page.py`) carry the same kind of incidental
cross-reference comment. See
`.agents/memory/qa-engineer/dead_code_guard_class_name_substring_scoping_still_false_passes.md`.

**Round 3 fix — real usage signal, not substring.**
(`_files_referencing_skills_list_page()`) now requires either the actual
import line (`from pages.skills_list_page import SkillsListPage`) or an
instantiation call (`SkillsListPage(`) — a comment or docstring mentioning
the class name by itself no longer qualifies a file for scope. The page
object's own source is still always included, so internal `self.<field>`
usages inside `SkillsListPage`'s own methods still count.
`test_reference_scoping_excludes_incidental_class_name_mentions` proves this
directly against a synthetic collision fixture mirroring the real one
found in `agents_list_page.py`, rather than trusting the scoping code by
inspection alone (the lesson from round 2).

Pure source inspection, no browser/Playwright infra — same style as the
rest of `tests/unit/` (see `tests/unit/conftest.py`).
"""

import re
from pathlib import Path

AUTOMATION_ROOT = Path(__file__).resolve().parents[2]
PAGE_OBJECT_FILE = AUTOMATION_ROOT / "pages" / "skills_list_page.py"
CLASS_NAME = "SkillsListPage"

_FIELD_DEF_RE = re.compile(r"^\s*(\w+)\s*=\s*LocatorDescriptor\(", re.MULTILINE)

# A file is "in scope" only if it actually imports or instantiates the
# class — a bare mention of the class name (comment, docstring, cross-
# reference prose) does NOT qualify. This is deliberately narrower than
# `CLASS_NAME in text`: that substring check is what let an incidental
# comment in `agents_list_page.py` ("CredentialsListPage/SkillsListPage/
# McpListPage; ...") pull the whole `AgentsListPage` file — and its own
# same-named `card_view_button`/`table_view_button` fields — into scope.
_REAL_USAGE_RE = re.compile(
    r"from\s+pages\.skills_list_page\s+import\s+SkillsListPage\b"
    r"|\bSkillsListPage\s*\("
)


def _locator_descriptor_field_names(source: str) -> list[str]:
    return _FIELD_DEF_RE.findall(source)


def _files_referencing_skills_list_page(
    root: Path = AUTOMATION_ROOT, page_object_file: Path = PAGE_OBJECT_FILE
) -> list[Path]:
    """Files in scope for dead-code reference counting.

    Always includes the page object's own source (so `self.<field>` usages
    inside `SkillsListPage`'s own methods count), plus every other file
    under `root` that actually **imports or instantiates**
    `SkillsListPage` (see `_REAL_USAGE_RE`) — i.e. a file that could
    plausibly hold a real `<skills_list_page_var>.<field>` reference.

    Deliberately excludes any file that only *mentions* the class name in
    prose (a comment, a docstring cross-reference) without importing or
    instantiating it: those can only contribute same-named-field false
    positives from an unrelated class, exactly the
    `AgentsListPage.card_view_button` / `.table_view_button` collision
    this fix closes (round 2's bare-substring scoping still missed it).

    `root` / `page_object_file` are parameterized (default: the real
    `automation/` tree) purely so the scoping mechanism itself can be
    exercised against a synthetic fixture tree in a test, without needing
    to plant files inside the real source tree.
    """
    files = [page_object_file]
    for py_file in root.rglob("*.py"):
        if py_file == page_object_file or "__pycache__" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        if _REAL_USAGE_RE.search(text):
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


def test_reference_scoping_excludes_incidental_class_name_mentions(tmp_path):
    """Direct regression test for the round-2→round-3 finding: the scoping
    mechanism must key off a REAL import/instantiation signal, not a bare
    `"SkillsListPage"` substring.

    Builds a synthetic fixture tree that reproduces the exact collision a
    fresh-session reviewer traced statically in the real repo
    (`agents_list_page.py` mentions `SkillsListPage` only inside a comment,
    yet defines its own same-named `table_view_button` field/usage):

    - `pages/skills_list_page.py` — the page object under test.
    - `pages/agents_list_page.py` — mentions "SkillsListPage" ONLY in a
      comment; defines and uses its OWN `table_view_button` field. Must be
      EXCLUDED from scope, or its usage would count as a (false) reference
      for `SkillsListPage.table_view_button`.
    - `tests/ui/skills/test_real_caller.py` — actually
      `from pages.skills_list_page import SkillsListPage` and instantiates
      it, using `list_page.table_view_button`. Must be INCLUDED in scope —
      this is the genuine reference case the guard must still catch.

    This proves the fix by exercising the scoping function against a live
    collision, per `.agents/memory/qa-engineer/dead_code_guard_class_name_
    substring_scoping_still_false_passes.md` ("verify via a live collision,
    don't trust the scoping code")."""
    page_object_file = tmp_path / "pages" / "skills_list_page.py"
    page_object_file.parent.mkdir(parents=True)
    page_object_file.write_text(
        "class SkillsListPage(BasePage):\n"
        '    table_view_button = LocatorDescriptor(testid="skills-table-view-button")\n',
        encoding="utf-8",
    )

    incidental_file = tmp_path / "pages" / "agents_list_page.py"
    incidental_file.write_text(
        "class AgentsListPage(BasePage):\n"
        "    # Shared card layout with CredentialsListPage/SkillsListPage/McpListPage;\n"
        '    table_view_button = LocatorDescriptor(testid="agents-table-view-button")\n'
        "\n"
        "    def switch_to_table_view(self):\n"
        "        self.table_view_button.click()\n",
        encoding="utf-8",
    )

    real_caller_dir = tmp_path / "tests" / "ui" / "skills"
    real_caller_dir.mkdir(parents=True)
    real_caller_file = real_caller_dir / "test_real_caller.py"
    real_caller_file.write_text(
        "from pages.skills_list_page import SkillsListPage\n"
        "\n"
        "def test_something(page):\n"
        "    list_page = SkillsListPage(page)\n"
        "    list_page.table_view_button.click()\n",
        encoding="utf-8",
    )

    scoped_files = _files_referencing_skills_list_page(
        root=tmp_path, page_object_file=page_object_file
    )

    assert page_object_file in scoped_files, "the page object's own source must always be in scope"
    assert real_caller_file in scoped_files, (
        "a file that imports + instantiates SkillsListPage must be in scope — "
        "this is the genuine-reference case the guard must not lose"
    )
    assert incidental_file not in scoped_files, (
        "a file that only MENTIONS 'SkillsListPage' in a comment — without "
        "importing or instantiating it — must be EXCLUDED from scope; "
        "including it reproduces the exact false-pass a fresh-session "
        "reviewer traced in agents_list_page.py (round 2's bare-substring "
        "scoping did not close this)"
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
