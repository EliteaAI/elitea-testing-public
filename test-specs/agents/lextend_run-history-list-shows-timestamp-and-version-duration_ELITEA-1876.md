# Test Case: Run History panel — every listed entry displays a timestamp (and the
# live product's actual per-row columns, in place of the case's stale "preview")

## Metadata
- **TMS ID**: ELITEA-1876
- **Linked Story**: none
- **Priority**: l2 (matches the priority of the spec being extended, ELITEA-1877)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`)
- **User set**: localhost dev auth (`auth_state` / `VITE_DEV_TOKEN`) — no explicit `${TEST_USER}` needed
- **Analyst**: qa-engineer (analyst slot), batch `agents-batch1-1277`
- **Status**: extend-existing

## Extension target
- **Covering spec**: `test-specs/agents/l2_run-history-select-past-run-loads-messages_ELITEA-1877.md`
- **Covering test**: `automation/tests/ui/agents/test_agent_run_history_select_past_run.py::TestAgentRunHistorySelectPastRun::test_select_past_run_loads_chat_messages`
- **Merge status**: merged to `origin/automation/base` — confirmed via
  `git merge-base --is-ancestor b02c88ec origin/automation/base` → `YES`
  (`b02c88ec` = "merge ELITEA-1877 into tests/batch-approved-top10", itself an
  ancestor of `origin/automation/base`).

### Behavioural-overlap argument
ELITEA-1877's test already drives the exact precondition chain ELITEA-1876 needs
(navigate to an agent detail page → send messages in the embedded chat → open Run
History via `pipeline-history-tab` → the list renders) and already asserts:
- the panel opens and the Configuration form/embedded chat are replaced by it
  (step 3 — the click succeeds and `run-history-list-item` elements become visible)
- **at least one** entry is present — in fact it asserts `item_count >= 2`, a
  strictly stronger version of ELITEA-1876 step 5 ("at least one run history entry
  is present")
- clicking a specific entry selects it (`data-selected="true"`) and loads that
  entry's own conversation content into the right-hand chat panel

That is ELITEA-1876 steps 1–5 in full. What it does **not** assert is ELITEA-1876
step 6: that **each listed entry itself** (in the row, before any click) displays a
timestamp and a content preview. ELITEA-1877's assertions only ever read the
**count** of rows (`get_run_history_item_count()`) and the **selected-run detail
panel's** message text (`get_run_history_chat_messages_text()`) — no existing
assertion ever reads what text is rendered inside an unselected row. That is
exactly this case's gap.

## Live product finding — case text vs actual UI (case-text drift, not a defect)
**Filed**: `EliteaAI/elitea-testing-public#1282` (label `question`/Clarification,
strict-per-bug, not blocking).

ELITEA-1876 step 6 says each entry shows "a timestamp and a preview of the
conversation (first message or title)". Live + code-confirmed
(`RunHistoryListItem.jsx`, `RunHistoryList.jsx`'s `tableHeaderItems`,
`RunHistorySortableHeader.jsx`), each row renders exactly **three** columns —
**Date**, **Version**, **Duration** — and nothing else. There is no cell in the row
that shows the conversation's first message or a title; that content only appears
in the right-hand `RunHistoryChat` panel **after** a row is clicked (already
covered by ELITEA-1877). Live snapshot (`manual_test_agent`, agent id 5189):

```
Date                    Version   Duration
17-07-2026, 05:57 PM    base      9.33 s
17-07-2026, 05:55 PM    base      6.35 s
17-07-2026, 05:44 PM    base      3.85 s
17-07-2026, 05:20 PM    base      3.3 s
```

Per the reverse-masking guard (`.agents/testing.md`), the live design is coherent
and not obviously broken — this is the case text that's stale, not the product.
This AFS's gap assertions therefore assert the **live contract** (Date + Version +
Duration per row), not the case's literal "preview" wording.

