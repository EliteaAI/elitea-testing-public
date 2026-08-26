---
tms_id: ELITEA-2454
title: "Run Details — Delete Run from History"
priority: high
module: pipelines
status: ready-for-automation
surface_key: pipeline-run-details-panel
---

# ELITEA-2454: Run Details — Delete Run from History

## Status: ready-for-automation

Executed live end-to-end against `http://localhost:5173` (probe pipeline id
8771, single LLM node → END, created via `PipelineAPI.create_pipeline_with_llm_node`,
deleted at session end). All 7 case steps are directly verifiable; one
extra concrete handle (the history-menu toggle icon) needs adding via
`add-data-testid` — everything else the case touches already has a testid
(inherited from ELITEA-2450's implementation).

**Analyst self-correction (transparency, not a defect):** mid-session I
initially misjudged "multiple runs never accumulate" as a product defect and
filed `EliteaAI/elitea-testing-public#1377` — then found the actual trigger
(a testid-less clock-icon button I'd missed) and retracted/closed it in the
same session with the corrected mechanism documented in the closing comment.
The feature works correctly; see § Live-Confirmed Mechanics below for the
real, verified behaviour. No defect is being carried forward from this case.

## Preconditions

- User is logged in (`auth_state` on localhost).
- A pipeline exists with at least one executable node (LLM → END is
  sufficient and is what this session used).

## Live-Confirmed Mechanics (read this before automating)

The case's "Run history" is **NOT** the embedded chat's separate "view run
history" panel (`pipeline-history-tab`, shared `RunHistoryContainer` — see
`test-specs/pipelines/_surface.md` "Run History panel — Pipeline surface").
It is the **on-canvas run-node stack** above the Flow canvas
(`RunStateNodeGroup.jsx`/`RunStateNode.jsx`/`RunStateDialog.jsx` — the SAME
feature already covered by ELITEA-2450/2451/2452/2453), confirmed by the case
text itself: step 2 explicitly says to note a label like `"Run 3 details"`,
which is this feature's exact wording.

- **Client-side only, per `useRunEvent.hooks.js`'s `pipelineRunNodes` state
  (`useState([])`)** — no persistence, no REST endpoint. Confirmed via
  `browser_network_requests`: no requests beyond Socket.IO polling across 3
  executions + 2 deletes.
- **Each execution's run gets a genuinely distinct id**
  (`` `EliteA_Pipeline__State_${nextRunName}` ``, e.g.
  `EliteA_Pipeline__State_Run 2 details`) and DOES append to the array — 3
  sequential chat messages in one conversation produced 3 real entries,
  confirmed by directly inspecting `pipelineRunNodes`'s rendered effect (see
  below), not just the label text.
- **Only the newest (`last`) run renders its OWN visible
  `[data-testid="pipeline-run-node-label"]` directly on the canvas.** All
  older runs are inside a **closed-by-default MUI `Menu`**
  (`id="runNodes-history-menu"`, no `data-testid`) that only mounts its
  children (each an inner `RunStateNode`, reusing the SAME
  `pipeline-run-node-label` testid) while open. **This is the trap that
  caused my own mid-session false-positive**: querying
  `[data-testid="pipeline-run-node-label"]` count, or checking for
  `#runNodes-history-menu` in the DOM, BEFORE opening the history toggle
  always returns 1 / absent — that does NOT mean only one run exists, it
  means the menu is closed. **Always open the history toggle first** before
  asserting "how many runs exist."
- **The history-toggle button (`RunStateNodeGroup.jsx`'s `historyWrapper`
  `Box`, a clock icon, lines 41-46) renders ONLY when `nodes.length > 1`**,
  as a sibling immediately BEFORE the visible run-node `Box` — and has
  **zero testid, zero `aria-label`, zero Tooltip** (confirmed via
  `grep -n "data-testid" RunStateNodeGroup.jsx` — no hits at all). This is
  the ONE concrete handle this case needs that doesn't already exist —
  see § Concrete Handles.
