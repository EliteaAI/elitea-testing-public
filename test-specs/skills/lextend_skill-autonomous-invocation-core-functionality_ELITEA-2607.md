# Test Case: Skill Autonomous Invocation — Core Functionality

## Metadata
- **TMS ID**: ELITEA-2607
- **Source case**: `.agents/automation/skills-remaining-w4/cases/ELITEA-2607.md`
  (snapshot; frontmatter `status: draft`, `execution_type: manual`, tags
  `[automated:UI:regression, feat:skills, feat:autonomous-invocation]` — matches
  the intake selector, no case-gate exclusion applies)
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI dev server on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399),
  model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing

## Extension target

**Covering spec/test file**:
`automation/tests/ui/skills/test_skill_agent_interaction.py:117` —
`TestInteractWithSkillsFromAgent.test_interact_with_skills_from_agent` (covers
ELITEA-1735, merged to `origin/automation/base` as of `ed4138e5`).

### Behavioural-overlap argument (what's already proven)

The merged test already creates two skills (uppercase / underscore transforms,
each gated by a distinct description-trigger condition), attaches BOTH to one
agent, and drives exactly the observable this case's **Part A** and **Part B**
assert:

1. **Step 6** sends a plain message with no trigger keyword and no `~mention` and
   asserts NEITHER skill's transform appears in the response — this is ELITEA-2607
   Part B (non-matching context does not invoke a skill) verbatim, just phrased as
   "neither of two attached skills" instead of "the one attached skill."
2. **Steps 7-8** send messages matching each skill's own description trigger
   condition (no `~mention`) and assert the response reflects that skill's
   transform (`AUTONOMOUS_TRIGGER_FORMAL` → all-uppercase, `AUTONOMOUS_TRIGGER_FUN`
   → underscore-delimited) — this is ELITEA-2607 Part A's core autonomous-invocation
   claim (steps 6-7 of the case: attached skill invoked automatically when message
   context matches, response reflects the skill's instructions).
3. Steps 9-10 additionally cover V1 explicit `~mention` invocation, which
   ELITEA-2607 doesn't test at all (out of this case's scope, not a gap).

This is Rule-6 partial overlap on the case's own numbered steps 1-3, 5-7, 10-11:
skill creation, agent creation, single-skill attachment (the merged test attaches
two, which subsumes "attach one"), and autonomous-invocation-on-match /
non-invocation-on-mismatch are already proven live and merged. A fresh
`test_*` reimplementing "create 2 skills, attach to agent, autonomous invoke on
match, no invoke on mismatch" would duplicate this test's setup and Steps 6-8
almost verbatim.

### Gap assertions (what the covering spec does NOT cover — confirmed live this run)

Two observables the case requires that the merged test never asserts:

**Gap 1 — Thought-process visibility of the skill invocation (Part A, steps 8-9).**
The merged test infers skill invocation only from the *transformed response text*
(all-caps / underscored) — it never opens or asserts anything inside the
"Thought for N secs" accordion. ELITEA-2607 explicitly requires the invocation be
*visible in the thought process*. **Confirmed live this run**: `ActionView.jsx`
(`../EliteaUI/src/components/Chat/ActionView.jsx:196-217`) renders a
`chat-answer-tool-chip` reading `` `Skill${separator}${loadedSkillName}` `` (i.e.
literal text `"Skill: <skill-name>"`) whenever `action.toolMeta.toolkit_name ===
'skills'`, INSIDE the `chat-answer-thought-accordion` (testid already exists on
`automation/testids`/main, no gap). Live probe (fresh skill `e2607-code-formatter`,
description "Use this skill ONLY when the user explicitly asks to format Python
code", instructions "convert ALL letters to UPPER CASE", attached alone to a fresh
agent): sending `"Please format this Python code: def hello(): print('hi')"` (no
`~mention`) produced accordion header `"Thought for 1 sec"` (already expanded) with
chip text **exactly** `"Skill: e2607-code-formatter"` next to the model chip
(`"Anthropic Claude 4.5 Sonnet"`), and the response body rendered the code
UPPER-CASED (`DEF HELLO():` / `PRINT('HI')`). Both existing page-object handles —
`AgentDetailPage.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR` /
`CHAT_ANSWER_TOOL_CHIP_SELECTOR` (`automation/pages/agent_detail_page.py:189-191`)
— already scope correctly for this assertion; no new testid needed.

