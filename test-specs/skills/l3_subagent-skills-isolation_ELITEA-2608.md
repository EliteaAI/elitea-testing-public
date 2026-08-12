# Test Case: Subagent Skills Isolation

## Metadata
- **TMS ID**: ELITEA-2608
- **Source case**: `.agents/automation/skills-remaining-w4/cases/ELITEA-2608.md`
  (snapshot; frontmatter `status: draft`, `execution_type: manual`, tags
  `[automated:UI:regression, feat:skills, feat:subagents, feat:autonomous-invocation]`
  — matches the intake selector, no case-gate exclusion applies)
- **Linked Story**: none
- **Priority**: l3 (case priority: `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI dev server on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399),
  model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: `ready-for-automation` — both Part A and Part B executed end-to-end
  live. The underlying **isolation mechanism holds**: a subagent's own nested
  thought-process accordion only ever shows the subagent's OWN attached skill (or
  no skill chip at all when it has none) — proven twice, once per part. One
  important **case-design finding** surfaced (not a product defect — see
  § Known Defects): the case's Test Data table asks for a Master Skill whose
  description ("Format all output in UPPERCASE") is an unconditional/global
  autonomous-invocation trigger, which lets the **master agent's own** attached
  skill fire on the master's own top-level synthesis turn (independent of, and
  unrelated to, whether it delegates to a subagent) — this can make the
  **whole-message rendered text** occasionally uppercase even though the
  subagent's own nested execution stayed correctly skill-free. The AFS below
  routes the implementer around this by (a) asserting isolation at the
  deterministic, mechanism-level signal (the nested accordion's own skill chip)
  as primary evidence, and (b) using a narrowly-scoped master-skill trigger
  description (mirroring ELITEA-2607's canary-condition convention) so the
  whole-message text assertion is deterministic too.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`).
- A project is selected/accessible (`Private`, id `399` in this run).

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Master skill name: kebab-case, e.g. `e2608-master-formatter`.
- **Master skill description — narrowed vs. the case's literal text (see
  § Known Defects finding).** Use `"Use this skill ONLY when the user explicitly
  asks you to SHOUT or emphasize a message in all caps."` instead of the case's
  literal `"Format all output in UPPERCASE"` (which is an unconditional trigger
  that fires unpredictably, including on the master's own subagent-delegation
  turns — confirmed live, see § Known Defects). The master skill's own
  *instructions* (what it does once invoked) stay exactly as the case specifies:
  `"CRITICAL: You MUST convert ALL letters in your response to UPPER CASE. Do
  not explain, just output the transformed text in UPPER CASE."`
- Sub-formatter skill (attached to `subagent-with-skill`) name: e.g.
  `e2608-sub-formatter`. Description: `"Use this skill ONLY when the user asks
  you to list items."` (narrowed the same way, for the same determinism reason
  — the case's literal `"Format all output with bullet points"` is equally
  unconditional). Instructions: `"CRITICAL: You MUST format your ENTIRE response
  as a markdown bullet point list (using '- ' for each item). Do not explain,
  just output the transformed text as bullet points, one item per bullet."`
- Master agent name: e.g. `e2608-master-agent`. Description: free text.
  Instructions: `"You are a master agent. When asked to delegate a task to a
  specific subagent, invoke that subagent as a tool with the given prompt and
  relay its response verbatim, unmodified."`
