---
name: Chat participants popper Escape gap, MCP login-check false-positive, agent+pipeline state bug
description: chat-participants-popper doesn't close on Escape (ClickAway only) — use a raw mouse click outside it, not message_input.click() (can be disabled); remoteMcpLoggedOut flags ALL no-auth MCPs as misconfigured (#687); Agent+Pipeline coexisting can crash Send via wrong version_id (#684) — the picker-exclusion symptom below was RECLASSIFIED to its own issue, #689, correlated but not confirmed-same-mechanism (see UPDATE at bottom) (from ELITEA-2094, PR #688)
type: feedback
---

Discovered implementing ELITEA-2094 (Chat — Agent/Pipeline/Toolkit/MCP participants panel),
localhost:5173. Three separate, real findings — two product defects (filed/updated), one
infra timing bug (fixed in `ChatPage`):

## 1. `chat-participants-popper` does not respond to Escape

Unlike the plus-menu popper (`_ensure_plus_menu_closed` — click `message_input`, works, and
unlike a MUI `Modal`-backed component), `CollapsedParticipantsDropdown.jsx` wires only a
`ClickAwayListener` — no keydown/Escape handler. `page.keyboard.press("Escape")` is a
silent no-op on it. Consequence discovered live: opening section A's popper, pressing Escape,
then opening section B's popper (same shared `chat-participants-popper` testid across ALL 4
sections) leaves BOTH matching simultaneously → Playwright strict-mode violation
("resolved to 2 elements"). A fixed `page.wait_for_timeout(200)` after Escape masked nothing
— the first popper just never closed.

**Also**: `self.message_input.click()` as the dismiss mechanism (mirroring the WORKING
plus-menu technique) is itself fragile here — the composer textarea is legitimately
`disabled` while a just-added/just-switched participant's version/tools are resolving, and
Step 8's loop runs straight into that window, so `.click()` on a disabled element times out
("element is not enabled").

**Working fix**: a raw coordinate mouse click (`page.mouse.click(x, y)`) at a point in the
upper-left of the main content column (e.g. 30%/20% of viewport) — doesn't require ANY
target element's enabled/visible state, only needs to land outside the popper's DOM subtree
for `ClickAwayListener` to fire. Not a "locator" in the testid-only-policy sense (raw input
primitive, same category as `keyboard.press`). New method: `ChatPage.close_participants_popover()`.

## 2. Healthy remote MCP toolkits are ALWAYS falsely flagged as misconfigured (filed EliteaAI/elitea-testing-public#687)