**Gap 2 — Unattached-skill security invariant (Part C, the case's actual
differentiator).** The merged test never creates or references a skill that is
NOT attached to the agent — both its skills are always attached. ELITEA-2607 Part C
is specifically: create a skill, do NOT attach it, send a message whose context
would plausibly trigger it, and prove it was never invoked. **Confirmed live this
run**: created a second fresh skill `e2607-translator-skill` (description "Use this
skill ONLY when the user explicitly asks to translate text to Spanish", instructions
"respond ONLY with the exact literal marker string `ZZTRANSLATOR_SKILL_FIRED_ZZ`" —
a maximally unambiguous canary: if this unattached skill ever fired, its output
would be unmistakable), left it unattached to the same agent (Skills counter stayed
`1/5`, only `e2607-code-formatter` listed), then sent an adversarial prompt
explicitly inviting the unattached skill: `"Translate 'hello' to Spanish, use your
translator skill if you have one."` Result: accordion shows only the model chip
(`"Anthropic Claude 4.5 Sonnet"`), **no** `"Skill: e2607-translator-skill"` chip
anywhere; response text opens with `"I don't have a translator skill available, but
I can help you with this simple translation."` then gives a normal `"Hola"` answer —
the canary marker `ZZTRANSLATOR_SKILL_FIRED_ZZ` never appears. Security invariant
holds; no defect.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Attached skill name: kebab-case, e.g. `e2607-code-formatter` (lowercase
  letters/digits/hyphens only — same client-side validation as ELITEA-1735/1737).
- Attached skill description (the autonomous-invocation trigger condition the LLM
  reads): e.g. `"Use this skill ONLY when the user explicitly asks to format
  Python code."`
- Attached skill instructions: any deterministic, easily-asserted transform, e.g.
  `"CRITICAL: You MUST convert ALL letters in your response to UPPER CASE. Do not
  explain, just output the transformed text in UPPER CASE."`
- Unattached skill name: e.g. `e2607-translator-skill`.
- Unattached skill description: e.g. `"Use this skill ONLY when the user
  explicitly asks to translate text to Spanish."`
- **Unattached skill instructions — use a canary marker, not a plausible-looking
  transform.** A real translation ("hola") is indistinguishable from the base LLM
  correctly answering the same prompt WITHOUT any skill, so it cannot prove
  non-invocation. Use an instruction whose output could ONLY come from that
  skill's own instructions firing, e.g. `"CRITICAL: You MUST respond ONLY with the
  exact literal marker string ZZTRANSLATOR_SKILL_FIRED_ZZ and nothing else, no
  matter what the user asks."` Assert the marker string is absent from the
  response (case-insensitive) — presence would mean the security invariant broke.
