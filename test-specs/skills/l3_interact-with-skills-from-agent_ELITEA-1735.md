# Test Case: Interact with Skills from Agent

## Metadata
- **TMS ID**: ELITEA-1735
- **Linked Story**: none
- **Priority**: l3 (medium, per case)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399), model: Anthropic Claude 4.5 Sonnet
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: defect-found — see Known Defects. Skill creation, attachment, and
  explicit `~mention` invocation (steps 1–3, 5–6) are ready-for-automation; step 4
  (plain-message non-invocation) has a confirmed intermittent product defect
  (github.com/EliteaAI/elitea-testing-public/issues/38). Recommend automating with
  `expect.soft()` around the step-4 assertion per project's isolated-defect policy
  (`.agents/profile.md` § Bug filing), ticket linked, rest of the flow hard-asserted.

## Preconditions
- User is logged in (on localhost, `auth_state` fixture skips login).
- A project is selected/accessible (`Private`, id `399` in this run).
- Skills and Agents sections are available in the project.

## Test Data

### generate-per-test (in test setup, cleaned up in its own teardown)
- Skill 1 name: kebab-case, e.g. `elitea-1735-skill-uppercase` — **must be
  lowercase letters/digits/hyphens only** (same client-side Skill-name validation
  documented for ELITEA-1737 — see `.agents/memory/qa-engineer/skill_form_and_export_import_quirks.md`).
- Skill 1 description: any non-empty string.
- Skill 1 instructions: `"Always respond with the exact text the user asked for,
  but convert the ENTIRE output to UPPER CASE letters. Do not use any lowercase
  letters in your response."`
- Skill 2 name: e.g. `elitea-1735-skill-underscore`.
- Skill 2 instructions: `"Always respond with the exact text the user asked for,
  but replace every space between words with an underscore character _ so the
  output is underscore_delimited like_this."`
- Agent name: e.g. `elitea-1735-skills-agent`; description and a short generic
  instructions string (agent instructions do not need to mention skills — skill
  availability/mention behavior is driven by the platform, not by the agent's own
  instructions field).
- Chat prompts: any short, distinct plain-language request per turn (e.g. "Tell
  me a fun fact about <topic>") — vary wording per attempt so response content
  itself doesn't accidentally satisfy the uppercase/underscore check by coincidence.

No `reuse-existing` or shared fixture applies — this is a fresh-state flow (2
skills + 1 agent, all created and torn down within the test).

## Test Steps

1. Navigate to `${BASE_URL}/skills/create`. Fill Name (`skill-name-input`),
   Description (`skill-description-input`), and Instructions
   (`skill-instructions-editor-content`, a CodeMirror editor — use
   `press_sequentially`/`type`, not `fill`, so React state updates) with the
   Skill 1 uppercase-instruction data above. Click Save
   (`skill-save-button`).
   - **Verify**: a "There are unsaved changes. Are you sure you want to leave?"
     nav-blocker dialog appears immediately after Save (same quirk as
     ELITEA-1737) — confirm it via `alert-dialog-confirm-button` testid. URL
     settles on `/skills/all/{id}`; note Skill 1's ID (e.g. `66`).
2. Repeat step 1 for Skill 2 with the underscore-instruction data. Note Skill
   2's ID (e.g. `67`).
   - **Verify**: same nav-blocker/Save flow; Skill 2 saved with a distinct ID.
3. Navigate to `${BASE_URL}/agents/create`. Fill Name
   (`agent-name-input`), Description (`agent-description-input`), and
   Instructions (`agent-instructions-input`) with generic agent data. Click
   Save (`agent-save-button`).
   - **Verify**: navigates to `/agents/all/{agent-id}?destTab=configuration...`;
     note the Agent ID (e.g. `4565`).
4. On the agent detail page, expand the **Skills** accordion section (heading
   text "Skills"). Click the **add-skill button** (a small icon-only button,
   **no `data-testid` and no accessible name in current DOM** — located as
   the first button inside the Skills section's header row; recommend filing
   an `add-data-testid` request, e.g. `agent-add-skill-button`, before
   automating this step). A "Mention skill"-style popper opens listing
   available skills by name.
   - **Verify**: popper lists both Skill 1 and Skill 2 by their actual names
     (menuitem role, accessible name = skill name).
5. Click the Skill 1 menuitem to attach it, then repeat step 4–5 to attach
   Skill 2.
   - **Verify**: after each attach, the Skills section counter updates
     ("1/5 skills added." → "2/5 skills added.") and a card renders per
     attached skill showing its name and `base` version. **Attachment is
     immediate/auto-saved via API** — confirmed via network trace:
     `PATCH /api/v2/elitea_core/skill/prompt_lib/{project}/{skill-id}` →
     `201 Created` fires on each attach; the page-level `Save`/`Save As
     Version` button stays disabled throughout (no explicit agent-level save
     needed for skill attachment).
6. In the agent's embedded chat panel, type a plain message with **no `~`
   mention** (e.g. "Tell me a fun fact about cats.") into
   `chat-message-input` and press Enter (or click `chat-send-button`).
   - **Verify (expected per case)**: response text uses normal sentence
     case, no forced ALL-CAPS, words separated by spaces (not underscores).
   - **Known defect** — see Known Defects below; this assertion is flaky.
7. Clear the chat (button inside the "Clear the chat" tooltip group, no
   stable testid observed — located via accessible name `clear the chat`).
   Click into `chat-message-input`, type `~` using `slowly`/`press_sequentially`
   (NOT `fill` — see Known Defects/quirks note on the mention chip), select
   Skill 1 from the "Mention skill" popper's menuitem (accessible name =
   skill's own name, e.g. `elitea-1735-skill-uppercase`), then append a
   prompt (again via `slowly`/`press_sequentially` — `fill()` overwrites the
   inserted mention chip since it replaces the whole textbox value rather
   than inserting at the cursor). Send.
   - **Verify**: response text is entirely UPPER CASE (all letters
     uppercased, e.g. `"ELEPHANTS ARE THE ONLY MAMMALS THAT CANNOT
     JUMP!..."`). The chat's visible "Thinking" trace (expand the
     "Thought for N secs" toggle) shows the model explicitly recognizing the
     `~<skill-name>` mention and invoking `load_skill` for it — useful signal
     if this step needs debugging, not something to assert on directly (it's
     an internal reasoning trace, not a stable contract).
