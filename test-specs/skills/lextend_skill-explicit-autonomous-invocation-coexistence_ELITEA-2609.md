# Test Case: Skill Explicit and Autonomous Invocation Coexistence

## Metadata
- **TMS ID**: ELITEA-2609
- **Source case**: `.agents/automation/skills-remaining-w4/cases/ELITEA-2609.md`
  (snapshot; frontmatter `status: draft`, `execution_type: manual`, tags
  `[automated:UI:regression, feat:skills, feat:autonomous-invocation,
  feat:backward-compatibility]` — matches the intake selector, no case-gate
  exclusion applies)
- **Linked Story**: none
- **Priority**: l3 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI dev server on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399),
  model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing

## Extension target

**Covering spec/test file**:
`automation/tests/ui/skills/test_skill_agent_interaction.py` (class
`TestInteractWithSkillsFromAgent`), which lives on this batch's trunk
(`tests/batch-skills-remaining-w4`, commits `ab9888bf`/`018b254e`/`c83ca52a`,
not yet merged to `origin/automation/base` — qualifies per the merged-target
rule) and covers BOTH:

- `test_interact_with_skills_from_agent` (ELITEA-1735) — V1 explicit
  `~mention` invocation (its own Steps 9-10, `:296-333`) and V2 autonomous
  invocation (Steps 7-8, `:277-295`), **each demonstrated separately, on
  separate messages**.
- `test_skill_autonomous_invocation_thought_process_and_security`
  (ELITEA-2607 extension) — autonomous invocation's thought-process
  visibility (`"Skill: {name}"` chip) and the unattached-skill security
  invariant.

### Behavioural-overlap argument (what's already proven)

The merged-to-trunk suite already independently proves, on this exact chat
surface:

1. **Explicit `~skill-name` invocation still works** (Part A of this case) —
   `test_interact_with_skills_from_agent` Steps 9-10 send
   `~{SKILL_1_NAME} {neutral text}` and `~{SKILL_2_NAME} {neutral text}` (no
   context-trigger match in the appended text — `NEUTRAL_TEXT_FOR_SKILL` is
   deliberately trigger-neutral) and assert the skill's transform. This is
   the case's Part A steps 4-6 verbatim: backward-compatible explicit
   invocation, response reflects the mentioned skill.
