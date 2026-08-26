# Test Case: Chat – HITL Authorization – Sensitive Action Authorization Card Displays When Toolkit Called Directly

## Metadata
- **TMS ID**: ELITEA-2211
- **Linked Story**: none
- **Priority**: l2
- **Environment Explored**: local (`http://localhost:5173`) — **the full case, end to end,
  including the Sensitive Action Authorization card itself.** No deployed env, no Admin UI.
- **User set**: `${TEST_USER}` (dev-token bypass on localhost; `ELITEA_API_TOKEN` for the
  precondition write)
- **Analyst**: qa-engineer
- **Status**: ready-for-automation
- **Revision**: 2026-08-27 — **RE-ANALYSIS. Supersedes the 2026-08-03 pass entirely.**
  The prior pass classified the HITL trigger precondition as unreachable on localhost and
  routed the whole module behind `pytest.mark.guardrails` + a deployed-env CI path. That
  conclusion was **wrong** — it was reached from one interface (the Admin UI) without
  probing for another. The card was produced live on `localhost:5173` this pass, 2 of 2
  attempts, and every assertion in the merged test is now verified against a real card
  instead of against source-reading. See § What changed and why.

---

## What changed and why (read this first — the merged test needs rework)

The test for this case is **already written and merged** to `automation/base`
(`automation/tests/ui/chat/test_hitl_sensitive_action_authorization.py::TestSensitiveActionCardDisplay::test_sensitive_action_card_displays_for_direct_toolkit_call`)
but **has never executed**: it carries `pytest.mark.guardrails`, which excludes it from the
local loop, and its module-scoped `sensitive_delete_file_toolkit` fixture drives the Admin
UI at `{elitea_url}/admin/app/configuration#guardrails`, which renders Page404 on localhost
(issue #1140).

Three facts established this pass, in order:

1. **The Admin UI genuinely is not on localhost, and never was.** `EliteaUI/src/routes.js`
   has no `/admin` route — the Admin UI is a **separate deployed application**. This is an
   environment boundary, not a product regression, so #1140 is correctly filed but is not a
   blocker for this case.
2. **The guardrails config is reachable by REST — under a different mode segment than the
   one previously probed.** `prompt_lib` is denied to the standard user; **`administration`
   is not**:

   | Request (standard-user `ELITEA_API_TOKEN`) | Result |
   |---|---|
   | `GET  {api}/admin/plugin_config_values/prompt_lib/guardrails` | **403** `{"ok": false, "error": "access_denied"}` |
   | `GET  {api}/admin/plugin_config_values/administration/guardrails` | **200** — full config, `sensitive_tools: {}` |
   | `PUT  {api}/admin/plugin_config_values/administration/guardrails` | **200** `{"saved": true, "requires_restart": []}` — readback confirms `sensitive_tools: {"artifact": ["delete_file"]}` |

   `requires_restart: []` — the change is **live immediately**; no restart, no redeploy, no
   re-attaching the toolkit, no new conversation.
3. **`artifact`/`delete_file` is NOT sensitive by default.** Verified by running the case's
   own flow with `sensitive_tools: {}`: the tool executed straight through, the file was
   deleted (confirmed via `ArtifactAPI.list_bucket_files` → `[]`), and no card ever
   appeared. So the precondition is real work, not dead weight — it just does not need the
   Admin UI.

**Verdict: the case is fully automatable on `http://localhost:5173`, with the card produced
by the real backend HITL flow.** The rework is confined to the precondition mechanism plus
two assertion tightenings — see § Rework delta for the implementer.

---

## Preconditions

- An Artifact-type toolkit exists with `delete_file` in its `selected_tools`
  (`ToolkitAPI.create_artifact_toolkit()` already includes it — reuse `artifact_toolkit`).
- The toolkit's bucket contains at least one file (`artifact_seeded_file` — already exists).
- **`artifact` / `delete_file` is marked as a Sensitive Action Tool via the guardrails
  config REST endpoint** (NOT the Admin UI):

  ```
  GET  {ELITEA_API_BASE}/admin/plugin_config_values/administration/guardrails
  PUT  {ELITEA_API_BASE}/admin/plugin_config_values/administration/guardrails
       {"values": {<the full GET body>, "sensitive_tools": {"artifact": ["delete_file"]}}}
  ```

  Confirmed live this pass with the standard test user's `ELITEA_API_TOKEN`. **The PUT
  requires the FULL values object** — read it first, mutate `sensitive_tools`, PUT it back.
  Restore the captured original on teardown by PUTting it verbatim (verified: readback
  returned to `sensitive_tools: {}`).
- **Sensitivity is toolkit-TYPE scoped and ORG-WIDE** (the key is `artifact`, the toolkit
  *type*, while the rendered card names the toolkit *instance* — `hitlprobe779009.delete_file`
  — confirming type-scoped matching). Any other suite calling `delete_file` on ANY artifact
  toolkit while the flag is set will hit the authorization card. **Teardown restore is
  mandatory, not optional**, and it must run even when the test fails.
- No agent is used — the toolkit is added directly as a chat participant via the main
  `/chat` page's "+ > Toolkits" flow.

---

## Test Data

### generate-per-test (created in setup, cleaned up in teardown)
- Artifact bucket + toolkit + seeded file — `artifact_toolkit` / `artifact_seeded_file`
  fixtures, unchanged. Confirmed live this pass (bucket `hitl-probe-779009`, toolkit id
  `3385`, project 399, created via `ArtifactAPI`/`ToolkitAPI` on the `ELITEA_API_TOKEN`
  Bearer fallback — no browser cookies needed).
- Fresh conversation — `conversation_id` fixture. **Use it.** Bare `/chat` restores the
  user's most recent conversation (the documented `#1082` pollution class), which landed
  this pass on an unrelated prior chat.

### Message text
`"use delete_file toolkit to remove from the bucket all files"` (the case's literal text)
is **ambiguous and does not reach a tool call** — RE-CONFIRMED, unchanged from the prior
pass. The implementer's existing `_unambiguous_delete_message()` helper is correct and was
re-verified live this pass, 2 of 2 attempts:

```
Use delete_file toolkit to delete a file named "{file_key}" from bucket "{bucket_name}". Execute the tool now, do not ask for clarification.
```

This is a **case-text CLARIFICATION**, not a product defect (reverse-masking guard).

---

## Test Steps

1. *(setup)* Create bucket + toolkit + seed a file. Capture the current guardrails config,
   then PUT it back with `sensitive_tools = {"artifact": ["delete_file"]}`.
2. *(setup)* Create a fresh conversation; navigate to `/chat/{conversation_id}`.
3. **Add the toolkit as a participant via "+ > Toolkits" (no agent).**
   - Verify: the toolkit row's switch becomes checked and the "Toolkits in this
     conversation" counter reads `1`. *(Observed live; the merged test instead treats the
     downstream card naming `delete_file` as the causal proof the toolkit was attached —
     that remains valid and is the stronger signal. Either is acceptable.)*
4. **Send the unambiguous delete-file message.**
   - Verify: the "Thought for X secs" accordion appears (`chat-answer-thought-accordion`).
     Observed live: "Thought for less than a second" on the fresh-conversation run and
     "Thought for 2 secs" on the first run — **the text is variable, so assert visibility,
     never the literal string.**
5. **Verify the Sensitive Action Authorization card appears.**
   - Verify: `[data-testid="sensitive-action-panel"]` becomes visible. Observed live in
     **both** shapes — a fresh conversation's first turn and a second turn in an existing
     conversation. **Latency: >5 s, <25 s** from send (the panel was absent at a 5 s poll
     and present by 25 s). The merged test's 30 s `SENSITIVE_ACTION_TIMEOUT` is adequate;
     do not lower it.
6. **Verify the heading text.**
   - Verify: panel contains `"Sensitive Action Authorization Required"`. Observed live,
     rendered with a leading `⚠️` emoji: `⚠️ Sensitive Action Authorization Required`.
     Assert the phrase as a substring, not the emoji-prefixed literal.
7. **Verify "Agent is about to perform:" + the tool name.**
   - Verify: panel contains `"Agent is about to perform:"` **and** the composed action name
     **`{toolkit_name}.{tool_name}`** — observed live as `hitlprobe779009.delete_file`.
   - **The case's `aaa.delete_file` is LITERAL FORMAT, not an illustration.** The prior
     pass could not verify this and told the implementer to assert only the bare
     `delete_file` substring; that assertion is weaker than the product supports.
     **Tighten it to `f"{toolkit_name}.{SENSITIVE_TOOL_NAME}"`.**
8. **Verify all three buttons render.**
   - Verify: `sensitive-action-authorize-button` ("Authorize"),
     `sensitive-action-block-button` ("Block"),
     `sensitive-action-block-with-comment-button` ("Block with Comment") are all visible.
     All three confirmed live by DOM query on the rendered panel — **all three testids
     already exist, on `main`** (§ Concrete Handles). The case's colour annotations
     (green / red / gray) are `BaseBtn` `variant` props (`positive` / `alarm` /
     `secondary`), not asserted by computed style.
9. *(teardown)* Resolve the pending card so the conversation does not stay paused (click
   Block — verified live to close the panel), then restore the guardrails config, delete
   the toolkit / bucket / conversation.

---

## Expected Results

- The Sensitive Action Authorization card appears, produced by the real backend HITL flow,
  with the correct heading, the `{toolkit}.{tool}` action name, and exactly three action
  controls.
- No console **errors** during the flow (0 observed). See § Known Defects for the console
  **warning** that does occur.

---

## Coverage Map

**Axis 1 — every element of the TMS case:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` (dev-token bypass on localhost) | fixture | asserted (implicitly — no step reaches the composer unauthenticated) |
| Precondition: toolkit configured with HITL authorization is added as participant | sensitivity applies to `delete_file` | steps 1 + 3 | guardrails REST PUT (setup) + step 3 | asserted — **now live-verified on localhost**, no longer env-gated |
| 1 Add a toolkit with HITL `delete_file` via + > Toolkits (no agent) | Toolkit in PARTICIPANTS | step 3 | step 3 | asserted |
| 2 Send message triggering sensitive action | 'Thought for X secs' appears | step 4 | step 4 | asserted *(clarification: the "X secs" text is variable — "less than a second" observed — so visibility is asserted, not the literal)* |
| 3 Authorization card appears with orange/warning border | Authorization card shown | step 5 | step 5 | asserted *(clarification: the `sensitive-action-panel` testid renders ONLY for `guardrail_type` `sensitive_tool`/`parallel_sensitive_tools` — `ChatHitlActions.jsx:22` — so its presence IS the "sensitive" signal; the orange is `palette.warning.main` via inline `sx`, no class to assert)* |
| 4 Heading 'Sensitive Action Authorization Required' in orange text | Heading correct | step 6 | step 6 | asserted |
| 5 Card shows 'Agent is about to perform:' with tool name (e.g. 'aaa.delete_file') | Tool name shown | step 7 | step 7 | asserted — **format now verified live as `{toolkit_name}.{tool_name}`; the case's example was accurate** |
| 6 Three buttons: Authorize (green), Block (red), Block with Comment (gray) | All three visible | step 8 | step 8 | asserted *(clarification: colours are `BaseBtn` variants, asserted as identity + visibility, not computed CSS colour)* |
| Expected Final State: card appears with correct content and buttons | — | steps 5–8 | steps 5–8 | asserted |

**Axis 2 — analyst additions (beyond the case):**
- **No console/JS errors across the whole flow** — *added: standard side-channel check.
  HITL rides an async WebSocket envelope, exactly the shape that swallows errors silently.
  0 errors observed live; note the warning in § Known Defects.*
- **Unambiguous, explicit-bucket message text instead of the case's literal wording** —
  *added: the case's own text was re-confirmed live not to reach a tool call at all against
  a project with many buckets; without this the test never gets a card to assert on.*
- **Fresh `conversation_id` rather than bare `/chat`** — *added: bare `/chat` restored an
  unrelated prior conversation live this pass (the documented `#1082` pollution class).*

**Deliberately NOT specced** (observed but out of the case's scope, and speccing them would
require adding testids to elements no test exercises — `.agents/testing.md` § Locator policy
blanket-add ban): the `Parameters ▸` expander (`SensitiveToolParams.jsx`, has no testids)
which renders `filename` / `bucket_name`, and the policy-message line *"Agent is about to
call: `{action}` tool. According to **ELITEA** AI policy, this action requires explicit user
approval."* (template-driven from the guardrails config key
`sensitive_action_message_template`, so asserting it would couple the test to org config).