8. Clear the chat again. Repeat step 7's mention flow with Skill 2 instead
   (mention `elitea-1735-skill-underscore`, different prompt text, e.g.
   "Tell me a fun fact about penguins.").
   - **Verify**: response text has every space between words replaced with
     `_` (e.g. `"Penguins_can_drink_saltwater_because_they_have_a_special_
     gland_above_their_eyes_that_filters_out_the_salt_from_their_
     bloodstream."`) and is NOT upper-cased.

## Handles Reference

| Element | testid / locator | Notes |
|---|---|---|
| Skill Name field | `skill-name-input` | kebab-case validation |
| Skill Description field | `skill-description-input` | |
| Skill Instructions editor | `skill-instructions-editor-content` | CodeMirror; use `press_sequentially` |
| Skill Save button | `skill-save-button` | |
| Nav-blocker confirm | `alert-dialog-confirm-button` | fires on every Save from create form |
| Agent Name field | `agent-name-input` | |
| Agent Description field | `agent-description-input` | |
| Agent Instructions field | `agent-instructions-input` | |
| Agent Save button | `agent-save-button` | |
| Agent add-skill button | **none** — but has a stable accessible name: `getByRole('button', { name: 'Skill', exact: true })` (BaseBtn renders a plus icon + visible "Skill" text label) | **implementer-amendment (ELITEA-1735 Phase 2):** original analyst note said "role/position only, no accessible name" — re-verified against `SkillMenu.jsx` source and live DOM; the button's accessible name IS "Skill", stable and unambiguous (distinct from the Toolkits section's "+ Toolkit" button, name "Toolkit"). No `add-data-testid` request needed. |
| Skill-attach popper item (add-skill flow, step 4-5) | Real MUI `MenuItem`, `role="menuitem"`, accessible name = skill name, `data-testid="toolkit-menu-item"` (generic/shared name, reused from the Toolkits popper) | Confirmed via `UnifiedDropdown.jsx` — `getByRole('menuitem', { name: 'elitea-1735-skill-uppercase' })` works as originally documented. |
| Chat "~mention" popper item (step 7-8) | **implementer-amendment (ELITEA-1735 Phase 2):** the original row here claimed the same "ARIA `menuitem`" handle for this popper too — that is **incorrect for this popper**. `MentionSkillList.jsx` / `MentionToolItem.jsx` (the "Mention skill" header popper triggered by typing `~` in chat) renders items as plain `<Box>` divs with **no ARIA role and no `data-testid`** — an entirely different, unrelated component from the add-skill-to-agent popper above (which does use real `role="menuitem"`). Automated via text-based lookup scoped under the "Mention skill" header container: `page.get_by_text("Mention skill", exact=True).locator("xpath=ancestor::div[2]").get_by_text(skill_name, exact=True)`. | corrects the Handles Reference row that conflated the two distinct "Mention skill"-labeled poppers used in this case (add-skill-to-agent vs. chat `~mention`). |
| Chat message input | `chat-message-input` | mention-aware; use `press_sequentially`, never `fill()`, when a `~mention` chip must be preserved |
| Chat send button | `chat-send-button` | |
| Clear-the-chat button | accessible name `clear the chat` (no testid) | |
| Skill controls (overflow) menu | `skill-controls-menu-button` | opens VERSION/SKILL grouped menu |
| Delete-skill menu item | `skill-delete-menu-item` | in the SKILL group |
| Agent actions (overflow) menu | `agent-actions-menu-button` | opens VERSION/AGENT grouped menu |
| Delete-agent menu item | `delete-agent-menuitem` | in the AGENT group |
| Delete-confirmation name field | `delete-confirm-name-input` (scope to inner `#name` field) | shared component, used by both skill and agent delete flows |
| Delete-confirmation confirm button | `getByRole('button', { name: 'Delete' })` scoped to the dialog | enabled only once the typed name matches |