- **Clicking a run's label inside the open history menu opens ITS OWN
  `RunStateDialog` (same testids as ELITEA-2450: `pipeline-run-details-panel`
  / `-header` / `-status-badge` / `-delete-button` / `-close-button`) WITHOUT
  closing the menu** — confirmed live: after clicking "Run 1 details" inside
  the menu, `#runNodes-history-menu` was still in the DOM (`menuStillOpen:
  true`) at the same time the panel opened. No auto-close is wired
  (`RunStateNodeGroup.jsx`'s `MenuItem` has no `onClick`; only the label's
  `onOpen` fires).
- **Delete has NO confirmation dialog** (matches ELITEA-2450's sibling
  finding) — clicking `pipeline-run-details-delete-button` calls
  `onDelete` → `deleteRunNode(id)` (`RunStateNode.jsx:48-54`) →
  `setPipelineRunNodes(prev => prev.filter(node => node.id !== id))`
  (`useRunEvent.hooks.js:23-25`) → the panel closes immediately AND that
  run's entry is removed from the array. Confirmed live twice (deleted the
  newest run, then an older one from inside the history menu) —  **each
  delete removes exactly the clicked run; every other run's entry, label,
  and content is untouched.**
- **When the array drops back to length 1, the whole group re-renders as
  the bare single-node branch** — the history toggle AND the `Menu`
  disappear from the DOM entirely (not just visually collapsed); this is
  the live, verifiable form of "re-open run history — verify the deleted
  run no longer appears" when only one run is left. With ≥2 runs still
  remaining after a delete, re-clicking the toggle re-opens the (still
  testid-less) menu, and the deleted run's label is verifiably absent
  while the survivor(s)' labels are present — this is the stronger,
  case-literal form of steps 6-7 and is what this AFS specifies (§ Test
  Data uses 3 runs, deletes the newest, for exactly this reason).

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Embedded chat input | `chat_input` (existing `LocatorDescriptor`, `pipeline_detail_page.py`) | on-main ✓ (pre-existing, used by `send_message_in_embedded_chat`) |
| Run node label (last/current run) | `[data-testid="pipeline-run-node-label"]` — `run_node_label` field | on-`automation/testids` (added ELITEA-2450, `EliteaAI/EliteaUI@fb66d978`) — same testid reused for EVERY run's label, disambiguate by text |
| Run Details panel root | `[data-testid="pipeline-run-details-panel"]` — `run_details_panel` field | same provenance as above |
| Run Details panel header | `[data-testid="pipeline-run-details-header"]` — `run_details_header` field | same provenance |
| Run Details panel status badge | `[data-testid="pipeline-run-details-status-badge"]` (+`data-status`) — `run_details_status_badge` field | same provenance |
| **Run Details panel delete (trash) button — THIS case's step 3** | `[data-testid="pipeline-run-details-delete-button"]` — `run_details_delete_button` field (already exists, unused by any test yet) | same provenance — Completed-branch only, per ELITEA-2450's AFS note; this case only exercises `Completed` runs |
| Run Details panel close button | `[data-testid="pipeline-run-details-close-button"]` — `run_details_close_button` field | same provenance |
| **History-toggle (clock) icon — needed for steps 1/2/7** | `testid needed: pipeline-run-node-history-button` | **needs-adding.** Source: `RunStateNodeGroup.jsx:41-46` — the `historyWrapper` `Box` (`onClick={e => toggleHistory(e.currentTarget)}`, wraps `<ClockIcon />`). Renders only when `nodes.length > 1`, immediately before the visible run-node `Box`. Zero testid/aria-label/Tooltip today (confirmed via grep — no hits). Naming follows the sibling forward-reference already in ELITEA-2450's AFS (`pipeline-run-node-delete-button`, for the OUTER on-canvas delete icon — NOT needed by this case since step 3 uses the PANEL's delete button, not the outer one; not requested here per the "scope = elements this test touches" rule). |

