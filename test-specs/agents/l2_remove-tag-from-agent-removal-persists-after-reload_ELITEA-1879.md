# Test Case: Remove a tag from agent — removal persists after reload

## Metadata
- **TMS ID**: ELITEA-1879
- **Linked Story**: none
- **Priority**: medium (`l2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}` (project id `399` on this run)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot (batch `agents-batch1-1277`,
  cluster dispatch with ELITEA-1878 — one live session, per-case execution;
  written as a separate AFS rather than a family — this case's steps
  (start from an agent that already HAS a tag, remove one, verify the OTHER
  remains) differ in shape from ELITEA-1878's steps (start empty, add two),
  not merely in data, so per the skill's "differ only in data → family;
  differ in steps → separate AFS" test this is its own spec)
- **Status**: `ready-for-automation` — case executed end-to-end live against
  `http://localhost:5173` (agent id `5189`, `manual_test_agent`, seeded with
  two tags via this session's ELITEA-1878 run), all 6 steps verified, **no
  functional defect**. Same testid gap as ELITEA-1878 on the Tags
  input/chips, PLUS this case additionally needs the chip delete-icon
  testid (`chipDeleteTestId`) since it actually removes a tag — see
  Concrete Handles.

## Preconditions

- User is logged in (on localhost, `auth_state` fixture skips login).
- An agent with at least one saved tag exists.

**Implementation guidance:** same as ELITEA-1878 — use a **dedicated,
disposable agent** via `AgentAPI.create_agent_full()` (`reasoning_effort:
"none"`, no `temperature`), but this case additionally needs the agent
**pre-seeded with 2 tags already saved** (e.g. via the agent-creation API
payload's `version_details.tags`, or via an initial add-tags-and-save pass
identical to ELITEA-1878's Steps 2-3) before the test's own remove-and-verify
steps run — matching the case's own Precondition ("An agent with at least
one saved tag exists"). Recommend seeding exactly 2 tags (e.g.
`keep_this_tag` + `remove_this_tag`) so the test can assert BOTH halves of
the case's Expected Result: the removed tag is gone AND the remaining tag
is intact — a 1-tag seed can only prove removal, not "remaining tags stay
intact." Do **not** reuse the shared `manual_test_agent` (id `5189`) for the
automated test — see Cleanup below (this analyst's live exploration on it
was fully reverted).

## Test Data

No case-specified literal values (case's own Test Data table says "(none
required)"). This analyst's live exploration used the two tags carried over
from the ELITEA-1878 run in this same session (`regression_test`,
`automation`) — removed `automation`, verified `regression_test` remained.
The implemented test should use its own explicit literal values per the
Implementation guidance above (e.g. `keep_this_tag` / `remove_this_tag`) —
matching the project's convention of self-documenting test data rather than
implicitly depending on another case's leftover state.

## Test Steps

1. Navigate to an agent that has at least one saved tag.
   - **Verify — PASSES.** Agent detail page loads with the saved tag(s)
     visible as chips in the Tags field (confirmed live: both
     `regression_test` and `automation` chips present, carried over from
     the prior saved state).
2. Click the X on one tag to remove it.
   - **Verify — PASSES.** Clicking the chip's delete icon (an `img` inside
     the chip, `onDelete` handler in `AutoCompleteDropDown.jsx`) removes
     the chip immediately — pure client-side state change, confirmed no
     network request fires on this click alone (same "no request until
     Save" shape as the Discard flow documented in `_surface.md`, though
     here the mechanism is `TagEditor`'s `onChangeTags` → Formik
     `setFieldValue`, not `resetForm()`).
3. Verify the tag chip disappears from the field.
   - **Verify — PASSES.** The removed tag's chip is no longer present in
     the accessibility snapshot immediately after the click (no debounce/
     wait needed); the remaining tag's chip is still present and unaffected.
4. Click Save.
   - **Verify — PASSES.** `agent-save-button` click fires
     `PUT /api/v2/elitea_core/application/prompt_lib/{projectId}/{agentId}`
     → `201 Created`. 0 console errors after save.
5. Reload the page.
   - **Verify — PASSES.** Page reloads (fresh navigation).
6. Verify the removed tag is no longer present; any remaining tags are
   intact.
   - **Verify — PASSES.** Post-reload, the removed tag's chip is absent and
     the remaining tag's chip (`regression_test`) is present, confirmed via
     accessibility snapshot
     (`test-results/screenshots/ELITEA-1879-step-06-removed-tag-absent-after-reload.png`).

## Expected Results

After reload, the removed tag is absent from the Tags field and all
remaining tags are intact. Confirmed live exactly as specified — no
case-text drift on this case (unlike ELITEA-1878's hyphen/underscore typo).

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (steps above) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | covered |
| Precondition: agent with ≥1 saved tag exists | Agent detail page reachable with saved tag(s) visible | Test-data setup (pre-seeded 2-tag agent, see Implementation guidance) | agent created + tags saved before test's own steps | covered |
| Step 1: navigate to agent with saved tag(s) | Page loads with saved tag(s) visible | Step 1 | chip(s) visible matching the seeded tags | covered |
| Step 2: click X on one tag to remove it | Tag chip disappears from the field | Steps 2-3 | removed-tag chip locator count == 0 immediately after click | covered |
| Step 3: verify the tag chip disappears | Removed tag no longer shown | Step 3 | same assertion as Step 2 (case text splits click and verify into two steps; this AFS's Step 3 asserts what Step 2's click caused) | covered |
| Step 4: click Save | Save completes successfully | Step 4 | PUT to `application/prompt_lib/{proj}/{id}` returns `201` | covered |
| Step 5: reload the page | Page reloads | Step 5 | fresh navigation + `wait_for_page_load()` | covered |
| Step 6: verify removed tag absent, remaining tags intact | Removed tag absent; other tags still displayed | Step 6 | removed-tag chip absent AND remaining-tag chip present, both checked post-reload | covered |
| Expected Final State: removed tag absent, remaining tags intact | — | Step 6 | see above | covered |
| Pass criterion: "removed tag does not reappear... remaining tags preserved" | — | Step 6 | see above | covered |
| Fail criterion: "removed tag reappears after reload, or remaining tags are lost" | n/a (negative condition) | Step 6 | both halves independently asserted (not just "chip count changed by 1") | covered |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| No network request fires on the chip-delete click itself (only on Save) | Documents the causal mechanism (client-side Formik state until Save) so the implementer/reviewer don't go looking for a premature PUT/PATCH on delete-click, matching the project's existing Discard-flow precedent for "when does this UI action actually hit the network" |
| Save PUT returns `201 Created` (network-level) | Same rationale as ELITEA-1878 — asserts the causal persistence mechanism, not just the DOM |
| 0 console errors after the delete-click, after Save, and after reload | Side-channel check per the skill's mandatory rule; three checkpoints because this case has three distinct moments (delete, save, reload) where a silent error could hide |
| Remaining tag's chip is unaffected/unchanged by the removal of the other (same accessible name, still clickable) | The case's own Fail criterion calls out "remaining tags are lost" as a failure — verifying the remaining chip is not just present-by-text but still a functioning chip (not, e.g., a stale/orphaned DOM node) catches a partial-removal-side-effect bug the case text doesn't spell out but its own Pass criterion implies |

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Save button | `agent-save-button` | pre-existing (`AgentFormPage.save_button`) |
| Tags input | `agent-tags-input` | needs-adding — same gap as ELITEA-1878, see that AFS for the exact `ApplicationEditForm.jsx` threading change. This case's implementation should land the SAME commit as ELITEA-1878's (both are in this batch) — don't duplicate the `add-data-testid` work if ELITEA-1878 implements first. |
| Tag chip (rendered) | `agent-tags-chip-{tag_name}` (dynamic) | needs-adding — identical to ELITEA-1878's handle, same commit. |
| Tag chip delete icon | **testid needed: `agent-tags-chip-delete-{tag_name}`** (dynamic, parameterized by tag name) | needs-adding — THIS case is what actually exercises it (ELITEA-1878 never removes a tag, so per canon #511 scope discipline that prop must stay unwired for ELITEA-1878's own diff; it becomes "referenced" only once THIS case's implementation calls it). `AutoCompleteDropDown.jsx:240-249` already supports `chipDeleteTestId` as either a static string or a function of the option (identical shape to `chipTestId`) — wire `chipDeleteTestId={option => \`agent-tags-chip-delete-${option.name}\`}` alongside the `chipTestId` change in `ApplicationEditForm.jsx`'s Agent branch. Page-object side: class-level template constant, e.g. `AGENT_TAGS_CHIP_DELETE = '[data-testid="agent-tags-chip-delete-{}"]'`. |

**Naming rationale:** identical to ELITEA-1878's — see that AFS's Concrete
Handles section for the full `{section}-{element}-{param}` reasoning; this
case adds exactly one new element (`tags-chip-delete`) to the same
call-site/ternary pattern.

## Network Behavior

- Delete-click: no network request (client-side Formik state, confirmed
  live via `browser_network_requests` — no new request appeared between the
  chip-delete click and the subsequent Save click).
- Save: `PUT /api/v2/elitea_core/application/prompt_lib/{projectId}/{agentId}`
  → `201 Created`. Confirmed live (project id `399`, agent id `5189`).
- Reload: `GET /api/v2/elitea_core/application/prompt_lib/{projectId}/{agentId}`
  → `200 OK`, response `version_details.tags` reflects the post-removal set.

## Known Defects Found During Exploration

None. Remove-tag/save/reload-persist works correctly, and the remaining tag
survives intact — confirmed live, no functional defect. The chip
delete-icon testid gap is implementer work (`add-data-testid`), not a
product bug.

## Cleanup

1. Live exploration (this analyst pass, same session as ELITEA-1878) reused
   the shared `manual_test_agent` (id `5189`, project `399`) immediately
   after ELITEA-1878's own exploration left it with 2 saved tags
   (`regression_test`, `automation`) — removed `automation`, saved,
   reloaded, verified `regression_test` remained
   (`test-results/screenshots/ELITEA-1879-step-06-removed-tag-absent-after-reload.png`).
2. **`regression_test` was then also removed and re-saved** to fully revert
   `manual_test_agent` to its original zero-tags state before handoff —
   confirmed via a final reload + accessibility-snapshot check (Tags field
   shows only the empty combobox, no chips left).
3. The automated test itself must use its own dedicated, disposable,
   pre-seeded agent (see Preconditions/Implementation guidance above) — do
   not touch `manual_test_agent` from automated test code.