## Expected Results
- Skills 1 and 2 are created and saved successfully with distinct IDs.
- The agent is created and both skills attach with `base` version shown on
  each card; attachment persists immediately (API-level auto-save, no
  agent-level Save needed).
- A plain message with no `~mention` should NOT apply either skill's
  formatting — **this is not reliably true; see Known Defects**.
- A message with `~<skill-1-name> <prompt>` returns the prompt's answer
  entirely in UPPER CASE.
- A message with `~<skill-2-name> <prompt>` returns the prompt's answer with
  every space replaced by `_`.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Create Skill 1 (uppercase) | Skill created & saved | Test Step 1 | Skill ID assigned, URL settles on `/skills/all/{id}` | covered |
| Step 2: Create Skill 2 (underscore) | Skill created & saved | Test Step 2 | Skill ID assigned, distinct from Skill 1 | covered |
| Step 3: Create Agent, attach both skills | Agent created, both skills listed attached | Test Steps 3–5 | Skills section shows "2/5 skills added.", both cards render | covered |
| Step 4: Plain message → no skill formatting | Response NOT uppercase, NOT underscore-delimited | Test Step 6 | Response text asserted for absence of forced-uppercase/underscore pattern | **defect** — intermittently fails (1/3 in this run); see Known Defects |
| Step 5: `~skill1 <prompt>` → uppercase | Response entirely UPPER CASE | Test Step 7 | Response text asserted all-caps | covered |
| Step 6: `~skill2 <prompt>` → underscore-delimited | Response uses `_` between words | Test Step 8 | Response text asserted underscore-delimited, not uppercase | covered |
| Test Data: invocation syntax `~skill1`/`~skill2` (case placeholder names) | literal `~skill1`/`~skill2` strings | N/A — **case-text drift**, not a defect | Live syntax is `~<mention>` via an autocomplete keyed on the skill's actual name, triggered by typing `~` | clarification (reverse-masking; case uses generic placeholder names, product correctly uses real skill names as mention targets) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Skill-attach network call (`PATCH .../skill/prompt_lib/{project}/{id}` → `201`) | Confirms attachment is an immediate API-level auto-save, not deferred to agent-level Save — material for correct wait strategy in automation (don't wait on/assert `agent-save-button` state after attaching a skill) |
| Console messages checked after every step | Zero errors observed across all 8 steps; ruled out silent JS failures as an explanation for the intermittent defect |
| `fill()` vs `press_sequentially()` on the mention-aware chat input | `fill()` replaces the entire textbox value, destroying an already-inserted `~mention` chip; this is a load-bearing automation gotcha, not explicit in the case, but any implementer will hit it on first attempt |

## Known Defects

### github.com/EliteaAI/elitea-testing-public/issues/38 — [MAJOR] Agent applies skill formatting to plain (non-invoked) messages intermittently
- **Repro rate**: 1/3 attempts in this run. Plain message "Write one short
  sentence about the weather today." (no `~mention`) returned
  `THE_SUN_IS_SHINING_BRIGHTLY_THIS_AFTERNOON.` — both skills' formatting
  applied simultaneously with no invocation. Two subsequent plain-message
  attempts ("Tell me a fun fact about cats.", "What is the capital of
  France?") returned normal, unformatted prose.
- **Root-cause hint**: the model's own "Thinking" trace (observed during the
  explicit-invocation steps) shows the agent is instructed to scan
  `<available_skills>` and autonomously decide whether to `load_skill` based
  on relevance to the user's message — not gated purely on the `~mention`
  syntax. This makes plain-message behavior a model judgment call rather
  than a deterministic contract.