- Agent name: e.g. `e2607-autonomous-test-agent`; description + a short generic
  instructions string (agent instructions do not need to mention skills — same
  precedent as ELITEA-1735's Test Data).
- Context-matching prompt (attached skill): e.g. `"Please format this Python
  code: def hello(): print('hi')"` — sent with NO `~mention`.
- Adversarial prompt (unattached skill): e.g. `"Translate 'hello' to Spanish, use
  your translator skill if you have one."` — deliberately invites the unattached
  skill by name/intent to maximize the security check's strength; sent with NO
  `~mention` (and the unattached skill has no `~mention` entry to select even if
  attempted, since `MentionSkillList` only lists attached skills — pre-existing
  ELITEA-1791 coverage).

No `reuse-existing` fixture applies — same fresh-state-per-test reasoning as
ELITEA-1735: 2 skills + 1 agent, created and torn down within the test.

## Test Steps

1. Create Skill 1 (attached) via `${BASE_URL}/skills/create`: fill Name
   (`skill-name-input-field`), Description (`skill-description-input-field`),
   Instructions (`skill-instructions-editor-content`, CodeMirror — use
   `press_sequentially`, not `fill`). Click Save (`skill-save-button`).
   - **Verify**: URL settles on `/skills/all/{id}`; note Skill 1's ID.
2. Repeat step 1 for Skill 2 (to remain unattached) with the canary-marker
   instructions above.
   - **Verify**: distinct ID from Skill 1.
3. Create an Agent via `${BASE_URL}/agents/create`: fill Name
   (`agent-name-input`), Description (`agent-description-input`), Instructions
   (`agent-instructions-input`). Click Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`.
4. On the agent detail page, expand the Skills accordion, click the add-skill
   button (`agent-add-skill-button` — **confirmed live, pre-existing testid**;
   the ELITEA-1735 AFS's "no testid, recommend `add-data-testid`" note is now
   stale — the UI team added it since that pass). Attach ONLY Skill 1 from the
   popper (menuitem role, accessible name = skill name). Do NOT attach Skill 2.
   - **Verify**: Skills counter reads `"1/5 skills added."`; exactly one skill
     card renders (Skill 1's name).
5. In the agent's embedded chat panel, type the context-matching prompt (no `~`
   mention) into `chat-message-input`, press Enter.
   - **Verify**: response reflects Skill 1's transform (e.g. all-uppercase).
     Expand/read the `chat-answer-thought-accordion` for the last message; assert
     a `chat-answer-tool-chip` with text exactly `"Skill: {skill-1-name}"` is
     present (Gap 1).
6. Clear the chat (`chat-clear-button`). Send a non-matching plain message (no
   trigger keyword, no `~mention`).
   - **Verify**: response is normal, no transform applied; no
     `chat-answer-tool-chip` reading `"Skill: {skill-1-name}"` present (already
     proven by the covering spec's Step 6 pattern — re-asserted here for
     completeness on the single-attached-skill topology if the implementer keeps
     this as its own step, or reused as-is if folded into the covering spec).
7. Clear the chat. Send the adversarial prompt naming/inviting Skill 2 (the
   UNATTACHED skill) by intent, no `~mention` (none available — Skill 2 was
   never attached, so it cannot appear in the `~` mention popper either, per
   ELITEA-1791's established scoping).
   - **Verify (Gap 2 — security)**: response does NOT contain Skill 2's canary
     marker string (case-insensitive). No `chat-answer-tool-chip` reading
     `"Skill: {skill-2-name}"` anywhere in the thought accordion.

## Expected Results

1. An attached skill is invoked automatically (no `~mention`) when the message
   context matches its description trigger — response reflects the skill's
   instructions.
2. The invocation is visible in the thought process as a `"Skill: {name}"` chip
   inside the `chat-answer-thought-accordion`.
3. A non-matching message does not invoke the attached skill (no transform, no
   chip).
4. An unattached skill is NEVER invoked, even when explicitly invited by an
   adversarial prompt matching its own trigger description (security invariant).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Steps 1-2 (create skills) | Skills created | Extension Steps 1-2 (new) + covering spec's `_create_skill()` helper (already proven) | new test / `test_skill_agent_interaction.py:75-98` | covered |
| Steps 3-4 (create agent, attach ONLY the intended skill) | Agent created, 1 skill attached | Extension Steps 3-4 (new); covering spec attaches 2 (subsumes "attach 1") | new test | covered |
| Steps 6-7 (send matching prompt, agent invokes skill) | Response demonstrates skill's transform | Covering spec Steps 7-8 (`test_skill_agent_interaction.py:216-254`) | covering spec, re-confirmed live this run with a fresh single-skill topology | already-proven — no new test code needed for the transform-text half |
| Steps 8-9 (thought process shows invocation) | `chat-answer-tool-chip` = `"Skill: {name}"` inside `chat-answer-thought-accordion` | Extension Step 5 (new) — **Gap 1** | new test | gap — implementer adds |
| Steps 10-11 (non-matching prompt does not invoke) | No transform, no skill chip | Covering spec Step 6 (`test_skill_agent_interaction.py:196-215`) | covering spec | already-proven |
| Step 12 (check thought process for non-invocation) | No skill invocation shown | Implied by covering spec Step 6 (never asserted directly on the chip, only on response text) | new test may add the chip-absence assertion alongside the reused text check | minor gap — cheap to fold into Step 6 if implementer keeps a local copy |
| Steps 13-16 (unattached skill never invoked, even when context matches) | No transform via the unattached skill's instructions; not shown in thought process | Extension Step 7 (new) — **Gap 2**, the case's actual differentiator | new test | gap — implementer adds |

### Axis 2 — Analyst additions

| Additional observable asserted | Reason |
|---|---|
| Canary-marker instructions for the unattached skill (`ZZTRANSLATOR_SKILL_FIRED_ZZ`) rather than a plausible real transform | A real translation is indistinguishable from the base LLM's own general knowledge answering the same prompt with zero skill involvement — it cannot prove the security invariant either way. A marker that could ONLY come from that skill's own instructions firing is the only assertion that actually falsifies "the unattached skill was invoked." |
| `chat-answer-tool-chip` text asserted verbatim (`"Skill: {name}"`) rather than just "a chip is present" | Confirms the chip specifically identifies it as a SKILL invocation (vs. a toolkit/tool chip, which shares the same testid/DOM shape per `ActionView.jsx`'s ternary) — the case's own "invocation is visible" bar requires the observer to be able to tell it was a skill. |

## Gap Assertions To Append (implementer-facing)

Extend `TestInteractWithSkillsFromAgent` (or add a sibling test in the same file,
implementer's call per file-size/clarity) with:

1. **Thought-process chip assertion** — after Step 7/8's autonomous-trigger
   sends (or a fresh single-skill-topology test per this AFS's own Steps 1-5),
   call `AgentDetailPage.get_outer_thought_accordion()` then locate
   `CHAT_ANSWER_TOOL_CHIP_SELECTOR` scoped inside it; assert
   `.to_contain_text(f"Skill: {SKILL_NAME}")`.
2. **Unattached-skill security test** — new skill created but never attached
   (skip the `attach_skill()` call for it); send the adversarial prompt; assert
   (a) response text does NOT contain the canary marker (case-insensitive), and
   (b) no `chat-answer-tool-chip` inside the thought accordion contains
   `f"Skill: {UNATTACHED_SKILL_NAME}"` (use `.count()` on a filtered locator, or
   iterate `get_thought_accordion_tool_chip_texts()`-style helper if one exists —
   grep `agent_detail_page.py` for the plural-chip-text reader used by
   `get_nested_agent_tool_chip_locator`'s sibling methods before writing a new
   one).
3. Both new assertions get their own teardown entries in the existing
   `try/finally` skill/agent cleanup block (same pattern as the covering test).

## Cleanup

- `AgentAPI.delete_agent(agent_id)` then `SkillAPI.delete_skill(skill_id)` for
  both skills, in a `try/finally` — identical pattern to the covering spec's own
  teardown (`test_skill_agent_interaction.py:296-310`).
- This analysis run's own live test data was deleted via direct API calls
  (`DELETE .../elitea_core/application/prompt_lib/399/9211`,
  `DELETE .../elitea_core/skill/prompt_lib/399/1792`,
  `DELETE .../elitea_core/skill/prompt_lib/399/1793` — all `204`) — nothing left
  behind on the DEV backend.

## Concrete Handles (discovered during exploration — all pre-existing, no new
testid needed)

| Element | Handle | Provenance |
|---|---|---|
| Skill name input | `[data-testid="skill-name-input-field"]` | on-main ✓ (pre-existing, used by ELITEA-1735/1737 lineage) |
| Skill description input | `[data-testid="skill-description-input-field"]` | on-main ✓ |
| Skill instructions editor | `[data-testid="skill-instructions-editor-content"]` | on-main ✓ |
| Skill save button | `[data-testid="skill-save-button"]` | on-main ✓ |
| Agent name/description/instructions inputs | `agent-name-input` / `agent-description-input` / `agent-instructions-input` | on-main ✓ |
| Agent save button | `[data-testid="agent-save-button"]` | on-main ✓ |
| Add-skill button (agent detail, Skills section) | `[data-testid="agent-add-skill-button"]` | **on-main ✓, confirmed live this run** — supersedes the ELITEA-1735 AFS's stale "no testid, gap" note; the UI team added it since that earlier pass. |
| Chat message input | `[data-testid="chat-message-input"]` | on-main ✓ |
| Clear-chat button | `[data-testid="chat-clear-button"]` | on-main ✓ |
| Thought accordion (outer, per-message) | `[data-testid="chat-answer-thought-accordion"]` | on-main ✓ — `AgentDetailPage.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR` (`automation/pages/agent_detail_page.py:189`) |
| Model chip | `[data-testid="chat-answer-model-chip"]` | on-main ✓ — `CHAT_ANSWER_MODEL_CHIP_SELECTOR` |
| Tool/skill chip | `[data-testid="chat-answer-tool-chip"]` | on-main ✓ — `CHAT_ANSWER_TOOL_CHIP_SELECTOR` (`automation/pages/agent_detail_page.py:191`); text is `"Skill: {name}"` when the invoked entity is a skill (`ActionView.jsx:196-217`), `"{toolkit}: {tool}"` for a toolkit/tool call (canon ruling #277 shape (b) — both branches already named and referenced elsewhere in the suite). |

## Network Behavior

- Skill attach: `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}`
  → `201 Created` (confirmed pattern from ELITEA-1735's AFS; not independently
  re-traced this run, same UI flow).
- Predict/chat traffic is WebSocket-based (not independently re-traced this run;
  same mechanism the covering spec and every other chat test already rely on —
  `.agents/testing.md` § Hooks & fixtures, ~2s+ latency, condition waits only).
- Skill/agent cleanup via direct DELETE (see § Cleanup) — `204 No Content` both
  times for skills, `204 No Content` for the agent.

## Known Defects Found During Exploration

None. Both gap observables (thought-process chip, unattached-skill security
invariant) confirmed working correctly live — no product defect, no case-text
drift.

## Blocked Steps

None.

## Automation Hints

- Reuse `TestInteractWithSkillsFromAgent`'s `_create_skill()` helper
  (`test_skill_agent_interaction.py:75-98`) for both this extension's skills —
  it already returns the numeric skill ID and handles the CodeMirror
  `press_sequentially` gotcha.
- The unattached-skill canary-marker assertion should be case-insensitive
  substring match (`"ZZTRANSLATOR_SKILL_FIRED_ZZ".lower() not in response.lower()`)
  — an LLM could plausibly echo it in mixed case if it ever leaked partially.
  A partial/garbled leak is just as much a security failure as a clean one, so
  don't over-narrow the check to an exact-case match.
  Same `@pytest.mark.flaky(reruns=3, reruns_delay=5)` marker as the covering
  test — LLM response timing/content has the same inherent variability this
  project already accepts for skill-invocation assertions (per ELITEA-1735's
  own precedent), though the NEW assertions here (chip presence, marker
  absence) are considerably more deterministic than "is every letter
  uppercase" and may need fewer reruns in practice — implementer's call based
  on live gate runs.