2. **Thought-process visibility of a single invocation** (Part A step 6 /
   Part B step 9's "invoked exactly once" half) —
   `test_skill_autonomous_invocation_thought_process_and_security` Step
   5-6 asserts exactly one `chat-answer-tool-chip` reading
   `"Skill: {name}"` for an AUTONOMOUS (non-`~mention`) invocation. The
   mechanism (chip rendering, one chip per invoked skill) is proven; only
   the EXPLICIT+AUTONOMOUS-simultaneous topology is untested.
3. **Both invocation methods produce correct, equivalent-quality output**
   (Part C) — the explicit-invocation steps (1735 Steps 9-10) and the
   autonomous-invocation steps (1735 Steps 7-8 / 2607 Steps 5-6) both
   assert the skill's own deterministic transform is applied correctly.
   Since skill instructions execution is identical regardless of the
   invocation TRIGGER (mention parsing vs. LLM-side context matching
   feed into the same execution path — same instructions payload, same
   `ActionView.jsx` chip rendering), no new mechanism is exercised by
   proving this a third time; the case's own Part C steps 11-14 are
   satisfied by 1-2 above without a dedicated new test.

This is Rule-6 partial overlap: skill creation, agent creation, single/dual
skill attachment, explicit-alone invocation, and autonomous-alone invocation
(with its thought-process chip) are all already proven live and merged onto
the trunk. A fresh spec reimplementing "create skill(s), attach, invoke
explicitly, invoke autonomously" from scratch would duplicate that setup and
those steps almost verbatim.

### Gap assertions (what the covering spec does NOT cover — confirmed live this run)

**Gap — No double-injection when explicit `~mention` AND context-match
co-occur on the SAME message (Part B, the case's actual differentiator).**
Neither covering test ever sends a message that is BOTH an explicit
`~skill-name` mention AND whose appended text also matches that same
skill's own autonomous-trigger description — every existing message is one
or the other, never both at once. This is exactly Part B's scenario (case
steps 7-10) and it is the only scenario in the whole case that isn't a
subset of an already-independently-proven invocation mode.

**Confirmed live this run.** Created a fresh skill
(`elitea-2609-explicit-autonomous`, description `"Use this skill ONLY when
the user explicitly asks to format text as markdown."`, instructions
`"CRITICAL: You MUST convert ALL letters in your response to UPPER CASE. Do
not explain, just output the transformed text in UPPER CASE."` — a
deterministic transform whose repetition would be visually obvious: a
double-invoked/double-injected skill applying "convert to uppercase" twice
is indistinguishable in TEXT from applying it once, so the transform text
alone cannot prove non-duplication — the THOUGHT-PROCESS CHIP COUNT is the
load-bearing assertion here, not the response text), attached it to a fresh
agent (`elitea-2609-coexistence-agent`, agent id `9221`, skill id `1804`),
then sent, with NO prior chat history:

```
~elitea-2609-explicit-autonomous Format as markdown: Title, item1, item2, item3
```

— i.e. an explicit `~mention` of the skill, immediately followed by prompt
text that ALSO independently matches the skill's own description trigger
("asks to format text as markdown"). Result:

- Exactly **ONE** `chat-answer-tool-chip` reading
  `"Skill: elitea-2609-explicit-autonomous"` inside the
  `chat-answer-thought-accordion` (`"Thought for 1 sec"`) — not two, not
  zero.
- Response body: a single, clean, non-duplicated markdown render — heading
  `TITLE` + a 3-item list `ITEM1` / `ITEM2` / `ITEM3` — i.e. the skill's
  UPPER-CASE transform applied exactly once (a double-injection defect
  would most plausibly surface as either a duplicated/concatenated output
  block or a garbled response; neither occurred).
- Zero console errors on the interaction (`browser_console_messages`,
  level `error`: 0 messages).

No product defect — the security/idempotency invariant holds: explicit
mention and context-match, when they coincide, do not stack into two
invocations.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Attached skill name: kebab-case, e.g. `elitea-2609-explicit-autonomous`.
- Attached skill description (autonomous-invocation trigger condition):
  `"Use this skill ONLY when the user explicitly asks to format text as
  markdown."`
- Attached skill instructions: a deterministic, easily-asserted transform
  that is ALSO cheap to visually detect if duplicated at the STRUCTURE
  level (not just the text level) — this run used an UPPER-CASE transform
  on a markdown-structured response (heading + list), so a double-injection
  defect would show as a duplicated heading/list block, not merely
  "still uppercase." e.g. `"CRITICAL: You MUST convert ALL letters in your
  response to UPPER CASE. Do not explain, just output the transformed text
  in UPPER CASE."`
- Agent name: e.g. `elitea-2609-coexistence-agent`; description + a short
  generic instructions string (agent instructions do not need to mention
  skills — same precedent as ELITEA-1735/2607's Test Data).
- Combined prompt (explicit mention + context match, same message): e.g.
  `"~{SKILL_NAME} Format as markdown: Title, item1, item2, item3"` — the
  appended text after the mention chip must independently satisfy the
  skill's own description trigger, not just be neutral text (neutral text
  after a mention would not exercise Part B at all — it would just be a
  repeat of the already-covered "explicit-alone" case).

No `reuse-existing` fixture applies — same fresh-state-per-test reasoning as
ELITEA-1735/2607: 1 skill + 1 agent, created and torn down within the test.

## Test Steps

1. Create the skill via `${BASE_URL}/skills/create`: fill Name
   (`skill-name-input-field`), Description (`skill-description-input-field`),
   Instructions (`skill-instructions-editor-content`, CodeMirror — use
   `press_sequentially`, not `fill`). Click Save (`skill-save-button`).
   - **Verify**: URL settles on `/skills/all/{id}`; note the skill's ID.
2. Create an Agent via `${BASE_URL}/agents/create`: fill Name
   (`agent-name-input`), Description (`agent-description-input`),
   Instructions (`agent-instructions-input`). Click Save
   (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`.
3. On the agent detail page, expand the Skills accordion, click the
   add-skill button (`agent-add-skill-button`). Attach the skill from the
   popper (menuitem role, accessible name = skill name).
   - **Verify**: Skills counter reads `"1/5 skills added."`.
4. In the agent's embedded chat panel (`chat-message-input`), type `~`,
   wait for the mention popper (`skill-mention-list`), click the row
   scoped by `SKILL_MENTION_ITEM_SELECTOR.format(skill_name)`, then append
   (via `press_sequentially`, never `fill` — would destroy the mention
   chip) a prompt whose text ALSO matches the skill's own description
   trigger. Send.
   - **Verify (Gap — Part B)**: exactly ONE `chat-answer-tool-chip` reading
     `"Skill: {skill_name}"` is present inside the last message's
     `chat-answer-thought-accordion` (`CHAT_ANSWER_TOOL_CHIP_SELECTOR`
     scoped to `get_outer_thought_accordion()`, asserted via `.count() ==
     1`, not merely "present" — the count IS the double-injection
     assertion). Response body reflects the skill's transform exactly once
     (no duplicated/concatenated block).

## Expected Results

1. Explicit `~skill-name` invocation continues to work (proven by the
   covering spec's existing Steps 9-10 — reused, not re-implemented).
2. When a message is BOTH an explicit `~mention` and independently context-
   matching, the skill is invoked exactly ONCE — the thought-process chip
   count is 1, not 2 (this AFS's own Gap, new assertion).
3. The response is a single, clean, non-duplicated transformed output.
4. Both explicit and autonomous invocation independently produce correct,
   equivalent-quality output (proven by the covering spec's existing
   Steps 7-10 across both test methods — reused, not re-implemented).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Part A steps 1-6 (explicit `~mention` still works, visible in thought process) | Response formatted, `"Skill: {name}"` chip visible | `test_interact_with_skills_from_agent` Steps 9-10 (explicit-alone, response-text) + `test_skill_autonomous_invocation_thought_process_and_security` Steps 5-6 (chip-rendering mechanism, proven for the autonomous case, same DOM/testid path for explicit) | covering specs (both already merged onto trunk) | already-proven — no new test code needed |
| Part B steps 7-10 (explicit + context-match together ⇒ exactly ONE invocation, clean output) | Exactly 1 skill chip, single clean output | New Extension Step 4 — **the Gap**, confirmed live this run | new test | gap — implementer adds |
| Part C steps 11-14 (both methods produce equivalent, correct results) | Both explicit and autonomous work correctly | `test_interact_with_skills_from_agent` Steps 7-10 (both modes independently proven correct on the SAME skill mechanism) | covering spec | already-proven — the case only requires "equivalent in quality," not a byte-identical diff; both modes feed the same skill-execution path, confirmed by the existing per-mode assertions |

### Axis 2 — Analyst additions

| Additional observable asserted | Reason |
|---|---|
| Chip **count** (`.count() == 1`), not just chip presence | "No double-injection" is a COUNT claim, not a presence claim — a test asserting only "a chip exists" would pass even if the skill were invoked twice (two chips would still satisfy "a chip is present"). The count is the assertion that actually falsifies double-injection. |
| Response STRUCTURE (heading + list, not just text case) rather than a plain prose transform | A duplicated/malformed output from double-injection is far more visually and structurally distinctive on a markdown-formatted response (a repeated heading/list block) than on a flat prose transform, where "still all-uppercase" is compatible with either 1 or 2 invocations. |
| Console-error check (`browser_console_messages`, level `error`) on the combined-invocation interaction | Silent errors are the ones that ship — no assertion in the covering specs checks the console specifically for this combined-trigger path. |

## Known Defects Found During Exploration

None. The coexistence and no-double-injection invariants both hold — no
product defect, no case-text drift.

## Blocked Steps

None.

## Concrete Handles (discovered during exploration — all pre-existing, no new
testid needed)

| Element | Handle | Provenance |
|---|---|---|
| Skill name input | `[data-testid="skill-name-input-field"]` | on-main ✓ (reused from ELITEA-1735/2607 lineage) |
| Skill description input | `[data-testid="skill-description-input-field"]` | on-main ✓ |
| Skill instructions editor | `[data-testid="skill-instructions-editor-content"]` | on-main ✓ |
| Skill save button | `[data-testid="skill-save-button"]` | on-main ✓ |
| Agent name/description/instructions inputs | `agent-name-input` / `agent-description-input` / `agent-instructions-input` | on-main ✓ |
| Agent save button | `[data-testid="agent-save-button"]` | on-main ✓ |
| Add-skill button (agent detail, Skills section) | `[data-testid="agent-add-skill-button"]` | on-main ✓ — confirmed live this run |
| Chat message input | `[data-testid="chat-message-input"]` | on-main ✓ |
| Mention popper container | `[data-testid="skill-mention-list"]` | on-main ✓ |
| Mention popper row (dynamic) | `SKILL_MENTION_ITEM_SELECTOR` = `[data-testid="skill-mention-item-{}"]` | on-main ✓ — `AgentDetailPage.SKILL_MENTION_ITEM_SELECTOR` class constant |
| Send button | `[data-testid="chat-send-button"]` | on-main ✓ |
| Thought accordion (outer, per-message) | `[data-testid="chat-answer-thought-accordion"]` | on-main ✓ — `AgentDetailPage.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR` (`automation/pages/agent_detail_page.py:189`), returned as a Locator by `get_outer_thought_accordion()` |
| Tool/skill chip | `[data-testid="chat-answer-tool-chip"]` | on-main ✓ — `CHAT_ANSWER_TOOL_CHIP_SELECTOR` (`automation/pages/agent_detail_page.py:191`); text is `"Skill: {name}"` when the invoked entity is a skill (`ActionView.jsx:196-217`) |

## Network Behavior

- Skill attach: `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}`
  → `201 Created` (same pattern as ELITEA-1735/2607's AFS; not
  independently re-traced this run).
- Predict/chat traffic is WebSocket-based (not independently re-traced this
  run — same mechanism the covering specs and every other chat test already
  rely on; `.agents/testing.md` § Hooks & fixtures, ~2s+ latency, condition
  waits only).
- Skill/agent cleanup via direct API calls — `AgentAPI.delete_agent(9221)`
  and `SkillAPI.delete_skill(1804)`, both successful (no HTTP error raised).

## Automation Hints

- Reuse `TestInteractWithSkillsFromAgent`'s `_create_skill()` helper
  (`test_skill_agent_interaction.py:75-98`) — it already returns the
  numeric skill ID and handles the CodeMirror `press_sequentially` gotcha.
- Reuse `AgentDetailPage.send_chat_message_with_mention()` for the mention
  half, but note it does NOT append arbitrary trailing context-matching
  text by design in the covering test's existing calls — this new
  assertion needs the appended prompt text to be chosen so it independently
  matches the skill's own description trigger (unlike
  `NEUTRAL_TEXT_FOR_SKILL`, which is deliberately non-triggering). Either
  call `send_chat_message_with_mention(skill_name, context_matching_text)`
  directly (the method already supports arbitrary trailing text — it was
  only ever exercised with neutral text before), or compose the same three
  calls (`type_tilde_in_chat()` → click the mention row → append text
  + send) inline if finer control over the intermediate state is wanted.
- Assert chip count via
  `get_outer_thought_accordion().locator(AgentDetailPage.CHAT_ANSWER_TOOL_CHIP_SELECTOR)`
  → `expect(locator).to_have_count(1)`, filtered/asserted by text
  `f"Skill: {SKILL_NAME}"` (via `.filter(has_text=...)` or a
  `to_contain_text` check on `.first`) to also rule out a hypothetical
  double-count coming from an unrelated chip (e.g. a toolkit chip on the
  same message) rather than a genuine duplicate skill invocation.
- Same `@pytest.mark.flaky(reruns=3, reruns_delay=5)` marker as the
  covering tests — LLM response timing/content has the same inherent
  variability this project already accepts for skill-invocation assertions.
- This test can live as a third method on `TestInteractWithSkillsFromAgent`
  in `test_skill_agent_interaction.py` (implementer's call per
  file-size/clarity, same pattern as the ELITEA-2607 extension itself was
  added as a sibling method rather than a new file).