**Bonus finding (informational, not filed separately):** the previously-reproduced
defect `EliteaAI/elitea-testing-public#1093` ("no UI way to close Run History") now
appears **fixed** — `RunHistoryContainer.jsx` renders a wired
`aria-label="close run history"` `IconButton` whenever `onClose` is passed, and
live-clicking it (confirmed this run, `manual_test_agent`) correctly closes the
panel and restores the Configuration form + embedded chat. Flagged for a human to
verify and close #1093; `test-specs/agents/_surface.md` updated accordingly (its
prior "no close button exists" note was accurate for the ELITEA-1877/2026-08-02
run but is now stale).

## Preconditions
- User is on the Agent detail page's Configuration tab (`/agents/all/{id}?viewMode=owner`).
- Run History panel is already open with **≥ 2** entries — i.e. this extension runs
  as additional assertions appended to ELITEA-1877's existing test, immediately
  after its own Step 3 ("Open the Run History panel"), reusing that test's already-
  created two conversations. No new test data of its own.

## Test Data
- None beyond what ELITEA-1877's test already creates (Message A / Message B,
  each producing its own Run History entry).

## Test Steps (appended to ELITEA-1877's Step 3)
1. After ELITEA-1877's Step 3 assertion (`item_count >= 2`), read the full rendered
   text of **every** `run-history-list-item` row (not just the one about to be
   clicked) — e.g. `page.locator(RUN_HISTORY_LIST_ITEM_SELECTOR).all_text_contents()`
   or an equivalent per-row `text_content()` loop.
   - **Verify**: each row's text contains a substring matching the rendered date
     format `dd-MM-yyyy, hh:mm a` (regex `\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)`,
     case-insensitive on AM/PM) — this is case step 6's "timestamp" half, asserted
     for every entry, not just the clicked one.
2. On the same per-row text, additionally verify a **Version** segment (non-empty
   text — for an Agent-sourced Run History, always populated; live-confirmed value
   `"base"` for these disposable agents) and a **Duration** segment (non-empty,
   matches `\d+(\.\d+)?\s*s` — e.g. `9.33 s`) are both present.
   - **Verify**: this documents the live contract (Date + Version + Duration) in
     place of the case's stale "preview (first message or title)" wording — see
     § Live product finding.

## Expected Results
- Every Run History list row — not only the row selected in ELITEA-1877's own
  flow — displays a well-formed timestamp matching the app's date format.
- Every row also displays its Version and Duration columns, non-empty.
- No row is missing any of the three columns.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to an agent detail page | Page loads | ELITEA-1877 step 1 | `test_agent_run_history_select_past_run.py` Step 1 | asserted *(via extension target — not re-implemented)* |
| 2 Send at least one message in embedded chat | Message sent, response received | ELITEA-1877 step 2 | same file, Step 2 | asserted *(via extension target)* |
| 3 Click the run history icon | Run History panel opens | ELITEA-1877 step 3 | same file, Step 3 | asserted *(via extension target)* |
| 4 Verify the run history panel opens | Panel is visible | ELITEA-1877 step 3 | same file, Step 3 (`run-history-list-item` becomes visible, replacing the Configuration form) | asserted *(via extension target)* |
| 5 Verify at least one entry is listed | ≥1 entry present | ELITEA-1877 step 3 | same file, Step 3 (`item_count >= 2`, strictly stronger) | asserted *(via extension target — supersedes)* |
| 6a Each entry shows a timestamp | Timestamp visible per entry | this AFS, step 1 | new per-row text assertion, all rows | **gap — newly asserted here** |
| 6b Each entry shows a preview (first message or title) | Preview visible per entry | this AFS, step 2 (documents actual contract) | new per-row text assertion, Version+Duration | **case-text drift — filed `EliteaAI/elitea-testing-public#1282`; live product asserts Version+Duration instead, no preview exists** |

**Axis 2 — Analyst additions**
- None beyond the case-text drift already logged above (Axis 1, row 6b) and the
  #1093-appears-fixed bonus observation (informational, § Live product finding).

