# Test Case: Chat – Regenerate After Stopped Generation Produces New Output

## Metadata
- **TMS ID**: ELITEA-2186
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: test-automation-engineer (combined analyst+implementer)
- **Status**: **blocked** — the case's own precondition ("a conversation where a previous generation was stopped exists") cannot be honestly reached against the live system. Reproduced live this session, deterministically, on the first attempt: sending `"generate a poem"` (case's own Test Data) and clicking Stop mid-stream does **not** leave a "stopped response" message to hover over and regenerate — it removes the **entire exchange** (both the user's message and the partial AI reply) from the conversation, client- and server-side, reverting the message list to its pre-send state. This is the SAME already-filed, already-linked defect documented for the sibling case ELITEA-2182 (`https://github.com/EliteaAI/elitea-testing-public/issues/1569`, "Stop wipes the entire message exchange, not just the streaming response") — re-confirmed here in a fresh conversation, independent of that case's own test run.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).
- A conversation where a previous generation was stopped exists — **this precondition cannot itself be constructed against the live product** (see § Blocked Steps).

## Test Data

| Field | Value |
|-------|-------|
| Message | `generate a poem` |

## Test Steps (as specified by the case — none reachable past step 1)

1. Type `'generate a poem'` and click Send; click stop to cancel mid-stream.
   - **Attempted live, this session**: sent the message, waited ~3s for streaming to begin (confirmed the loading placeholder + `chat-stop-generation-button` appeared), then clicked Stop.
   - **Observed** (defect #1569, re-confirmed): the message-item list reverted from what would have been 6 items (existing 4 + the new user message + its AI reply) back to the original 4 — the new exchange is entirely gone, not merely truncated/partial. The composer's text input was silently refilled with `"generate a poem"` (the typed text, not sent), and the last VISIBLE message in the list is again whatever it was BEFORE this exchange was sent.
   - **Expected per case**: "Generation stopped; partial or no content in response" — implying the exchange (or at least a stopped-state placeholder) remains visible to interact with. The live product instead removes it entirely.
2. Hover over the stopped response and click Regenerate.
   - **Blocked**: there is no "stopped response" message in the DOM to hover over — it was removed by step 1's defect. This step cannot be executed as specified against the current product.
3. Verify orange stop button appears during regeneration.
   - **Not reached** (depends on step 2).
4. Wait for new response to complete.
   - **Not reached**.
5. Verify Regenerate and action icons reappear; user message unchanged.
   - **Not reached**.

## Expected Results
Not established — the case's precondition cannot be constructed. See § Blocked Steps.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: a conversation where a previous generation was stopped exists | — | attempted, live, this session | § Blocked Steps | blocked |
| 1 Type message, Send, click Stop mid-stream → Generation stopped; partial or no content in response | stopped state exists | step 1 (attempted) | live DOM/message-count observation | blocked *(live behavior removes the entire exchange instead of leaving a stopped/partial response — known defect #1569)* |
| 2 Hover over stopped response and click Regenerate → New generation begins | — | not reached | — | blocked |
| 3 Verify orange stop button appears during regeneration → Stop button visible | — | not reached | — | blocked |
| 4 Wait for new response to complete → Full response generated | — | not reached | — | blocked |
| 5 Verify Regenerate/action icons reappear; user message unchanged → Actions visible; message unchanged | — | not reached | — | blocked |
| Expected Final State: "Regenerate after stop produces a new complete response." | — | not reached | — | blocked |
| Pass/Fail: "Regenerate after stop works." | — | not reached | — | blocked |

### Axis 2 — Analyst additions
None — the case could not progress past its own precondition; no additional observables were explored beyond confirming and cross-referencing the root cause.

## Cleanup
No conversation was persisted for teardown beyond the reused, pre-existing exploration conversation's own state (its 4 pre-existing messages were left intact — the wiped exchange left no trace to clean up, confirming the defect's own description).

## Fidelity Declaration
No substitution — the blocking observation (the exchange vanishing after Stop) is itself the live system's real, unmodified behavior; nothing was fabricated or bypassed to reach this verdict.

## Concrete Handles (discovered during exploration)
Not applicable beyond what is already documented for ELITEA-2182/2183 (`chat-stop-generation-button`, `chat-regenerate-button`) — the case never reaches the Regenerate interaction this AFS would otherwise document handles for.

## Network Behavior
Not explored beyond confirming the same Stop-click behavior already characterized for ELITEA-2182 (client list AND the conversation's own REST `GET .../conversation/{id}` both reflect the exchange's removal, per that case's own soft-asserted evidence — not re-derived here, cross-referenced).

## Known Defects Found During Exploration
- **Not a new filing** — cross-referenced to already-open, already-linked defect `https://github.com/EliteaAI/elitea-testing-public/issues/1569` ("Stop wipes the entire message exchange, not just the streaming response"), originally found and filed during ELITEA-2182's analysis/implementation. Re-confirmed live this session in an independent, fresh conversation (`generate a poem` prompt, per THIS case's own Test Data — a different prompt than ELITEA-2182 used) — same symptom, same root cause, same single-cause signature. No duplicate issue filed (`.agents/profile.md` § Bug filing — dedup before filing; this is a same-object, same-trigger, same-expected/actual match, not a sibling).

## Blocked Steps
- **Step 1 onward.** The case's foundational precondition — "a conversation where a previous generation was stopped exists," with the stopped response still present to interact with — cannot be constructed against the live product while defect #1569 is open. This is not "one isolable step at the tail" (`.agents/testing.md` § Merge gate, analysis-time entry) that could be soft-asserted and the rest of the flow still exercised — it is the object every remaining step (hover, click Regenerate, verify the orange stop button, wait for completion, verify actions reappear) depends on. Routing per `.agents/role-overrides.md`: this AFS is `blocked` → lead → track against #1569; re-attempt once #1569 ships a fix (the WIP work observed on this same batch trunk for ELITEA-2182/2183, commit `d2c3dcc2`, suggests active work on the underlying Stop-handling code — worth re-checking this case shortly after that lands).

## Automation Hints
Not applicable — no test was built for this case. When #1569 is resolved, re-run this analysis fresh (the live product's post-fix Stop behavior may differ enough from this AFS's assumptions — e.g. what exactly remains as "the stopped response" — that a full re-exploration is warranted rather than resuming from this AFS's steps 2-5, which were never observed live).