---

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority |
|---|---|---|
| The guardrails **precondition** is configured via `PUT {api}/admin/plugin_config_values/administration/guardrails` instead of through the Admin UI | **Transit** | The case's observable — the Sensitive Action Authorization card and its contents — is produced **entirely by the real backend HITL flow**: the real LLM decides to call the real tool, the real backend interrupts it, and the real WebSocket frame renders the real card. The substitution only *reaches* the step under test. The Admin UI is not the subject of this case (it appears in neither the case's steps nor its expected results — it was the *prior analyst's* chosen mechanism, not the case's), and it is not served on the local target at all. |

**No terminal substitution anywhere in this spec.** Nothing about the card is mocked,
injected, fabricated or routed. `page.route`, `route.fulfill`, `page.evaluate` and
monkeypatching are **not** used and must not be introduced. If the card cannot be produced,
the test fails naturally.

*Note for the implementer's Run Report grep:* the required
`\.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\(` self-check should return
**0 hits** on this case's diff. The guardrails PUT is an ordinary `requests` call in an API
client / fixture, not a Playwright interception, so it does not appear in that grep — it is
declared here instead.

---

## Rework delta for the implementer (the merged test already exists)

| # | Change | Where |
|---|---|---|
| 1 | **Replace the fixture's Admin-UI driver with the REST config write.** Drop the `browser.new_context()` / `GuardrailsAdminPage` / `navigate_to_guardrails()` / `add_sensitive_tool()` / `save_configuration()` body. Read the current config, PUT it back with `sensitive_tools = {"artifact": ["delete_file"]}`, yield, then PUT the captured original verbatim in teardown. | `automation/fixtures/data_fixtures.py:1855` `sensitive_delete_file_toolkit` |
| 2 | **Add the guardrails config methods to the API layer** (`get_guardrails_config()` / `set_guardrails_config(values)`), rather than raw `requests` in the fixture — matches `.claude/rules/api-patterns.md`. Endpoint + payload shape are in § Preconditions. | `automation/api/client.py` |
| 3 | **Remove `pytest.mark.guardrails` from `pytestmark`.** The whole reason for the marker is gone: this module no longer touches the Admin UI, so it belongs in the local loop. Keep `ui`, `chat`, `p2`, `regression`. **Do not** touch `test_guardrails_live_reload.py` / `test_guardrails_cleanup_only.py` — those genuinely test the Admin UI and keep the marker. | `tests/ui/chat/test_hitl_sensitive_action_authorization.py:63` |
| 4 | **Tighten the action-name assertion** from the bare `SENSITIVE_TOOL_NAME` substring to `f"{toolkit_name}.{SENSITIVE_TOOL_NAME}"`. The format is now live-verified. | same file, Step 5 block |
| 5 | **Delete the "unverified live / precondition unreachable" caveats** from the module docstring, the Step 5 `allure.step` label, and the sibling cases' comments. Every one of them is now false. Replace the module docstring's "CONFIRMED ENVIRONMENT LIMITATION" block with the § What changed and why summary. | same file |
| 6 | **Keep the fixture module-scoped.** Marking/unmarking once per module (not per test) is still right for ELITEA-2211..2214, and the org-wide blast radius is a reason to keep the window short. | fixture |
| 7 | The teardown restore **must** be in a `finally` and must PUT the captured original — not a hardcoded `{}`. If another suite or a human has set other sensitive tools, a hardcoded `{}` silently wipes their config. | fixture |