`ParticipantStatusRunner.jsx`'s `remoteMcpLoggedOut` check is `toolkit_type === 'mcp' &&
!hasRemoteMcpLoggedIn` — and `hasRemoteMcpLoggedIn` is a PURE client-side localStorage
OAuth-token-presence check (`useMcpTokenChange`). A no-auth-required remote MCP server (e.g.
public `mcp.deepwiki.com`) never triggers the backend's `mcp_authorization_required` socket
event, so it can NEVER obtain that token — meaning it's permanently flagged "Server is
disconnected! Reconnect it to use." regardless of actual health. Confirmed on 3 independent
toolkit instances including the environment's own long-standing "Remote Github" fixture (id
3) — this isn't a fixture bug, it's universal for this toolkit subtype. `sync_mcp_tools()`
(the API call the "Load Tools" button makes) succeeding with real tools does NOT set this
state — there's currently no API path to make a no-auth MCP toolkit read as "logged in" at
all. **Don't build a fixture expecting a "healthy, no-warning" MCP participant state — it's
currently unreachable.** Soft-assert (`expect.soft()`) any check depending on it.

## 3. Agent+Pipeline participants coexisting → wrong version_id → crash/state corruption (generalizes EliteaAI/elitea-testing-public#684)

Originally filed as specific to one broken pipeline (project 471, orphaned version record).
**Reproduced deterministically with a completely FRESH, healthy pipeline** (`create_pipeline_with_llm_node`)
whenever an Agent participant is added before it — root cause confirmed via direct id
comparison across 5 independent fresh agent+pipeline pairs: the pipeline's own version-detail
fetch on Send (`GET version/prompt_lib/{project}/{pipeline_id}/{version_id}`) uses the
**agent's** version_id, not the pipeline's own — a state cross-contamination bug (stale
closure/memoized value from the previously-active participant), not a data-integrity issue
with any specific record. 400s, then crashes an unguarded `versionDetails.meta.icon_meta`
read in `ChatBox.jsx`'s `onSelectVersion` (the sibling `NewConversationView.jsx` version
already guards this exact case with `?.`).

**Race-condition-shaped, not deterministic in the full flow**: a rapid minimal repro
(agent+pipeline only, Send within ~1s) hit it 5/5; the full case flow (agent, pipeline,
toolkit, MCP, THEN send — more elapsed time) hit it roughly 1-in-3 to 1-in-5 across ~12 runs.
More wall-clock time before Send gives the race more chances to resolve harmlessly first —
don't add an artificial stabilization sleep to dodge it (that's exactly the kind of thing
that would mask a real defect a fast-clicking real user would still hit).

**A SECOND, independent symptom of the same fragility**: `useFilteredEntityItems.js`'s
already-added-entity exclusion filter (pure, synchronous, reads only the live `participants`
array — confirmed by reading the source, no dependency on the crash-prone version-fetch code
at all) ALSO intermittently fails once Agent+Pipeline coexist — even though it's logically
unrelated code. Isolated live: works correctly every time with an Agent-only participant.
Ruled out as a timing lag (added a condition-based poll around it — didn't resolve within the
window, so it's a real stale-state read, not a delay). Treat as evidence the underlying bug
is broader than "wrong version_id in one fetch call" — something about Agent+Pipeline
coexistence produces stale/inconsistent participant state more generally.

**Test-design takeaway**: if a case requires an Agent participant AND a Pipeline participant
in the same conversation before Send, expect BOTH the Send-crash symptom and the
picker-exclusion symptom to intermittently fire — soft-assert both, single mechanism
(`expect.soft()` throughout, don't mix with a manual `pytest.fail()` collector in the same
test — matches `.agents/testing.md`'s "identical mechanism" merge-gate requirement).

Full AFS: `test-specs/chat-interface/l2_add-agent-pipeline-toolkit-mcp-participants-panel_ELITEA-2094.md`.
Test: `automation/tests/ui/chat/test_chat_participants_panel.py`. PR #688.

## UPDATE (PR #688 fix-only pass, review round): picker-exclusion symptom split into its own issue, #689

A fresh reviewer session caught that bucketing the picker-exclusion symptom (item 3's
second paragraph above) under #684 overstated the confidence of the root-cause link:
#684's own 2026-07-20T17:03 comment explicitly says that symptom is "Not yet root-caused
to a specific line" — correlated with the same Agent+Pipeline trigger condition, but NOT
confirmed to share #684's precisely-diagnosed version_id-mixup mechanism (a completely
different code path — `useFilteredEntityItems.js` vs `ChatBox.jsx`'s `onSelectVersion`).
Filed as [EliteaAI/elitea-testing-public#689](https://github.com/EliteaAI/elitea-testing-public/issues/689),
cross-linked to #684 both ways. **Lesson for future correlation-based defect bucketing**:
"same trigger condition" is not "same root cause" — check the linked issue's OWN comments
for a root-cause confidence caveat before citing it as the mechanism for a second symptom,
even one discovered in the same session as the first. Also fixed this session: Step 9's
`assert conv_id` hard failure now runs a runtime signature check (console + pageerror +
network listeners) instead of asserting the #684 link on faith — see
`console_vs_pageerror_for_uncaught_exceptions.md` for the mechanics — and
`get_participant_section_icon_markup` no longer chains `badge.locator("svg").first`
(now a dedicated `chat-participants-badge-icon-{section}` testid).
