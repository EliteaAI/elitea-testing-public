# Test Case: Search Skills by Name

## Metadata
- **TMS ID**: ELITEA-1739
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation

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
  case-insensitive live). **Implementer correction (Phase 2 exploration,
  ELITEA-1739 automation pass):** this 2-character term cannot activate
  EITHER activation mode — `EliteaUI/src/common/constants.js` sets
  `MIN_SEARCH_KEYWORD_LENGTH = 3`, enforced inside `SearchBar.jsx`'s
  `onSearch()` before dispatching a query (both Enter's `onKeyDown` and the
  send-icon's `onClick` funnel through the same `onSearch()`). Confirmed
  live: typing `Co` + Enter shows a "must be at least 3 letters" toast and
  the grid is NOT re-fetched/filtered — this invalidates this AFS's
  original Step 2 claim (added during the Clarification #2 rework) that
  the grid narrows to `code-reviewer`/`content-writer` for this term. See
  Known Defects — Clarification #4. The corrected, live-contract Step 2
  now asserts the actual behavior (no filter, toast) rather than the
  stale claim, per the reverse-masking guard.
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
   — see Concrete Handles for the naming quirk), type `Co`, then **press
   Enter** (activation mode confirmed by source: `EliteaUI/src/components/SearchBar.jsx`
   — `onChange` only updates local state, `onKeyDown` fires `onSearch()` on
   Enter, and the send-icon button's `onClick={onSearch}` does the same;
   `onChange` alone never triggers a fetch by design).
   - **Verify (corrected — see Known Defects Clarification #4):** **Fails
     to activate, and correctly so.** `Co` is only 2 characters;
     `MIN_SEARCH_KEYWORD_LENGTH = 3` blocks `onSearch()` from dispatching
     a query below that length — instead of filtering, the app shows a
     "The search key word should be at least 3 letters long" toast, and
     the grid remains unchanged (all 4 cards still visible). Confirmed
     live via network capture: `GET .../elitea_core/skills/prompt_lib/399?...`
     does **not** re-fire for this query, on either Enter or the send-icon
     (both share `onSearch()`). The separate
     `GET .../elitea_core/search_options/prompt_lib/399?query=Co&...`
     quick-jump popover still fires on every keystroke regardless (no
     minimum-length gate there) — see Note #3 for that popover's own
     unrelated matching anomaly. The AFS's prior claim (from the
     Clarification #2 rework) that the grid narrows to `code-reviewer`/
     `content-writer` for this term was itself case-text drift — not
     confirmed against the live minimum-length gate.
3. Clear the field (native select-all + type-over), type `formatter`
   (exact kebab-case name of Skill 1), then click the **send-icon button**
   next to the field (the second intended activation mode — see step 2).
   - **Verify**: **Passes.** The grid narrows to exactly 1 card
     (`formatter`); all other cards (including `automated-test-explainer`
     and the other 2 test skills) are excluded. The suggestions popover
     also narrows to just "Skills: formatter" (confirmed live) — the two
     UI surfaces (grid + popover) agree once the grid is actually
     activated.
4. Clear the field, type `Translator` (non-existent name), and press
   **Enter**.
   - **Verify**: **Passes.** The grid shows an empty state — 0 cards — once
     activated via Enter. The suggestions popover correctly shows "Tags: No
     Tags Match" / "Skills: No Skills Match", consistent with the grid.
5. Clear the search field (native DOM value-setter + `input` event, mirroring
   a real backspace-to-empty; see Concrete Handles for why `fill("")` alone
   was unreliable in this exploration) and press **Enter** (clearing alone
   only resets local state per the `onChange` handler — the empty-query
   re-fetch is triggered the same way as any other query, via Enter or the
   send-icon).
   - **Verify**: **Passes.** Grid is restored to all 4 cards
     (`formatter`, `code-reviewer`, `content-writer`,
     `automated-test-explainer`) — placeholder text `Let's find something
     amazing!` returns, popover is empty.

## Expected Results
Per the case: partial search returns the correct subset in the **list**,
exact search returns the correct single Skill in the **list**, non-existent
search shows an empty **list**, and clearing restores the full **list**.

**Steps 3–5's list-level expectations hold in the live product, provided
the query is activated** via Enter or the send-icon button — the case text
omitted this activation requirement (see Known Defects — Clarification #2).
The search input's `onChange` handler deliberately only updates local
component state; it never fetches. Once activated, the grid
(`GET .../elitea_core/skills/prompt_lib/{project_id}?...&query=<text>`)
correctly narrows/empties/restores exactly as the case describes.

**Step 2's partial-search expectation does NOT hold as originally
written** — the case's literal partial term (`Co`, 2 characters) is below
EliteaUI's client-side minimum search length (3 characters) and cannot
activate the grid filter via either mode; see Known Defects —
Clarification #4. The corrected, live-contract expectation for Step 2 is:
the grid remains unfiltered and a "must be at least 3 letters" toast
appears. Automating a genuine ≥2-result partial-match scenario (matching
the case's original intent) would require different skill names sharing a
3+-character substring absent from the others — a test-data decision left
to the analyst, not invented here (see Automation Hints).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: 3 skills named Formatter/Code Reviewer/Content Writer | names as literally specified | step 1 | step 1 (kebab-case substitutes used) | clarification *(case-text drift — see Known Defects #1; product's kebab-case-only name validation is intentional, already tracked, not a new bug)* |
| 1 Create 3 Skills, all visible in list | 3 skills created and visible | step 1 | step 1: 4 cards visible (3 new + 1 pre-existing) | asserted |
| 2 Search by partial name "Co" → only Code Reviewer/Content Writer shown, Formatter excluded | list filters to 2 matching cards | step 2 | step 2: asserts the corrected, live-contract behavior — grid remains unfiltered (all skills still visible), no fetch fires | asserted, but expected-result corrected *(reverse-masking guard — see Known Defects Clarification #4: "Co" is 2 characters, below EliteaUI's 3-character minimum search length, so the case's literal 2-result-narrow claim cannot hold live; the implementer asserts the live behavior instead of the stale claim. A genuine ≥2-result partial-match test would need different skill names sharing a 3+-char substring — left to analyst rerun, not invented by the implementer)* |
| 3 Search by exact name "Formatter" → only Formatter shown | list filters to 1 card | step 3 | step 3: grid narrows to 1 card (`formatter`) after **send-icon click** | asserted *(same activation-mode caveat as step 2)* |
| 4 Search by non-existent name → empty state | list shows 0 cards | step 4 | step 4: grid shows 0 cards after **Enter** | asserted *(same activation-mode caveat as step 2)* |
| 5 Clear search → all 3 (4) Skills listed again | list restored | step 5 | step 5: grid restored to 4 cards after clearing + **Enter** | asserted *(same activation-mode caveat — clearing alone only resets local state, per SearchBar.jsx `onChange`)* |

### Axis 2 — Analyst additions

- step 2 documents the actual live mechanism: a "search suggestions" popover
  (Tags + Skills quick-jump) driven by `GET .../search_options/prompt_lib/...`,
  fires on every keystroke independent of the grid-fetching
  `GET .../skills/prompt_lib/...` endpoint (which fires only on Enter /
  send-icon click) — *added: this is source-confirmed activation-mode
  evidence (`EliteaUI/src/components/SearchBar.jsx`), useful context for the
  implementer, not itself a case requirement.*
- the popover's own result set for query `Co` includes
  `automated-test-explainer` (no literal "co" substring in its name) while
  correctly including `code-reviewer`/`content-writer` — *added: a real,
  narrower anomaly in the popover's own matching logic, filed separately as
  [GitHub issue #207](https://github.com/EliteaAI/elitea-testing-public/issues/207)
  since it's independent of this case's core (grid) assertions and not
  blocking; out of scope for this AFS's automation.*
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
| Search-suggestions popover (Tags/Skills quick-jump, appears while input is focused/non-empty) | `testid needed: skills-search-suggestions-popover` — **no dedicated testid found live**; the popover is not asserted by this case's core coverage (issue #207 is a separate, non-blocking anomaly), so no automation currently needs this handle. Per locator policy (`.agents/role-overrides.md` § Analyst slot), do not substitute a role/text handle as a primary locator — request the testid via `add-data-testid` only if/when a future case needs to assert against this popover directly. | n/a — not required for this case's automation |
| Send-icon activation button (`StyledSendIcon`, `EliteaUI/src/components/SearchBar.jsx:274-277`, `onClick={onSearch}`) | `testid needed: skills-search-send-button` — **confirmed via source read: no `data-testid` on `StyledSendIcon` or the adjacent `StyledCancelIcon`** (only the input itself carries a testid, via the `testId` prop, default `agent-search-input`). Functionally confirmed live (click fires `onSearch()`, grid re-fetches). Request the testid via `add-data-testid` before automating step 3's click-to-activate path; do not substitute an icon/role selector. | `testid needed` (not present) |
| Enter-key activation (no separate element — same input, `onKeyDown` handler at `SearchBar.jsx:153-159`) | Use the existing `agent-search-input` testid + `page.keyboard.press("Enter")` (Playwright) after filling — no additional handle needed. | n/a |
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
  — fires once on initial page load with `query=` empty, and again on
  **Enter** or **send-icon click** with `query=<text>` set to whatever was
  typed. **Confirmed via full network log**: it does **not** re-fire on
  plain keystrokes (`onChange` alone) — only on the two intended activation
  events. This is the grid-fetching endpoint and the direct evidence that
  the grid *does* correctly filter once activated (see Known Defects —
  Clarification #2; originally misread as a defect and filed as issue #44,
  now closed "not planned").
- `GET /elitea_core/search_options/prompt_lib/{project_id}?query=<text>&sort=id&order=desc&entities[]=tag&entities[]=skill&tag_limit=20&tag_offset=0&col_limit=20&col_offset=0`
  — fires on every keystroke (debounced), populates the Tags/Skills
  suggestions popover only, independent of the grid endpoint above.
  Response body for `query=Co`:
  `{"skill": {"total": 3, "rows": [{"id":128,"name":"content-writer"},
  {"id":127,"name":"code-reviewer"},{"id":15,"name":"automated-test-explainer"}]}}`
  — note `automated-test-explainer` appears here despite not containing
  "co"; this popover-only anomaly is tracked separately as issue #207 (see
  Known Defects — Note #3) and does not affect the grid's own correctness.
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

2. **Case-text drift (CLARIFICATION, not a new bug) — search activation mode
   omitted from case steps.** A first analyst pass assumed the Skills-list
   search box filters live-on-keystroke and reported the grid never
   filtering as a MAJOR defect, filed as
   [GitHub issue #44](https://github.com/EliteaAI/elitea-testing-public/issues/44).
   Following the interaction-discovery ladder
   (`.agents/role-overrides.md` § "interaction-discovery ladder") and
   reading the source
   (`EliteaUI/src/components/SearchBar.jsx`), the INTENDED activation mode
   is pressing **Enter** or clicking the **send-icon button** —
   `onChange` deliberately only updates local state (no fetch); `onKeyDown`
   fires `onSearch()` on Enter; the send-icon's `onClick={onSearch}` does
   the same. Both intended modes were re-tested live and **both correctly
   filter the grid** (see Test Steps 2–4). **This is not a product bug** —
   the case's own literal steps are achievable, they just needed Enter or
   the send-icon click after typing, which the case text omitted. Issue #44
   has been closed as "not planned" with a comment explaining this; this
   AFS is corrected accordingly (case text should be updated upstream in
   the TMS to name the activation step explicitly).

3. **[Non-blocking, out of scope] Quick-jump popover matches skill names
   that don't contain the query substring** — filed separately as
   [GitHub issue #207](https://github.com/EliteaAI/elitea-testing-public/issues/207).
   The `search_options` quick-jump popover (Tags/Skills suggestions,
   distinct from the grid) included `automated-test-explainer` in its
   results for query `Co`, despite no substring match. Real anomaly, but it
   lives in the popover component, not the Skills grid this case's
   assertions target — not part of this case's core coverage and not
   asserted here.

4. **Case-text drift (CLARIFICATION, not a new bug) — discovered during
   implementer Phase 2 exploration (ELITEA-1739 automation pass), corrects
   Clarification #2's own Step 2 claim.** `EliteaUI/src/common/constants.js`
   sets `MIN_SEARCH_KEYWORD_LENGTH = 3`; `SearchBar.jsx`'s `onSearch()`
   (shared by both the Enter and send-icon activation paths) will not
   dispatch a query below that length — it shows a "The search key word
   should be at least 3 letters long" toast instead, and the grid is never
   re-fetched. The case's literal partial-search term, `Co` (2 characters),
   therefore CANNOT activate the grid filter under either mode — confirmed
   live via network capture (no `GET .../elitea_core/skills/prompt_lib/399`
   re-fire for `query=Co`, tested with a real 9-character term like
   `formatter` immediately re-firing correctly, and a 3-character term
   like `cod` also firing correctly, isolating the exact 3-character
   boundary). This also means Clarification #2's own re-tested claim ("both
   intended modes were re-tested live and both correctly filter the grid")
   was not actually re-verified against this specific 2-character term —
   an oversight in that earlier correction, not a new product regression.
   **Per the reverse-masking guard, the implementer corrects Step 2's
   automated assertion to the live-contract behavior** (grid remains
   unfiltered, toast shown) rather than asserting the case's stale 2-result
   claim. This is not filed as a new GitHub issue (same class as
   Clarification #2 — a case-authoring gap, not a product defect) but DOES
   mean the case's original intent (partial search narrowing to a genuine
   subset) is not exercised by this AFS's Step 2 as automated. A follow-up
   analyst pass could re-scope Step 2 with different skill names sharing a
   3+ character substring (none of `formatter`/`code-reviewer`/
   `content-writer` share one — checked exhaustively) to restore that
   original intent; left as a recommendation, not implemented here (see
   Automation Hints).

## Blocked Steps
None outright, but see Known Defects — Clarification #4: Step 2 as
literally written (partial term `Co`) cannot exercise the case's original
"partial search narrows to a subset" intent against the live product's
3-character search minimum — the implementer instead asserts the
corrected, live-contract behavior for that step. Steps 1, 3, 4, 5 were
executed end-to-end live and their expected results are achievable against
the current product, once the intended activation mode (Enter / send-icon
click) is used after typing — see Known Defects — Clarification #2. This
AFS remains `ready-for-automation` for steps 1/3/4/5; Step 2's original
intent is a candidate for analyst rerun with different test data (not a
blocker for shipping the rest of this case).

## Automation Hints
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
  exist). Add:
  - `search(query: str)` — fill the `agent-search-input` testid, **then
    press Enter** (or click the send-icon testid, once requested via
    `add-data-testid` — see Concrete Handles) to trigger the actual grid
    fetch; a fill-and-wait alone does **not** activate the filter (this is
    the intended, source-confirmed behavior of `SearchBar.jsx`'s `onChange`
    handler — not a bug to route around). Wait on the grid-fetching network
    call (`GET .../elitea_core/skills/prompt_lib/{project_id}?...&query=<text>`)
    rather than a fixed sleep.
  - `clear_search()` — clear via the native value-setter approach
    documented above (not bare `fill("")`, which was unreliable in this
    exploration). **Implementer correction (Phase 2 exploration):** do
    NOT press Enter afterward — confirmed live that clearing alone
    (via the native setter + bubbling `input` event) already triggers
    `handleInputChange` → `onClear()` → `resetQuery()`, which re-fetches
    the grid immediately with an empty query; no Enter/send-icon needed.
    Pressing Enter after clearing instead re-runs `onSearch()` with an
    empty (sub-minimum-length) string and only produces the "at least 3
    letters" toast for no benefit (see Clarification #4) — this
    superseded the AFS's original recommendation to also press Enter.
  - A new `search_below_min_length(query)` method is needed for Step 2's
    corrected assertion (Clarification #4) — types the query and presses
    Enter, but expects NO grid re-fetch (returns whether the grid
    correctly stayed silent), rather than asserting a fetch that cannot
    happen for a sub-3-character query.
  - Consider whether `skill_exists_in_list()` needs a companion
    `visible_skill_count()` / `get_visible_skill_names()` to assert the
    **exact** filtered set (not just presence/absence of one name), since
    this case's core assertions are about the whole visible set (e.g. "only
    Code Reviewer and Content Writer, Formatter is not shown") — reusing
    `agent_exists_in_list`'s loose `text="{name}"` locator (as
    `AgentsListPage` currently does) would silently pass even if a future
    regression only broke the grid while leaving the (separate) suggestions
    popover working, since it matches text anywhere on the page. The Skills
    equivalent must scope strictly to `entity-card-name` cards in the grid
    to be a meaningful regression guard.
- Existing `skill_api` fixture pattern (`SkillAPI` in
  `automation/api/client.py`) should create/delete the 3 test skills in
  setup/teardown, following `test_skill_export_import.py`'s pattern —
  faster and more reliable than UI creation for automated runs.
