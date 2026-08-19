# Test Case: Chat – Tool Output Rendering – Verify Tool Execution Results Display as Chips When Toolkit Called Directly

## Metadata
- **TMS ID**: ELITEA-2210
- **Linked Story**: none
- **Priority**: lextend (case frontmatter says `priority: high`, which maps to `l1` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend) — this pass is a **source + sibling-AFS verified** dedup analysis (see Overlap check
  below); no fresh browser session was needed because the exact mechanism, message-text pitfall, and
  rendering code path were all independently confirmed live by two sibling cases in THIS SAME batch
  within the last few hours (ELITEA-2215, ELITEA-2211), plus a direct read of the rendering component
  (`ActionView.jsx`) to confirm tool-agnosticism — this is the same "source-verified" evidentiary
  standard ELITEA-2211's own AFS already used for its un-reachable-on-localhost precondition.
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `chat-remaining-w15`
- **Status**: **extend-existing** — zero-diff extension (see § Gap assertions: NONE below). Target:
  `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py::TestDirectToolkitCallCompleteFlow::test_direct_toolkit_call_complete_flow`.
  Core chip-display assertions merged to `origin/automation/base` (ELITEA-2215, commits `ddaf8b31b` /
  `ea705530d` / `ae27893c2`); participants-panel assertion merged onto this batch's trunk
  `tests/batch-chat-remaining-w15` (ELITEA-2209, commit `6e5286012`, merged via `b4203e695`).

## Overlap check vs existing automation

**Covering spec**: `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py` — originally
ELITEA-2215 ("Chat – Tool Action and Output – Complete Flow from Direct Toolkit Call to Output
Display"), already extended once this batch by ELITEA-2209 (participants-panel Setup assertion, AFS
`test-specs/chat-interface/lextend_direct-toolkit-call-participants-panel-verification_ELITEA-2209.md`).

**ELITEA-2210 and ELITEA-2215/2209 test the SAME live flow and the SAME observable** — a toolkit added
as the sole chat participant (no agent), sending a message that triggers a real tool call, and
verifying the model chip + toolkit/tool chip render above the response. Side-by-side against
ELITEA-2210's own steps:

| ELITEA-2210 step | Expected | Covered by the covering spec (current trunk state)? |
|---|---|---|
| 1. Add toolkit 'aaa' via + > Toolkits (no agent) | Toolkit in PARTICIPANTS | **Covered by ELITEA-2209's extension** — `assert chat.is_participants_badge_visible(section="toolkits")` runs unconditionally in the Setup step, BEFORE the message is sent and before any tool-specific logic — so it applies identically regardless of which tool the toolkit exposes. |
| 2. Send message; "Thought for X secs" appears | Accordion visible | Covering spec Step 1 (`chat.answer_thought_accordion` visible) — covered, tool-agnostic (accordion is a generic streaming indicator, not tied to which tool fires). |
| 3. Wait for tool execution; LLM response appears | Response visible | Covering spec Step 2/2b/5 — covered. |
| 4. Chips: LLM model chip + toolkit tool chip (e.g. `"aaa: delete_file"`) shown horizontally | Both chips shown | Covering spec Step 4 (`model_chip_count >= 1`, `answer_tool_chip` count==1 with `"{toolkit_name}: {tool_name}"` text) — covered, **and this is the SAME generic component regardless of which tool fires** (see § Tool-agnosticism argument below). |
| 5. Each chip has appropriate icon and label | Icons/labels correct | Covered as a corollary of the chip-visibility assertion — the icon renders as a child node of the SAME chip element the testid is placed on (`ActionView.jsx`'s `Box sx={styles.iconContainer}` sibling to the label, both inside the one `data-testid` chip root); there is no code path that renders the label without the icon or vice-versa, so `expect(chip).to_be_visible()` + text-content assertion necessarily proves both. Same treatment ELITEA-2209's own Coverage Map already gave this exact wording ("Chip visible with icon" → "asserted (reused)", no separate icon-only assertion invented). |

**No case element of ELITEA-2210 is unproven by the covering spec's current state.**

### Tool-agnosticism argument (why `delete_file`/'aaa' needs no new code vs the covering spec's `create_file`/artifact-toolkit)

Read `EliteaUI/src/**/ActionView.jsx` (the component both `chat-answer-model-chip` and
`chat-answer-tool-chip` are rendered from):
- The tool-chip's text is built by `buildTitle()` as `"{toolkitName}: {toolName}"` — a plain string
  template with no branching on the specific tool name. `delete_file` renders through the identical
  code path as `create_file`.
- The chip's icon comes from `renderIcon()`, which branches on `toolkitType` (`'application'` /
  `'pipeline'` / else `getToolIconByType(toolkitType, ...)`) — **branches on TOOLKIT TYPE, never on
  the individual tool name.** An `artifact`-type toolkit's `delete_file` and `create_file` tools
  therefore render the exact same icon.
