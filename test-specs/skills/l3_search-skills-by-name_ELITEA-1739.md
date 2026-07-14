# Test Case: Search Skills by Name

## Metadata
- **TMS ID**: ELITEA-1739
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: defect-found

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills section is available.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill 1 name: `formatter` — **not** `"Formatter"` as literally written in the
  case's Test Data table. See Known Defects/Clarification #1 — the live Skill
  `Name *` field enforces lowercase-kebab-case-only client-side validation
  (same behavior already tracked for ELITEA-1737/1738, see
  `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`); a
  capitalized single word like `"Formatter"` is rejected with "Name must be
  lowercase letters, digits and hyphens only (no spaces), and cannot start or
  end with a hyphen." Confirmed live in this run (screenshot: typing
  `Formatter` into the Name field shows this exact validation message).
- Skill 2 name: `code-reviewer` (kebab-case equivalent of case's "Code Reviewer").
- Skill 3 name: `content-writer` (kebab-case equivalent of case's "Content Writer").
- Skill description (all 3): `"Test skill for ELITEA-1739 search-by-name
  verification."` (any non-empty string satisfies the required field; content
  not asserted by this case).
- Skill instructions (all 3): any non-empty string under the 2500-char limit,
  e.g. `"You are a test skill created for ELITEA-1739 search-by-name
  verification. Respond with FORMATTER."` (content not asserted by this case).
- Partial search term: `Co` (case-preserved as written; matching is
  case-insensitive live).
- Exact search term: `formatter` (kebab-case equivalent of case's "Formatter").
- Non-existent search term: `Translator` (as written in the case).
- Pre-existing skill in the same project at exploration time: `automated-test-explainer`
  (id `15`) — present throughout, relevant because it unexpectedly appears in
  partial-match results (see Known Defects).

No `reuse-existing` or `generate-shared-with-cleanup` data applies — search
verification only needs the 3 skills created fresh and torn down in the same
run.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`, create 3 skills named `formatter`,
   `code-reviewer`, `content-writer` (fill Name/Description/Instructions,
   Save, confirm the "unsaved changes" nav-blocker dialog for each — same
   flow as ELITEA-1737/1738). Navigate to `${BASE_URL}/skills/all`.
   - **Verify**: all 3 new skill cards plus the pre-existing
     `automated-test-explainer` (4 total) render in the grid. Confirmed live
     (skill ids `126`, `127`, `128`).
2. Click into the page-header search box (`data-testid="agent-search-input"`
   — see Concrete Handles for the naming quirk) and type `Co`.
   - **Verify**: **Fails.** The Skills grid does **not** filter — all 4 cards
     remain visible, unchanged. A separate dropdown/popover appears below the
     search box showing "Tags: No Tags Match" and "Skills:
     automated-test-explainer, code-reviewer, content-writer" — this is a
     global quick-jump suggestions panel, not a list filter, and its result
     set doesn't match a plain substring rule either (see Known Defects #2).
     Network capture: `GET .../elitea_core/search_options/prompt_lib/399?query=Co&...`
     fires; `GET .../elitea_core/skills/prompt_lib/399?...&query=...` (the
     actual grid-fetching endpoint) does **not** re-fire.
3. Clear the field (native select-all + type-over) and type `formatter`
   (exact kebab-case name of Skill 1).
   - **Verify**: **Fails** for the same reason as step 2 — grid unchanged
     (still 4 cards). The suggestions popover correctly narrows to just
     "Skills: formatter" this time (confirmed live), but that popover is not
     the Skills list the case is about.
4. Clear the field and type `Translator` (non-existent name).
   - **Verify**: **Fails** for the same reason — grid still shows all 4
     cards (no empty state at the grid level). The suggestions popover
     correctly shows "Tags: No Tags Match" / "Skills: No Skills Match".
5. Clear the search field (native DOM value-setter + `input` event, mirroring
   a real backspace-to-empty; see Concrete Handles for why `fill("")` alone
   was unreliable in this exploration).
   - **Verify**: grid still shows the same 4 cards it always showed (never
     changed across steps 2–5) — placeholder text `Let's find something
     amazing!` returns, popover is empty. This is the one case expectation
     that trivially "passes", precisely because the grid was never filtered
     to begin with.

## Expected Results
Per the case: partial search returns the correct subset in the **list**,
exact search returns the correct single Skill in the **list**, non-existent
search shows an empty **list**, and clearing restores the full **list**.

**None of steps 2–4's list-level expectations hold in the live product** — see
Known Defects. Only step 5 (list unchanged after clearing) holds, incidentally,
because there was never any list-level filtering to undo.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: 3 skills named Formatter/Code Reviewer/Content Writer | names as literally specified | step 1 | step 1 (kebab-case substitutes used) | clarification *(case-text drift — see Known Defects #1; product's kebab-case-only name validation is intentional, already tracked, not a new bug)* |
| 1 Create 3 Skills, all visible in list | 3 skills created and visible | step 1 | step 1: 4 cards visible (3 new + 1 pre-existing) | asserted |
| 2 Search by partial name "Co" → only Code Reviewer/Content Writer shown, Formatter excluded | list filters to 2 matching cards | step 2 | step 2: grid unchanged (4 cards, not 2) | **defect** *(see Known Defects #2 — filed as GitHub issue #44)* |
| 3 Search by exact name "Formatter" → only Formatter shown | list filters to 1 card | step 3 | step 3: grid unchanged (4 cards, not 1) | **defect** *(same root cause as #2, not re-filed separately)* |
| 4 Search by non-existent name → empty state | list shows 0 cards | step 4 | step 4: grid unchanged (4 cards, not 0) | **defect** *(same root cause as #2, not re-filed separately)* |
| 5 Clear search → all 3 (4) Skills listed again | list restored | step 5 | step 5: grid unchanged throughout (still 4 cards) | asserted *(trivially true — list was never filtered)* |

### Axis 2 — Analyst additions

- step 2 documents the actual live mechanism: a "search suggestions" popover
  (Tags + Skills quick-jump) driven by `GET .../search_options/prompt_lib/...`,
  entirely separate from the grid-fetching `GET .../skills/prompt_lib/...`
  endpoint — *added: this is the root-cause evidence for the defect, useful
  for whoever picks up the fix, not itself a case requirement.*
- step 2 documents the popover's own result set for query `Co` includes
  `automated-test-explainer` (no literal "co" substring in its name) while
  excluding `formatter` — *added: a second, narrower oddity in the
  popover's matching logic, noted for the fix owner but not filed as a
  separate ticket since the primary defect (grid never filters) makes this
  moot for the case's own pass/fail criteria.*
- step 2 asserts no console errors from the app itself during normal typing,
  and separately documents one transient CORS/redirect error on a single
  debounced `search_options` request (302 → `dev.elitea.ai` auth-oidc-login,
  immediately followed by a successful retry) — *added: standard
  side-channel check; the transient error is called out but not filed since
  it self-recovered and wasn't reproducible at will (likely a local
  dev-session blip, not a reproducible product defect).*

## Cleanup
1. Delete each of the 3 test skills via the overflow menu → "Delete skill" →
   type the skill name to confirm → click Delete (same flow as
   ELITEA-1737/1738). Verified in this run: all 3 (`formatter` id `126`,
   `code-reviewer` id `127`, `content-writer` id `128`) deleted cleanly;
   grid returned to just the pre-existing `automated-test-explainer`.
2. For automated cleanup, use the existing `skill_api` fixture
   (`SkillAPI.delete_skill(skill_id)`, `automation/api/client.py:1182`) in
   test teardown for all 3 created skill IDs, mirroring the pattern in
   `test_skill_export_import.py` — do not rely on UI delete in automated
   tests (slower, more brittle); UI-delete was only used here for
   interactive verification/cleanup.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Skills-list page-header search input | `page.get_by_test_id("agent-search-input")` — confirmed live; **note**: this is the *same* shared component/testid used on `/agents/all` (`AgentsListPage.search_input`) — the testid literally says "agent" even though it renders on the Skills page. Not a functional defect (it works), but a naming smell worth flagging to `add-data-testid` if a Skills-specific testid is wanted later. | `page.locator('input[placeholder="Let\'s find something amazing!"]')` |
| Search-suggestions popover (Tags/Skills quick-jump, appears while input is focused/non-empty) | `page.get_by_role("tooltip")` scoped, containing `page.get_by_text("Skills")` header — **no dedicated testid found**; confirmed live via accessibility snapshot (renders as a `tooltip` role node with a `list`/`listitem` structure) | none robust yet — flag via `add-data-testid` if this AFS's defect fix ends up wiring the popover into an actual filter and it needs direct assertions |
| Skills grid cards | Existing `SkillsListPage.skill_exists_in_list(name)` (`automation/pages/skills_list_page.py`) — uses `page.get_by_test_id("entity-card-name")` | n/a — reuse existing page object method |
| Skill create form fields | Existing `SkillFormPage` (`automation/pages/skill_form_page.py`) — `name_input`, `description_input`, `instructions_editor_content`, `save_button` | n/a — reuse existing page object |
| Delete-skill flow | Existing `SkillDetailPage` methods / testids `skill-controls-menu-button`, `skill-delete-menu-item`, `delete-confirm-name-input` (per ELITEA-1737/1738 AFS) | n/a — reuse existing page object |

**Clearing-the-search-field caveat (important for the implementer):** Playwright's
`.fill("")` and even `Control+a` + `Delete` were **unreliable** on this
specific input during this exploration — one attempt left stale characters
concatenated with new input (`"Coformatter"`), and a `Control+a` press only
deleted one character instead of selecting the full value. What **did**
work reliably: setting the input's value via the native HTMLInputElement
value setter and dispatching a bubbling `input` event
(`Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,
'value').set.call(el, ''); el.dispatchEvent(new Event('input', {bubbles:
true}))`), matching the existing `AgentsListPage.clear_search()`
implementation's likely intent (`self.search_input.fill("")`) — **if the
implementer reuses `clear_search()` as-is for a Skills-search test, verify
it doesn't hit the same flakiness observed here**; consider an explicit
triple-click-then-type or a native backspace loop as a more robust
alternative if `fill("")` proves flaky in CI.

## Network Behavior
- `GET /elitea_core/skills/prompt_lib/{project_id}?sort_by=created_at&sort_order=desc&query=&tags=&limit=20&offset=0`
  — fires **exactly once**, on initial page load, with `query=` always empty.
  **Confirmed via full network log**: no follow-up call to this endpoint
  fires on any subsequent keystroke, across every query tried (`Co`,
  `Coformatter`, `formatter`, `Translator`, and clearing) in this run. This
  is the direct evidence for the defect (Known Defects #2 / GitHub issue #44).
- `GET /elitea_core/search_options/prompt_lib/{project_id}?query=<text>&sort=id&order=desc&entities[]=tag&entities[]=skill&tag_limit=20&tag_offset=0&col_limit=20&col_offset=0`
  — fires on every keystroke (debounced), populates the Tags/Skills
  suggestions popover only. Response body for `query=Co`:
  `{"skill": {"total": 3, "rows": [{"id":128,"name":"content-writer"},
  {"id":127,"name":"code-reviewer"},{"id":15,"name":"automated-test-explainer"}]}}`.
- One `search_options` call (for `query=Co`) received a `302` redirect to
  `https://dev.elitea.ai/forward-auth/auth_oidc/login?...`, which failed
  with a browser CORS error (`net::ERR_FAILED`); the very next debounced
  call with the same query returned `200` normally. Transient, self-healed,
  not reproduced a second time in this run — documented, not filed.

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a new bug)** — the case's Test Data
   names ("Formatter", "Code Reviewer", "Content Writer", capitalized with
   spaces) cannot be created live: the Skill `Name *` field's kebab-case-only
   client-side validation (confirmed live in this run, and already tracked
   for ELITEA-1737/1738 — see
   `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`)
   rejects them. This AFS substitutes kebab-case equivalents
   (`formatter`, `code-reviewer`, `content-writer`) that preserve the case's
   search-matching intent. Not re-filed as a new issue — same underlying,
   already-documented product behavior.

2. **[MAJOR] Skills list search box does not filter the Skills grid** — filed
   as [GitHub issue #44](https://github.com/EliteaAI/elitea-testing-public/issues/44).
   The page-header search input never triggers a re-fetch of the Skills
   grid (confirmed via full network log: the grid-fetching endpoint fires
   once at page load and never again, regardless of what's typed). Instead,
   typing only drives a separate "search suggestions" popover
   (Tags/Skills quick-jump) that doesn't affect the grid. This means **all
   of the case's core assertions (steps 2–4) fail against the live
   product** — the Skills list cannot currently be filtered by name through
   this UI at all. This is the reason for this AFS's `defect-found` status;
   automating the case as literally written would require asserting
   behavior the product does not have.

## Blocked Steps
None in the sense of "couldn't execute" — all 5 case steps were executed
end-to-end live. However, steps 2–4's **expected results cannot be achieved**
against the current product (see Known Defects #2), so this AFS cannot be
handed off as `ready-for-automation` — automating it now would mean writing
assertions for a filter behavior that doesn't exist, or asserting the wrong
thing (the popover) to make a test pass, which would mask the defect. Per
skill discipline (`test-case-analysis` § Classify findings), this AFS stops
at `defect-found`; re-run analysis once issue #44 is fixed to confirm actual
grid-filtering behavior and produce the automatable version of this spec.

## Automation Hints (for after issue #44 is fixed)
- Framework: Playwright + pytest, per `.agents/testing.md`. Likely home:
  `automation/tests/ui/skills/test_skill_management.py` (mirrors
  `TestAgentList.test_agent_search` / `test_agent_search_no_results` in
  `automation/tests/ui/agents/test_agent_management.py`), or a new
  `test_skill_search.py` if the team prefers a dedicated file.
- `SkillsListPage` needs a **new `search()` / `clear_search()` pair**
  analogous to `AgentsListPage.search()` / `clear_search()` — currently
  `SkillsListPage` has no search method at all (confirmed via source read
  before this run: only `navigate`, `navigate_to_create`,
  `skill_exists_in_list`, `wait_for_skill_absent`, and the import methods
  exist). Once issue #44 is fixed and the grid actually filters, add:
  - `search(query: str)` — fill the `agent-search-input` testid, wait for
    network (the grid endpoint should then re-fire with `query=<text>`).
  - `clear_search()` — clear via the native value-setter approach
    documented above (not bare `fill("")`) if `fill("")` proves flaky.
  - Consider whether `skill_exists_in_list()` needs a companion
    `visible_skill_count()` / `get_visible_skill_names()` to assert the
    **exact** filtered set (not just presence/absence of one name), since
    this case's core assertions are about the whole visible set (e.g. "only
    Code Reviewer and Content Writer, Formatter is not shown") — reusing
    `agent_exists_in_list`'s loose `text="{name}"` locator (as
    `AgentsListPage` currently does) would NOT have caught this defect,
    since it matches text anywhere on the page including the (currently
    non-functional) suggestions popover. The Skills equivalent must scope
    strictly to `entity-card-name` cards in the grid to be a meaningful
    regression guard.
- Existing `skill_api` fixture pattern (`SkillAPI` in
  `automation/api/client.py`) should create/delete the 3 test skills in
  setup/teardown, following `test_skill_export_import.py`'s pattern —
  faster and more reliable than UI creation for automated runs.
