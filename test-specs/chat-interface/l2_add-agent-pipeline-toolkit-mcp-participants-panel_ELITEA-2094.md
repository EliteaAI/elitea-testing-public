# Test Case: Chat — Create New Conversation with Agent, Toolkit, MCP, and Pipeline — Verify All Participants Are Added and Displayed Correctly

## Metadata
- **TMS ID**: ELITEA-2094
- **Linked Story**: [EliteaAI/elitea-testing-public#297](https://github.com/EliteaAI/elitea-testing-public/issues/297) (originating tracking issue)
- **Priority**: l2 (case frontmatter says `priority: high` → 2=high per AFS convention)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via `VITE_DEV_TOKEN` — dev-token user renders as "Test Bot"/"Test!" in the UI)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live (all 11 steps observed, both explicit and implied preconditions probed), one real product defect found and filed (#684). No AFS-blocking gaps; a data/environment gap (default project has zero pipelines/MCPs) and a locator/testid gap (plus-menu entity pickers have no testids) are both flagged below with a concrete path to resolve, not left as silent omissions.

## Overlap check vs existing automation (required before classifying `ready-for-automation`)

`automation/tests/ui/chat/test_chat_interface.py` was read in full before this run. Its module
docstring claims "Includes participants panel tests (TC-CHAT-014 to 016)" but **no test methods
for TC-CHAT-014/015/016 exist in the file** (confirmed via `grep` — the docstring reference is
stale/orphaned; the actual participants-adjacent tests present are `TestHashSearch`'s
`test_hash_search_participants` / `test_add_participant_via_hash_search`, TC-CHAT-017/018, which
exercise the **`#` mention** flow, not the **`+` plus-menu → Agents/Pipelines/Toolkits/MCPs**
flow this case is about). No other test file in `automation/tests/ui/` adds an Agent + Pipeline +
Toolkit + MCP to the same conversation, checks icon distinctness, checks for duplicate entries,
or exercises the misconfiguration-warning UI. **This case's core scenario is not covered by any
existing test** — it is a fresh scenario, not a gap-fill.

`automation/pages/chat_page.py` already has substantial, working participant infrastructure that
this AFS's automation should reuse rather than duplicate:
- `add_agent_participant(agent_name_prefix)` — plus menu → Agents → search → select (line ~2066)
- `add_toolkit_participant(toolkit_name)` — plus menu → Toolkits → search → select-by-click
  (line ~2110) — **note**: case step 4 says "enable a toolkit via toggle"; live behavior
  confirmed the toolkit row IS a switch (`role="switch"`) that must be toggled, not merely
  clicked — `add_toolkit_participant`'s existing implementation clicks the `li[role="menuitem"]`
  row itself (not the switch), which happens to also toggle the switch as a side effect of the
  row's own click handler (confirmed live: clicking the row toggled a `alita (artifact)` toolkit
  on). Both approaches work today; no change needed to the existing method.
- `is_participants_badge_visible(section=...)`, `open_participants_popover(section=...)`,
  `PARTICIPANTS_BADGE`, `PARTICIPANTS_BADGE_BUTTON`, `participants_popper`, `PARTICIPANT_ROW`,
  `PARTICIPANT_REMOVE_BUTTON`, `remove_agent_participant(agent_id)` — all already accept/return
  a `section` parameter documented as "agents" (default), "pipelines", "toolkits", or "mcp" —
  the docstrings explicitly note "this case only ever exercises 'agents'" for the prior case
  (ELITEA-1793) that added them. **ELITEA-2094 is the first case to actually exercise the other
  three sections** — confirmed live this run that `chat-participants-badge-pipelines`,
  `chat-participants-badge-toolkits`, and `chat-participants-badge-mcp` (singular "mcp", not
  "mcps" — see § Concrete Handles) all resolve exactly as the existing generic methods predict.

**Gap**: no `add_pipeline_participant()` or `add_mcp_participant()` method exists yet. Both are
straightforward siblings of `add_toolkit_participant()` (MCPs are also toggle/switch rows;
pipelines are click-to-select rows like agents) — see § Automation Hints for the exact shape.

**Dedup verdict (Rule 6): no overlap.** This is `ready-for-automation`, not `extend-existing` —
the existing methods are reusable building blocks, not a covering test to extend.