**Blast radius:** only `tests/ui/chat/test_hitl_sensitive_action_authorization.py` consumes
`sensitive_delete_file_toolkit` (verified by grep), so this rework touches nothing else.

**Siblings ELITEA-2212 / 2213 / 2214** ride the same fixture and the same
`_reach_sensitive_action_card()` helper, so they unblock with the identical change. Two of
their observables were incidentally confirmed live this pass: clicking **Block** closes the
panel, and the target file **survived** the blocked call (`hitl-probe-seed2.txt` still
present after Block). Their own AFS files were not re-analysed — flag to the lead.

---

## Cleanup

1. Resolve any pending card (click Block) so the conversation is not left paused.
2. **Restore the guardrails config** by PUTting the captured original — mandatory, org-wide
   side effect, must run on failure too.
3. Delete the toolkit (`ToolkitAPI.delete_toolkit`) — confirmed working live.
4. Delete the conversation (`ConversationAPI.delete_conversation`) — confirmed working live.
5. Delete the bucket (`ArtifactAPI.delete_bucket`) — **re-confirmed flaky**: 404 on
   `p--{project_id}.{bucket_name}` for a bucket created minutes earlier. Non-blocking (the
   `artifact_bucket` fixture already swallows it with a `logger.warning`), but it is the
   likely source of the project's accumulated bucket pollution. Unchanged tech-debt note.

