# Test Case: Chat – Conversation Rename – Tooltip Validation Message Content

## Metadata
- **TMS ID**: ELITEA-2111
- **Linked Story**: none (case `requirements: []`)
- **Priority**: lextend (case frontmatter says `priority: medium`, which maps to `l3`; filename
  prefix replaced per spec-format.md's rule that `extend-existing` outcomes use `lextend_`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids`, DEV backend; project "Elitea Testing Team", `projectId=471`)
- **User set**: `${TEST_USER}` — localhost `auth_state`/`VITE_DEV_TOKEN` bypasses login
- **Analyst**: qa-engineer (agent, combined analyst+implementer slot), batch `chat-remaining-w03`
- **Status**: **extend-existing** — case executed live end-to-end (all 5 steps + precondition
  observed against the running product, `conversation id=420` "Review attached documents", edit
  cancelled afterward so no persisted mutation). Zero product defects, zero case-text drift — the
  case's own expected tooltip string matches `ConversationNameWarningMessage` **verbatim**,
  character-for-character, confirmed both by source read and live DOM read.
- **family_afs**: false — this is a single-case extension, not a new parameter-table family.

## Overlap check vs existing automation

**Covering spec**:
`automation/tests/ui/chat/test_conversation_rename_invalid_chars_and_recovery.py` (merged onto
this batch's own trunk `tests/batch-chat-remaining-w03`, commit `db9a08aa` — eligible per the
MERGED-TARGET rule: "extend-existing may target a spec merged to `origin/automation/base` **or
already on this batch's trunk**"). Its own AFS:
`test-specs/chat-interface/l3_conversation-rename-invalid-chars-leading-space-and-recovery_ELITEA-2110_2112_2113.md`
— read in full before this run, along with the merged test file and
`ConversationItem.jsx`/`src/common/constants.js` source.

**What the covering spec already proves, verbatim, for ELITEA-2111's own expected results:**
- `test_rename_checkmark_inactive_for_invalid_input_shows_tooltip` (parametrized, ELITEA-2110 row)
  ALREADY asserts, for a charset-invalid name: hover the confirm checkmark → tooltip appears with
  the **exact** `ConversationNameWarningMessage` string (byte-for-byte the same message ELITEA-2111
  quotes) → `data-disabled == "true"` → click is a genuine no-op (no PUT, input stays open,
  persisted name unchanged). This is ELITEA-2111 steps 2–4 in full, just with a different literal
  invalid string (`"HI Chat$$%"` there vs `"$ % @"`-flavoured chars named in this case's Test Data
  table) — source-confirmed (`ConversationNameRegExp`, character-class-based) and live-confirmed
  this session (below) that the mechanism does not care WHICH disallowed characters appear; ONE
  static message fires for any regex-failure reason.
- `test_rename_recovers_and_saves_after_invalid_value_replaced` (ELITEA-2113) ALREADY asserts, for
  invalid→valid recovery: after replacing an invalid name with a fully valid one,
  `data-disabled == "false"` AND (explicitly, not inferred) `get_conversation_name_confirm_tooltip_text(timeout=1500) == ""`
  — i.e. the tooltip is confirmed GONE, not merely assumed absent from the enabled state. This is
  ELITEA-2111 step 5 in full ("Tooltip disappears; checkmark becomes active").

**What ELITEA-2111 demands that the covering spec does NOT yet assert:** nothing structurally new.
The one gap is **data fidelity to this case's own literal test-data hint** ("name with $ % @
characters") — the covering spec's existing charset-invalid row uses a different invalid string
(`"HI Chat$$%"`, no `@`). Per source (`ConversationNameRegExp` is a character-class check, not an
enumerated blacklist) this makes no mechanistic difference, but per the project's own
reverse-masking guard ("assert against the live contract, not a paraphrase") the honest choice is
to add ONE new parametrize row using characters drawn from this case's own data hint, rather than
silently re-tagging someone else's row. This is the entire Gap assertions section below — a new
parametrize row (genuine new execution) plus a coverage-tag on the already-fully-sufficient
Shape B (ELITEA-2113) test for step 5, with no new assertion code needed there.

**Live re-confirmation this session** (Playwright MCP against `localhost:5173`, conversation
id=420): typed `"Ch$t %@name"` (contains `$`, `%`, `@`) into
`chat-conversation-name-input` → hovered `chat-conversation-name-confirm-button` →
`chat-conversation-name-confirm-tooltip-content`'s text read via DOM
(`textContent`) == the exact case-quoted string, `data-disabled == "true"`. Then replaced with a
valid, changed name (`"Chat name recovered"`) → `data-disabled == "false"`,
`chat-conversation-name-confirm-tooltip-content` no longer present in the DOM at all (element
count 0, not just visually hidden). Edit cancelled (`chat-conversation-name-cancel-button`)
afterward — no persisted mutation to the shared conversation. Console: only the pre-existing,
environment-wide `secrets/secrets/default` 403 noise (documented ambient exclusion,
`_is_known_secrets_403()` in the covering test file) — no new errors.

## Preconditions
- User is logged in (`${TEST_USER}` / dev-auth on localhost).
- At least one conversation exists — the covering test's own `conversation_api.create_conversation()`
  setup satisfies this per row (no separate precondition setup needed; extends the SAME
  parametrized test method for the new row, and the SAME already-passing Shape B test for step 5).

## Test Data

### generate-per-test (new parametrize row only — reuses the covering test's existing setup/cleanup)
- New invalid name: `"Ch$t %@name"` — drawn from this case's own Test Data hint ("name with $ % @
  characters"), distinct from the existing `"HI Chat$$%"` (ELITEA-2110) and `" ab"` (ELITEA-2112)
  rows so the parametrize table stays non-duplicative.

## Test Steps (delta over the covering spec)

1. **New parametrize row on `test_rename_checkmark_inactive_for_invalid_input_shows_tooltip`**:
   `pytest.param("ELITEA-2111", "Ch$t %@name", id="ELITEA-2111-dollar-percent-at-characters")`
   alongside the existing ELITEA-2110/ELITEA-2112 rows. Runs the SAME method body (Steps 1–4 of
   Shape A, unchanged) against this case's own literal invalid characters:
   - Step 1 (reused): Rename editor opens, pre-filled with current name.
   - Step 2 (reused, this case's own data): clear + type `"Ch$t %@name"`; input value matches
     exactly.
   - Step 3 (reused): hover the checkmark → `chat-conversation-name-confirm-tooltip-content` text
     equals `ConversationNameWarningMessage` verbatim; `data-disabled == "true"`.
   - Step 4 (reused): click is a no-op — no PUT fires, input stays open, persisted name unchanged
     (via `conversation_api.get_conversation(id)["name"]`).
2. **Coverage-tag only** on `test_rename_recovers_and_saves_after_invalid_value_replaced`
   (ELITEA-2113): add a third `@allure.issue(...)` decorator referencing ELITEA-2111's TMS case
   link, alongside the existing ELITEA-2113 one. No new assertion code — its existing Step 3
   already asserts exactly ELITEA-2111's step 5 (`data-disabled == "false"` AND
   `get_conversation_name_confirm_tooltip_text(timeout=1500) == ""` after replacing an invalid
   name with a valid one), data-value-agnostically (the assertion is against the CURRENT state,
   not tied to which invalid string preceded it).

## Expected Results
- Hovering the inactive checkmark while the input holds a name containing `$ % @` (or any other
  regex-disallowed character) shows a tooltip whose text is byte-for-byte
  `"The chat name should be 3 to 64 characters long. It can include letters (a-z, A-Z), numbers
  (0-9), underscores (_), brackets ([]), parentheses (()), dots (.), hyphen(-), and spaces. Please
  note that the first character should not be a space."`
- The checkmark stays `data-disabled="true"` for the whole time invalid characters are present.
- Replacing the invalid name with a valid one (≥3 chars, changed from the original) makes the
  tooltip disappear (element count 0) and the checkmark flip to `data-disabled="false"`.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | covering spec `auth_state` fixture | fixture | asserted (reused) |
| Precondition: ≥1 conversation exists | — | covering spec `conversation_api.create_conversation` | covering spec setup | asserted (reused) |
| Step 1 Navigate/hover/3-dot/Edit → editable | Conversation name is editable | new parametrize row, Shape A step 1 (reused method body) | `chat-conversation-name-input` visible + pre-filled value | asserted |
| Step 2 Clear + type invalid name ($ % @ chars), hover inactive check icon → tooltip appears | Tooltip appears near the input field | new parametrize row, Shape A steps 2–3 | tooltip element visible via testid locator after real hover | asserted |
| Step 3 Tooltip text reads the exact quoted string | Tooltip shows exact expected text | new parametrize row, Shape A step 3 | `chat-conversation-name-confirm-tooltip-content` text == `ConversationNameWarningMessage`, exact string match | asserted |
| Step 4 Checkmark remains inactive while invalid chars present | Checkmark stays inactive | new parametrize row, Shape A step 3 | `data-disabled == "true"` | asserted |
| Step 5 Remove invalid chars, replace with valid name ≥3 chars → tooltip disappears; checkmark active | Tooltip disappears; checkmark becomes active | ELITEA-2113 test, existing Step 3 (coverage-tag only, no new code) | `data-disabled == "false"` + `get_conversation_name_confirm_tooltip_text(timeout=1500) == ""` | asserted (reused verbatim) |
| Expected Final State: exact tooltip text; checkmark activates after valid input | — | rows above | rows above | asserted (composite) |
| Pass/Fail criteria | — | rows above | rows above | asserted (composite) |

Disposition key: `asserted` / `already-covered` / `clarification` / `blocked` / `out-of-scope`.

### Axis 2 — Analyst additions
None. Every case element maps 1:1 to an existing or minimally-extended assertion; no additional
observable was added beyond what ELITEA-2111's own case text requests.

## Cleanup
New parametrize row reuses the covering test's existing `try`/`finally`
(`conversation_api.delete_conversation(conv_target_id)`) — no additional cleanup. Step 5's
coverage-tag addition adds no new test execution, so no additional cleanup there either.

## Concrete Handles (discovered during exploration)
All handles are pre-existing testid-only `LocatorDescriptor`/class-constant fields already used by
the covering spec — no new testids required for this case.

| Element | Testid | Provenance | Notes |
|---|---|---|---|
| Conversation-rename inline input | `chat-conversation-name-input` | on `main` ✓ (ELITEA-2099, `EliteaAI/EliteaUI@ff56e29d`) | `ChatPage.conversation_name_input` |
| Conversation-rename confirm (checkmark) button | `chat-conversation-name-confirm-button`, `data-disabled="true"/"false"` | on `main` ✓ (same commit) | `ChatPage.conversation_name_confirm_button` / `is_conversation_name_confirm_enabled()` |
| Conversation-rename validation tooltip content | `chat-conversation-name-confirm-tooltip-content` | on `automation/testids` only (awaiting human promotion to `main`) — added ELITEA-2110/2112/2113, `EliteaAI/EliteaUI@888dac13` | `ChatPage.get_conversation_name_confirm_tooltip_text()` |
| Conversation-rename cancel button | `chat-conversation-name-cancel-button` | on `main` ✓ (commit `ff56e29d`) | `ChatPage.conversation_name_cancel_button` |

Fresh provenance check this session (`cd ../EliteaUI && git fetch origin` first):
```
$ git grep -in -- "chat-conversation-name-confirm-tooltip-content" origin/main -- src/
(no output — NOT on main)
$ git grep -in -- "chat-conversation-name-confirm-tooltip-content" origin/automation/testids -- src/
origin/automation/testids:src/[fsd]/features/chat/conversation-list/ui/conversations/ConversationItem.jsx:516:          slotProps={{ popper: { 'data-testid': 'chat-conversation-name-confirm-tooltip-content' } }}
```

## Network Behavior
Same as the covering spec — no new network behavior. The new parametrize row asserts NO PUT fires
on the no-op click (`capture_requests_matching("/conversation/prompt_lib", method="PUT")` staying
empty); step 5's coverage-tag reuses the existing PUT-on-successful-save assertion from ELITEA-2113
unchanged.

## Known Defects Found During Exploration
None. Case text and live product match exactly — no clarification needed (contrast with the
sibling `_surface.md` finding for ELITEA-2099's stale menu-item label, which does not apply here).

## Blocked Steps
None.

## Automation Hints
- Framework: Playwright + pytest. **Artefact is an edit to the covering spec**
  (`test_conversation_rename_invalid_chars_and_recovery.py`), not a new file:
  1. Add `pytest.param("ELITEA-2111", "Ch$t %@name", id="ELITEA-2111-dollar-percent-at-characters")`
     to the existing `@pytest.mark.parametrize("case_id, invalid_name", [...])` list on
     `test_rename_checkmark_inactive_for_invalid_input_shows_tooltip` — pure addition, the two
     existing rows (ELITEA-2110, ELITEA-2112) stay byte-identical.
  2. Add a third `@allure.issue(...)` decorator to that same method, and a second one to
     `test_rename_recovers_and_saves_after_invalid_value_replaced`, both referencing ELITEA-2111's
     TMS case link — this is the coverage-tag chain for step 5, since that method's existing Step 3
     assertion is already exactly what step 5 needs (data-value-agnostic).
  3. Verify additive-only: `git diff <covering-spec> | grep -E '^-[^-]'` → empty (no removed line
     among the pre-existing rows/decorators).
  4. Run the FULL extended parametrized test (all 3 rows) + the Shape B test, to prove the
     additive-only contract holds for the original 2 rows too.
- `chat-conversation-name-confirm-tooltip-content` is `automation/testids`-only as of this session
  — same promotability caveat the covering spec's own AFS already recorded; nothing new to flag.