**Deliberately NOT requested** (scope discipline, `.agents/role-overrides.md`
§ locator policy): a testid on the `Menu` container itself
(`id="runNodes-history-menu"`) and per-item `MenuItem` testids. Not needed —
every history item's label already carries the reusable
`pipeline-run-node-label` testid; "how many runs currently exist" is
answered by opening the toggle first, then counting ALL
`[data-testid="pipeline-run-node-label"]` elements on the page (last node +
every open-menu item, since the menu unmounts entirely when closed) — no
extra scoping handle required. Do not add one "while in there."

## Coverage Map

### Axis 1 — Case element → Coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Execute a pipeline ≥2 times for multiple runs in history | Action completes without error | Send 3 messages via embedded chat, `wait_for_embedded_chat_response()` after each | Step 1 | covered (3 runs used, not 2, to exercise "other runs" meaningfully in step 6) |
| Step 2: Open Run Details for one run, note the run number | Panel loads | Open the history toggle, click a specific run's label (e.g. "Run 2 details") inside the menu; assert header text | Step 2 | covered |
| Step 3: Click trash/delete icon in the Run Details header | Control responds | Click `pipeline-run-details-delete-button` | Step 3 | covered |
| Step 4: Confirm deletion if prompted | Operation completes | No dialog exists (confirmed live, source-verified `RunStateDialog.jsx:118`) — panel closes immediately on click; assert panel `to_be_hidden()` | Step 4 | covered (case's "if prompted" is conditional; confirmed live there is no prompt) |
| Step 5: Verify the run is removed from run history | Run gone from history | Re-open the toggle; assert the deleted run's label (`has_text="Run 2 details"`) has count 0 among `[data-testid="pipeline-run-node-label"]` | Step 5 | covered |
| Step 6: Verify other runs remain unaffected | Other runs intact | Assert the remaining 2 runs' labels ("Run 1 details", "Run 3 details") are both still present and each opens its own panel with unchanged header/status | Step 6 | covered |
| Step 7: Re-open run history — deleted run no longer appears | Deleted run absent on re-open | Close then re-open the history toggle (or simply the same re-open from step 5); assert absence persists | Step 7 | covered (folded into step 5's assertion — re-opening is literally what step 5 already does) |

### Axis 2 — Extra observables asserted beyond the case (grounded reasons)

| Observable | Reason |
|---|---|
| No confirmation dialog exists | Case step 4 says "if prompted" — asserting its absence explicitly prevents a future regression (adding a confirm dialog) from going unnoticed as "still passing" |
| History toggle disappears entirely (not just visually) when only 1 run remains | Confirmed live behaviour of `RunStateNodeGroup`'s branch logic; a strong, cheap regression guard for the group/single-node render switch |
| Deleting doesn't touch the embedded chat message list | Confirmed live — chat history (`Hello run 1/2/3` + AI replies) unaffected by any of the 2 deletes performed in-session; guards against a coupling regression between chat history and run-node state |

## Known Defects

None open for this case. (See § Status — Analyst self-correction for the
filed-then-retracted `#1377`; it was resolved as not-a-defect within the
same analysis session, before this AFS was written.)

## Blocked Steps

None.

## Automation Hints

- **Page object:** `automation/pages/pipeline_detail_page.py`
  (`PipelineDetailPage`). Existing methods to reuse:
  `navigate(pipeline_id)`, `send_message_in_embedded_chat(message)`,
  `wait_for_embedded_chat_response(initial_count)`,
  `open_run_details_panel()` / `close_run_details_panel()` (these currently
  assume a SINGLE run node — see next bullet), `get_run_details_header_text()`.
- **New methods needed** (the existing `open_run_details_panel()` clicks
  `run_node_label` directly, which only reaches the CURRENT/last run — it
  cannot reach an older run inside the history menu):
  - `open_run_node_history()` — click the new
    `pipeline-run-node-history-button` testid, wait for
    `#runNodes-history-menu`-equivalent visibility (assert via the count of
    `pipeline-run-node-label` elements increasing, since there is no
    dedicated container testid — see § Concrete Handles for why one wasn't
    requested).
  - `get_run_history_labels() -> list[str]` — after opening the history
    toggle, return the text of every `[data-testid="pipeline-run-node-label"]`
    element (this naturally includes the current/last run too, matching the
    live semantics: "all runs that currently exist").
  - `open_run_details_by_label(label: str)` — after opening the history
    toggle, click the `pipeline-run-node-label` element whose text equals
    *label* (Playwright: `.filter(has_text=label)` or exact string match —
    the labels are short and non-overlapping, e.g. "Run 1 details" vs
    "Run 2 details" vs "Run 12 details"; use exact match, not substring, to
    avoid "Run 1" matching "Run 12").
  - `delete_current_run_details()` — thin wrapper: click
    `run_details_delete_button`, then wait for `run_details_panel` to be
    hidden (delete auto-closes the panel, confirmed live — no separate close
    click needed).
  - Method naming avoids colliding with the EXISTING (unrelated)
    `open_run_history()` (chat-level Run History panel, `pipeline-history-tab`,
    ELITEA-2011) — use `open_run_node_history()` for this feature to keep the
    two clearly distinct in the page object.
- **Fixture:** `pipeline_with_llm_id` (existing, `automation/fixtures/data_fixtures.py`)
  is sufficient — single LLM node → END, executes and completes in ~1s per
  message in this session.
- **Timing:** each execution completed (AI response fully rendered) within
  ~5-10s in this session; `wait_for_embedded_chat_response()`'s default
  60s timeout is more than adequate. No `sleep()`/`wait_for_timeout` needed
  anywhere in this flow — every state transition (panel open/close, menu
  open, label count change) is a DOM mutation `expect(...).to_be_visible()`/
  `to_have_count()` can wait on directly.
- **Suggested step sequence** (mirrors the Coverage Map, 3 runs, delete the
  newest to leave 2 survivors and re-exercise the toggle on the way back
  down to 1):
  1. `navigate(pipeline_id)`; send "Hello run 1" → wait for response.
  2. Send "Hello run 2" → wait for response.
  3. Send "Hello run 3" → wait for response.
  4. `open_run_node_history()`; assert
     `get_run_history_labels()` == {"Run 1 details", "Run 2 details", "Run 3 details"}
     (order not guaranteed to matter — use a set/unordered comparison).
  5. `open_run_details_by_label("Run 3 details")`; assert
     `get_run_details_header_text() == "Run 3 details"` and
     `get_run_details_status() == "Completed"`.
  6. `delete_current_run_details()`.
  7. `open_run_node_history()` again; assert
     `get_run_history_labels()` == {"Run 1 details", "Run 2 details"} (Run 3
     absent — step 5/7; Run 1 + Run 2 present, unaffected — step 6).
  8. Optionally: delete one more (e.g. "Run 1 details" from inside the
     menu) and assert the toggle/menu disappear ENTIRELY once only
     "Run 2 details" remains (`pipeline-run-node-history-button` testid
     itself has `to_have_count(0)`), as the strongest form of "no longer
     appears."

## Test Data

None required beyond an executable pipeline (LLM node → END) and 3 short
chat messages (content is irrelevant to the assertions — this pipeline has
no toolkits/attachments and the LLM's response text is never asserted on).

## Evidence

- `test-results/screenshots/ELITEA-2454-step-run-nodes-after-2-runs.png` —
  after 2 executions, history toggle closed (menu not yet opened in this
  screenshot — see mechanics note above for why this alone doesn't prove
  single-run).
- `test-results/screenshots/ELITEA-2454-step-run-nodes-after-3-runs.png` —
  after 3 executions, same closed-toggle state, label correctly "Run 3 details".
- `test-results/screenshots/ELITEA-2454-step-after-delete-run3.png` — after
  deleting "Run 3 details" (from inside the then-open history menu),
  "Run 2 details" becomes the bare/current run.
