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
- Skill 2 name: `content-reviewer` — **renamed from `code-reviewer`** (analyst
  rerun, this amendment). See Known Defects — Clarification #5 for why:
  the original kebab-case trio (`formatter`/`code-reviewer`/`content-writer`)
  shares **no natural 3+-character substring at all** between any two names
  (checked exhaustively — confirmed empty for every pair), so no partial
  term could ever satisfy the case's core "type a partial name, see the
  matching subset" intent without a rename. `content-reviewer` is a minimal,
  same-family rename of `code-reviewer` (still "a reviewer skill", just
  reviewing content instead of code) chosen specifically to share the
  `content` token with `content-writer` — see the rationale in
  Clarification #5 for why `formatter` was left untouched (it anchors
  Step 3's exact-match assertion) and why the more obvious `ter` substring
  (already shared naturally between `formatter`/`content-writer`) was
  rejected.
- Skill 3 name: `content-writer` (kebab-case equivalent of case's "Content
  Writer") — **unchanged**.
- Skill description (all 3): `"Test skill for ELITEA-1739 search-by-name
  verification."` (any non-empty string satisfies the required field; content
  not asserted by this case). **Important, discovered this amendment:** the
  Skills grid search endpoint matches this description text too, not just
  the name — see Clarification #5. This shared description string does
  NOT itself contain `content` (or `format`/`formatter`), so it does not
  contaminate either search term used in this AFS; keep it that way if the
  description is ever changed.
- Skill instructions (all 3): any non-empty string under the 2500-char limit,
  e.g. `"You are a test skill created for ELITEA-1739 search-by-name
  verification. Respond with FORMATTER."` (content not asserted by this case).
- Partial search term: `content` (7 characters — well above the 3-character
  minimum). **Corrected this amendment (analyst rerun following the
  implementer's Clarification #4 finding — see Known Defects Clarification
  #5 for the full investigation):** matches `content-writer` and
  `content-reviewer` (renamed above) by substring in the NAME; excludes
  `formatter` (no `content` substring) and the pre-existing
  `automated-test-explainer` (no `content` substring in name OR
  description). Live-verified via network capture: grid response for
  `query=content` returns `{"total": 2, "rows": [{"id":..,"name":
  "content-writer"}, {"id":..,"name":"content-reviewer"}]}` — exactly the
  2 expected cards, nothing else. This restores the case's original
  partial-match intent (a genuine narrow-to-a-subset assertion), which
  Clarification #4's correction had left unexercised.
- Exact search term: `formatter` (kebab-case equivalent of case's
  "Formatter") — **unchanged, and re-verified this amendment** to still
  isolate exactly 1 card after the `code-reviewer` → `content-reviewer`
  rename (network response: `{"total": 1, "rows": [{"name":
  "formatter"}]}`) — confirming the rename does not regress Step 3.
- Non-existent search term: `Translator` (as written in the case) — unchanged.
- Pre-existing skill in the same project at exploration time: `automated-test-explainer`
  (id `15`) — present throughout, relevant because it unexpectedly appears in
  partial-match results **for some terms** (see Known Defects — both
  Clarification #3, the popover-only anomaly, and Clarification #5, the
  newly-discovered grid-level description-matching behavior). The
  corrected term `content` was chosen specifically because it does NOT
  appear in this skill's name or description, so it is correctly excluded
  in this AFS's Step 2.

No `reuse-existing` or `generate-shared-with-cleanup` data applies — search
verification only needs the 3 skills created fresh and torn down in the same
run.

## Test Steps
1. Navigate to `${BASE_URL}/skills/create`, create 3 skills named `formatter`,
   `content-reviewer`, `content-writer` (fill Name/Description/Instructions,
   Save, confirm the "unsaved changes" nav-blocker dialog for each — same
   flow as ELITEA-1737/1738). Navigate to `${BASE_URL}/skills/all`.
   - **Verify**: all 3 new skill cards plus the pre-existing
     `automated-test-explainer` (4 total) render in the grid. Confirmed live
     this amendment (skill ids `438` `formatter`, `439` `content-reviewer`,
     `440` `content-writer` — re-verified end-to-end in a fresh run; prior
     AFS versions used ids `126`/`127`/`128` for the original
     `code-reviewer` name, now superseded).
2. Click into the page-header search box (`data-testid="agent-search-input"`
   — see Concrete Handles for the naming quirk), type `content`, then
   **press Enter** (activation mode confirmed by source:
   `EliteaUI/src/components/SearchBar.jsx` — `onChange` only updates local
   state, `onKeyDown` fires `onSearch()` on Enter, and the send-icon
   button's `onClick={onSearch}` does the same; `onChange` alone never
   triggers a fetch by design).
   - **Verify (corrected this amendment — see Known Defects Clarification
     #5):** **Passes, and exercises the case's actual partial-match
     intent.** `content` (7 characters, above the 3-character minimum)
     activates the grid fetch and narrows it to exactly 2 cards:
     `content-writer` and `content-reviewer`; `formatter` and the
     pre-existing `automated-test-explainer` are correctly excluded.
     Confirmed live via network capture:
     `GET .../elitea_core/skills/prompt_lib/399?...&query=content` →
     `{"total": 2, "rows": [{"id":440,"name":"content-writer"},
     {"id":439,"name":"content-reviewer"}]}`. Zero console errors during
     this interaction. This step previously (Clarification #4) asserted a
     no-op/toast edge case instead of a real partial-match narrowing,
     because the case's literal term `Co` (2 characters) could never
     activate the grid filter — see Clarification #4 for that history,
     and Clarification #5 for why `Co`/`ter` were replaced with `content`
     plus the `content-reviewer` rename rather than simply picking a
     different 2-character-safe term.
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
     (`formatter`, `content-reviewer`, `content-writer`,
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

**Step 2's partial-search expectation, as originally written, could not
hold live** — the case's literal partial term (`Co`, 2 characters) is
below EliteaUI's client-side minimum search length (3 characters) and
cannot activate the grid filter via either mode; see Known Defects —
Clarification #4. **This amendment restores the case's original intent**
by correcting the test data instead of the assertion: partial term
`content` (7 characters, safely above the minimum) plus renaming Skill 2
from `code-reviewer` to `content-reviewer` (see Known Defects —
Clarification #5) now narrows the grid to exactly the expected 2-card
subset (`content-writer`, `content-reviewer`), excluding `formatter` and
`automated-test-explainer` — live-verified via network capture. This is
the genuine partial-match narrowing the case describes, not an
edge-case substitute.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Test Data: 3 skills named Formatter/Code Reviewer/Content Writer | names as literally specified | step 1 | step 1 (kebab-case substitutes used; Skill 2 further renamed `code-reviewer` → `content-reviewer`) | clarification *(case-text drift — see Known Defects #1 for the kebab-case substitution and #5 for the `content-reviewer` rename; product's kebab-case-only name validation is intentional and already tracked, not a new bug; the rename is a test-data fix, not a product-behavior clarification)* |
| 1 Create 3 Skills, all visible in list | 3 skills created and visible | step 1 | step 1: 4 cards visible (3 new + 1 pre-existing) | asserted |
| 2 Search by partial name "Co" → only Code Reviewer/Content Writer shown, Formatter excluded | list filters to 2 matching cards | step 2 | step 2 (this amendment): grid narrows to exactly `content-writer` + `content-reviewer`, excluding `formatter` and `automated-test-explainer`, via corrected term `content` | asserted *(case's original intent now genuinely exercised — see Known Defects Clarification #5. Supersedes the prior amendment's Clarification #4 substitute, which had asserted an unfiltered-grid/toast edge case instead of a real partial-match narrowing because the case's literal term "Co" (2 chars) could never activate the grid filter)* |
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
- the popover's own result set for the (now-superseded) query `Co` included
  `automated-test-explainer` (no literal "co" substring in its name) while
  correctly including the pre-rename `code-reviewer`/`content-writer` —
  *added: a real, narrower anomaly in the popover's own matching logic,
  filed separately as
  [GitHub issue #207](https://github.com/EliteaAI/elitea-testing-public/issues/207)
  since it's independent of this case's core (grid) assertions and not
  blocking; out of scope for this AFS's automation. This is a distinct
  finding from Clarification #5's grid-level description-matching
  discovery below — the popover anomaly matches with NO substring at all,
  while the grid's `content`/`ter` behavior matches via the DESCRIPTION
  field, which is a real (if different) mechanism, not a bug.*
- **(this amendment) the Skills grid search endpoint matches on
  DESCRIPTION text, not just NAME** — discovered while investigating why
  the naturally-shared `ter` substring (between `formatter` and
  `content-writer`) unexpectedly also matched `automated-test-explainer`
  (via "interac**ter**action"... i.e. "in**ter**action" in its
  description) and stray `elitea-1793-ghost-skill` fixtures (via "af**ter**"
  in their description). This is a genuine, previously-undocumented
  product search behavior — *added: not itself filed as a defect (broader
  full-text search across name+description is plausibly intentional
  product behavior, not obviously wrong), but it directly shaped this
  amendment's test-data choice: the corrected term `content` and the
  `content-reviewer` rename were verified clean against BOTH name and
  description fields of every skill present in the live exploration
  environment, not just name. See Clarification #5 for the full
  investigation trail.*
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
   ELITEA-1737/1738). Verified in the original exploration: all 3
   (`formatter` id `126`, `code-reviewer` id `127`, `content-writer` id
   `128`) deleted cleanly; grid returned to just the pre-existing
   `automated-test-explainer`. **Re-verified this amendment** with the
   corrected fixture set (`formatter` id `438`, `content-reviewer` id
   `439` — renamed live from `code-reviewer` mid-run, then deleted under
   its new name, `content-writer` id `440`) — same clean deletion flow,
   same restored end state.
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
| Send-icon activation button (`StyledSendIcon`, `EliteaUI/src/components/SearchBar.jsx:274-277`, `onClick={onSearch}`) | `testid needed: skills-search-send-button` — **confirmed via source read: no `data-testid` on `StyledSendIcon` or the adjacent `StyledCancelIcon`** (only the input itself carries a testid, via the `testId` prop, default `agent-search-input`). Functionally confirmed live (click fires `onSearch()`, grid re-fetches). Request the testid via `add-data-testid` before automating step 3's click-to-activate path; do not substitute an icon/role selector. **Amended 2026-07-16:** landed as `skills-search-send-button`, then renamed to the generic `search-send-button` by EliteaUI PR #581 review fix `e0407b70` (shared components carry generic testids — `.agents/testing.md` § Locator policy); page object updated. | `testid needed` (not present) → delivered, now `search-send-button` |
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
  Response body for the now-superseded `query=Co`:
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
- **(this amendment) the grid-fetching endpoint itself matches on
  DESCRIPTION text, not just NAME.** Response body for `query=ter`
  (investigated, then rejected as the Step 2 term — see Clarification #5):
  `{"total": 5, "rows": [{"id":440,"name":"content-writer"},
  {"id":438,"name":"formatter"},{"id":288,"name":"elitea-1793-ghost-skill"},
  {"id":286,"name":"elitea-1793-ghost-skill"},
  {"id":15,"name":"automated-test-explainer"}]}` — `elitea-1793-ghost-skill`
  and `automated-test-explainer` both matched via their DESCRIPTION text
  ("ghost-skill-af**ter**-remove verification" and "step-by-step
  breakdown with in**ter**action layer", respectively), not their names.
  Response body for the corrected `query=content` (Step 2's final term):
  `{"total": 2, "rows": [{"id":440,"name":"content-writer"},
  {"id":439,"name":"content-reviewer"}]}` — clean, exactly the 2 expected
  skills, verified against both name and description of every skill
  present in the live exploration environment.
- Response body for the unchanged exact-match term `query=formatter`
  (Step 3), re-verified after the `code-reviewer` → `content-reviewer`
  rename: `{"total": 1, "rows": [{"id":438,"name":"formatter"}]}` —
  confirms the rename does not regress Step 3's single-card assertion.

## Known Defects Found During Exploration

1. **Case-text drift (CLARIFICATION, not a new bug)** — the case's Test Data
   names ("Formatter", "Code Reviewer", "Content Writer", capitalized with
   spaces) cannot be created live: the Skill `Name *` field's kebab-case-only
   client-side validation (confirmed live in this run, and already tracked
   for ELITEA-1737/1738 — see
   `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`)
   rejects them. This AFS substitutes kebab-case equivalents
   (`formatter`, `content-writer`, and originally `code-reviewer` — see
   Clarification #5 for its subsequent rename to `content-reviewer`) that
   preserve the case's search-matching intent. Not re-filed as a new
   issue — same underlying, already-documented product behavior.

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
   original intent; left as a recommendation, not implemented here — this
   recommendation is what triggered the analyst rerun documented in
   Clarification #5.

5. **Test-data fix (analyst rerun, this amendment) — restores Step 2's
   original partial-match intent, closing the gap left by Clarification
   #4.** Following Clarification #4's recommendation, this amendment
   re-scoped Step 2's test data instead of its assertion. First
   investigated the exhaustively-checked claim from Clarification #4:
   confirmed computationally that no pair among `formatter`/
   `code-reviewer`/`content-writer` shares any 3+-character substring at
   all (checked all pairwise 3-grams — empty in every case), so **some**
   change to the test data was unavoidable to get a genuine ≥2-result
   partial-match scenario. The one *natural* candidate once a name is
   allowed to change — reusing the un-renamed pair `formatter`/
   `content-writer`, which DO share `ter` (from "forma**tter**" and
   "wri**ter**") — was tried first and **rejected**: live network capture
   (`GET .../skills/prompt_lib/399?query=ter`) showed the grid search
   endpoint matches on **description text, not just name**, and both the
   pre-existing `automated-test-explainer` (description contains
   "in**ter**action") and stray same-environment `elitea-1793-ghost-skill`
   fixtures (description contains "af**ter**-remove") leaked into the
   `ter` result set — contaminating the "excludes automated-test-explainer"
   requirement and demonstrating `ter` is a poor, high-collision choice
   generally (a very common English trigram). This description-matching
   behavior is itself a new, previously-undocumented finding — see Network
   Behavior for the raw response — but is not filed as a defect since
   full-text search across name+description is plausibly intentional, not
   obviously wrong.
   Given that constraint, and that `formatter` needed to stay untouched
   (Step 3's exact-match assertion depends on it being the only skill
   whose name contains "formatter" — renaming `content-writer` to
   something formatter-family, e.g. `content-formatter`, was considered
   and rejected because it would make Step 3's exact search for
   `formatter` match 2 cards instead of 1, regressing an already-passing,
   untouched step), the minimal remaining option was renaming Skill 2:
   `code-reviewer` → `content-reviewer`. This shares the `content` token
   (7 characters) with `content-writer` as a distinctive, low-collision
   term (verified clean against every skill's name AND description in the
   live exploration environment, unlike `ter`) while keeping `code-reviewer`
   recognizably in the same family (still "a reviewer skill", now
   reviewing content instead of code — a natural adjacent skill name, not
   an arbitrary token). Live-verified end-to-end after the rename:
   Step 2's corrected term `content` narrows the grid to exactly
   `content-writer` + `content-reviewer` (network: `{"total": 2, ...}`),
   and Step 3's unchanged term `formatter` still isolates exactly 1 card
   (network: `{"total": 1, ...}`), confirming no regression. Not filed as
   a GitHub issue — this is purely a test-data correction, not a product
   defect or case-text drift.

## Blocked Steps
None. Step 2's partial-match scenario, left unexercised after Clarification
#4's edge-case substitution, is now restored via the Clarification #5
test-data fix (rename + corrected term) and live-verified end-to-end.
Steps 1, 3, 4, 5 remain executed end-to-end live and their expected
results are achievable against the current product, once the intended
activation mode (Enter / send-icon click) is used after typing — see
Known Defects — Clarification #2. This AFS is `ready-for-automation` for
all 5 steps.

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
  - **(this amendment) `search_below_min_length(query)` is no longer
    needed for Step 2** — the corrected term `content` (7 characters) is a
    normal, above-minimum query, so Step 2 now uses the same `search()`
    method as every other step. This method remains a candidate for a
    *separate*, dedicated edge-case test of the 3-character minimum
    (`MIN_SEARCH_KEYWORD_LENGTH`) if the team wants explicit coverage of
    that boundary — see the retired scenario preserved in Known Defects
    Clarification #4 — but it is not part of this case's automated flow
    any more.
  - Consider whether `skill_exists_in_list()` needs a companion
    `visible_skill_count()` / `get_visible_skill_names()` to assert the
    **exact** filtered set (not just presence/absence of one name), since
    this case's core assertions are about the whole visible set (e.g. "only
    Content Reviewer and Content Writer, Formatter is not shown") — reusing
    `agent_exists_in_list`'s loose `text="{name}"` locator (as
    `AgentsListPage` currently does) would silently pass even if a future
    regression only broke the grid while leaving the (separate) suggestions
    popover working, since it matches text anywhere on the page. The Skills
    equivalent must scope strictly to `entity-card-name` cards in the grid
    to be a meaningful regression guard.
  - **(this amendment) exact-set assertions must account for the grid's
    description-matching behavior** (Clarification #5) — a naive
    `get_visible_skill_names() == {expected}` assertion is only safe if the
    chosen search term is verified clean against every OTHER skill's
    description in the target environment, not just its name. Prefer
    distinctive, low-collision terms (e.g. `content`, a full recognizable
    word) over short/common substrings (e.g. `ter`) precisely because the
    latter are far more likely to collide with unrelated skills' free-text
    descriptions in a shared or long-lived test environment.
- Existing `skill_api` fixture pattern (`SkillAPI` in
  `automation/api/client.py`) should create/delete the 3 test skills in
  setup/teardown, following `test_skill_export_import.py`'s pattern —
  faster and more reliable than UI creation for automated runs.
