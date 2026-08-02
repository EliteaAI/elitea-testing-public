# Test Case: Build with AI from Agent — created Skill is auto-attached and user is redirected back to Agent

## Metadata
- **TMS ID**: ELITEA-1999
- **Linked Story**: none
- **Priority**: l2 (case priority: `high`)
- **Status**: `ready-for-automation`
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}`=399)
- **User set**: `${TEST_USER}` (dev-token auth on localhost, `auth_state` skips login)
- **Analyst**: qa-engineer (Sage), analyst slot — cluster dispatch with ELITEA-1920 (shared session, separate AFS: the two cases share the "Build with AI" family but diverge in every step from step 2 onward — different origin page, different entity created, different completion mechanism — so per the cluster's "differ in STEPS, not just data" test they are NOT a family AFS)
- **Case-gate note**: same recurring gap as every prior "Build with AI" AFS: `.agents/testing.md` has no `TMS case-gate` section defining excluded statuses. Case frontmatter carries `status: draft` / `execution_type: manual`; per the skill's default this run proceeded. Flagging again for scout (now flagged 5+ times across this case family — worth escalating as a standing gap rather than a per-case note).
- **Tooling note**: no Playwright MCP server was available this session; explored via standalone `sync_playwright` scripts driving the existing page objects (`AgentDetailPage`, `AgentFormPage`, `GenerateSkillModalPage`) plus `AgentAPI`/`SkillAPI` for fixture setup/cleanup. Not committed, scratch-only.

## Coverage decision — why `ready-for-automation`

No existing spec exercises this round-trip at all. A repo-wide search for the
mechanism this case depends on (`newSkillId` / `ReturnUrl` / `SourceApplicationId`
query-param handshake — the exact same "create-new-from-a-picker, get sent
back with the new id" pattern the source code's own comments call "mirrors
the toolkit newToolkitId round-trip") returns **zero hits** anywhere in
`automation/tests/`, `automation/pages/`, or `test-specs/` — this flow (for
either Skills or the analogous Toolkit picker) has never been automated.
ELITEA-1911 (the nearest sibling AFS) covers a *different* Skill-attachment
mechanism entirely: selecting an already-*suggested* Skill while generating
a brand-new Agent via Build with AI. ELITEA-1999 instead edits an
**existing** Agent, opens its SKILLS section's own "+ Skill → Create new"
picker, and creates a **brand-new** Skill via Build with AI from *there* —
a completely different entry point, with a completion contract (redirect
back to the Agent editor, not to the Skill's own details page) that only
exists because of the `sourceApplicationId`/`returnUrl` query params
`SkillMenu.jsx`'s "Create new" handler attaches to the navigation (source
read: `SkillMenu.jsx` `handleCreateNew()`, `CreateSkillTabBar.jsx` `onSave()`,
`GenerateSkillModal.jsx`'s approve handler — all three check for these
params and branch the post-save redirect target accordingly).

## Preconditions
- User is logged in with admin/editor role; at least one existing Agent is available for editing (case's own preconditions). This run created a disposable fixture Agent (`autotest_1999_fixture`, via `AgentAPI.create_agent()`) rather than requiring a pre-existing one — any saved Agent with a persisted version works identically (the mechanism keys off `entityVersionId`/`isEntityUnsaved`, not the Agent's specific content).
- The Build with AI feature is accessible (`generate-skill-open-button` renders and is clickable for `${TEST_USER}` on the Skill-create page — same permission finding as every prior "Build with AI" AFS).
- **Precondition gap investigated (case doesn't explain the entry point at all):** the case's step 2–4 wording ("+ Skill" → "+ Create New" → "Build with AI") describes a nested picker whose exact navigation contract the case never states. Investigation confirmed: `SkillMenu.jsx`'s "+ Skill" button (`agent-add-skill-button`) opens a searchable dropdown (`UnifiedDropdown`) with a "Create new" item (`showCreateNew`/`onCreateNew`, plus-icon prefixed) that navigates to `/skills/create?source_application_id={agentId}&return_url={encoded current agent URL}`. The Skill-create page's own "Build with AI" button (`generate-skill-open-button`) is the SAME shared component used everywhere else in the Skill-management surface (ELITEA-1988/1989/1990/1991/1993/2001) — it has no awareness of the query params at all; the params are read only by the SAVE path (manual `CreateSkillTabBar.onSave()` AND the Build-with-AI modal's own approve handler, `GenerateSkillModal.jsx`), which is what makes the redirect-back-to-Agent behavior work identically whether the Skill was created manually or via Build with AI.
- **Skill name field constraint** (confirmed again this run, same as ELITEA-1911): lowercase letters/digits/hyphens only, max 32 chars. The Build-with-AI-generated name (`"github-pr-test-coverage"` this run) already conforms — the generation model appears to target this format directly (not independently re-verified against a name that WOULD violate it; out of scope, ELITEA-1993's own subject).

## Test Data

### created-with-cleanup (created via API/UI in this run; both deleted at run end)
- Fixture Agent `autotest_1999_fixture` (id created live = `6740` this run) — created via `AgentAPI.create_agent()` with default `reasoning_effort: "medium"`, `temperature: null` (the project's own `_default_llm_settings()` helper — the known #524 payload gotcha does not apply here since this helper already avoids the bad combination).
- Skill generated via Build with AI, natural-language prompt: `"A skill that reviews GitHub pull request diffs and flags missing unit tests."` (not verbatim from the case, which gives no exact wording) — generated name `"github-pr-test-coverage"` (id created live = `1181` in the first exploration run, `1182` in the timing-verification re-run — see step 4's note).

No data is left behind — the fixture Agent and the generated Skill are deleted in Cleanup, verified live both runs.

## Test Steps

1. Navigate to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner` (an existing, saved Agent). Scroll to the SKILLS section (`agent-skills-section`), click **"+ Skill"** (`agent-add-skill-button`, force-click per this project's existing MUI-overlay convention).
   - **Verify**: the skill selection dropdown opens (`UnifiedDropdown` popper) — confirmed live.

2. In the dropdown, click **"Create new"** (case wording: "+ Create New" — a trivial capitalization difference from the live label, not a case-text drift worth filing; the plus-icon-prefixed rendering matches the case's intent exactly).
   - **Verify**: navigates to `${BASE_URL}/skills/create?source_application_id={agent_id}&return_url=%2Fagents%2Fall%2F{agent_id}%3FviewMode%3Downer%26name%3D{agent_name}` — confirmed live, exact query-string captured (`source_application_id=6740&return_url=%2Fagents%2Fall%2F6740%3FviewMode%3Downer%26name%3Dautotest_1999_fixture` this run).

3. Click **"Build with AI"** (`generate-skill-open-button`). Fill the prompt textarea (`generate-skill-prompt-input`) with the Test Data prompt, click **"Generate"** (`generate-skill-submit-button`).
   - **Verify**: `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` resolves `200` (confirmed live). Review form renders with generated Name (`generate-skill-review-name-input`, value `"github-pr-test-coverage"` this run), Description, Instructions (case step 6's "Review the generated Name, Description, and Instructions" — Name/Description/Instructions fields confirmed present and pre-populated; Description/Instructions values not independently re-verified character-by-character, that's ELITEA-1990's own subject).

4. Click **"Create Skill"** (`generate-skill-approve-button`).
   - **Verify**: `POST /api/v2/elitea_core/skills/prompt_lib/399` resolves `201` (confirmed live, skill id `1181`/`1182` across the two exploration runs). The URL transitions to `${BASE_URL}/agents/all/{agent_id}?viewMode=owner&name={agent_name}&newSkillId={skill_id}` — **NOT** to a Skill-details URL (`/skills/all/{id}`) — confirmed live, this is the case's central step-8 claim and it holds. The `newSkillId` query param is visibly stripped from the URL within a few seconds once the auto-attach effect finishes processing it (confirmed live: present at t≈2.4s, gone by t≈4.4s in the timing re-run — see Network Behavior).

5. Verify the user lands on the Agent editor, not the Skill details page (case step 8, restated).
   - **Verify**: page URL contains `/agents/all/{agent_id}`; the Agent editor's own SKILLS section (`agent-skills-section`) and other Agent-editor chrome are present — confirmed live, `is_on_agent_page: True`, `is_on_skill_details: False` both exploration runs.

6. Verify the newly created Skill is automatically attached to the Agent in the SKILLS section (case step 9).
   - **IMPORTANT — this is asynchronous and takes several seconds; do NOT assert immediately after the redirect.** A dedicated timing-verification re-run (no Save click at all) polled the counter/skill-card every second post-redirect: **0/5 + no card at t=2.4s/3.4s/4.4s, then 1/5 + card visible at t=5.5s** (total ≈4s of async processing after the redirect completes, driven by `SkillMenu.jsx`'s own `useEffect` picking up the `newSkillId` param — see Network Behavior for the exact call sequence). An implementer who checks the counter/card with a short/no wait (as this AFS's own FIRST exploration run did, by accident) will see a **false negative** ("0/5", no card) purely from checking too early — this is NOT a product defect, it is a real async chain (GET skill details → PATCH attach → refetch the skills list) that must be awaited with a real condition (`expect(skill_card).to_be_visible(timeout≈10000)` or equivalent polling on the counter text), never a fixed short sleep and never asserted synchronously right after the URL changes.
   - **Verify**: `agent-skills-counter` reads `"1/5 skills added."` and `skill-card-{skill_id}` (`AgentDetailPage.SKILL_CARD_SELECTOR`, pre-existing) is visible — confirmed live once properly awaited.

7. Save the Agent (`agent-save-button`) and re-open it (reload the page) (case steps 10–11).
   - **Verify**: the attached Skill is still present and correctly linked after save + reload — confirmed live (`skill-card-{skill_id}` visible after reload, counter still `"1/5 skills added."`). **Analyst note (Axis 2):** the attachment is ALREADY server-persisted the moment the `PATCH .../skill/prompt_lib/399/{skill_id}` call (step 6) resolves `201` — it does not depend on the Agent's own "Save" button at all (confirmed by the timing re-run, which never clicked Save and still showed the attachment fully persisted via the natural async chain). The case's own step 10 ("Save the Agent and re-open it") is followed literally here, but an implementer should know the Save click is not the causal mechanism for persistence — reloading alone, without ever clicking Save, would show the same result.

## Expected Results
Matches the case's stated Pass criteria in full: creating a Skill via Build
with AI from inside an Agent's SKILLS section redirects back to the Agent
editor (never the Skill details page — step 8), the Skill is auto-attached
to the Agent's SKILLS section once the async attach chain completes (step
9), and the attachment persists after an explicit Save + reload (steps
10–11). All 11 case steps executed live across two exploration runs (the
first established the flow end-to-end including an over-eager, since-
corrected "not yet attached" observation; the second isolated and confirmed
the async timing precisely — see step 6). No product defect found.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: admin/editor role, existing Agent, Build with AI accessible | reachable | Preconditions | fixture Agent created, `generate-skill-open-button` clickable | asserted |
| 1 Open an existing Agent for editing | Agent editor displayed | step 1 | navigated to `/agents/all/{id}` | asserted |
| 2 In SKILLS section, click "+ Skill" | dropdown/dialog opens | step 1 | `UnifiedDropdown` popper visible | asserted |
| 3 Select "+ Create New" | option selected | step 2 | navigates to `/skills/create?source_application_id=...&return_url=...` | asserted |
| 4 Choose "Build with AI" | modal opens | step 3 | `generate-skill-open-button` click → `generate-skill-modal` visible | asserted |
| 5 Enter description, click Generate | draft produced | step 3 | `generate_skill_draft` → 200 | asserted |
| 6 Review generated Name/Description/Instructions | review form shows values | step 3 | review-form fields present, name value observed | asserted |
| 7 Click "Create Skill" | creation initiated | step 4 | `POST .../skills/prompt_lib/399` → 201 | asserted |
| 8 Redirected to Agent editor, not Skill details | Agent editor displayed | steps 4–5 | URL = `/agents/all/{id}?...&newSkillId=...` | asserted |
| 9 New Skill auto-attached in SKILLS section | Skill appears | step 6 | `skill-card-{id}` visible, counter `1/5` (after correct async wait) | asserted |
| 10 Save the Agent and re-open it | saved + reopened | step 7 | `agent-save-button` clicked, page reloaded | asserted |
| 11 Attached Skill still present after save/reopen | persists | step 7 | `skill-card-{id}` visible after reload | asserted |

### Axis 2 — Analyst additions

- Step 6's async-timing warning (the 0/5→1/5 transition over ~4 seconds, precisely measured with a poll loop and the full network call sequence) — *added: this is the single highest-value fact in this AFS. Without it, the most natural first implementation (assert immediately after the redirect resolves) reproduces this AFS's own first-pass false negative and gets misdiagnosed as a product defect. The Concrete Handles/Network Behavior sections give the implementer the exact call chain to wait on instead of guessing a timeout.*
- Step 7's persistence-mechanism note (attachment is PATCH-persisted immediately, independent of the Agent's "Save" button) — *added: saves the implementer from either (a) believing Save is required and adding an unnecessary dependency, or (b) writing a flaky test that races Save against the async attach chain.*
- Preconditions' navigation-contract documentation (`source_application_id`/`return_url` query params, the exact string this run captured) — *added: the case never explains HOW the redirect-back mechanism works; without this an implementer would have to reverse-engineer it from network traffic alone.*

## Cleanup
1. Created Skill (`github-pr-test-coverage`, both run's ids `1181`/`1182`) — deleted via `SkillAPI.delete_skill()`, confirmed via subsequent list/404 check.
2. Fixture Agent (`autotest_1999_fixture`, ids `6740`/`6741` across the two runs) — deleted via `AgentAPI.delete_agent()`. Deleting the Agent does NOT cascade-delete the Skill (independent entities, same pattern as ELITEA-2166's Agent/conversation note) — the Skill is deleted first-and-separately in this Cleanup, same order rationale.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | PROVENANCE | Fallback |
|---|---|---|---|
| "+ Skill" button | `AgentDetailPage.agent_add_skill_button` (`agent-add-skill-button`) | on-main ✓ (fresh `git fetch origin`, case-insensitive `git grep` this run) | n/a — already present |
| SKILLS accordion / counter | `AgentDetailPage.skills_section` / `get_skills_counter_text()` (`agent-skills-section` / `agent-skills-counter`) | on-main ✓ | n/a — already present |
| Attached-skill card | `AgentDetailPage.SKILL_CARD_SELECTOR.format(skill_id)` (`skill-card-{id}`) | on-main ✓ | n/a — already present |
| "Build with AI" (Skill) open/prompt/generate/approve/review-name | `GenerateSkillModalPage.open_button` / `.prompt_input` / `.generate_button` / `.approve_button` / `.review_name_input` (`generate-skill-*`) | on-main ✓ | n/a — already present |
| Agent Save button | `AgentFormPage.save_button` (`agent-save-button`) | on-main ✓ | n/a — already present |
| **"Create new" menu item (the dropdown's create-new item)** | **`testid needed: agent-add-skill-create-new-button`** — currently a bare `<MenuItem onClick={onCreateNew}>` inside the SHARED `UnifiedDropdown.jsx` (source-read: `src/components/UnifiedDropdown.jsx`, the `showCreateNew`/`onCreateNew`/`createNewLabel` prop trio, no testid at all on the rendered `MenuItem`). Per `.agents/testing.md`'s "shared components never hardcode feature-scoped testids" rule, the fix is to thread a `createNewTestId` prop through `UnifiedDropdown` (same pattern as the existing `showCreateNew`/`onCreateNew`/`createNewLabel` trio) and have `SkillMenu.jsx` (the SKILLS-section caller) pass `"agent-add-skill-create-new-button"` — exact precedent already set by ELITEA-2166's `agents-create-new-button` (a different shared submenu, same "thread a testid prop through the shared component, name it for the CALLER's section" pattern). This run located the item by `page.get_by_role("menuitem", name=re.compile("Create new", re.I))` for exploration only — **not** a compliant locator, implementer must run `add-data-testid` before writing the real test. | **needs-adding** | none — testid-only policy, no fallback permitted |

**Summary for the implementer:** one new testid needed (`agent-add-skill-create-new-button`, threaded through `UnifiedDropdown`'s existing prop-passing pattern per the ELITEA-2166 precedent). Everything else — the Skill-create page's Build-with-AI modal, the Agent's SKILLS section, the Save button — already carries testids confirmed on `origin/main` this run (fresh `git fetch origin`, case-insensitive `git grep`).

## Network Behavior
- `POST /api/v2/elitea_core/generate_skill_draft/prompt_lib/399` → `200` — generates the draft (agent-analog: `generate_application_draft`).
- `POST /api/v2/elitea_core/skills/prompt_lib/399` → `201` — creates the base Skill (plural path, per this project's list/create-plural convention). Response includes the new Skill's `id`.
- **Post-redirect async attach chain** (fires automatically, no user action needed, confirmed via the timing re-run's full network capture, ~4s total observed):
  1. `GET /api/v2/elitea_core/applications/prompt_lib/399?...` ×2 (classic + pipeline agent-type refetches — unrelated background list refresh, not part of the attach chain itself, but fires in the same window).
  2. `GET /api/v2/elitea_core/skill/prompt_lib/399/{skill_id}` → `200` — `fetchSkillDetails`, reads the new skill's `version_details.id` (mirrors ELITEA-1911's already-documented contract for the OTHER Skill-attachment mechanism — same shape, different trigger).
  3. `PATCH /api/v2/elitea_core/skill/prompt_lib/399/{skill_id}` → `201` — attaches the Skill to the Agent (`skillsApi.js`'s `updateSkillRelation`, same endpoint/payload shape ELITEA-1911 documented).
  4. `GET /api/v2/elitea_core/application_skills/prompt_lib/399/{agent_version_id}` → `200` — refetches the Agent's skills list (`useGetApplicationSkillsQuery`), which is what actually updates the counter/card in the UI. **This is the call an implementer should wait on** (or simply poll the UI-visible counter/card with a real timeout) rather than guessing a fixed delay.
- The `newSkillId` URL param is stripped (`stripParam()`, `SkillMenu.jsx`) once the effect finishes — confirmed by its disappearance from the URL between t≈2.4s and t≈4.4s in the timing re-run, roughly coinciding with the PATCH resolving.

## Known Defects Found During Exploration
**No product defect found.** See step 6's async-timing note — this is real, documented async behavior, not a defect, but it is exactly the kind of thing that would masquerade as a flaky/broken test if an implementer doesn't know to wait for it (hence the emphasis in this AFS).

## Blocked Steps
None. All 11 case steps executed live end-to-end across two exploration runs (the second run specifically to nail down step 6's timing with a proper poll instead of a single early check).
