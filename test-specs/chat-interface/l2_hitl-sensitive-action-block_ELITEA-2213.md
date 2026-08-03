# Test Case: Chat – HITL Authorization – Click Block Prevents the Toolkit Tool from Executing

## Metadata
- **TMS ID**: ELITEA-2213
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local for the toolkit-call/chip mechanics;
  source-verified (`ChatHitlActions.jsx`) for the Block button itself. See
  ELITEA-2211 § Preconditions for the shared environment-limitation note
  (not repeated here).
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
Same as ELITEA-2212 — own fresh authorization-card instance (own
conversation), do not share resume state across 2212/2213/2214.

## Test Data
Same fixture shape as ELITEA-2211/2212.

## Test Steps
1. Reach the authorization card (own fresh conversation): toolkit added as
   participant, unambiguous delete-file message sent, `sensitive-action-panel`
   visible with Authorize/Block/Block-with-Comment.
2. Click Block (source: `ChatHitlActions.jsx:175-183`, `variant="alarm"` =
   red, **no testid today** — see § Concrete Handles).
   - **Verify**: `handleReject` fires — `onHitlResume({action: 'reject', toolCallId, interruptId})`
     (`ChatHitlActions.jsx:107-109`); the card unmounts once `hitlInterrupt`
     clears.
3. Verify the toolkit tool does NOT execute.
   - **Verify**: the fixture bucket's designated file is STILL present
     (`ArtifactAPI.list_bucket_files`) — backend-verified non-execution, the
     Block-side mirror of ELITEA-2212's execution-proof assertion. A
     UI-only "card closed" signal cannot distinguish Block from a silent
     failure; the file's continued presence is the actual proof.
4. Verify the LLM response indicates the action was blocked.
   - **Verify**: the assistant's follow-up message text is non-empty and
     acknowledges the block (case's own wording: "response indicates action
     was blocked") — **format not verified live** (precondition unreachable
     locally); assert a loose, resilient signal (e.g. response text is
     non-empty and does not claim success) rather than a hardcoded phrase,
     since the exact LLM wording is non-deterministic. Implementer should
     tighten this once run against CI with real observed text.
5. Verify NO tool-execution chip renders for the blocked tool.
   - **Verify**: no toolkit/tool chip (see ELITEA-2212's Concrete Handles —
     the new `chat-answer-tool-chip` testid) appears for `delete_file` in
     this turn's accordion — an ABSENCE assertion
     (`expect(locator).to_have_count(0)`), which per canon ruling #511 IS a
     first-class "reference" to the testid, satisfying the requirement that
     a newly-added testid be exercised on some case's executed path.

## Expected Results
- Block closes the card without executing the tool.
- File remains present in the bucket (backend-verified).
- LLM response acknowledges the block.
- No tool-execution chip for the blocked call.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Buttons visible | visible | step 1 | reused from ELITEA-2211 as this case's own precondition/setup (own conversation, executed independently) | asserted |
| 2 Click Block | card closes/updates | step 2 | step 2 | asserted |
| 3 Tool does NOT execute | no execution | step 3 | step 3 (backend file-listing, file still present) | asserted |
| 4 LLM response indicates block | response mentions block | step 4 | step 4 (loose non-empty/non-success signal, see step 4 note) | asserted *(clarification: exact wording not verifiable locally, see note)* |
| 5 No execution chips for blocked tool | no chips shown | step 5 | step 5 (absence assertion on the new tool-chip testid) | asserted |

**Axis 2 — Analyst additions:**
- Backend file-presence check as the ground truth for non-execution —
  *added: a UI-only "no chip" signal could also occur if the tool executed
  but the chip simply failed to render (a rendering bug would then read as
  a false negative for the product); checking the actual file is the only
  way to prove Block genuinely stopped the delete.*

## Cleanup
Same as ELITEA-2211/2212 (remove sensitivity flag once per test-file, delete
toolkit/bucket). Additionally: since the file is expected to SURVIVE this
case, explicit fixture teardown must still delete it (via bucket deletion)
rather than relying on the (already Block-confirmed) tool call.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Block button | **testid needed**: `sensitive-action-block-button` — add via `add-data-testid` to `ChatHitlActions.jsx`'s sensitive-tool "Block" `BaseBtn` (line ~175, currently zero testid) | none |
| Bucket file-listing (non-execution proof) | `ArtifactAPI.list_bucket_files(bucket_name)` | none |
| Toolkit/tool chip (absence check) | same new testid as ELITEA-2212 (`chat-answer-tool-chip`, once added) scoped to THIS turn's accordion, `to_have_count(0)` | none |

## Network Behavior
Resume action `onHitlResume({action: 'reject', ...})` — actual frame shape
not captured live (see ELITEA-2211's Network Behavior note).

## Known Defects Found During Exploration
None found.

## Blocked Steps
None beyond the shared precondition constraint (see ELITEA-2211).

## Automation Hints
- Same markers as ELITEA-2211/2212.
- Own fresh conversation per case (isolation, see ELITEA-2212's note).
