# Test Case: Skill Version Selection Behavior

## Metadata
- **TMS ID**: ELITEA-2610
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter/body)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model:
  Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation`
- **Case-gate note**: case frontmatter carries `status: draft`, `execution_type: manual`
  — per `.agents/test-automation.yaml` § `intake`, `draft` is the intake-eligible
  value, not an exclusion. Proceeded to full execution.
- **Dedup / reuse check**: grepped `test-specs/skills/` and `automation/tests/ui/skills/`
  by behaviour (version selector + agent chat + skill invocation). Closest
  neighbours, both merged to `automation/base`:
  - `l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md` /
    `test_skill_agent_version_selector.py` — proves the AGENT-attach version
    selector UI is present, shows the default (`base`), and opens a real
    "Versions" menu. That skill only ever had ONE saved version in that run, so
    the flow of actually SELECTING a non-base option, and of that selection
    changing the AGENT's CHAT behaviour, was never exercised there.
  - `l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md` /
    `test_skill_test_panel_version_instructions.py` — proves version-switching
    changes the response inside the **Skill's own detail-page SkillTestPanel**
    (a skill-scoped test surface). This case is a DIFFERENT surface: the
    **Agent's live chat**, where the skill is attached and invoked
    autonomously as one of the agent's tools (tags: `feat:autonomous-invocation`),
    not run directly against the skill's own test panel.
  - `lextend_skill-autonomous-invocation-core-functionality_ELITEA-2607.md` /
    `lextend_skill-explicit-autonomous-invocation-coexistence_ELITEA-2609.md` —
    prove the autonomous-invocation MECHANISM (the model decides to `load_skill`,
    a `chat-answer-tool-chip` reading `"Skill: {name}"` appears) but never vary
    the ATTACHED VERSION — always whatever the skill's single/default version is.

  None of the three combines "agent has a skill attached with a specific
  NON-BASE version selected" + "agent chat autonomously invokes it" +
  "switching the attached version changes the next chat turn's behaviour
  immediately, no reload/new-chat/agent-Save needed." Genuinely new coverage —
  proceeded as `ready-for-automation`, not `already-covered`/`extend-existing`.

## Preconditions
- User is logged in to the Elitea platform with Admin or Editor role (on
  localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- The Skills and Agents sections are available in the project.

## Test Data

### generate-per-test (created in test setup, cleaned up in teardown)
- **Skill name**: kebab-case, e.g. `elitea-2610-response-style` (must satisfy the
  Name field's lowercase-letters/digits/hyphens client-side validation, same
  constraint documented for ELITEA-1737/1735/1789/2440). The case's literal Test
  Data name examples (a bare `response-style` skill with human-readable version
  names `casual`/`technical`) are usable close to as-written; only the skill name
  itself needs kebab-casing.
- **Instructions — DETERMINISTIC MARKER TAGS, not the case's literal "formal
  tone" / "casual tone with emojis" / "technical details" prose.** Live
  execution confirms the LLM reliably follows an explicit "start your response
  with this exact tag" instruction, but "is this response in a casual tone" is
  a subjective judgment call that doesn't make a reliable automated assertion.
  Mirrors the deterministic-marker pattern already established by ELITEA-2440
  (`"Always say BASE"` / `"Always say V1"`) — used here as a **prefix tag**
  instead of an exact one-word reply, because the case's own Pass criteria
  ("distinct and identifiable... behavior") is about the STYLE differing, not
  about response length, so a tag + a couple of style-appropriate sentences
  keeps the test close to the case's spirit while still asserting exactly:
  - Base version instructions: `"Start every response with the exact tag
    [BASE-STYLE] followed by a colon, then answer formally."`
  - v2 (`casual`) instructions: `"Start every response with the exact tag
    [CASUAL-STYLE] followed by a colon, then answer in a casual tone with
    emojis."`
  - v3 (`technical`) instructions: `"Start every response with the exact tag
    [TECH-STYLE] followed by a colon, then answer with technical details and a
    short code example."`