## Preconditions
- User is logged in to the Elitea platform (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`).
- **Available agents, pipelines, toolkits, and MCPs exist in the project** — confirmed live this
  run this precondition **does NOT hold for the suite's default project**
  (`${ELITEA_PROJECT_ID}` = `399` / "Private" — confirmed via `automation/.env.test`): that
  project has **zero pipelines** (`/pipelines/all` shows "No pipelines yet") and **zero MCPs**
  (plus-menu → MCPs → "No MCPs available"; `/mcps/create` redirect on the MCPs nav link, itself
  a sign zero exist). It does have agents and toolkits. A second project checked, "UI Testing"
  (id `400`), has 1 pipeline but still zero MCPs. A third, "Elitea Testing Team" (id `471`), has
  all four entity types richly populated (confirmed live: dozens of agents/pipelines, 1 MCP,
  ~19 toolkits) and is what this exploration used. **This is a real test-data gap for
  automation** — see § Automation Hints for the recommended fix (seed via API into the default
  project rather than depend on the shared, mutable `471` fixtures).

## Test Data
### reuse-existing
- `${TEST_USER}` — dev-token auth, no explicit login needed on localhost.
- Message text: `"Hi"` (per case's own Test Data table).

### generate-per-test (seed via API into the test's own project, clean up in the test's own teardown)
- One agent (`AgentAPI.create_agent(...)`).
- One **executable** pipeline (`PipelineAPI.create_pipeline_with_llm_node(...)` — NOT the bare
  `create_pipeline(...)`, which produces an empty pipeline with no nodes; NOT a pipeline that
  mirrors the broken "HelloPipeline" fixture found live in project 471 — see § Known Defects).
- One toolkit (any type; `ToolkitAPI.create_artifact_toolkit(...)` is cheapest — no external
  credential needed).
- One **misconfigured** MCP, to exercise case step 11 honestly (see § Coverage Map row for step
  11) — `ToolkitAPI.create_remote_mcp_toolkit(name, description, url="<unreachable-url>",
  tools=[])` — a remote MCP toolkit pointed at an unreachable/invalid URL reproduces the same
  "Server is disconnected!" misconfiguration state confirmed live against the project-471 "asd
  (mcp)" fixture (see § Concrete Handles / § Known Defects for that fixture's exact warning
  text). This is more reliable than depending on the shared "asd (mcp)" toolkit, which is
  project-471-specific, unowned by this suite, and could be fixed/deleted/renamed by another
  tester at any time.

No `generate-shared-with-cleanup` applies — all four entities are cheap, per-test, and already
have working create/delete API coverage.

## Test Steps

*(Case's own 11 steps, executed live this run against project "Elitea Testing Team" (id `471`)
— chosen because the default `399` project fails this case's own precondition, see above. Two
full passes were run: an initial pass (conversation id `150`, deleted via UI at end of session)
plus a pristine re-verification pass in a fresh conversation for the pipeline defect specifically
— see § Known Defects for why.)*

1. Navigate to Chats and click "+ Chat".
   - **Verify**: new blank conversation opens (`"Hello, Test!"` greeting), `sidebar-create-button`
     becomes `disabled`, and the right-sidebar PARTICIPANTS area shows **no badges at all**
     (confirmed live via `document.querySelectorAll('[data-testid^="chat-participants-badge"]')`
     → empty array — the panel isn't rendered with a "0" state, it's simply absent until the
     first participant is added).
2. Click the `+` icon (`plus-menu-button`), click "Agents", select an agent from the list.
   - **Verify**: `chat-participants-badge-agents` appears (aria-label `"Agents in this
     conversation"`), count `"1"`; the composer's `chat-switch-participant-button` shows the
     agent's name. Confirmed live with agent **"Test Agent"**.
3. Click `+`, click "Pipelines", select a pipeline from the list.
   - **Verify**: `chat-participants-badge-pipelines` appears, count `"1"`; composer button now
     shows the pipeline's name instead of the agent's (the composer button is a single active-
     participant slot, not additive — confirmed live: adding a pipeline after an agent REPLACES
     the composer button's displayed name from "Test Agent" to the pipeline name, while the
     Agents badge itself still independently shows count `"1"`. This nuance isn't stated in the
     case text; flagged as Axis 2 below).
4. Click `+`, click "Toolkits", enable a toolkit via toggle.
   - **Verify**: `chat-participants-badge-toolkits` appears, count `"1"`. Confirmed live with
     toolkit **"alita (artifact)"** — clicking the row (which contains a `role="switch"`) toggles
     it on; no separate confirmation step needed.
5. Click `+`, click "MCPs", enable an MCP via toggle.
   - **Verify**: normally `chat-participants-badge-mcp` (**note singular** — see § Concrete
     Handles) would appear with a healthy count. Confirmed live this run with MCP **"asd (mcp)"**
     that this fixture is itself misconfigured (disconnected) — the badge instead renders with
     `aria-label="Misconfiguration error in mcps"` and an orange/yellow warning-triangle icon
     overlay. This is the case's own step 11 scenario firing early/naturally because the only
     MCP available in the explored project happens to be broken — see step 11 below for the full
     detail popper, and § Test Data for how automation should seed a **healthy** MCP for this
     step specifically (so step 5's own expectation — a clean "toolkit/MCP appears" — is
     satisfied) plus a **separate, deliberately-misconfigured** one for step 11.
6. Verify all four sections are visible in PARTICIPANTS: AGENTS, PIPELINES, TOOLKITS, MCPS.
   - **Verify**: confirmed live — but the case's phrase "PARTICIPANTS panel" does **not**
     correspond to one combined panel with four labelled subsections. It's **four independent
     collapsed badges** stacked vertically in the right sidebar (one per entity type, each with
     its own icon + count), and clicking any one badge opens **its own scoped popper** titled
     with the section name in caps (`"AGENTS"`, `"PIPELINES"`, `"TOOLKITS"`, `"MCPS"` — confirmed
     live via screenshot for all four). This satisfies the case's intent (all four types visible
     and individually inspectable) via a different UI shape than the case's wording implies —
     documented as a `clarification`-flavoured Axis-1 row, not a defect (reverse-masking guard:
     the live product's shape is intentional and correct, the case text just under-specifies it).
7. Verify each participant has a distinct icon (robot for agent, flowchart for pipeline, wrench
   for toolkit, plugin for MCP).
   - **Verify**: confirmed live via screenshot — four visually distinct SVG icons, one per badge
     (a grid/module-style icon for Agents, a share/branch icon for Pipelines, a wrench icon for
     Toolkits, a paperclip icon for MCPs). Icon shapes are close-but-not-literal matches to the
     case's illustrative names ("robot", "flowchart", "plugin") — the case's descriptions are
     approximate/illustrative, not literal SVG specs; distinctness (the actual pass/fail
     criterion) holds.
8. Verify no duplicate entries for any participant.
   - **Verify**: confirmed live two ways: (a) every badge's popper showed exactly one row for the
     one entity added to it (Agents → "Test Agent" ×1, Pipelines → the pipeline ×1, Toolkits →
     "alita" ×1); (b) **stronger signal, Axis 2 addition**: re-opening the Agents picker after
     "Test Agent" was already added showed **"Test Agent" no longer listed at all** — the UI
     actively excludes already-added entities from the picker, which is a stronger duplicate-
     prevention guarantee than merely "the popper shows one row."
9. Type "Hi" and click Send.
   - **Verify**: conversation is created (confirmed: URL changes to `/chat/{id}`, entry appears
     in the sidebar "Today" group), and a new `chat-participants-badge` for the **owner**
     appears — aria-label `"Users in this conversation"`, count `"1"` (a fifth, previously-absent
     badge; confirmed live it does not exist before the first message is sent, and appears
     immediately after).
10. Verify all participants are visible under their type sections.
    - **Verify**: confirmed live — all five badges (Users, Agents, Pipelines, Toolkits,
      MCPs-with-warning) persist unchanged after send; none disappear, none change count.
11. Verify misconfigured entities show yellow warning messages.
    - **Verify**: confirmed live and organically (not fabricated — see § Test Data for why
      automation should still deliberately seed its own misconfigured fixture rather than depend
      on this one). The project's only available MCP ("asd (mcp)") is itself disconnected.
      Its badge renders with an orange/yellow warning-triangle SVG overlaid on the paperclip
      icon (confirmed via computed-style-adjacent screenshot evidence, not just an aria-label
      string). Opening its popper shows a bordered/highlighted row: **"asd"** with a warning icon
      and the text **"Server is disconnected! Reconnect it to use. Log in."** (with "Log in." as
      a clickable link). This is exactly the case's expected "yellow warning message" — for
      MCPs. **Pipelines do NOT get the same treatment** — see § Known Defects: a specific broken
      pipeline in the same project produces an uncaught console crash with **no warning UI at
      all**, rather than the graceful warning MCPs show. Agents and Toolkits misconfiguration
      states were not independently reproduced this run (no known-misconfigured fixture of
      either type was found in the explored project) — flagged as unverified, not asserted
      either way.

## Expected Results
- All four participant types (Agents, Pipelines, Toolkits, MCPs), once added, render as
  independent badges in the right-sidebar PARTICIPANTS area, each with a distinct icon and an
  accurate count.
- No duplicate entries — confirmed both by popper-row-count and by the picker's own exclusion of
  already-added entities.
- Sending the first message adds a fifth "owner" (`Users in this conversation`) badge.
- A genuinely misconfigured **MCP** shows a yellow/orange warning-triangle badge overlay and a
  clear in-popper explanation with a remediation link. A genuinely misconfigured **pipeline**
  (see § Known Defects) does not — this is the one live divergence from the case's blanket "yellow
  warning" expectation, filed as issue #684.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: agents/pipelines/toolkits/MCPs exist in the project | All four entity types selectable | Preconditions + Test Data | confirmed live default project (399) fails this precondition (0 pipelines, 0 MCPs); project 471 satisfies it; recommended fix = API-seed into the test's own project | `clarification` — case precondition doesn't hold for the suite's default project; automation must seed, not assume |
| Step 1: Navigate to Chats, click "+ Chat" | New conversation, empty PARTICIPANTS | Test Step 1 | `chat-participants-badge*` query returns empty array pre-first-participant | asserted |
| Step 2: Add agent | Agent in AGENTS section | Test Step 2 | `chat-participants-badge-agents` aria-label + count, `chat-switch-participant-button` text | asserted |
| Step 3: Add pipeline | Pipeline in PIPELINES section | Test Step 3 | `chat-participants-badge-pipelines` aria-label + count | asserted *(composer-button-replaces-not-adds nuance is a new Axis-2 addition, not case-required)* |
| Step 4: Add toolkit via toggle | Toolkit in TOOLKITS section | Test Step 4 | `chat-participants-badge-toolkits` aria-label + count | asserted |
| Step 5: Add MCP via toggle | MCP in MCPS section | Test Step 5 | `chat-participants-badge-mcp` (singular) aria-label + count — **automation must seed a healthy MCP for this step's own assertion to hold as case-written**; the live-available MCP fixture is itself broken | asserted (badge presence) / soft-asserted (no-misconfiguration) — **see § Implementer Phase 2 finding: healthy MCP false-positive misconfiguration (#687)**: badge presence still asserted hard; the "no warning shown" portion is a real product defect (deterministic, filed), soft-asserted per no-masking policy rather than hard-failed |
| Step 6: All four sections visible in PARTICIPANTS | 4 sections displayed | Test Step 6 | four `chat-participants-badge-{section}` elements present simultaneously | asserted *(shape clarification: 4 independent badges/poppers, not 1 combined panel — reverse-masking guard, not a defect)* |
| Step 7: Distinct icons per type | Icons distinct | Test Step 7 | screenshot comparison of the four badge SVGs (no shared/duplicate icon across sections) | asserted |
| Step 8: No duplicate entries | No dupes | Test Step 8 | popper row-count = 1 per added entity; **additionally** already-added entity absent from re-opened picker | row-count: asserted (hard) for agents/pipelines/toolkits; soft-asserted for "mcp" — see § Implementer Phase 2 finding (#687): the misconfigured-branch row renders with no `chat-participant-row-*` testid, so the row-count reads 0 for a reason unrelated to duplication. Picker-exclusion guarantee (Axis 2, "agents"): also soft-asserted — see § Implementer Phase 5 finding **(amended 2026-07-20, PR #688 fix-only pass — see § AFS Amendments below)**: correlated with #684's Agent+Pipeline trigger condition (confirmed live: works correctly with an Agent-only participant; intermittently fails once a Pipeline participant also coexists) but NOT confirmed to share #684's root-caused mechanism — filed as its own issue, [#689](https://github.com/EliteaAI/elitea-testing-public/issues/689), cross-linked to #684 as "possibly same underlying instability, mechanism not yet confirmed shared" |
| Step 9: Type "Hi" and Send | Conversation created, owner badge added | Test Step 9 | URL becomes `/chat/{id}`; conversation appears in sidebar "Today" group | **BLOCKING defect (#684, see finding below)** — asserted as a natural hard failure, not soft-asserted: Send can crash the client-side navigation once both an Agent and a Pipeline participant are present (required by steps 2-3), independent of pipeline health — a race condition, ~1/5 of full-flow runs in this implementation's sample, not every run. Was `asserted` before this discovery; downgraded here — see § Implementer Phase 5 finding: Agent+Pipeline Send crash |
| Step 9 (owner-badge sub-case) | New `chat-participants-badge` for owner, aria-label `"Users in this conversation"`, count `"1"` | — | confirmed live in project 471 (non-private); **confirmed live this run NOT renderable in project 399** — `showUsersSection = !isPrivateProject` in `CollapsedPerticapantsList.jsx` unconditionally omits the whole Users badge block for the account's own Private project, regardless of participants seeded | `blocked` — see § Implementer Phase 2 finding: private-project owner-badge gap. **Also now unreachable regardless, per #684 above (Step 9 itself never completes).** |
| Step 10: All participants remain listed | All badges persist post-send | Test Step 10 | all 4 entity badges (agents/pipelines/toolkits/mcp) present, unchanged counts, after send | `blocked` (transitively, via #684) — the code asserts this correctly and will pass once #684 is fixed, but Step 9's crash currently prevents this test from ever reaching Step 10 |
| Step 11: Misconfigured entities show yellow warning | Warning shown | Test Step 11 | MCP: `chat-participants-badge-mcp` aria-label `"Misconfiguration error in mcps"` + warning-triangle SVG + popper text "Server is disconnected! Reconnect it to use. Log in." | code is `asserted` for MCPs *(confirmed live, organically)* — **caveat added post-implementation (#687, see finding below): this check's discriminating power is currently undermined** — a healthy MCP now shows the identical warning, so the assertion no longer proves the entity is UNIQUELY broken, only that SOME warning renders (which is still literally true and still passes). **Also transitively `blocked` by #684** — this step is currently unreachable since Step 9 never completes |
| Step 11 (pipeline sub-case) | Warning shown for misconfigured pipeline | — | a specific broken pipeline (project 471, "HelloPipeline" #1) produces an **uncaught crash with no warning UI**, not a warning | **defect** — filed as [#684](https://github.com/EliteaAI/elitea-testing-public/issues/684); do not assert a pipeline warning-UI claim until fixed |
| Step 11 (agent/toolkit sub-case) | Warning shown for misconfigured agent/toolkit | — | no misconfigured agent or toolkit fixture was found/seeded this run | `blocked` — see § Blocked Steps |
| Pass/Fail criteria: "All four participant types display correctly with distinct icons" | — | Steps 6–7 | as above | asserted |

### Axis 2 — Observables asserted beyond the case
- **Composer's active-participant button REPLACES, not adds** (step 3 finding) — *added:
  observed live that adding a pipeline after an agent changes what `chat-switch-participant-
  button` displays; the badges are independently additive but the composer's single "active"
  slot is not — a real UI nuance the case's step-by-step wording could be misread as implying
  cumulative composer display.*
- **Already-added entity excluded from its own picker** (step 8 finding) — *added: a materially
  stronger duplicate-prevention signal than "the popper shows one row" — asserts the prevention
  mechanism itself, not just its absence of visible symptoms.*
- **`chat-participants-badge-mcp` uses the singular "mcp"**, while agents/pipelines/toolkits use
  the plural (`-agents`, `-pipelines`, `-toolkits`) — *added: a naming inconsistency worth
  capturing exactly since it will silently break a templated `PARTICIPANTS_BADGE.format(section)`
  call if someone assumes uniform pluralization (confirmed live via DOM query — see § Concrete
  Handles).*
- **Owner badge (`"Users in this conversation"`) does not exist before the first message is
  sent, and cannot be probed as "count 0"** — *added: mirrors the same absent-not-zero pattern
  already documented for the agents badge in `remove_agent_participant`'s existing docstring
  (ELITEA-1793); confirming it also holds for the owner badge closes a gap the case's step 9
  implies but doesn't spell out (a naive `get_text() == "0"` assertion would need to become an
  existence check instead).*
- **Console error monitoring during every add-participant action** — *added: caught the pipeline
  defect (issue #684) purely from side-channel console observation; the UI itself gave zero
  visual indication anything was wrong at add-time.*

## Cleanup
1. Delete the conversation created during this exploration (id `150`, "HI Chat", project 471) —
   done via UI (three-dot menu → Delete → confirm) during this session; confirmed removed (only
   the pre-existing "HI Chat" conversation, id `129`, which predates this session and was not
   created or modified by it, remains).
2. No agent/pipeline/toolkit/MCP entities were created by this exploration (all four fixtures
   used — "Test Agent", "HelloPipeline", "alita (artifact)", "asd (mcp)" — were pre-existing in
   project 471, added as participants only, never created or deleted). Nothing to clean up there.
3. For the automated version: the test's own API-seeded agent/pipeline/toolkit/MCP (see § Test
   Data) must be deleted in a `finally`/fixture-teardown block, and the conversation deleted via
   `conversation_api.delete_conversation(int(conv_id))` (existing pattern, see ELITEA-2090 AFS).

## Evidence (screenshots captured this run)
- `test-results/screenshots/ELITEA-2094-step5-mcp-misconfig-badge.png` — plus menu open, MCP
  toggle just enabled, orange warning-triangle badge visible in right sidebar (step 5/11).
- `test-results/screenshots/ELITEA-2094-step6-7-all-4-badges-distinct-icons.png` — all four
  collapsed badges (Agents/Pipelines/Toolkits/MCP) stacked with distinct icons, menu closed
  (steps 6–7).
- `test-results/screenshots/ELITEA-2094-step6-agents-popper.png` — AGENTS popper open, single
  "Test Agent" row (steps 6, 8).
- `test-results/screenshots/ELITEA-2094-step8-pipelines-popper-no-dup.png` — PIPELINES popper,
  single "HelloPipeline" row despite two same-named pipelines existing in the project (step 8).
- `test-results/screenshots/ELITEA-2094-step8-toolkits-popper-no-dup.png` — TOOLKITS popper,
  single "alita" row (step 8).
- `test-results/screenshots/ELITEA-2094-step9-10-owner-added-all-participants-persist.png` — all
  5 badges (Users/Agents/Pipelines/Toolkits/MCP-warning) persisting after "Hi" sent; the pipeline
  execution error visible in the transcript (steps 9–10; also the Known-Defect execution-failure
  evidence).
- `test-results/screenshots/ELITEA-2094-step11-mcp-popper-misconfig-detail.png` — MCPS popper
  open on the misconfigured "asd" MCP: "Server is disconnected! Reconnect it to use. Log in."
  (step 11).

## Concrete Handles (discovered during exploration)

**Locator policy note (overrides spec-format's generic ladder):** this project's locator policy
(`.agents/testing.md` § Locator policy) is **testid-only, no fallback ladder**. Handles below
marked "NO TESTID" are a real, confirmed gap — flagged per policy rather than silently
implemented as a raw CSS/role locator. `ChatPage`'s existing `add_agent_participant` /
`add_toolkit_participant` methods already use raw role/placeholder locators for this exact
surface (pre-existing tech debt, `.agents/testing.md`: "~350 call sites... not precedent" — cited
here only as *context* for why the gap exists, not as license to extend it further).

| Element | testid | Notes |
|---|---|---|
| "+ Chat" button | `sidebar-create-button` | Matches existing `ChatPage.create_conversation_button`. |
| Plus menu (entry point) | `plus-menu-button` | Matches existing `ChatPage.plus_menu_button`. |
| "Modules"/Internal Tools menu item | `internal-tools-menuitem` | The ONLY plus-menu item with a testid. |
| "Agents" / "Pipelines" / "Toolkits" / "MCPs" / "Invite Users" plus-menu items | **NO TESTID** | Confirmed live via `document.querySelectorAll('[role="menuitem"]')` — all `null`. Located today via `get_by_role("menuitem", name="Agents")` etc. (existing precedent in `add_agent_participant`/`add_toolkit_participant`). **Flagged for `add-data-testid`** — these are elements this case (and its automation) directly touches, so per policy scope they qualify for testids, not just tolerance of the existing debt. |
| "Search agents..." / "Search pipelines..." / "Search toolkits..." / "Search MCPs..." inputs | **NO TESTID** | Confirmed live (`input.getAttribute('data-testid')` → `null`). Located via `get_by_placeholder(...)`. Same flag as above. |
| Individual entity rows in each picker (e.g. "Test Agent", "HelloPipeline", "alita (artifact)", "asd (mcp)") | **NO TESTID** | Confirmed live on an agent row (`li[role="menuitem"]`, no `data-testid`). Toolkit/MCP rows additionally contain a bare `role="switch"` (also no testid). Same flag as above — this is the largest of the three gaps since it's per-row, not per-menu. |
| Composer's active-participant button | `chat-switch-participant-button` | Matches existing `ChatPage.switch_participant_button`. Shows agent OR pipeline name (last-added wins, not cumulative — see Axis 2). |
| Agents badge (collapsed) | `chat-participants-badge-agents` | Matches `PARTICIPANTS_BADGE.format("agents")`. |
| Pipelines badge (collapsed) | `chat-participants-badge-pipelines` | Confirmed live — same template, `.format("pipelines")`. |
| Toolkits badge (collapsed) | `chat-participants-badge-toolkits` | Confirmed live — same template, `.format("toolkits")`. |
| MCP badge (collapsed) | `chat-participants-badge-mcp` | **Confirmed live: singular "mcp", NOT "mcps"** — `.format("mcp")`, breaking the otherwise-uniform pluralization pattern. Existing docstrings in `chat_page.py` already say `"mcp"` (not `"mcps"`) for this section — this AFS confirms that's correct, not a typo. |
| Owner/"Users" badge (collapsed) | `chat-participants-badge-users` *(inferred from the template — not independently confirmed via DOM query this run, only via its aria-label/count text in the accessibility snapshot)* | aria-label confirmed live: `"Users in this conversation"`. Recommend a quick live DOM check (`document.querySelector('[data-testid="chat-participants-badge-users"]')`) before relying on this testid in code — flagged as a minor confirmation gap, not a blocker. |
| Badge's clickable icon button (scoped) | `chat-participants-badge-button` | Matches `PARTICIPANTS_BADGE_BUTTON`. Confirmed present under all 4+1 badges. |
| Opened section popper | `chat-participants-popper` | Matches `ChatPage.participants_popper`. Confirmed live for Agents/Pipelines/Toolkits/MCPs poppers — same testid regardless of section, disambiguated by which badge was clicked. |
| Per-participant row inside a popper | `PARTICIPANT_ROW` template (`chat-participant-row-{uniqueId}`) | Confirmed live **only** for the agent case (existing code: `application_{agent_id}_{project_id}`) via prior ELITEA-1793 work. **Not independently re-confirmed this run** for pipeline/toolkit/mcp `uniqueId` prefixes (e.g. whether it's `pipeline_...`/`tool_...`/`mcp_...`) — flagged as a confirmation gap for whoever implements remove-participant support for these three types (not required for THIS case, which never removes a participant). |
| Message input | `chat-message-input` | Matches existing `ChatPage.message_input`. |
| Send button | `chat-send-button` | Matches existing `ChatPage.send_button`. |

## Network Behavior
- **Adding an agent/toolkit participant**: no unexpected requests; `wait_for_network()` after
  the click is sufficient (existing pattern in `add_agent_participant`/`add_toolkit_participant`).
- **Adding the specific broken pipeline** (see § Known Defects): `GET /api/v2/elitea_core/
  version/prompt_lib/471/106/151` → **400 Bad Request**, immediately followed by an uncaught
  `TypeError` (not a network event, but a direct consequence of the 400 going unhandled).
- **Sending a message with a broken pipeline as active participant**: pipeline execution itself
  fails server-side; the UI renders "An unexpected error occurred while processing your request"
  as the assistant's reply. The conversation and user message are still persisted successfully.
- **Secrets endpoint 403**: `GET /api/v2/secrets/secrets/default/{project_id}` returns 403 on
  every page load in project 471 for this user — reproduced consistently, appears unrelated to
  the PARTICIPANTS feature (fires on page load, not on any participant action) and unrelated to
  the pipeline defect (different endpoint, different timing). Not filed as a defect this run —
  flagged here only in case a future session finds it relevant to a different case.

## Known Defects Found During Exploration

- **[MAJOR] Filed as [EliteaAI/elitea-testing-public#684](https://github.com/EliteaAI/elitea-testing-public/issues/684)**:
  Adding a specific pipeline ("HelloPipeline", pipeline id `106`, version id `151`, in project
  471 — one of two pipelines sharing that display name; the *other* one, and every other
  agent/pipeline/toolkit/MCP tested, adds cleanly) as a chat participant triggers `GET .../
  version/prompt_lib/471/106/151` → `400 Bad Request`, then an uncaught `TypeError: Cannot read
  properties of undefined (reading 'icon_meta')` at `ChatBox.jsx:1516:44` (×2). No warning UI is
  shown — the badge renders as healthy. Sending a message with this pipeline active then fails
  with "An unexpected error occurred while processing your request." **Reproduced 2/2** in two
  separate fresh conversations (real UI clicks throughout, no synthetic events) via a clean-room
  comparison: the pipeline's own *duplicate-named sibling* and a *different, uniquely-named*
  pipeline ("GenerateStory") both added with zero console errors, isolating the cause to this one
  entity's orphaned/broken version record, not "any pipeline" or "duplicate names" generally. A
  contrast test against a genuinely misconfigured **MCP** in the same project showed MCPs DO get
  a graceful warning UI for the equivalent situation — making this pipeline's silent-crash
  behavior a real, in-scope divergence from what the case's own step 11 expects ("misconfigured
  entities show yellow warning messages"). Automation should NOT use this specific pipeline as a
  fixture; use `expect.soft()` + `# Known defect: #684` if a future case specifically wants to
  assert pipeline-misconfiguration-warning parity with MCPs (this case's own automation should
  seed a healthy pipeline instead — see § Test Data — since asserting the crash isn't this
  case's job).

## Blocked Steps
- Step 11's **agent** and **toolkit** misconfiguration sub-cases (case step 11 is written
  generally — "misconfigured entities" — not MCP-specific) could not be verified this run: no
  misconfigured agent or toolkit fixture was found in the explored project, and this analyst pass
  did not attempt to artificially construct one (would require either finding an agent with a
  broken LLM/credential reference, or a toolkit with invalid settings — out of scope for a single
  analysis pass without a known repro). **Not treated as a defect** (per the dispatch's own
  instruction: flag honestly rather than fabricate). Recommend the automation engineer either (a)
  scope this case's automated assertion to the MCP sub-case only (already fully proven, plus the
  pipeline sub-case which is a filed defect) and open a follow-up TMS case for agent/toolkit
  misconfiguration specifically, or (b) attempt to seed a broken agent/toolkit via API (e.g. an
  agent referencing a deleted credential) if that turns out to be a supported combination.

## Implementer Phase 2 finding: private-project owner-badge gap (discovered during ELITEA-2094 implementation)

**Finding**: the suite's default/mandated seeding project (`${ELITEA_PROJECT_ID}` = `399`,
"Private") structurally cannot render the owner/"Users in this conversation" participants
badge that Step 9/10 require, **regardless of how the test seeds data**. This is not a
testid gap and `add-data-testid` cannot fix it — the element is never mounted.

**Root cause** (confirmed live + by reading source): `EliteaUI/src/[fsd]/features/chat/
participants/ui/CollapsedParticipants/CollapsedPerticapantsList.jsx:87-88` —
```js
const isPrivateProject = selectedProjectId == user.personal_project_id;
const showUsersSection = !isPrivateProject;
```
The entire Users-badge `<StyledTooltip>...<UsersParticipantDropdown>...</StyledTooltip>`
block (lines 145-177) is conditionally rendered on `showUsersSection`. Confirmed live this
run: sending a message in project 399 (after switching the account's active project to
"Private" via the sidebar project selector) produces **zero** `[data-testid^="chat-
participants-badge"]` elements — not just a missing Users badge, but the entire collapsed-
participants row stays unmounted until an entity participant is added, and even then the
Users badge specifically never appears, at any participant count. The same flow in project
471 (non-private) renders the Users badge correctly (aria-label `"Users in this
conversation"`, count `"1"`), confirming this is a private-vs-non-private gate, not a
generic bug.

**Why the AFS didn't catch this**: the analyst pass exclusively exercised project 471
(documented precondition workaround for pipelines/MCPs — see § Preconditions); it never
independently verified step 9 against project 399, so the private-project gate was
invisible to that pass.

**Resolution taken this implementation**: per the dispatch's explicit instruction to seed
into "whatever project this suite's fixtures already target" (399, confirmed via the
existing `agent_id`/`pipeline_with_llm_id`/`artifact_toolkit`/`mcp_toolkit_with_tools`
fixtures' `settings.elitea_project_id` default), the test runs entirely in project 399 and
asserts everything provable there — Steps 1-8, the URL/sidebar portion of Step 9, the
4-entity-badge portion of Step 10, and Step 11's MCP sub-case. The owner-badge portion of
Steps 9/10 is scoped `blocked` (see Coverage Map) rather than asserted-and-silently-passing
or masked. This mirrors the AFS's own precedent for Step 11's agent/toolkit sub-case
(`blocked`, tracked separately). **Recommend a follow-up decision** (orchestrator-level,
analogous to picking a TMS adapter): designate a standing non-private, automation-owned
project for any future case needing the owner/"Users" participant signal, so it doesn't
depend on the shared, analyst-curated "Elitea Testing Team" (471).

## Implementer Phase 2 finding: healthy remote MCP toolkits always show a false-positive misconfiguration warning (discovered during ELITEA-2094 implementation, Phase 4 Execute → Phase 5 Debug)

**Finding**: a remote MCP toolkit that is genuinely reachable, correctly configured, and has a
real, freshly-synced tool list (the exact `mcp_toolkit_with_tools` fixture § Test Data
recommends) is **always** rendered by the chat PARTICIPANTS panel as misconfigured — the same
"Server is disconnected! Reconnect it to use. Log in." treatment a genuinely broken MCP gets.
This makes Step 5's literal expectation ("MCP appears... no warning") and Step 8's "mcp"
duplicate-row-count check (built on a testid that's only emitted on the non-misconfigured
render branch) fail for a real product reason, not a fixture or automation defect.

**How this was found**: the implementer's first execution attempt failed at Step 5
(`assert not chat.is_participant_section_misconfigured(section="mcp", ...)`). Per the no-masking
policy, root cause was investigated (systematic-debugging) rather than weakening the assertion:
1. Reproduced live via `playwright-cli` against a **freshly-created** MCP toolkit (not the
   test's own fixture, to rule out a fixture bug) pointed at `https://mcp.deepwiki.com/mcp` — a
   public, no-auth-required, `curl`-verified-reachable (`HTTP 200`) endpoint — with a real,
   freshly-synced 3-tool list (`ask_question`, `read_wiki_contents`, `read_wiki_structure`) baked
   in via the same `sync_mcp_tools` call the UI's own "Load Tools" button makes.
2. Toggled it on as a chat participant; polled `document.querySelector('[data-testid="chat-
   participants-badge-mcp"]').getAttribute('aria-label')` every 1s for 8s — **no change**,
   ruling out a timing/health-check-in-flight explanation. Result: persistently
   `"Misconfiguration error in mcps"`; popper text: `"Server is disconnected!  Reconnect it to
   use. Log in."`.
3. Reproduced independently on 2 more pre-existing toolkit instances — the environment's own
   long-standing "Remote Github" MCP (toolkit id 3) and the reused `autotest_deepwiki_mcp_1954`
   fixture (from ELITEA-1954) — same false positive on both. Not specific to any one toolkit.
4. Read the EliteaUI source to confirm root cause: `EliteaUI/src/[fsd]/features/chat/
   participants/lib/context/ParticipantStatusRunner.jsx:136-137`:
   ```js
   const remoteMcpLoggedOut =
       isToolkitParticipant && participant?.entity_settings?.toolkit_type === 'mcp' && !hasRemoteMcpLoggedIn;
   ```
   `hasRemoteMcpLoggedIn` (`useMcpTokenChange.hooks.js`) is a **pure client-side check**: does
   `localStorage` hold an OAuth access token for this server URL? That token is only ever
   written by `startMcpAuthFlow` (`mcpAuthFlow.helpers.js`), itself only triggered when the
   backend emits an `mcp_authorization_required` socket event — which a no-auth-required server
   like deepwiki never sends, since it genuinely needs no login. The check has no way to
   distinguish "this MCP doesn't need login" from "this MCP needs login and hasn't gotten it" —
   every remote MCP toolkit of `toolkit_type === 'mcp'` without a manually-completed OAuth flow
   in the current browser session is permanently `remoteMcpLoggedOut = true`, feeding into
   `hasError` (line 150-159) unconditionally. Confirmed via API too: `GET .../tool/prompt_lib/
   399/<id>` on the freshly-created toolkit returns `"online": false` despite 3 real synced
   tools; toolkit id 3 ("Remote Github") returns `"meta": {"check_connection_supported":
   false, ...}` — this toolkit *type* was never wired to report a real connection state at all.
5. Also confirmed (by reading `ParticipantItem.jsx`) that the misconfigured/"attention" render
   branch (lines 379-460) emits **no** `chat-participant-row-{uniqueId}` testid on its root —
   only a hover-only `chat-participant-remove-button` — explaining why Step 8's
   `get_participant_popper_row_count("mcp")` independently reads `0`, not `1`, as a direct
   cascade of the same root cause (not a second, unrelated defect).

**Filed**: [EliteaAI/elitea-testing-public#687](https://github.com/EliteaAI/elitea-testing-public/issues/687)
(MAJOR) — distinct from #684 (pipelines show NO warning even when genuinely broken — the
opposite problem) and #685 (verifies the warning correctly fires for a *genuinely* disconnected
MCP — it does; #687 is that it *also* fires for healthy ones).

**Resolution taken this implementation**: per the no-masking policy (Hard Rule 2,
product-isolated defect), the two directly-affected checks are `expect.soft()`-asserted with
`# Known defect: EliteaAI/elitea-testing-public#687` comments rather than hard-failed, so the
rest of the flow (Steps 6-11) still runs and is still verified:
- Step 5's misconfiguration-absence check (`ChatPage.get_participants_badge_locator("mcp")`,
  new additive getter method, `not_to_have_attribute("aria-label", ...)`).
- Step 8's "mcp" duplicate-row-count check (`ChatPage.get_participant_popper_rows_locator("mcp",
  ...)`, new additive getter method, `to_have_count(1)`), pulled out of the shared
  agents/pipelines/toolkits loop (which stays a hard assert — unaffected by this defect).

Step 5's badge-**presence** check and Step 11's misconfigured-MCP-shows-warning check are
**not** affected — both remain hard asserts and both are expected to still pass (the badge
renders regardless of state; the warning fires for the intentionally-broken MCP too, just no
longer *uniquely* — see the Step 11 Coverage Map row caveat above). At the time this #687
finding was written, this meant the test's overall implementer-local verdict was expected to
be a **sanctioned RED** (per `.agents/testing.md` § Merge gate: deterministic, single-cause,
tied to one open, linked defect) rather than GREEN. **Superseded by the #684 finding
immediately below**, discovered when the test was actually re-run after this fix: Step 9 now
blocks before Steps 10-11 (where #687's Step-11 caveat would even matter) are ever reached.
Both findings stand — #687 remains real and will matter again once #684 is fixed — but #684
is the CURRENT proximate cause of the test's red status.

**No AFS re-scoping needed** (for #687): this is a genuine product defect in an area the case
(and the AFS's own Axis-1 row for Step 5) already correctly specified as in-scope — it does
not change *what* the case asks to be verified, only *how* the current product behaves when
verified. Per the implementer slot contract, this is handled in-place (soft-assert + file
defect), not routed back as `needs-analyst-rerun`.

## Implementer Phase 5 finding: Agent+Pipeline participants crash Send, blocking conversation creation (discovered re-running the test after the #687 fix; updates issue #684)

**Finding**: once BOTH an Agent participant (case step 2) and a Pipeline participant (case
step 3) are present in a conversation — required by the case's own literal flow — sending the
first message (case step 9) can crash the client-side navigation to `/chat/{id}`. This is
**not** specific to any particular pipeline's health: reproduced with a completely fresh,
valid pipeline created via `PipelineAPI.create_pipeline_with_llm_node` (the AFS's own §
Automation Hints recommendation, specifically chosen to avoid #684's originally-reported
broken "HelloPipeline" fixture). **Reproduction reliability is race-condition-shaped, not a
hard 100%**: a minimal, rapid repro (agent + pipeline only, Send within ~1s) hit it 5/5; the
FULL test's own 5-run sample (all 4 participant types, the case's own step ordering) hit it
1/5 — more elapsed wall-clock time before Send (from adding the toolkit + MCP afterward) gives
the underlying race more chances to resolve harmlessly before Send fires. The root cause
(pipeline's version-detail fetch using the agent's version_id — see below) is unaffected by
this correction; only the *observed frequency* differs by scenario. When it fires, Steps 10
and 11 become unreachable as a direct consequence — there is no conversation id to operate on.
When it doesn't fire, the test proceeds through Steps 9-11 normally.

**How this was found**: after fixing the #687 discovery and a separate Step-8 popper-
duplication timing bug (see `close_participants_popover` in `chat_page.py` — an unrelated
infrastructure fix, Escape does not close this popper; see its docstring), re-running the test
surfaced a NEW failure at Step 9: `expect(page).to_have_url(...)` timing out, URL staying at
`/chat`. Root-caused (systematic-debugging, not weakened) via a standalone Python/Playwright
script replicating the test's own page-object calls with response/console capture added:
1. Reproduced with the full 4-entity set (agent+pipeline+toolkit+mcp) — 3 console errors
   (`400 Bad Request`, 2× `TypeError: Cannot read properties of undefined (reading
   'icon_meta')`) — the SAME crash signature #684 already documented.
2. Narrowed to a minimal repro: agent + pipeline ONLY (no toolkit, no MCP) — same crash, same
   navigation block. Confirms toolkit/MCP are irrelevant; the trigger is agent+pipeline
   coexisting as participants.
3. Captured the failing request precisely: `GET .../version/prompt_lib/399/<pipeline_id>/
   <requested_version_id>` → 400, body `{"error": "Application[<pipeline_id>]
   version[<requested_version_id>] not found"}`.
4. Compared the requested version id against BOTH participants' actual version ids (captured
   directly from each entity's own creation response, not inferred) across 5 independent
   fresh agent+pipeline pairs — **every single time**, the requested-but-404ing version id
   exactly matched the **agent's** version id, never the pipeline's own (e.g. one run:
   `agent version=5509`, `pipeline version=5510`, requested version `5509`). This is a
   deterministic state cross-contamination bug (most likely a stale closure/memoized value
   carried over from the previously-active participant when a new one becomes active), not a
   data-integrity issue with any specific pipeline record — which generalizes #684
   significantly beyond its original "one orphaned version record" characterization.
5. Confirmed a conversation IS still created server-side despite the client never navigating
   (`ConversationAPI.list_conversations()` showed 6 orphaned "New Chat" entries accumulated
   from repro runs, since without a URL-derived id the test's own cleanup couldn't find and
   delete them — cleaned up manually as part of this investigation). This means a real user
   hitting this sees an unresponsive Send button with zero feedback — worse than #684's
   original report, which described the conversation/message still succeeding and only the
   pipeline's own AI response failing.
6. Read `EliteaUI/src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx`'s `onSelectVersion`: it
   reads `versionDetails.meta.icon_meta` with no optional chaining, where `versionDetails`
   comes from `fetchOriginalVersionDetails(...)` — which returns `{}` (not `undefined`, per
   `useFetchParticipantDetails.hooks.js`) on a failed fetch, so `{}.meta` is `undefined` and
   `.icon_meta` on that throws exactly the observed `TypeError`. The sibling implementation in
   `NewConversationView.jsx`'s own `onSelectVersion` already guards this exact case
   (`versionDetails?.icon_meta`) — confirming the missing guard in `ChatBox.jsx` is the
   proximate crash, on top of the deeper wrong-version-id bug.

**Filed / updated**: added this evidence as a comment on the existing
[EliteaAI/elitea-testing-public#684](https://github.com/EliteaAI/elitea-testing-public/issues/684)
(same crash site — not a duplicate) rather than opening a new issue, since it's clearly the
same underlying defect, now understood far more precisely and shown to be more general/severe
than originally reported.

**Resolution taken this implementation**: per Hard Rule 2 (no defect masking) — this is
**product-blocking**, not isolated, so it is NOT a candidate for `expect.soft()`: Steps 10-11
genuinely cannot run without a real conversation id, so soft-asserting Step 9 and continuing
would just produce a cascade of meaningless downstream failures with no diagnostic value. Step
9's `assert conv_id` is left as a natural, hard, unmasked failure with a `# Known defect: #684`
comment directly above it explaining the mechanism — matching `.agents/testing.md` § Merge
gate's sanctioned-RED exception, which explicitly accepts EITHER a soft-assert OR a `# Known
defect: #N` comment as the linking mechanism for a deterministic, single-cause, open, linked
defect. Steps 10-11's code is left exactly as designed (not skipped, not removed) — it will
run and be verified for real once #684 ships a fix; until then it simply never executes,
which is the correct, honest behavior for a natural assertion failure partway through a test
function.

**No AFS re-scoping needed**: same reasoning as the #687 finding above — this is a real
product defect in functionality the case (steps 2, 3, 9) already correctly specifies as
in-scope. It does not change what the case asks to be verified, only exposes that the product
currently cannot fulfil its own step-9 expected result ("Conversation is created") once an
agent and a pipeline coexist — which is itself the honest, correct test outcome to report, not
grounds for `needs-analyst-rerun`.

**Operational note for the lead**: on the runs where #684 fires as the Send-crash symptom, it
prevents the test's own conversation-id-based cleanup from running, leaking one orphaned "New
Chat" conversation in project 399 per occurrence. Not worked around here (a query-most-recent-
conversation fallback was considered and rejected — a real risk of deleting an unrelated
conversation under any concurrent test activity, and it would be building resilience around a
known defect rather than testing the feature). Flagging for awareness; a periodic manual sweep
of empty "New Chat" conversations in project 399, or fixing #684, are the two ways to stop the
leak.

**Second symptom, same root defect class (discovered stabilizing the Step 8 "picker exclusion"
check)**: after soft-asserting the Send-crash symptom, re-running the test surfaced a THIRD
distinct failure (Step 8's "already-added agent excluded from its own picker" check,
`useFilteredEntityItems.js`) — reproducing 2/2 before being addressed. Isolated live: with an
Agent participant alone (no Pipeline/Toolkit/MCP), the exclusion filter works correctly every
time; once a Pipeline participant also coexists, it intermittently fails. Ruled out as a simple
timing lag: added a condition-based poll around the check first (`is_entity_excluded_from_picker`
in `chat_page.py` still carries this defensive poll), and the wrong state did NOT resolve within
the poll window — a real state issue, not a delay this implementation could wait out. Treated as
a further symptom of #684's participant-state fragility (not a new, separate issue — added as a
comment on #684 rather than filing a duplicate) and soft-asserted the same way, via two new
additive page-object methods (`get_picker_matching_rows_locator`, `close_picker_menu`) so the
check could use `expect.soft()` — the SAME aggregation mechanism as the #687 checks, per
`.agents/testing.md` § Merge gate's "identical mechanism" requirement (no mixing
`expect.soft()` with a separate `pytest.fail()`-based collection in the same test).

**Final stabilized signature**: after soft-asserting all three known-defect touch points, the
test's own 3-consecutive-run verification (this implementation's local gate, matching the
dispatch's own request) produced **3/3 IDENTICAL failures** — `ExceptionGroup: Soft assertion
failures (3 sub-exceptions)`, always exactly: #687 (badge misconfiguration) × 2 + #684 (picker-
exclusion symptom) × 1 — satisfying `.agents/testing.md` § Merge gate's sanctioned-RED bar in
its strict form (not just the closed-set variant). This is the CURRENT deterministic signature;
it does not preclude the Send-crash symptom of #684 (also confirmed real, also linked, but not
observed in this specific final 3-run set — see the Coverage Map Step 9 row and the dedicated
finding above for that symptom's own evidence).

## AFS Amendment (2026-07-20, PR #688 fix-only pass — reviewer finding #2)

A fresh reviewer session on PR #688 flagged that the "second symptom" paragraph above (and the
Coverage Map's Step 8 row) bucketed the picker-exclusion failure under #684 on **correlation**
(both symptoms occur only when Agent+Pipeline coexist), not a **confirmed shared root cause** —
#684's own 2026-07-20T17:03 comment explicitly says the picker-exclusion symptom is "Not yet
root-caused to a specific line," whereas #684's Send-crash symptom (the version_id mixup) IS
precisely diagnosed. The merge gate's closed-set variant requires every bucketed member to
independently satisfy single-cause-tied-to-an-open-defect, not merely "correlated with a defect
that does."

**Resolution**: filed the picker-exclusion symptom as its own issue,
[#689](https://github.com/EliteaAI/elitea-testing-public/issues/689), cross-linked to #684 as
"possibly the same underlying participant-state instability, mechanism not yet confirmed
shared." #684 stays scoped to the Send-crash symptom it actually root-caused. The test's Step 8
`expect.soft()` comment, its `@allure.issue(...)` decorator, and the `KNOWN_DEFECT_*` constant
now point at #689 for this specific check. This is a documentation/attribution correction only —
no change to what Step 8 asserts or how it's asserted (still `expect.soft()` on
`get_picker_matching_rows_locator("agents", ...)`).

## Automation Hints
- Framework: Playwright + pytest (confirmed from `.agents/testing.md`).
- **New test file recommended**: `automation/tests/ui/chat/test_chat_participants_panel.py` (or
  add a new test class to `test_chat_interface.py` if the lead prefers consolidation — no
  existing class in that file owns this scenario).
- **Seed test data via API, into whatever project the test's own fixtures already point at** —
  do not hardcode a dependency on project 471's manually-curated agents/pipelines/toolkits/MCPs
  (shared, mutable, could change under this test at any time). Confirmed available API surface
  in `automation/api/client.py`:
  - `AgentAPI.create_agent(name, description, instructions)`
  - `PipelineAPI.create_pipeline_with_llm_node(name, description, model_name=...)` — produces an
    **executable** pipeline (unlike bare `create_pipeline`, which has zero nodes) — use this, not
    the broken "HelloPipeline" fixture, for the case's own happy-path pipeline.
  - `ToolkitAPI.create_artifact_toolkit(name, description, bucket_name)` — cheapest toolkit type,
    no external credential required.
  - `ToolkitAPI.create_remote_mcp_toolkit(name, description, url, tools)` — pass a genuinely
    unreachable `url` (and `tools=[]`) to deterministically reproduce the "Server is
    disconnected!" misconfigured state for step 11, independent of the shared "asd (mcp)"
    fixture. Seed a **second**, healthy MCP (real URL + `sync_mcp_tools(url)` result) for step
    5's own literal expectation ("MCP appears" with no warning).
- **New page-object methods needed** (`automation/pages/chat_page.py`), siblings of the existing
  `add_toolkit_participant`:
  ```python
  @action("Add pipeline participant")
  def add_pipeline_participant(self, pipeline_name_prefix: str, timeout: int = 10000):
      # plus menu -> "Pipelines" menuitem -> search "Search pipelines..." -> click matching row
      # (same shape as add_agent_participant; pipeline rows are click-to-select, not toggle)
      ...

  @action("Add MCP participant")
  def add_mcp_participant(self, mcp_name: str, timeout: int = 10000):
      # plus menu -> "MCPs" menuitem -> search "Search MCPs..." -> click matching row's switch
      # (same shape as add_toolkit_participant; MCP rows are toggle/switch, like toolkits)
      ...
  ```
- **New assertion helpers needed**: a way to read a badge's aria-label / warning-icon presence
  (e.g. `is_participant_section_misconfigured(section: str) -> bool` checking for the
  `"Misconfiguration error in {section}"` aria-label pattern vs. the healthy `"{Section} in this
  conversation"` pattern) and a way to open a specific section's popper by name (the existing
  `open_participants_popover(section=...)` already does this — reuse it for all four sections,
  not just "agents").
- **Testid gap — CLOSED during implementation** (per `.agents/testing.md` § Locator policy:
  "Missing testid on the target? That is work to do, not a reason to rung down" — the existing
  raw-locator precedent in `add_agent_participant`/`add_toolkit_participant` is tracked tech
  debt, not license to extend it). `add-data-testid` pass landed on `automation/testids`
  (EliteaAI/EliteaUI@73595e8d), confirmed live via `browser_evaluate` DOM queries before commit:
  - Plus-menu entity items: `agents-menuitem`, `pipelines-menuitem`, `toolkits-menuitem`,
    `mcps-menuitem` (`PlusChatButton.jsx` — `EXPANDABLE_ITEMS[].testId`).
  - Per-section search input: `{section}-search-input` (`agents`/`pipelines`/`toolkits`/`mcps`)
    — lands on the native `<input>` via MUI's lowercase `inputProps={{'data-testid': ...}}`
    (the `TextField`'s own `data-testid` resolves to the wrapper `<div>`, confirmed by the
    existing `mui_tooltip_aria_label_wrapper_differs_from_click_target_testid` memory pattern —
    verified live before committing, not assumed).
  - Per-row entity item: `{section}-menu-item-{item.key}` where `item.key` is the existing
    `agent-{project_id}-{id}` / `pipeline-...` / `toolkit-...` / `mcp-...` key already computed
    in `useDropdownData.jsx` — templated via a new `sectionKey` prop threaded from
    `PlusChatButton` into `PlusChatSubmenu` (`PlusChatSubmenu.jsx`).
  `add_pipeline_participant`/`add_mcp_participant` (below) consume these testid-only handles —
  no new raw-locator debt added. New page-object class-level template constants:
  `PLUS_MENU_ENTITY_MENUITEM = '[data-testid="{}-menuitem"]'`,
  `PLUS_MENU_SEARCH_INPUT = '[data-testid="{}-search-input"]'`,
  `PLUS_MENU_ENTITY_ITEM_PREFIX = '[data-testid^="{}-menu-item-"]'`.
- Wait strategy: `wait_for_network()` after each add-participant click (existing pattern);
  `wait_for_ai_response()` / equivalent is NOT needed for the badge assertions themselves (badges
  update synchronously with the click's own API response), only for the actual message-send step.
