# Test Case: Chat – HITL Authorization – Block with Comment Records the Reason and Blocks the Toolkit Action

## Metadata
- **TMS ID**: ELITEA-2214
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local for the toolkit-call/chip mechanics;
  source-verified (`BlockWithCommentControl.jsx`) for the comment control
  itself. See ELITEA-2211 § Preconditions for the shared environment note.
- **User set**: `${TEST_USER}`
- **Analyst**: qa-engineer (cluster run, ELITEA-2211..2215, 2026-08-03)
- **Status**: ready-for-automation

## Preconditions
Same as ELITEA-2213 — own fresh authorization-card instance.

## Test Data
- Same fixture shape as ELITEA-2211/2212/2213.
- Block comment: `"This action is too risky and could delete important data"`
  (case's literal text) — source-confirmed the control caps input at 2000
  chars (`BlockWithCommentControl.jsx:9`, `MAX_COMMENT_LENGTH`), so this
  string is well within range, no truncation risk.

## Test Steps
1. Reach the authorization card (own fresh conversation).
2. Click "Block with Comment" (collapsed-state trigger — source:
   `BlockWithCommentControl.jsx:71-82`, `variant="secondary"` = gray, **no
   testid today**).
   - **Verify**: an inline textarea + Cancel/submit-"Block with Comment"
     button pair appears IN PLACE on the card (source: the component swaps
     its OWN return branch on `open` state — this is NOT the
     conditional-testid-pair pattern from canon ruling #277, since these are
     two entirely separate DOM subtrees on different `open` states of the
     SAME component, not a same-element ternary; each needs its own testid).
3. Type the comment into the textarea.
   - **Verify**: textarea value updates (React-controlled — use `.fill()`
     then confirm via the input's own value, or `press_sequentially` per
     `.claude/rules/mui-patterns.md` if `.fill()` doesn't register — this
     is a plain MUI `TextField`, same pattern as other MUI form fields in
     this project).
4. Click Submit (the expanded-state's own "Block with Comment" button,
   `BlockWithCommentControl.jsx:110-118` — **note: SAME visible label text
   as the collapsed trigger from step 2, but a DIFFERENT DOM element** —
   disambiguate by testid, not text, once both have one).
   - **Verify**: `handleSubmit` fires only when `trimmedComment` is
     non-empty (`BlockWithCommentControl.jsx:51-56`) — calls
     `onSubmit(trimmedComment)` which the parent wires to
     `onHitlResume({action: 'block_with_comment', value: comment, toolCallId, interruptId})`
     (`ChatHitlActions.jsx:111-116`); textarea + comment-input UI collapses
     back (`setOpen(false)`).
5. Verify the toolkit tool does NOT execute.
   - **Verify**: file still present in the bucket (`ArtifactAPI.list_bucket_files`)
     — same backend-verified non-execution pattern as ELITEA-2213.
6. Verify the LLM response acknowledges the block.
   - **Verify**: same loose non-empty/non-success signal as ELITEA-2213
     step 4 — exact wording unverified live (precondition unreachable
     locally).

## Expected Results
- Block with Comment records the typed reason, sends it as
  `denial_reason` (per `BlockWithCommentControl.jsx`'s own docstring,
  line 18-19) and prevents execution.
- File remains present (backend-verified).
- LLM response acknowledges the block.

## Coverage Map

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Click Block with Comment | modal/input appears | step 2 | step 2 | asserted |
| 2 Type comment | comment entered | step 3 | step 3 | asserted |
| 3 Click Submit/Confirm | modal closes, card updates, blocked | step 4 | step 4 | asserted |
| 4 Tool does NOT execute | no execution | step 5 | step 5 (backend file-listing) | asserted |
| 5 LLM response acknowledges block | response about block | step 6 | step 6 (loose signal, see ELITEA-2213's equivalent note) | asserted *(clarification: exact wording unverified, see note)* |

**Axis 2 — Analyst additions:**
- Same backend-verified non-execution rationale as ELITEA-2213 — *added:
  ground-truth proof beats a UI-only "card closed" signal.*
- Note the case's own text calls this a "Modal" — source confirms it's an
  INLINE expansion on the same card (`BlockWithCommentControl.jsx`'s
  `Collapse`-free conditional render, not an MUI `Dialog`/`role="dialog"`)
  — *added: flagging so the implementer doesn't hunt for a `[role="dialog"]`
  that doesn't exist here; this is case-text imprecision, not a defect
  (the observable — "an input appears, submitting blocks the action" — is
  unaffected).*

## Cleanup
Same as ELITEA-2211/2212/2213.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback |
|---|---|---|
| Block with Comment (collapsed trigger) | **testid needed**: `sensitive-action-block-with-comment-button` — `BlockWithCommentControl.jsx:73` (`!open` branch) | none |
| Comment textarea | **testid needed**: `sensitive-action-block-comment-input` — `BlockWithCommentControl.jsx:87` `TextField` | none |
| Cancel button (expanded state) | **testid needed**: `sensitive-action-block-comment-cancel-button` — `BlockWithCommentControl.jsx:103` | none — not asserted by this case's steps, but the sibling to the Submit button worth naming while in there (implementer's call whether in-scope; this case's OWN executed path doesn't click Cancel, so per the testid-scope rule, only add it if a case actually exercises it — otherwise leave to a future case) |
| Submit button (expanded state) | **testid needed**: `sensitive-action-block-comment-submit-button` — `BlockWithCommentControl.jsx:110` (same visible text as the collapsed trigger — testid is the only reliable disambiguator) | none |
| Bucket file-listing (non-execution proof) | `ArtifactAPI.list_bucket_files(bucket_name)` | none |

## Network Behavior
Resume action `onHitlResume({action: 'block_with_comment', value: comment, ...})`
— actual frame shape not captured live (see ELITEA-2211's note).

## Known Defects Found During Exploration
None found.

## Blocked Steps
None beyond the shared precondition constraint (see ELITEA-2211).

## Automation Hints
- Same markers as the rest of the cluster.
- Do NOT add the Cancel-button testid unless this test (or a sibling in the
  same PR) actually clicks Cancel — per `.agents/role-overrides.md` §
  Every role locator policy, "touches" = the test's executed code path,
  not "plausible future use."