- The model chip is entirely independent of which tool fired — it reflects `toolkitType === 'model'`
  reasoning-chain entries, unrelated to the specific tool argument.

This is a genuine "differs only in DATA" case (toolkit name, tool name, message wording) against an
already-proven mechanism, not a differs-in-STEPS case — per `test-case-analysis` § Execute's
family/data test, and the project's own reuse-not-duplicate framing (`.agents/role-overrides.md`).

### Gap assertions: NONE

Every case element ELITEA-2210 requires is already asserted, unconditionally, by the covering spec's
CURRENT state on this batch's trunk (`tests/batch-chat-remaining-w15`) — no new test code, fixture, or
assertion is needed. The implementer's action for this case is **traceability only**:
1. Add a second `@allure.issue(...)` decorator on
   `TestDirectToolkitCallCompleteFlow.test_direct_toolkit_call_complete_flow` referencing ELITEA-2210's
   onetest-tms case link (same additive pattern ELITEA-2209 already used for its own link, alongside
   the original ELITEA-2215 one) — a one-line, zero-behavior-change addition.
2. No functional changes. No new fixture. No new markers.
3. Back-write ELITEA-2210 in the TMS pointing at the same
   `automation_test_id` the covering spec already carries (once that spec's `automation_test_id` is
   itself back-written at batch close — same multi-case-per-test-id shape
   `.agents/test-automation.yaml` § `backwrite_on_done` documents, "a case may list several tests /
   one test may cover several cases").

**Case-text CLARIFICATION, cross-referenced (not re-filed — already documented by a sibling case in
this same batch):** ELITEA-2210's own Test Data uses the literal message `"use delete_file toolkit to
remove from the bucket all files"`. ELITEA-2211's AFS
(`test-specs/chat-interface/l2_hitl-sensitive-action-card-display_ELITEA-2211.md` § Test Data)
already live-tested this **exact verbatim string** against a real artifact toolkit + bucket and found it
does **not** reach a real tool call — the LLM asks a clarifying question instead ("You have 588
buckets... which bucket(s)?"), because "the bucket" is ambiguous. This is a live-confirmed CLARIFICATION
(reverse-masking guard — the case text is imprecise, not a product defect), already on file; no new
tracker entry needed for THIS case since it's the identical wording issue ELITEA-2211 already surfaced.
Not relevant to this AFS's own disposition since no new message-driving code is written here (the
covering spec uses its own already-fixed unambiguous message), but noted so nobody re-discovers it.

## Preconditions
Same as the covering spec (post-ELITEA-2209): an Artifact-type toolkit is added as the ONLY participant
in a fresh conversation via "+ > Toolkits" (no agent). ELITEA-2210's own precondition ("toolkit 'aaa'
with delete_file tool") is satisfied by the same `artifact_toolkit` fixture the covering spec already
uses (its default `selected_tools` list includes `delete_file`, confirmed by ELITEA-2211's AFS which
reused the identical fixture for its own delete_file-based precondition).

## Test Data
No new test data. This is a zero-diff extension — reuses the covering spec's existing fixtures and
message constants verbatim.

## Test Steps
1.–5. (Existing, unchanged) — add toolkit as sole participant (with participants-panel assertion from
ELITEA-2209), send message, thinking-steps chip, model+tool chips, response — exactly as implemented in
the covering spec, already proven per the Overlap check table above for every one of ELITEA-2210's own
steps.

## Expected Results
Same as the covering spec: toolkit lands in PARTICIPANTS (no AGENTS section), thought accordion
appears, tool call executes, model chip(s) + one toolkit/tool chip render horizontally above the
response with correct icon+label, response text follows below the chips.

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Add toolkit 'aaa' via + > Toolkits (no agent) | Toolkit in PARTICIPANTS | covering spec Setup (ELITEA-2209 extension) | `test_direct_toolkit_call_complete_flow.py` Setup step, `chat.is_participants_badge_visible(section="toolkits")` | asserted (reused, already merged to trunk) |
| 2 Send message; "Thought for X secs" appears | Accordion visible | covering spec Step 1 | same file | asserted (reused, on `origin/automation/base`) |
| 3 Wait for tool execution; LLM response appears | Response visible | covering spec Step 2/2b/5 | same file | asserted (reused) |
| 4 Chips: model chip + toolkit tool chip, e.g. "aaa: delete_file" | Both chips shown horizontally | covering spec Step 4 | same file | asserted (reused) *(clarification: text format is colon-separated `"{name}: {tool}"`, matching the case's own bracketed example, per ELITEA-2215's already-documented drift)* |
| 5 Each chip has appropriate icon and label | Icons/labels correct | covering spec Step 4 (implicit) | same file | asserted (reused) *(icon and label are one rendered DOM subtree under the same testid — see Tool-agnosticism argument)* |
| Expected Final State: tool execution chips shown above LLM response | — | covering spec, all steps | — | asserted (reused, composite) |

**Axis 2 — Analyst additions**
- None. This extension adds no observable beyond what ELITEA-2210's own case text already requires,
  and no new assertion beyond what the covering spec already runs.

## Cleanup
Same as the covering spec (delete toolkit, delete bucket) — no new cleanup, no new state introduced.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Provenance | Notes |
|---|---|---|---|
| Thought accordion | `[data-testid="chat-answer-thought-accordion"]` | on `origin/automation/base` (ELITEA-2215) | `ChatPage.answer_thought_accordion` |
| Model chip(s) | `[data-testid="chat-answer-model-chip"]` | on `origin/automation/base` | `ChatPage.answer_model_chip` |
| Toolkit/tool chip | `[data-testid="chat-answer-tool-chip"]` | on `origin/automation/base` | `ChatPage.answer_tool_chip`, text `"{toolkit_name}: {tool_name}"` — tool-agnostic per `ActionView.jsx`'s `buildTitle()` |
| Toolkits participants badge | `[data-testid="chat-participants-badge-toolkits"]` | on this batch's trunk only (ELITEA-2209) | `ChatPage.is_participants_badge_visible(section="toolkits")` |
| Agents participants badge (absence check) | `[data-testid="chat-participants-badge-agents"]` | same | same method, `section="agents"` |

No new testid needed — every handle is pre-existing and already exercised by the covering spec on its
own executed path.

## Network Behavior
No new network behavior. Standard `chat_predict` websocket envelope, already covered by the covering
spec's own Network Behavior section (ELITEA-2215's AFS).

## Known Defects Found During Exploration
None NEW. Cross-reference (not this case's own finding): the covering spec's known, non-deterministic
defect `elitea-testing-public#1127` (direct-toolkit-call flow sometimes leaks tool-call intent as raw
text instead of invoking the real tool, 2/5 run rate) applies to ELITEA-2210 exactly as it applies to
ELITEA-2215/2209 — same underlying flow, same soft-fail/ground-truth classification already implemented
in the covering test. No separate handling needed since ELITEA-2210 introduces no new test code.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **This is a traceability-only extension — no test code, fixture, or
  assertion changes.** Add a second `@allure.issue(...)` decorator (ELITEA-2210's onetest-tms case
  link) to `TestDirectToolkitCallCompleteFlow.test_direct_toolkit_call_complete_flow`, alongside the
  existing ELITEA-2215/2209 decorators — same additive multi-case-link pattern already used twice in
  this file.
- No new `@pytest.mark` needed — priority/feature markers unchanged.
- The covering test remains excluded from this batch's N-consecutive-green hardening gate for the same
  reason ELITEA-2215/2209 are (non-deterministic known defect #1127, see `GATE_EXCLUDED_REASON` module
  constant) — this does not change with ELITEA-2210's traceability link added.