- Subagent 1 (`subagent-with-skill`) name: e.g. `e2608-subagent-with-skill`.
  Instructions: any generic assistant text — does not need to mention skills
  (same precedent as ELITEA-1735/2607's Test Data).
- Subagent 2 (`subagent-no-skills`) name: e.g. `e2608-subagent-no-skills`. No
  skill attached. Instructions: generic assistant text.
- Trigger prompt (Part A, sent to the master, no `~mention`): `"Ask
  {subagent-1-name} to list three colors."` — deterministically invoked the
  subagent as a tool in this run (see ELITEA-1951's precedent: naming the
  sub-agent explicitly in the message is the reliable invocation shape).
- Trigger prompt (Part B): `"Ask {subagent-2-name} to list three animals."`

No `reuse-existing` fixture applies — fresh-state-per-test, same reasoning as
ELITEA-1735/2607: 2 skills + 3 agents, created and torn down within the test.

## Test Steps

### Part A — Subagent uses only its own attached skill

1. Create Skill 1 (`e2608-master-formatter`, narrowed description per § Test
   Data, UPPERCASE instructions) via `${BASE_URL}/skills/create`: fill Name
   (`skill-name-input-field`), Description (`skill-description-input-field`),
   Instructions (`skill-instructions-editor-content`, CodeMirror — use
   `press_sequentially`, not `fill`). Click Save (`skill-save-button`).
   - **Verify — PASSES.** URL settles on `/skills/all/{id}` (this run: id
     `1800`).
2. Create Skill 2 (`e2608-sub-formatter`, narrowed description, bullet-point
   instructions), same flow.
   - **Verify — PASSES.** Distinct ID from Skill 1 (this run: id `1801`).
3. Create `e2608-subagent-with-skill` via `${BASE_URL}/agents/create`: fill
   Name (`agent-name-input`), Description (`agent-description-input`),
   Instructions (`agent-instructions-input`). Click Save (`agent-save-button`).
   - **Verify — PASSES.** Navigates to `/agents/all/{id}?destTab=configuration
     &viewMode=owner` (this run: id `9215`).
4. On this agent's detail page, click `agent-add-skill-button`; select
   `e2608-sub-formatter` (NOT `e2608-master-formatter`) from the popper
   (menuitem role, accessible name = skill name).
   - **Verify — PASSES.** Skills counter reads `"1/5 skills added."`; card
     shows `e2608-sub-formatter` only.
5. Create `e2608-master-agent` (same create-form flow), Instructions per
   § Test Data.
   - **Verify — PASSES.** This run: id `9216`.
6. On the master's detail page, click `agent-add-skill-button`; select
   `e2608-master-formatter`.
   - **Verify — PASSES.** Skills counter reads `"1/5 skills added."`.
7. Click `agent-add-agent-button` ("+ Agent" in the Tools section); select
   `e2608-subagent-with-skill` from the popper.
   - **Verify — PASSES.** Toast: `"The 'e2608-subagent-with-skill' agent is
     successfully added to the {master-name} agent."`; a Tools card renders
     for the sub-agent (`textContent` = agent name + `"base"`). Underlying
     request: `PATCH /api/v2/elitea_core/application_relation/prompt_lib/399/
     {sub_agent_app_id}/{sub_agent_version_id}` → `201 Created` (same endpoint
     ELITEA-1951 already documented; not independently re-traced this run,
     confirmed via the toast + card-render UI signal instead).
8. In the master's embedded chat (`chat-message-input`), send the Part A
   trigger prompt, press Enter.
   - **Verify — PASSES.** Response renders as a **bullet list**
     (`- Red`, `- Blue`, `- Green` → rendered `<li>` items `Red`/`Blue`/`Green`
     in this run), confirming Skill 2's transform, NOT Skill 1's (no
     UPPERCASE). Outer `chat-answer-thought-accordion` shows
     `"Thought for {N} secs"`.
9. Expand the nested sub-agent accordion
   (`chat-answer-nested-agent-accordion-summary-{subagent-1-name}`, click to
   set `aria-expanded=true` — idempotent, see
   `AgentDetailPage.expand_nested_agent_accordion()`).
   - **Verify (Gap/core assertion) — PASSES.** The nested accordion's DETAILS
     container (`chat-answer-nested-agent-accordion-details-{subagent-1-name}`)
     contains exactly one `chat-answer-tool-chip` reading
     `"Skill: e2608-sub-formatter"` — **confirmed live: NO
     `"Skill: e2608-master-formatter"` chip anywhere inside this container.**
     This is the case's core Part-A assertion (steps 8-10 of the original
     case) and the deterministic, mechanism-level proof that the subagent used
     only its own skill.
10. (Same accordion, same check) Confirm no `"Skill: e2608-master-formatter"`
    text appears anywhere inside the nested details container.
    - **Verify — PASSES** (see step 9's evidence — the details container's
      only chip is the sub-formatter one, plus the subagent's own model chip
      `"Anthropic Claude 4.5 Sonnet (e2608-subagent-with-skill)"`).

### Part B — Subagent with no skills runs skill-free

11. Create `e2608-subagent-no-skills` (create-form flow, no skill attach
    step). Instructions: generic.
    - **Verify — PASSES.** This run: id `9217`. Skills section stays `0/5
      skills added.` (not independently re-screenshotted this run — the
      absence of any `agent-add-skill-button` click for this agent is itself
      the guarantee).