## Cleanup
- None additional — rides ELITEA-1877's existing `agent_api.delete_agent(agent_id)`
  teardown (same test function, appended assertions).

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| Run history list item (row, full text incl. Date/Version/Duration) | Reuses `AgentDetailPage.RUN_HISTORY_LIST_ITEM_SELECTOR` = `'[data-testid="run-history-list-item"]'` (pre-existing, from ELITEA-1877) — no new testid needed; Date/Version/Duration are plain child `<Typography>` text nodes inside the SAME row element (`RunHistoryTooltipCell.jsx`), so the row's own `text_content()`/`all_text_contents()` already exposes all three | on-main ✓ (pre-existing, reused as-is — verified via `cd ../EliteaUI && git fetch origin` + `git grep -- 'run-history-list-item' origin/main -- src/`, 2026-08-06) | none — testid only |

**No new testid work is required for this extension** — per-row text is already
addressable through the existing row-level testid; adding per-cell testids for
Date/Version/Duration would violate the "scope = only what the test touches, don't
over-testid" rule for no functional gain (`.agents/role-overrides.md`).

**PROVENANCE freshness:** verified via `cd ../EliteaUI && git fetch origin` +
`git grep` against `origin/main`, 2026-08-06.

## Network Behavior
- None new — reuses ELITEA-1877's `GET /elitea_core/conversations/prompt_lib/{projectId}?source=agent&...`
  (Run History list fetch); this extension only reads DOM text already rendered
  from that same response, no additional request.

## Known Defects Found During Exploration
- **[CLARIFICATION]** `EliteaAI/elitea-testing-public#1282` — case-text drift: step 6
  describes a conversation "preview (first message or title)" per Run History
  entry; live product shows Date/Version/Duration columns only, no preview. Not
  blocking; this AFS's gap assertions assert the live contract instead.
- **Informational, not filed**: `EliteaAI/elitea-testing-public#1093` ("no UI way to
  close Run History") appears FIXED live (see § Live product finding) — flagged for
  a human to verify/close, not this case's action.

## Blocked Steps
- none

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- **Implementation shape: append, don't duplicate.** Add these 2 gap assertions as
  additional `allure.step`s inside the SAME
  `test_select_past_run_loads_chat_messages` test in
  `automation/tests/ui/agents/test_agent_run_history_select_past_run.py`, right
  after its existing "Step 3 — Open the Run History panel" block (before Step 4's
  row click) — reuses the same 2 conversations already created, no new fixture, no
  new test function. Do not write a second full test that re-creates the
  precondition chain from scratch.
- Add one small helper to `AgentDetailPage`
  (`automation/pages/agent_detail_page.py`, alongside the existing
  `get_run_history_item_count()`/`select_run_history_item()` methods):
  `get_run_history_item_texts() -> list[str]` returning
  `self.page.locator(self.RUN_HISTORY_LIST_ITEM_SELECTOR).all_text_contents()`.
  Then in the test, regex-match each string for the date pattern
  (`r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)"`, case-insensitive) and the duration
  pattern (`r"\d+(\.\d+)?\s*s\b"`), and assert `"base"` (the known version name for
  this disposable-agent fixture) appears too.
- **Note for the reviewer/implementer:** while re-running ELITEA-1877's existing
  test live during this analysis (2 consecutive `pytest` invocations, clean
  process each time), it failed **both** times — once with the Run History detail
  panel returning empty text for the selected historical run, once with the
  embedded chat's "last message" assertion not containing Message B's text. Two
  different failure signatures across 2 runs suggests AI-response/timing flakiness
  in the **existing, unrelated** assertions (message-content matching), not
  anything this extension's per-row Date/Version/Duration assertions touch. Not
  investigated further here (out of this case's scope — ELITEA-1876 doesn't touch
  message content) — flagged for the batch report / lead as a possible stability
  issue with the ELITEA-1877 spec worth a dedicated look before/at the next
  hardening gate.