- **Agent name — 32-char hard cap, ALREADY-DOCUMENTED constraint (ELITEA-1900,
  confirmed live 2026-08-07, `agent-name-input`'s native `maxlength="32"`,
  silent truncation, no validation error).** The case's literal example
  `version-behavior-agent` plus a distinguishing prefix easily exceeds 32
  chars (confirmed live this run: `elitea-2610-version-behavior-agent`, 35
  chars, silently truncated by the browser to `elitea-2610-version-behavior-age`
  — confirmed via `el.value`/`el.maxLength` this run: `maxLength=32`, stored
  value is exactly 32 chars, `elitea-2610-version-behavior-age`). Use a name
  that fits within 32 chars, or accept/assert the truncated form — do not treat
  the truncation itself as a defect (already tracked, not this case's finding).
- **Test prompt**: `"Explain what an API is"` — used as-authored, works fine
  (no case-text drift on this field).
- No `reuse-existing`/shared fixture applies — fresh-state flow (1 skill with 3
  versions + 1 agent, both created and torn down within the run).

## Test Steps

### Part A — Specific version behaviour is used

1. Create Skill `elitea-2610-response-style` via `/skills/create`
   (`skill-name-input-field`/`skill-description-input-field`/
   `skill-instructions-editor-content`, `press_sequentially` not `fill` — CodeMirror)
   with the BASE-STYLE instructions above. Click Save (`skill-save-button`).
   - **Verify**: navigates to `/skills/all/{id}` (skill id `1812` in this run,
     version id `1962`). No nav-blocker dialog fired on Save this run (differs
     from ELITEA-1789's original run, which DID see one — not a defect, the
     dialog is conditional on unsaved-changes state, both are legitimate live
     behaviours; don't hard-assert its presence).
2. Save As Version `casual` with the CASUAL-STYLE instructions — select-all
   (`Control+A`) in the instructions editor, `press_sequentially` the new text,
   click `skill-save-as-version-button`, name it `casual` in the dialog
   (`skill-create-version-name-input-field` → `skill-create-version-save-button`).
   - **Verify**: `PATCH /api/v2/elitea_core/skill/prompt_lib/399/1812` →
     `201 Created`; toast `Version "casual" created`; URL gains the new version
     segment (`/skills/all/1812/1963`).
3. Save As Version `technical` the same way, with the TECH-STYLE instructions.
   - **Verify**: same pattern, `201 Created`, URL `/skills/all/1812/1964`.
4. Create Agent `elitea-2610-version-behavior-agent` via `/agents/create`
   (`agent-name-input`/`agent-description-input`/`agent-instructions-input`,
   generic non-asserted instructions: `"You are a helpful assistant. Answer the
   user's question directly."`). Click Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{id}?destTab=configuration...`
     (agent id `9227` in this run). Name silently truncated to 32 chars (see
     Test Data note) — not a defect.
5. On the agent detail page, expand/confirm the Skills section, click
   `agent-add-skill-button`, select the skill from the popper by name.
   - **Verify**: `PATCH .../skill/prompt_lib/399/1812` → `201 Created`; Skills
     counter "0/5" → "1/5"; a card renders showing the skill name + a version
     selector currently reading `"base"` (the freshly-attached default).
6. Open the attached skill's version selector
   (`skill-version-selector-trigger-{skill_id}`, e.g.
   `skill-version-selector-trigger-1812` — click via a REAL click, not an
   accessibility-tree/`ref=`-resolved one; see ELITEA-1789's Known Defect #46,
   still present/reconfirmed live this run: the trigger has no ARIA role,
   `tabIndex=-1`, no accessible name). Click the `casual` menu item
   (`skill-version-option-casual`).
   - **Verify — NEW ground vs ELITEA-1789 (that AFS's skill only ever had ONE
     version, so an actual non-base SELECTION was never exercised)**: clicking
     a non-base version option fires `PATCH .../skill/prompt_lib/399/1812` →
     `201 Created`; the trigger's text updates to `"casual"` immediately, no
     agent-level Save needed (consistent with attach also being auto-saved).
7. Open the embedded chat (already on this page — `AgentDetailPage`'s own
   embedded chat panel, NOT a separate "open chat" navigation: the case's step
   7 "Open chat with the agent" is satisfied by the chat panel that is already
   present on the agent detail page after Save in step 4). Send the test
   prompt `"Explain what an API is"` (`chat-message-input` +
   `chat-send-button`).
   - **Verify**: message sends; response streams (`"Thought for N secs"` trace
     visible, then the answer body).
8. Verify the response uses the CASUAL version's behaviour (case steps 9-10:
   "uses casual tone with emojis" / "NOT formal").
   - **Verify — CONFIRMED LIVE, deterministic**: response text starts with
     `"[CASUAL-STYLE]:"` and contains at least one emoji (🤝 in this run,
     several more further in). `chat-answer-tool-chip` on the last message
     reads exactly `"Skill: elitea-2610-response-style"` — confirms the
     invocation was AUTONOMOUS (the case's `feat:autonomous-invocation` tag):
     the test prompt never used a `~mention`, the model decided on its own to
     `load_skill` (same autonomous-decision mechanism documented in
     ELITEA-1735/2607/2609), and it used the CURRENTLY-SELECTED (`casual`)
     version's instructions, not `base`'s.

### Part B — Changing version updates behaviour immediately

9. Go back to (i.e., stay on — no navigation needed) the agent detail page's
   Skills section. Open the version selector again, click
   `skill-version-option-technical`.
   - **Verify**: trigger text updates to `"technical"`; `201 Created` PATCH
     fires, same as step 6.
10. Send the SAME prompt again — **in the SAME chat conversation, no page
    reload, no new chat, no explicit agent-level Save** (case step 14 allows
    "or start new chat"; this run deliberately used the STRONGER form — same
    conversation — to prove the update is immediate at the next turn, not
    merely "after a fresh session").
    - **Verify — CONFIRMED LIVE**: the very next AI turn (2nd message in the
      same conversation) returns a response starting `"[TECH-STYLE]:"`,
      containing a fenced code block (a Python `requests` example) and
      "Key Components" bullet structure — technical-version behaviour, NOT a
      repeat of the casual-version response. `chat-answer-tool-chip` again
      reads `"Skill: elitea-2610-response-style"`.

### Part C — Revert to base version

11. Open the version selector once more, click `skill-version-option-base`.
    - **Verify**: trigger text updates back to `"base"`.
12. Send the SAME prompt a third time, in the same conversation.
    - **Verify — CONFIRMED LIVE**: 3rd-turn response starts
      `"[BASE-STYLE]:"`, formal register ("a formal specification that
      defines how software components should communicate..."), no emoji.
      `chat-answer-tool-chip` again reads `"Skill: elitea-2610-response-style"`.

**Result: 3/3 version switches (casual → technical → base) reflected correctly
on the very next chat turn, in the SAME conversation, with zero page reloads
and zero explicit agent-level Save actions. Zero console errors across all 12
steps (`browser_console_messages` level=error, 0 hits).** No functional
product defect found — the case's own Pass criteria are met exactly as
authored, and more strongly than the case's own text requires (case step 14
allows "start new chat"; this run proved it works mid-conversation, which is
the harder bar).

## Handles Reference

PROVENANCE verified fresh this session: `cd EliteaUI && git fetch origin`
(ran 2026-08-12), then `git grep` against `origin/main` and
`origin/automation/testids`.

```
$ git fetch origin
$ for t in agent-add-skill-button skill-version-selector-trigger skill-version-selector-menu skill-version-option chat-answer-tool-chip skill-controls-menu-button skill-delete-menu-item; do
    m=$(git grep -- "$t" origin/main -- '*.jsx' | grep -qiE '(data-testid|testid[[:space:]]*[:=])' && echo YES || echo no)
    t2=$(git grep -- "$t" origin/automation/testids -- '*.jsx' | grep -qiE '(data-testid|testid[[:space:]]*[:=])' && echo YES || echo no)
    printf "%-32s main:%-3s testids:%s\n" "$t" "$m" "$t2"
  done
agent-add-skill-button           main:YES testids:YES
skill-version-selector-trigger   main:YES testids:YES
skill-version-selector-menu      main:YES testids:YES
skill-version-option             main:YES testids:YES
chat-answer-tool-chip            main:YES testids:YES
skill-controls-menu-button       main:YES testids:YES
skill-delete-menu-item           main:YES testids:YES
```

All testids this case's OWN steps (1-12) touch are `on-main ✓` (the ELITEA-1789
rework's version-selector testids have since been promoted to `main`, unlike
that AFS's own PROVENANCE table which recorded them as
`on-automation/testids only`). **Zero new `add-data-testid` work required for
this case.**

`agent-actions-menu-button` / `delete-agent-menuitem` (used only in this
analyst run's OWN cleanup, not a case step) are **dynamically composed**
testids (`DotMenu.jsx`: `data-testid={testId ? `${testId}-menuitem` : undefined}`)
— a literal-substring `git grep` produces a false "not found" for these (the
known runtime-composed-testid blind spot documented in
`.agents/workflow.md` § Closure record). Confirmed live this session (clicked
both successfully via `browser_evaluate` + `querySelector`) and already
exercised by the merged `test_skill_agent_version_selector.py` cleanup —
no gap.

| Element | testid | PROVENANCE | Notes |
|---|---|---|---|
| Skill Name field | `skill-name-input-field` | on-main ✓ | kebab-case validation |
| Skill Description field | `skill-description-input-field` | on-main ✓ | |
| Skill Instructions editor | `skill-instructions-editor-content` | on-main ✓ | CodeMirror; `press_sequentially` |
| Skill Save button | `skill-save-button` | on-main ✓ | |
| Skill "Save As Version" button | `skill-save-as-version-button` | on-main ✓ | |
| "Create version" dialog Name field | `skill-create-version-name-input-field` | on-main ✓ | |
| "Create version" dialog Save button | `skill-create-version-save-button` | on-main ✓ | |
| Agent Name field | `agent-name-input` | on-main ✓ | 32-char maxlength, ELITEA-1900 |
| Agent Description field | `agent-description-input` | on-main ✓ | |
| Agent Instructions field | `agent-instructions-input` | on-main ✓ | |
| Agent Save button | `agent-save-button` | on-main ✓ | create form |
| Agent add-skill button | `agent-add-skill-button` | on-main ✓ | **PROMOTED since ELITEA-1789** (that AFS recorded it as `automation/testids`-only) |
| Attached-skill card scope | `skill-card-{skill_id}` | on-main ✓ | dynamic, param = skill's own numeric id |
| **Skill version-selector trigger** | `skill-version-selector-trigger-{skill_id}` | on-main ✓ | **PROMOTED since ELITEA-1789**. Real click required — accessibility-ref click still silently no-ops (issue #46 a11y half unchanged, reconfirmed live this run) |
| **Skill "Versions" menu container** | `skill-version-selector-menu-{skill_id}` | on-main ✓ | portals to `document.body`, not a DOM descendant of the card — scope by `skill_id`, not ancestry |
| **Skill version menu item — SELECTING it (NEW ground this case)** | `skill-version-option-{version_name}` | on-main ✓ | ELITEA-1789 only ever confirmed this testid existed/was clickable with a single `base` option present; this case is the first to confirm CLICKING a non-base option (`casual`/`technical`) actually re-PATCHes the attachment and changes chat behaviour |
| Chat message input (embedded, agent detail page) | `chat-message-input` | on-main ✓ | already `AgentDetailPage.chat_message_input` |
| Chat send button | `chat-send-button` | on-main ✓ | already `AgentDetailPage.chat_send_button` |
| Chat message item (per-turn container) | `chat-message-item` | on-main ✓ | already `AgentDetailPage._embedded_chat_messages()` |
| Autonomous-invocation chip | `chat-answer-tool-chip` | on-main ✓ | reads `"Skill: {skill_name}"`; already used by ELITEA-1735/2607/2608/2609 for the SUBAGENT-nested case — **this case needs the TOP-LEVEL (non-nested) reader**, see Automation Hints |
| Last AI response body (exact prefix assertion) | `skill_test_last_response` field (`AgentDetailPage.get_last_chat_response_text()`) | on-main ✓ | existing method already handles the "last message uses a different testid than earlier messages" quirk (ELITEA-1735 finding) |

## Expected Results
Matches the case's Pass criteria exactly, live-verified end-to-end, 3/3:
- The specific attached skill version's behaviour is used during invocation
  (casual → `[CASUAL-STYLE]` + emoji; confirmed).
- Changing the attached version immediately updates the agent's behaviour on
  the VERY NEXT chat turn — no agent recreation, no explicit Save, no page
  reload, and (stronger than the case text requires) no new chat needed either
  (confirmed casual→technical mid-conversation).
- All three version changes (casual → technical → base) work correctly
  (confirmed).
- Version behaviour is distinct and identifiable (deterministic `[X-STYLE]:`
  tag + register/structure differences, confirmed for all 3).
- Invocation is autonomous both times (case tag `feat:autonomous-invocation`;
  `chat-answer-tool-chip` fired on every turn without any `~mention`).

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Steps 1-3: Create skill + 2 named versions | Skill/versions created | Test Steps 1-3 | `201 Created` × 3, toast text, URL version-segment changes | covered |
| Step 4: Create agent | Agent created | Test Step 4 | navigation to `/agents/all/{id}` | covered |
| Step 5: Attach skill with `casual` version specifically selected | Skill attached with v2 (casual) version | Test Steps 5-6 | attach via popper (defaults to `base`), then version selector switched to `casual` — **case text implies selecting the version AT attach time; live product attaches at `base` first and version-switching is a separate post-attach action** (case-text drift/clarification, not a defect — the end state after step 6 is identical: skill attached, `casual` selected) | covered — clarification noted below |
| Step 6: Save the agent | Agent saved | N/A | attach + version-switch are both auto-saved via API (`201 Created` PATCHes); no literal agent-level Save action exists for these, same pattern as ELITEA-1789/1735 | covered — case-text drift (reverse-masking), consistent with prior AFS on this exact area |
| Step 7: Open chat with the agent | Chat loads | Test Step 7 | embedded chat panel already present on the agent detail page | covered — case-text drift: no separate "open chat" navigation exists/is-needed on this page |
| Step 8: Send test prompt | Message sent | Test Step 7 | `chat-message-input`/`chat-send-button` | covered |
| Steps 9-10: Response uses casual tone/emojis, NOT formal | condition holds | Test Step 8 | `[CASUAL-STYLE]:` prefix + emoji present, `[BASE-STYLE]` absent | covered |
| Step 11: Go back to agent settings | Agent settings page loads | N/A | already on the agent detail page throughout — no navigation needed (Skills section is part of the same page as chat) | covered — case-text drift (case implies a page transition; live product co-locates settings + chat on one page) |
| Step 12: Change version to `technical` | Version selection updated | Test Step 9 | trigger text updates, `201 Created` | covered |
| Step 13: Save the agent | Agent saved | N/A | same as step 6 — auto-saved, nothing to click | covered — case-text drift |
| Step 14: Return to chat (or start new chat) | Chat is ready | Test Step 10 | same conversation, no reload/new-chat needed (stronger than case requires) | covered |
| Step 15: Send same prompt | Message sent | Test Step 10 | | covered |
| Steps 16-17: Response uses technical tone/code, NOT casual | condition holds | Test Step 10 | `[TECH-STYLE]:` prefix + code block present, `[CASUAL-STYLE]` absent | covered |
| Steps 18-21: Revert to base, save, send, verify formal tone | condition holds | Test Steps 11-12 | `[BASE-STYLE]:` prefix, formal register, no emoji | covered |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| `PATCH .../skill/prompt_lib/{project}/{skill_id}` → `201 Created` on version-selection click | Confirms version-selection (not just attach) is an immediate API-level auto-save — material wait strategy for automation (wait on this PATCH, not a fixed sleep, before sending the next chat message) |
| `chat-answer-tool-chip` text on every one of the 3 chat turns | Proves invocation was AUTONOMOUS every time (no `~mention` ever used) — directly substantiates the case's own `feat:autonomous-invocation` tag, which the case's numbered steps don't explicitly test for |
| Zero console errors across all 12 steps | Side-channel discipline; rules out a silent JS failure masking as a passing-looking response |
| Mid-conversation version switch (no new chat between technical and casual turns) | Stronger proof than the case's own "or start new chat" allowance — shows the update takes effect at the granularity of "next send", not merely "next session" |
| Deterministic marker-tag instructions instead of the case's literal subjective tone descriptions | Load-bearing automation-reliability finding: an assertion on "casual tone" is not scriptable reliably; a `[TAG]:` prefix is. Implementer MUST use marker-tag instructions, not literally re-type the case's "formal"/"casual with emojis"/"technical" prose as the skill's own instructions verbatim |

## Known Defects
None found. Confirmed live 100% (3/3 version switches, 3/3 correct chat
behaviour, 0 console errors). Issue #46 (version-selector trigger not
keyboard-accessible / `tabIndex=-1`, from ELITEA-1789) is reconfirmed still
present but is pre-existing, already tracked, and non-blocking for this case
(this case's own steps use a real click, not keyboard navigation, matching
ELITEA-1789's own automation guidance).

## Cleanup
Two entities created per run: the Skill (with 3 versions) and the Agent that
attaches it. Both deleted live in this run, mirroring ELITEA-1789/1735's
established pattern:
1. **Delete the Agent first**: overflow menu (`agent-actions-menu-button`,
   dynamically-composed testid — see Handles Reference note) → "AGENT" group →
   "Delete agent" (`delete-agent-menuitem`) → type-to-confirm dialog
   (`delete-confirm-name-input` inner `#name` field, must match the
   TRUNCATED 32-char name) → `delete-confirm-button`. Verified: `DELETE
   /api/v2/elitea_core/application/prompt_lib/399/9227` → redirected away
   cleanly (to the last-viewed skill's page in this run — don't assert a fixed
   post-delete URL, same finding as ELITEA-1789).
2. **Then delete the Skill** (removes all 3 versions in one call): overflow
   menu (`skill-controls-menu-button`) → "SKILL" group → "Delete skill"
   (`skill-delete-menu-item`) → same type-to-confirm dialog → `delete-confirm-button`.
   Verified: `DELETE /api/v2/elitea_core/skill/prompt_lib/399/1812` → redirect
   to `/skills/all`.
3. **For automated cleanup, prefer the existing API fixtures**
   (`agent_api.delete_agent(agent_id)` / `skill_api.delete_skill(skill_id)`,
   same as ELITEA-1789/1735/2440) in a `finally` block — deleting the skill
   removes all 3 versions in one call, no separate per-version cleanup needed.

## Blocked Steps
None — case executed end-to-end live, all 12 steps (3 parts), including the
harder mid-conversation variant of the version-switch verification.

## Implementer Amendments (ELITEA-2610, this branch)

Two live findings during automation that the AFS's Test Data section didn't
anticipate — both technique (the **how**), not scope:

1. **Autonomous invocation is NOT guaranteed by attachment alone — the skill's
   own `description` field and the agent's own `instructions` field both need
   to nudge the model toward using it.** First implementation attempt used a
   generic skill description ("... — version selection behaviour") and agent
   instructions "Answer the user's question directly" (which actively
   discourages tool use) — the model answered the prompt directly with NO
   skill invocation at all (no `chat-answer-tool-chip`, generic unstyled
   response). Fixed per the established pattern already in
   `test_skill_agent_interaction.py` (ELITEA-2607/2609): skill description
   `"Use this skill for EVERY user question, no matter the topic."` + agent
   instructions `"You are a helpful assistant. Use your skills when
   appropriate."` — reliable invocation on all 3 turns after this change.
2. **A literal `"```"` (fenced code block) does NOT survive
   `get_last_chat_response_text()`'s `text_content()` extraction** — the
   markdown renderer converts it to a `<pre><code>` DOM structure, so the
   backtick characters themselves are gone from the extracted text (same
   class of issue the marker-tag approach already solved for tone). Fixed by
   extending the TECH-STYLE instructions to require a literal
   `[CODE-EXAMPLE]` tag immediately before the code snippet — a marker that
   DOES survive text extraction, same mechanism as `[BASE-STYLE]`/
   `[CASUAL-STYLE]`/`[TECH-STYLE]`. The test asserts on `"[CODE-EXAMPLE]" in
   response_technical` instead of `"```" in response_technical`.

New page-object methods added to `AgentDetailPage` (automation/pages/agent_detail_page.py):
- `select_skill_version(skill_name, version_name, timeout)` — opens the
  Versions menu (reusing `open_skill_version_selector`) and clicks the
  target option via the pre-existing `SKILL_VERSION_OPTION_SELECTOR`
  template constant (defined in the ELITEA-1789 rework, never previously
  called from a public method), then polls the trigger's text for the new
  value (mirrors `attach_skill()`'s counter-polling pattern).
- `get_last_message_tool_chip_texts(timeout)` — top-level (non-nested)
  counterpart to `get_nested_agent_tool_chip_texts()`, scoped to the last
  `chat-message-item`'s own `chat-answer-tool-chip` elements.

## Automation Hints
- Framework: Playwright + pytest. Likely home:
  `automation/tests/ui/skills/test_skill_agent_version_selection_behavior.py`
  (new file — no existing test combines agent-attach version SELECTION with a
  live chat-response behavioural assertion).
- **New page-object method needed** on `AgentDetailPage` — clicking a specific
  (non-base) version option is not yet wrapped. Existing methods
  (`open_skill_version_selector`, `get_versions_menu_item_names`,
  `close_versions_menu`) only open/read/close the menu; add e.g.
  `select_skill_version(skill_name: str, version_name: str)` that opens the
  trigger (reusing `open_skill_version_selector`'s skill_id resolution) and
  clicks `SKILL_VERSION_OPTION_SELECTOR.format(version_name)` (the
  class-level template constant already defined at line 259 — just never
  called from a public method). The testid itself is NOT a gap (see Handles
  Reference) — only the Python-side wrapper method is missing.
- **New/extended chip-reader needed**: `get_nested_agent_tool_chip_texts()`
  only reads chips SCOPED to a nested sub-agent accordion (ELITEA-2608
  use-case). This case needs a TOP-LEVEL reader — e.g.
  `get_last_message_tool_chip_texts()` scoped to
  `_embedded_chat_messages().last.locator(CHAT_ANSWER_TOOL_CHIP_SELECTOR)` —
  to assert `["Skill: elitea-2610-response-style"]` on each of the 3 turns
  without picking up a nested sub-agent's own chip (not applicable to this
  case's topology — no subagents involved — but keeping the method scoped to
  the last message avoids picking up an EARLIER turn's chip by accident once
  there are 3 messages in one conversation).
- `send_chat_message()` / `wait_for_chat_response()` / `get_last_chat_response_text()`
  (all pre-existing on `AgentDetailPage`) cover steps 7-8/10/12 as-is — no new
  work needed for the send/wait/read cycle itself.
- Wait strategy after clicking a version option: wait on the
  `PATCH .../skill/prompt_lib/{project}/{skill_id}` response (or poll the
  trigger's text for the expected new value) — NOT a fixed sleep — before
  sending the next chat message, mirroring `attach_skill()`'s existing
  counter-polling pattern.
- Cleanup: `agent_api.delete_agent(agent_id)` then `skill_api.delete_skill(skill_id)`
  in a `finally`, mirroring ELITEA-1789/1735/2440.