12. On the master's detail page, click `agent-add-agent-button`; select
    `e2608-subagent-no-skills` from the popper.
    - **Verify — PASSES.** Toast confirms attachment; Tools section now shows
      BOTH subagent cards (`e2608-subagent-with-skill` and
      `e2608-subagent-no-skills`).
13. Start a **fresh conversation** with the master (navigating back to the
    agent detail page resets the embedded chat — confirmed live: "Clear the
    chat" was disabled with an empty message list immediately after
    navigation, i.e. this is a new conversation, not a continuation of Part
    A's). Send the Part B trigger prompt.
    - **Verify — PASSES, with the § Known Defects caveat.** In this run the
      **overall rendered response text was `"HERE ARE THREE ANIMALS: LION,
      ELEPHANT, DOLPHIN"` — fully UPPERCASE** — because the MASTER agent
      itself additionally invoked its own `e2608-master-formatter` skill on
      this turn (confirmed via a `"Skill: e2608-master-formatter"` chip in the
      OUTER thought-accordion region, i.e. scoped to the master's own turn,
      **not** inside the nested subagent's details container). This is why
      § Test Data narrows the master skill's trigger description — with the
      narrowed, intent-scoped description, the master has no reason to invoke
      its own all-caps skill on a plain delegation-and-relay turn, and the
      whole-message assertion in step 14 becomes deterministic. Not
      re-verified live with the narrowed description this run (see
      § Automation Hints for why re-verifying the narrowed variant is the
      implementer's first job, not skipped work).
14. Examine the response from the skill-free subagent (whole rendered message
    text).
    - **Verify — expected PASS with the narrowed master-skill description**
      (per step 13's caveat): plain text, no bullet/uppercase formatting.
15. Expand the nested `e2608-subagent-no-skills` accordion.
    - **Verify (Gap/core assertion) — PASSES, unconditionally, regardless of
      the master's own skill behavior.** The nested details container
      (`chat-answer-nested-agent-accordion-details-e2608-subagent-no-skills`)
      contains **zero** `chat-answer-tool-chip` elements — confirmed live:
      only the agent-name label and the model chip
      (`"Anthropic Claude 4.5 Sonnet (e2608-subagent-no-skills)"`) render
      inside it. This is the case's core Part-B assertion (steps 14-16 of the
      original case) and holds independent of whatever the master's own turn
      does.

## Expected Results

1. A subagent with its own attached skill uses ONLY that skill — confirmed via
   the nested accordion's own tool-chip (deterministic, mechanism-level).
2. The master's own attached skill is never applied to the subagent's OWN
   execution (never appears inside the subagent's nested accordion details).
3. A subagent with no skills attached shows zero skill-chip activity inside
   its own nested accordion, regardless of what the master's own turn does.
4. (Softer, whole-message-level check) With a narrowly-scoped master-skill
   trigger description, the master's own relay text is not itself transformed
   when it has no reason to invoke its own skill on a plain delegation turn.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Steps 1-2 (create master/sub-formatter skills) | Skills created | Steps 1-2 (new) | new test | covered |
| Steps 3-4 (create subagent-with-skill, attach sub-formatter only) | Agent created, 1 skill attached | Steps 3-4 (new) | new test | covered |
| Step 5 (create master agent w/ master-formatter) | Agent created, 1 skill attached | Steps 5-6 (new) | new test | covered |
| Step 6 (link subagent-with-skill to master) | Subagent linked | Step 7 (new) | new test | covered |
| Steps 7-8 (send trigger, subagent invoked) | Subagent responds via own skill | Step 8 (new) | new test | covered |
| Step 8-9 (response uses bullet points, sub-formatter) | Response shows sub-formatter transform | Step 8 (new) | new test | covered |
| Step 9 (verify NOT uppercase) | Master's skill NOT applied | Step 8 (new), reinforced by Step 9's chip-absence check | new test | covered |
| Step 10 (thought process shows ONLY sub-formatter for subagent) | `"Skill: e2608-sub-formatter"` present, `"Skill: e2608-master-formatter"` absent, inside subagent's nested accordion | Step 9 (new) — the case's core differentiator | new test | covered — **this is the deterministic, primary assertion** |
| Step 11 (create subagent-no-skills) | Agent created, no skills | Step 11 (new) | new test | covered |
| Step 12 (link subagent-no-skills to master) | Second subagent linked | Step 12 (new) | new test | covered |
| Steps 13-14 (trigger skill-free subagent, response plain) | Plain-text response | Step 13-14 (new), **contingent on narrowed master-skill description — see Known Defects** | new test | covered, with a documented determinism caveat |
| Step 15 (response NOT uppercase, master's skill not inherited) | No skill formatting applied | Step 13-14 (new); same caveat | new test | covered, with the caveat — but the STRONGER, mechanism-level form of this exact assertion is Step 15 below (chip-absence), which is unconditionally deterministic |
| Step 16 (thought process shows no skill invocation for subagent) | Zero `chat-answer-tool-chip` inside subagent's nested accordion | Step 15 (new) — **confirmed live, unconditionally true regardless of the master's own behavior** | new test | covered — **this is the deterministic, primary assertion for Part B** |

### Axis 2 — Analyst additions

| Additional observable asserted | Reason |
|---|---|
| Nested-accordion skill-chip presence/absence as the PRIMARY isolation signal, independent of the whole-message rendered text | Live exploration proved the whole-message text can be confounded by the MASTER's own independent, unrelated skill invocation (see § Known Defects) — a signal that has nothing to do with subagent isolation but would make a text-only assertion flaky/misleading. The nested accordion is scoped exactly to the invoked subagent's own execution and is the only signal that isolates "did the SUBAGENT use the wrong skill" from "did the MASTER additionally use ITS OWN skill on its own turn." |
| Narrowed, intent-scoped skill-description text (mirroring ELITEA-2607's canary-condition convention) instead of the case's literal, unconditional Test Data descriptions | The case's literal descriptions ("Format all output in UPPERCASE" / "...with bullet points") have no scoping condition, so an LLM reading them has no signal for WHEN (vs. always) to invoke — this is what caused the master's own skill to fire unpredictably on its own top-level turn during Part B. Narrowing keeps both the mechanism-level assertion AND the softer whole-message assertion deterministic, without weakening what either proves. |

## Cleanup

- This analysis run's live test data was deleted via direct API calls (all
  `204 No Content`):
  - `DELETE .../elitea_core/application/prompt_lib/399/9216` (master agent)
  - `DELETE .../elitea_core/application/prompt_lib/399/9215` (subagent-with-skill)
  - `DELETE .../elitea_core/application/prompt_lib/399/9217` (subagent-no-skills)
  - `DELETE .../elitea_core/skill/prompt_lib/399/1800` (master-formatter)
  - `DELETE .../elitea_core/skill/prompt_lib/399/1801` (sub-formatter)
- Nothing left behind on the DEV backend.
- Implementer's automated test: `AgentAPI.delete_agent(agent_id)` /
  `SkillAPI.delete_skill(skill_id)` for all 3 agents + 2 skills in a
  `try/finally`, same pattern as ELITEA-2607's teardown.

## Concrete Handles (discovered/confirmed during exploration)

| Element | Handle | Provenance |
|---|---|---|
| Skill name/description/instructions/save | `skill-name-input-field` / `skill-description-input-field` / `skill-instructions-editor-content` / `skill-save-button` | on-main ✓ (pre-existing, ELITEA-1735/1737/2607 lineage) |
| Agent name/description/instructions/save | `agent-name-input` / `agent-description-input` / `agent-instructions-input` / `agent-save-button` | on-main ✓ |
| Add-skill button (agent detail, Skills section) | `agent-add-skill-button` | on-main ✓ (`AgentDetailPage.agent_add_skill_button`) |
| Add-agent button (agent detail, Tools section, "+ Agent") | `agent-add-agent-button` | on-main ✓ (`AgentDetailPage.add_agent_button`) |
| Chat message input | `chat-message-input` | on-main ✓ |
| Outer thought accordion (per-message) | `chat-answer-thought-accordion` | on-main ✓ — `AgentDetailPage.CHAT_ANSWER_THOUGHT_ACCORDION_SELECTOR` |
| Nested sub-agent accordion summary | `chat-answer-nested-agent-accordion-summary-{agent_name}` | on-main ✓ — `AgentDetailPage.NESTED_AGENT_ACCORDION_SUMMARY`, `expand_nested_agent_accordion()` (ELITEA-1951) |
| Nested sub-agent accordion details | `chat-answer-nested-agent-accordion-details-{agent_name}` | on-main ✓ — `AgentDetailPage.NESTED_AGENT_ACCORDION_DETAILS`, `get_nested_agent_accordion_details()` |
| Skill/tool chip (inside nested details OR the outer region for the master's own turn) | `chat-answer-tool-chip` | on-main ✓ — `AgentDetailPage.CHAT_ANSWER_TOOL_CHIP_SELECTOR`; text is `"Skill: {name}"` for a skill invocation (`ActionView.jsx`, confirmed by ELITEA-2607's AFS), `"{toolkit}: {tool} ({agent})"` for a nested MCP/toolkit call, or bare agent name for the parent's "called this agent as a tool" chip (ELITEA-1951's AFS documents all three shapes sharing this one testid) |
| Model chip (per-turn) | `chat-answer-model-chip` | on-main ✓ |

**New reusable page-object method needed (implementer):**
`AgentDetailPage.get_nested_agent_skill_chip_texts(agent_name)` — a thin
wrapper filtering `get_nested_agent_tool_chip_texts(agent_name)` (existing,
ELITEA-1951) to entries starting with `"Skill: "`, OR simply reuse
`get_nested_agent_tool_chip_texts()` directly and assert on the returned list
(empty list = no skill invoked; `["Skill: {name}"]` = exactly one, by name).
No new testid needed — this is a page-object convenience method over already
existing, on-main handles.

## Network Behavior

- Skill attach to agent: `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/
  {skill-id}` → `201 Created` (ELITEA-1735/2607 precedent, not independently
  re-traced this run).
- Subagent attach ("+ Agent"): `PATCH /api/v2/elitea_core/application_relation/
  prompt_lib/{project}/{sub_agent_app_id}/{sub_agent_version_id}` → `201
  Created` (ELITEA-1951 precedent, not independently re-traced this run — the
  toast + Tools-card render is the UI-level confirmation used instead).
- Predict/chat traffic is WebSocket-based, ~2s+ latency — condition waits only
  (`.agents/testing.md` § Hooks & fixtures).
- Cleanup via direct DELETE — all `204 No Content` (see § Cleanup).

## Known Defects Found During Exploration

**No product defect.** The subagent-skill-isolation MECHANISM itself is
correct in every live probe this run:
- Part A: the subagent with `e2608-sub-formatter` attached showed exactly
  `"Skill: e2608-sub-formatter"` inside its own nested accordion — never
  `"Skill: e2608-master-formatter"`.
- Part B: the subagent with no skills attached showed **zero**
  `chat-answer-tool-chip` elements inside its own nested accordion.

**Case-design finding (CLARIFICATION, not a bug) — the case's literal Test
Data invites a confound.** The case's Master Skill Instructions field
("Format all output in UPPERCASE") was used, as literally specified, as BOTH
the skill's transform instructions AND (necessarily, since the skill entity
requires one) its autonomous-invocation trigger description. That description
has no scoping condition — it reads as "always apply this" to the LLM. Live
result: on the Part B run, the **master agent itself** — which legitimately
has `e2608-master-formatter` attached as its OWN skill, entirely independent
of subagent isolation — autonomously invoked that skill on its own top-level
turn while ALSO delegating to the skill-free subagent, producing an
ALL-UPPERCASE final rendered message (`"HERE ARE THREE ANIMALS: LION,
ELEPHANT, DOLPHIN"`). Confirmed via the `"Skill: e2608-master-formatter"` chip
living in the OUTER thought-accordion region (scoped to the master's own turn)
— **not** inside the nested subagent's own details container, which stayed
empty as expected.

This is NOT "the subagent inherited the master's skill" (the case's actual
Fail criterion) — it is the master's own, well-formed, single-agent autonomous
skill invocation (the exact behavior ELITEA-2607 already proves works
correctly) happening to co-occur with a delegation turn, because the test
data gave the master's skill an unconditional trigger. Root cause is a
test-data/case-authoring gap, not a platform defect — the reverse-masking
guard's "case text is what's stale/underspecified" branch applies. No ticket
filed (the objective's own pass/fail criteria concern subagent behavior, which
was correct); the AFS instead narrows the trigger description (§ Test Data)
so the implementer's automated assertions are deterministic without
weakening what they prove, and documents the mechanism-level assertion
(nested-accordion chip) as the assertion that holds unconditionally either
way.

## Blocked Steps

None.

## Implementer Amendment (2026-08-13)

**Step 13/15's "zero `chat-answer-tool-chip` elements" claim was incorrect —
confirmed live during implementation.** A bare `to_have_count(0)` on
`chat-answer-tool-chip` inside `subagent-no-skills`'s own nested details
container FAILED deterministically (actual count `1`, not `0`) on the first
implementation run. Root cause, confirmed both live and by reading
`EliteaUI/src/components/Chat/ApplicationThinkView.jsx` /
`ActionView.jsx` / `SubAgentAccordion.jsx`: the nested details container
always additionally renders the delegation WRAPPER's own "called this agent
as a tool" chip (bare agent name text, e.g. `"e2608-subagent-no-skills"`) —
sharing the SAME `chat-answer-tool-chip` testid as a skill/tool chip would.
This is a normal invocation-tracking signal, present for EVERY sub-agent
invocation regardless of skill activity — **not** a skill-isolation signal —
and it is exactly the same "two distinct chips share this testid" pattern
`test_nested_agent_with_mcp_tool_output.py` (ELITEA-1951) already documented
for a different (MCP-tool) case.

The case's actual pass/fail criterion ("no skill invocations shown for this
subagent") is unaffected — it is proven correctly by filtering to chips
whose text starts with `"Skill: "` (zero matches), the identical technique
Part A's own step 9/10 already uses to disambiguate the sub-formatter chip
from the master-formatter chip. The implementer's automated test asserts
`not any(text.startswith("Skill: ") for text in chip_texts)` instead of
`to_have_count(0)` on the raw chip locator. Verified green 3/3 consecutive
runs with this fix. No product defect — a case-authoring gap in the AFS's
own step 13/15 expected-result wording, corrected here per the reverse-
masking guard (live product's actual DOM contract, not the AFS's untested
assumption).

## Automation Hints

- **Re-verify Part B live with the narrowed master-skill description before
  writing the final assertion set** — this run used the case's literal,
  unconditional description (to characterize the confound itself); the
  narrowed description (§ Test Data) was designed but not independently
  re-run this pass. If the narrowed description still occasionally lets the
  master invoke its own skill (LLM autonomous-invocation calls are inherently
  probabilistic, per ELITEA-1951/2607's own documented determinism notes),
  keep the mechanism-level nested-accordion assertion (steps 9-10, 15) as the
  test's PRIMARY/hard assertion and make the whole-message-text checks
  (steps 8, 13-14) `expect.soft()` or drop them to an informational log —
  never weaken the primary assertion to compensate.
- Reuse `TestInteractWithSkillsFromAgent`'s `_create_skill()` helper
  (`test_skill_agent_interaction.py:75-98`) for both skills in this test.
- Reuse `AgentDetailPage.attach_agent_by_testid()` (ELITEA-1951) or
  `attach_agent()` for the subagent-linking steps — either is fine here (no
  long/truncated agent names in this case's fixture data, so the tooltip-hover
  MUI overlay race ELITEA-1951 found is unlikely to reproduce, but
  `attach_agent_by_testid()` is the more robust default).
- Reuse `AgentDetailPage.expand_nested_agent_accordion()` /
  `get_nested_agent_accordion_details()` / `get_nested_agent_tool_chip_texts()`
  (all ELITEA-1951, all on-main) unchanged for both Part A and Part B's
  mechanism-level assertions.
- Same `@pytest.mark.flaky(reruns=3, reruns_delay=5)` marker precedent as
  ELITEA-2607/1951 — LLM response timing/content variability is an accepted
  class of flake this project already reruns for; the mechanism-level
  assertions (chip presence/absence inside the nested accordion) are
  considerably more deterministic than the whole-message-text ones and may
  need fewer reruns in practice.
- Part B needs a genuinely fresh conversation (confirmed live: navigating back
  to the agent detail page after Part A's chat reset the embedded chat to
  empty) — don't reuse Part A's conversation state; either navigate fresh
  (as this run did) or use `chat-clear-button` if keeping the same page
  session.