---

## Concrete Handles (verified live this pass)

Provenance verified after `cd ../EliteaUI && git fetch origin` on 2026-08-27.

| Element | Recommended Locator | PROVENANCE |
|---|---|---|
| Sensitive action panel | `LocatorDescriptor(testid="sensitive-action-panel")` — already a `ChatPage` field (`chat_page.py:986`) | **on-main ✓** |
| Authorize button | `LocatorDescriptor(testid="sensitive-action-authorize-button")` — `chat_page.py:997`; live text "Authorize" | **on-main ✓** |
| Block button | `LocatorDescriptor(testid="sensitive-action-block-button")` — `chat_page.py:1002`; live text "Block" | **on-main ✓** |
| Block with Comment button | `LocatorDescriptor(testid="sensitive-action-block-with-comment-button")` — `chat_page.py:1007`; live text "Block with Comment" | **on-main ✓** |
| Thought accordion | `LocatorDescriptor(testid="chat-answer-thought-accordion")` | **on-main ✓** |
| Plus menu button | `plus-menu-button` | **on-main ✓** |
| Toolkits submenu item | `toolkits-menuitem` | **on-main ✓** |
| Message composer | `chat-message-input` | **on-main ✓** |
| Toolkit participant row (dynamic) | `toolkits-menu-item-toolkit-{project_id}-{toolkit_id}` — live-confirmed as `toolkits-menu-item-toolkit-399-3385` | **on-main ✓** |

