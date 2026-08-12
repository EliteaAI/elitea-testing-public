# Test Case: Chat – HITL Authorization – Click Authorize Executes the Toolkit Tool Directly

## Metadata
- **TMS ID**: ELITEA-2212
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`) for the direct
  toolkit-call / chip-rendering portion; **source-verified**
  (`ChatHitlActions.jsx`, `ActionView.jsx`) for the Authorize-resume wiring —
  see ELITEA-2211's AFS § Preconditions for the shared environment-limitation
  note (Admin Guardrails route not served on localhost); not repeated here.
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
Same as ELITEA-2211 (`l2_hitl-sensitive-action-card-display_ELITEA-2211.md`
§ Preconditions) — toolkit with `delete_file` marked sensitive via Admin UI
Guardrails, `pytest.mark.guardrails`, CI-only execution. This case picks up
from the authorization card already showing (its own precondition line
literally says so) — implementer should chain it directly off ELITEA-2211's
test body (same conversation) rather than re-deriving the pause, OR give it
its own fresh conversation + repeat the trigger steps — either is fine, but
**do not share a live conversation/mutable state across parametrized test
runs** (pytest-xdist is serial-mode here per `.agents/testing.md` § Test data
strategy, but a shared conversation between 2212/2213/2214 would let one
case's resume action affect the others — each of 2212/2213/2214 needs its
OWN fresh authorization card instance, i.e. its own send-message-and-pause,
matching the isolation note ELITEA-2015's implementer already established
for pipeline HITL Approve vs Reject).

## Test Data
Same fixture shape as ELITEA-2211 (artifact bucket + toolkit, unambiguous
delete-file message naming the bucket explicitly — the case's own literal
message was confirmed live to not even reach a tool-call attempt, see
ELITEA-2211 § Test Data).

## Test Steps
1. Reach the authorization card (ELITEA-2211 steps 1–5): toolkit added as
   participant, unambiguous delete-file message sent, `sensitive-action-panel`
   visible with Authorize/Block/Block-with-Comment.
2. Click Authorize (`[data-testid="sensitive-action-authorize-button"]`).
   - **Verify**: the panel closes/updates (source: `handleApprove` calls
     `onHitlResume({action: 'approve', toolCallId, interruptId})` —
     `ChatHitlActions.jsx:103-105`; the panel's own component unmounts once
     `hitlInterrupt` clears from state, per `if (!hitlInterrupt) return null`
     at line 127).
3. Verify the toolkit call actually executes.
   - **Verify**: the fixture bucket's designated file is genuinely gone —
     assert via `ArtifactAPI`/S3-listing (`list_bucket_files`), not just a
     UI-only signal, so the assertion proves REAL backend execution, not
     merely that the card disappeared. (Case's own step 3 says "verify tool
     execution completes successfully" — a UI-only check would be
     insufficient given the whole point of Authorize is real execution.)
4. Verify tool-execution chips.
   - **Verify**: an LLM-model chip (`[data-testid="chat-answer-model-chip"]`,
     confirmed live via the ADJACENT ELITEA-2215 flow on the same toolkit —
     see that AFS for the confirmed DOM) AND a toolkit/tool chip showing
     `"{toolkit_name}: delete_file"` — **testid needed, see § Concrete
     Handles**; confirmed live this pass that the non-model chip renders
     with NO `data-testid` at all (`ActionView.jsx:360`,
     `data-testid={toolkitType === 'model' ? 'chat-answer-model-chip' : undefined}`
     — the ternary's `else` branch is unnamed).
5. Verify the conversation continues normally (no error state, composer
   re-enabled).

## Expected Results
- Authorize closes the card and the toolkit tool genuinely executes
  (backend-verified, not UI-only).
- Model chip + toolkit/tool chip both render.
- No console/JS errors.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Verify card + 3 buttons visible | visible | step 1 | step 1 setup, this case's OWN test body (see fix round 1 note below) | asserted *(fix round 1, 2026-08-03: originally cited ELITEA-2211 — a same-batch, not-yet-merged spec — as the sole site of this assertion; the reviewer contract requires "already-covered"/reuse citations to target a spec merged to base, which ELITEA-2211 is not. This case's own test now independently asserts all three buttons visible before clicking Authorize, so the row no longer depends on that citation)* |
| 2 Click Authorize | card closes, proceeds | step 2 | step 2 | asserted |
| 3 Tool execution completes | execution completes | step 3 | step 3 (backend file-listing check) | asserted |
| 4 Chips shown (model + tool) | chips visible | step 4 | step 4 | asserted |
| 5 Conversation continues normally | no errors | step 5 | step 5 | asserted |

**Axis 2 — Analyst additions:**
- Assert real backend execution via `ArtifactAPI.list_bucket_files`, not
  just the UI card disappearing — *added: the case's own "verify execution
  completes successfully" is unfalsifiable from the UI alone; a UI-only
  assertion would pass even if the backend silently failed the tool call.*
- Assert no console/JS errors — *added: standard side-channel discipline.*

## Cleanup
Same as ELITEA-2211: remove `delete_file` from Sensitive Action Tools + save
(shared project-wide flag — do this ONCE per test-file/class, not per case,
to avoid redundant admin round-trips if 2212/2213/2214 run in the same
session); delete the toolkit/bucket.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Authorize button | `[data-testid="sensitive-action-authorize-button"]` (exists, add to `ChatPage`) | none |
| Model chip | `[data-testid="chat-answer-model-chip"]` (exists, confirmed live) | none |
| Toolkit/tool chip | **testid needed**: e.g. `chat-answer-tool-chip` — add via `add-data-testid` to `ActionView.jsx:360`'s ternary, naming BOTH branches distinctly (`chat-answer-model-chip` for `toolkitType === 'model'`, a new `chat-answer-tool-chip` for the else branch) — this satisfies canon ruling #277 shape (b) since both this case and ELITEA-2215 reference both branches on their executed path | none — do not assert on chip TEXT alone (i18n/format risk); testid required per project locator policy |
| Bucket file-listing (execution proof) | `ArtifactAPI.list_bucket_files(bucket_name)` (existing API method) | none — this is the backend ground truth, no UI fallback needed |

## Network Behavior
- Resume action: `onHitlResume({action: 'approve', toolCallId, interruptId})`
  — implementer should capture the actual websocket frame shape once run
  against CI (not captured live this pass — see ELITEA-2211's Network
  Behavior note, same root cause).

## Known Defects Found During Exploration
None found.

## Blocked Steps
None — see ELITEA-2211's Blocked Steps note (same shared precondition
constraint, not repeated here).

## Automation Hints
- Same markers as ELITEA-2211: `guardrails`, `p2`, `chat`, `regression`.
- Chain this test's send-and-pause setup with ELITEA-2211's, or duplicate it
  in an isolated conversation — analyst recommends duplicating (own fresh
  conversation per case) to avoid cross-test resume-action coupling, per
  the isolation precedent ELITEA-2015 already established for pipeline HITL.