- **Evidence**: `test-results/screenshots/ELITEA-1735-step4-plain-message-defect.png`,
  `test-results/screenshots/ELITEA-1735-step4-plain-message-normal-attempt3.png`.
- **Automation guidance**: per `.agents/profile.md` § Bug filing (isolated
  defect → `expect.soft()` with ticket linked), assert step 6 (plain message)
  with a soft assertion referencing issue #38, and hard-assert the rest of
  the flow (skill creation, attachment, explicit-mention invocation for both
  skills) which reproduced 100% reliably across all attempts in this run.

## Cleanup

Three entities are created per run: Skill 1 (uppercase), Skill 2 (underscore),
and the Agent that attaches both. All three were deleted live in this run to
confirm the mechanics below.

1. **Delete the Agent first, then the two Skills.** Verified live: deletion
   order does **not** actually matter at the API level — a skill can be
   deleted via `SkillAPI.delete_skill()` / the UI overflow menu **while still
   attached to an agent**, with no dependency error (`DELETE
   .../skill/prompt_lib/{project}/{skill_id}` returned `204 No Content` with
   skill 66 still attached to agent 4565 at the time of deletion). The
   agent's Skills section self-corrects on next load — it silently dropped
   the deleted skill's card and updated the counter from "2/5 skills added."
   to "1/5 skills added." with no console error, no dangling-reference UI
   state. **Recommended order is still agent-before-skills** (delete the
   thing with more attached state first) purely for teardown hygiene/least
   astonishment, not because the API enforces it.
2. **Agent deletion**: via UI overflow menu → "AGENT" group → "Delete agent"
   (`data-testid="delete-agent-menuitem"`) → type-to-confirm dialog (same
   pattern as skills — `data-testid="delete-confirm-name-input"`, inner
   `#name` field) → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` → `204
   No Content`, redirects away from the agent detail page, no console
   errors. **For automated cleanup, prefer the existing `agent_api` fixture**
   (`automation/fixtures/api_fixtures.py`) — `AgentAPI.delete_agent(agent_id)`
   in `automation/api/client.py:452`. A project-level session-scoped safety
   net (`cleanup_autotest_agents_at_end` in
   `automation/fixtures/cleanup_fixtures.py`) already deletes any leftover
   `autotest_`-prefixed agents at session end, but is skipped on localhost
   (no browser-cookie auth) and only catches the `autotest_` naming
   convention — don't rely on it alone; give the agent an `autotest_`-
   prefixed name if you want that safety net to apply, and still delete it
   explicitly in the test's own teardown.
3. **Skill deletion (both Skill 1 and Skill 2)**: via UI overflow menu →
   "SKILL" group → "Delete skill" (`data-testid="skill-delete-menu-item"`) →
   same type-to-confirm dialog pattern → click "Delete". Verified: `DELETE
   /api/v2/elitea_core/skill/prompt_lib/{project}/{skill_id}` → `204 No
   Content` for both skills, no console errors (the immediate follow-up `GET
   .../skill/prompt_lib/{project}/{skill_id}` → `404` seen in the network
   log afterward is an expected stale-refetch artifact of the redirect, not
   a defect). **For automated cleanup, use the existing `skill_api` fixture**
   (`automation/fixtures/api_fixtures.py`) — `SkillAPI.delete_skill(skill_id)`
   in `automation/api/client.py:1227` — mirroring the `clean_skill` fixture
   pattern in `automation/tests/ui/skills/test_skill_management.py:32`
   (list-and-delete-if-exists before the test, delete again in teardown,
   tolerating "already gone" errors). Track both skill IDs from Test Steps 1
   and 2 and delete both.
4. **Recommended teardown fixture shape** (mirrors `clean_skill`): a
   function-scoped fixture that creates the agent + 2 skills via UI in the
   test body, yields their IDs, and in its `finally`/post-yield block calls
   `agent_api.delete_agent(agent_id)` then `skill_api.delete_skill(skill_id)`
   for each skill ID, wrapping each call in its own `try/except` so one
   failed delete doesn't skip the others (same tolerance pattern as
   `clean_skill`'s `_delete_if_exists`).

## Blocked Steps
None — case executed end-to-end; the one blocker encountered (defect above)
does not prevent the remaining steps from completing.