**No new testids are needed for this case.** All nine handles exist and are on
`EliteaAI/EliteaUI` `main` — this case is **fully promotable** with zero pending human
cherry-picks.

| Toolkits participants badge | `chat-participants-badge-toolkits` — via `ChatPage.is_participants_badge_visible(section="toolkits")` | **on-main ✓** (`CollapsedPerticapantsList.jsx:223`, runtime-composed `chat-participants-badge-${entity.section}`) |

**Implementer correction, 2026-08-27 (supersedes the note this replaced).** The AFS
previously recorded that `ChatPage.add_toolkit_participant()` — the legacy
accessible-name/`:has-text` search flow the merged test called — "still works... a
reasonable, optional upgrade, but not required by this case". **It is required.** In the
automated path that flow left the toolkit **UNATTACHED 3 runs out of 3** while reporting no
error: the model then had no `delete_file` tool, answered *"The file ... has been
successfully deleted"* anyway, and the seeded file was still in the bucket (verified via
`ArtifactAPI.list_bucket_files` after the run). No tool call ⇒ no backend interrupt ⇒ no
card, and the failure surfaced only as "the card did not appear". Root cause: that flow
types into the plus-menu's **non-debounced** search field and then clicks
`li[role="menuitem"]:has-text(...)`.first — the same race `chat_page.py`'s
`add_toolkit_participant_via_slash_menu()` docstring already warns about, and
`_surface.md` already records the legacy flow as **not reusable** for the toggle-switch
Toolkits rows.

