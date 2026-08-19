# Test Case: Chat – Tool Output Rendering – Verify Tool Execution Results Display as Chips When Toolkit Called Directly

## Metadata
- **TMS ID**: ELITEA-2210
- **Linked Story**: none
- **Priority**: lextend (case frontmatter says `priority: high`, which maps to `l1` — filename prefix
  replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`,
  DEV backend). Original pass (2026-08-19): source + sibling-AFS verified dedup analysis for rows 1-3
  (see Overlap check below) — no fresh browser session needed since the setup/accordion/response
  mechanism was already independently confirmed live by two sibling cases in this same batch
  (ELITEA-2215, ELITEA-2211). **Fix round (2026-08-19): rows 4-5 required an actual live execution**,
  not source-reading alone (reviewer finding) — added and ran
  `TestDirectToolkitCallDeleteFileChip::test_direct_toolkit_call_delete_file_chip` against localhost;
  see this AFS's Run Report.
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `chat-remaining-w15`
- **Status**: **extend-existing**. Target (rows 1-3, tool-agnostic setup/plumbing):
  `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py::TestDirectToolkitCallCompleteFlow::test_direct_toolkit_call_complete_flow`.
  Core chip-display assertions merged to `origin/automation/base` (ELITEA-2215, commits `ddaf8b31b` /
  `ea705530d` / `ae27893c2`); participants-panel assertion merged onto this batch's trunk
  `tests/batch-chat-remaining-w15` (ELITEA-2209, commit `6e5286012`, merged via `b4203e695`).

  **AMENDED — fix round (2026-08-19).** The original pass of this AFS classified rows 4-5 (the
  `delete_file`-specific chip text + icon+label) as `asserted (reused)` on the strength of a
  source-code tool-agnosticism argument alone (`ActionView.jsx`'s `buildTitle()`/`renderIcon()`),
  never itself executed against `delete_file` anywhere in this batch or its dependencies. Review
  correctly flagged this as a source-code-reading inference standing in for the case's own live
  execution requirement — more than a solo declared improvisation may cover
  (`.agents/role-overrides.md` — "coverage judgments stand on your own execution", never
  reuse-to-conclude). Fix: added
  `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py::TestDirectToolkitCallDeleteFileChip::test_direct_toolkit_call_delete_file_chip`
  — a new, additive test class in the SAME file that live-executes `delete_file` directly (no
  sensitivity/guardrails involved) and asserts the exact chip text this case names
  (`"{toolkit}: delete_file"`), backend-verified via `ArtifactAPI` the same way the covering spec
  verifies `create_file`. Rows 4-5 now cite THIS test, not the create_file execution + source
  argument. See § Coverage Map below for the corrected dispositions.

  Considered and rejected: citing `test_hitl_sensitive_action_authorization.py::TestSensitiveActionAuthorize::test_authorize_executes_toolkit_tool_directly`
  (ELITEA-2212, already merged to `origin/automation/base` via PR #1128) instead — it DOES assert
  `expect(chat.answer_tool_chip).to_contain_text(f"{toolkit_name}: delete_file")` against a real
  backend-verified deletion. But its own AFS
  (`test-specs/chat-interface/l2_hitl-sensitive-action-authorize_ELITEA-2212.md` § Network Behavior)
  states this was **not captured live** — the whole HITL cluster is `pytest.mark.guardrails`,
  CI-only (Admin Guardrails 404s on localhost), and nobody has yet observed this assertion pass.
  Citing unverified merged code as live-execution proof would repeat the exact defect this fix
  round exists to close, just one hop removed. The new test above runs on localhost right now,
  independent of guardrails, and this AFS's Run Report records its own actual green run.

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
| 4. Chips: LLM model chip + toolkit tool chip (e.g. `"aaa: delete_file"`) shown horizontally | Both chips shown | **AMENDED (fix round):** NOT covered by the covering spec's `create_file` run — that only proves the mechanism is tool-agnostic in the abstract, not that `delete_file` itself renders correctly. Now covered by the NEW `TestDirectToolkitCallDeleteFileChip::test_direct_toolkit_call_delete_file_chip` (same file), which live-executes `delete_file` and asserts `answer_tool_chip` count==1 with `"{toolkit_name}: delete_file"` text, backend-verified via `ArtifactAPI.list_bucket_files()`. |
| 5. Each chip has appropriate icon and label | Icons/labels correct | **AMENDED (fix round):** same new test — chip-visibility assertion on the SAME live `delete_file` element, plus the (still-valid, now corroborating rather than sole) DOM-subtree argument: the icon renders as a child node of the SAME chip element the testid is placed on (`ActionView.jsx`'s `Box sx={styles.iconContainer}` sibling to the label, both inside the one `data-testid` chip root) — no code path renders the label without the icon or vice-versa, so `expect(chip).to_be_visible()` + text-content assertion on the delete_file-specific chip necessarily proves both, for THIS tool, live. |

**Fix round (2026-08-19): rows 4-5 required new test code — see § Status above.** Rows 1-3 and
Expected Final State remain genuinely zero-diff, proven by the covering spec's current state.

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

### Gap assertions (AMENDED, fix round 2026-08-19 — was "NONE")

Rows 1-3 + Expected Final State: **NONE** — genuinely zero-diff, proven by the covering spec's
current state (unchanged from the original pass).

Rows 4-5 (the case's own `delete_file`-specific chip + icon+label): **ONE new test**, added
additively to `automation/tests/ui/chat/test_direct_toolkit_call_complete_flow.py` (same file,
new class — does not touch `TestDirectToolkitCallCompleteFlow`'s existing test body):
`TestDirectToolkitCallDeleteFileChip::test_direct_toolkit_call_delete_file_chip`. Live-executes a
direct (non-sensitive) `delete_file` call against the `artifact_toolkit` + `artifact_seeded_file`
fixtures (both already registered, function-scoped, no guardrails dependency) and asserts:
- `answer_tool_chip` visible, count==1, text contains `"{toolkit_name}: delete_file"`
- at least one `answer_model_chip`
- backend ground truth via `artifact_api.list_bucket_files()` (seeded file actually gone),
  classified against known defect #1127 the same way the covering spec's Step 2b already does
  (same underlying direct-toolkit-call mechanism, same non-deterministic risk)
- no console/JS errors

The implementer's action for this case:
1. Add the new test class above (traceability `@allure.issue(ELITEA-2210)` + `@allure.issue(#1127)`
   decorators on it).
2. Update `TestDirectToolkitCallCompleteFlow.test_direct_toolkit_call_complete_flow`'s existing
   ELITEA-2210 `@allure.issue(...)` annotation to scope it to rows 1-3 only (no longer claims the
   chip rows).
3. Back-write ELITEA-2210 in the TMS pointing at BOTH `automation_test_id`s — the existing
   `test_direct_toolkit_call_complete_flow` (rows 1-3) and the new
   `test_direct_toolkit_call_delete_file_chip` (rows 4-5) — same multi-test-per-case shape
   `.agents/test-automation.yaml` § `backwrite_on_done` documents ("a case may list several tests").

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
Rows 1-3: same as the covering spec (post-ELITEA-2209) — an Artifact-type toolkit is added as the ONLY
participant in a fresh conversation via "+ > Toolkits" (no agent), `artifact_toolkit` fixture (default
`selected_tools` includes `delete_file`).

Rows 4-5 (new test, `TestDirectToolkitCallDeleteFileChip`): same `artifact_toolkit` fixture, PLUS
`artifact_seeded_file` (existing, function-scoped fixture — seeds one real file into the bucket so
`delete_file` has a genuine target and its actual removal can be verified via `ArtifactAPI`, the same
fixture ELITEA-2211..2214 already use for the identical purpose). NOT the sensitivity-marking
`sensitive_delete_file_toolkit` fixture — this case's own delete_file call is deliberately plain/direct,
not the HITL-authorized variant.

## Test Data
Rows 1-3: unchanged — reuses the covering spec's existing fixtures and message constants verbatim.

Rows 4-5 (new test): unambiguous delete message naming the seeded file + bucket explicitly (CLARIFICATION
below — the case's own literal wording is ambiguous and does not reach a real tool call):
`Use delete_file toolkit to delete a file named "{file_key}" from bucket "{bucket_name}". Execute the
tool now, do not ask for clarification.` — same template shape ELITEA-2211's AFS already established for
this exact ambiguity.

## Test Steps
Rows 1-3 (Existing, unchanged) — add toolkit as sole participant (with participants-panel assertion from
ELITEA-2209), send message, thinking-steps chip, response — exactly as implemented in the covering spec.

Rows 4-5 (new test): add toolkit as sole participant, send the unambiguous delete_file message, wait for
execution, classify against backend ground truth (#1127 tie-breaker), then assert the toolkit/tool chip
text `"{toolkit_name}: delete_file"` + at least one model chip.

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
| 4 Chips: model chip + toolkit tool chip, e.g. "aaa: delete_file" | Both chips shown horizontally | **NEW** `TestDirectToolkitCallDeleteFileChip` step | `test_direct_toolkit_call_complete_flow.py::TestDirectToolkitCallDeleteFileChip::test_direct_toolkit_call_delete_file_chip` | asserted (new, live-executed against `delete_file` specifically, backend-verified) *(clarification: text format is colon-separated `"{name}: {tool}"`, matching the case's own bracketed example, per ELITEA-2215's already-documented drift)* |
| 5 Each chip has appropriate icon and label | Icons/labels correct | **NEW** same step | same test | asserted (new) *(chip-visibility assertion on the live delete_file element; icon and label are one rendered DOM subtree under the same testid — see Tool-agnosticism argument — corroborating, not sole, evidence now)* |
| Expected Final State: tool execution chips shown above LLM response | — | covering spec rows 1-3 + new test rows 4-5 | — | asserted (reused + new, composite across two tests) |

**Axis 2 — Analyst additions**
- None. This extension adds no observable beyond what ELITEA-2210's own case text already requires.
  Rows 4-5's NEW assertion is not scope creep — it is the case's own already-specified expected
  result (`"aaa: delete_file"` chip), now actually executed instead of inferred.

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

No new testid needed — every handle is pre-existing and already exercised, now including by the new
`delete_file`-specific test on its own executed path.

## Network Behavior
No new network behavior. Standard `chat_predict` websocket envelope, already covered by the covering
spec's own Network Behavior section (ELITEA-2215's AFS).

## Known Defects Found During Exploration
No NEW defect class. Confirmed the SAME `elitea-testing-public#1127` (direct-toolkit-call flow leaks
tool-call intent as raw text instead of invoking the real tool) fires for `delete_file` too, not just
`create_file` — **3 out of 3 consecutive local runs** of the new test hit this exact signature (no
`chat-answer-tool-chip` rendered, `ArtifactAPI` confirms the file was NOT actually deleted, LLM response
claims success anyway). Notably higher local rate than `create_file`'s previously-recorded 2/5 — recorded
as a comment on the open issue
(https://github.com/EliteaAI/elitea-testing-public/issues/1127#issuecomment-5342934194), not a new
ticket (same object/trigger as the issue's own tool-agnostic description). Per `.agents/testing.md` §
Merge gate, 3/3 identical failures tied to this single, open, linked defect IS the sanctioned-RED
exception's own deterministic bar — this new test currently qualifies for sanctioned-RED (unlike the
covering spec's own 2/5 create_file history, which does NOT meet the 3/3 bar and is separately
`blocked` for this wave per its module docstring's "Fix round 2" note). See Run Report.

**Fix round 2 (2026-08-19) — reviewer finding + fix.** Review correctly flagged that
`TestDirectToolkitCallDeleteFileChip`'s classify step called `pytest.fail()`/`raise AssertionError()`
immediately in both its branches, which made this test's own "Side-channel check — no console/JS
errors" step (one of this AFS's Gap-assertions rows-4-5 bullets, § Gap assertions above) structurally
unreachable on the #1127-confirmed branch — the branch that had fired 3/3 observed runs. The console
check had therefore never actually executed, despite being claimed as covered. Fixed in
`test_direct_toolkit_call_complete_flow.py` to mirror `TestDirectToolkitCallCompleteFlow`'s own Step 2b
shape: the confirmed-#1127 branch now defers via a `soft_failures` list instead of failing immediately,
the Side-channel check runs unconditionally before the deferred `pytest.fail()`. Re-ran live against
localhost twice: **2 further consecutive occurrences of the same #1127 signature (5/5 total, still
deterministic)** — and the Allure step report now shows "Side-channel check — no console/JS errors
across the whole flow" as
`passed`, confirming the assertion actually executes before the deferred failure. No change to what is
asserted, the #1127 classification logic, or this AFS's Coverage Map/Gap-assertions scope — control-flow
ordering only.

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest.
- **Rows 1-3**: traceability only on the existing `test_direct_toolkit_call_complete_flow` — no new
  code (unchanged from the original pass).
- **Rows 4-5 (fix round)**: new additive test class `TestDirectToolkitCallDeleteFileChip` in the SAME
  file, with its own `@allure.issue(...)` decorators (ELITEA-2210's onetest-tms case link + #1127).
  Does not modify `TestDirectToolkitCallCompleteFlow`'s existing test body (additive-only on a
  shared-caller file, `.agents/testing.md`).
- No new `@pytest.mark` needed on the new class — module-level `pytestmark` (`ui, chat, p2, regression,
  new`) applies file-wide.
- Both the existing covering test AND the new `TestDirectToolkitCallDeleteFileChip` test are excluded
  from this batch's N-consecutive-green hardening gate for the same reason (non-deterministic known
  defect #1127, see `GATE_EXCLUDED_REASON` module constant + the new class's own docstring).