The implementation therefore attaches via
`add_toolkit_participant_via_slash_menu(project_id, toolkit_id)` (dynamic testid — also the
locator-policy-compliant shape) and asserts the attachment explicitly with **AFS step 3's
own primary verification**, the "Toolkits in this conversation" badge, rather than inferring
it from the downstream card. `artifact_toolkit` already yields `project_id`, so no fixture
change was needed. The same helper serves ELITEA-2212/2213/2214.

*Provenance correction:* `_surface.md` recorded the plus-menu row testids as "on
`automation/testids` only, not yet on `main`". They **are on `main`** —
`PlusChatSubmenu.jsx:131` composes `` `${sectionKey}-menu-item-${item.key}` `` at runtime,
which a bare-substring grep for `toolkits-menu-item` cannot see (the exact false-negative
class `.agents/workflow.md` § Closure record warns about).

---

## Network Behavior

- The HITL pause/resume rides the `chat_predict` WebSocket envelope; the frontend
  disambiguates on `guardrail_type` (`sensitive_tool` / `parallel_sensitive_tools` —
  `ChatHitlActions.jsx:22`).
- The precondition write is a plain REST call:
  `PUT /admin/plugin_config_values/administration/guardrails` →
  `200 {"saved": true, "requires_restart": []}`.
- **New this pass:** during the card's arrival the backend also emits a
  `parallel_hitl_ready` socket message which the frontend does not handle — see
  § Known Defects.

---

## Known Defects Found During Exploration

- **#1831 (filed this pass, MINOR)** — the backend emits a `parallel_hitl_ready` WebSocket
  message during the sensitive-action HITL flow that the frontend has **no handler for**;
  it falls to the `default` branch of the socket switch (`src/components/Chat/hooks.js:1658`),
  logs `console.warn('unknown message type', ...)` and `return`s early, skipping the
  `setChatHistory` update that otherwise runs on every socket message. `grep -rn
  "parallel_hitl" src/` returns zero hits — no constant, no case. Observed 2 of 2 HITL
  invocations. **Not blocking:** the card renders correctly and Block resolves it, and it is
  a *warning*, so the test's errors-only side-channel assertion stays green. Do **not**
  weaken or filter that assertion for it.
- **#1140 (pre-existing)** — Guardrails admin route `/admin/app/configuration#guardrails`
  is Page404. Still true, still correctly filed, but **no longer a blocker for this case**:
  the Admin UI is a separate deployed application (no `/admin` route in
  `EliteaUI/src/routes.js`), and the config is reachable by REST. The lead may want to
  re-scope #1140 — it blocks `test_guardrails_live_reload.py` /
  `test_guardrails_cleanup_only.py`, which really do test the Admin UI, but not this module.
- Testid gaps: **none**. Nothing to add.

---

## Blocked Steps

**None.** Every step of the case, including the Sensitive Action Authorization card itself,
was executed and observed live on `http://localhost:5173` this pass.

---

## Automation Hints

- Framework: Playwright + pytest, per `.agents/testing.md`.
- Markers after rework: `ui`, `chat`, `p2`, `regression` — **not** `guardrails`.
- Wait budget: the card arrives >5 s and <25 s after send. Keep `SENSITIVE_ACTION_TIMEOUT`
  at 30 s; wait on the panel's visibility, never a sleep.
- The guardrails config change is live immediately (`requires_restart: []`) — no restart,
  no re-attach, no fresh conversation required. It applied mid-conversation to the very
  next turn.
- Run the module **serially** — the guardrails flag is org-wide while it is set, so this
  module must not run under `pytest-xdist` alongside anything touching artifact toolkits.
- The org-wide window is the real risk of this module. Prefer the tightest scope that still
  avoids per-test admin round-trips (module scope, as now), and make the restore
  unconditional.
