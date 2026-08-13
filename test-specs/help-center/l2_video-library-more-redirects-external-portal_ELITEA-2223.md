# Test Case: Help Center — Video Library "More..." redirects to full video portal

## Metadata
- **TMS ID**: ELITEA-2223
- **Linked Story**: none
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids` build) for
  the launch side; destination explored live on `videoportal.epam.com`
- **User set**: `${TEST_USER}` — via the `auth_state` fixture (localhost bypasses Keycloak via
  `VITE_DEV_TOKEN`; no login steps needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation *(steps 1–5 fully automatable and asserted; steps 6–8 are
  `blocked` — see § Blocked Steps. Partial-block within an otherwise automatable case, not a
  whole-case block — see reasoning below.)*

## Why this is its OWN AFS, not part of the ELITEA-2220/2221/2222/2224 family
Same launch mechanism (click a resource-card link, verify redirect), but this case has THREE
EXTRA steps the others don't (channel-page identity, Videos/Playlists tabs, video-listing
content with thumbnails/authors/durations) — a genuine STEPS difference, not just a data
difference (test-case-analysis SKILL.md's merge test). It also hits a real environmental wall
(EPAM SSO) none of the other four do.

## Preconditions
- User is authenticated (`auth_state` fixture; localhost skips login via `VITE_DEV_TOKEN`).
- No seeded state required.

## Test Data
### reuse-existing
- (none required)

## Test Steps
1. Navigate to `${BASE_URL}/help-center`.
   - **Verify**: `help-center-page-header` testid visible, text "Help Center".
2. Locate the Video Library card and verify its links are present: for each slug in
   `self-service-agent-publishing`, `clearer-shared-credential-setup`,
   `indexing-completion-summary-report`, `notification-center-inbox-style-management`,
   `video-library-more`, verify `help-center-tour-link-{slug}` is visible.
3. Verify `help-center-tour-link-video-library-more` has
   `href="https://videoportal.epam.com/channel/DdYPoMVa2X/videos"`.
4. Click `help-center-tour-link-video-library-more` (`target="_blank"` — new tab via
   `context.expect_page()`).
5. On the new page, verify the redirect leaves the Elitea app for an `epam.com`-hosted
   destination — **confirmed live**: the browser first resolves
   `videoportal.epam.com/channel/DdYPoMVa2X/videos`, which (unauthenticated) itself 302s to
   an EPAM SSO login gate (`access.epam.com/auth/realms/plusx/...`) before the channel page
   ever renders. Assert the FINAL resolved URL's host ends in `.epam.com` — this is the
   honest, environment-agnostic form of "redirected to the external Video Digital Platform
   portal" that doesn't assume SSO access this suite does not have (see § Blocked Steps).
6–8. **BLOCKED — see § Blocked Steps.** Cannot verify: channel page shows "Elitea - AI
  Collaborative Platform", Videos/Playlists tabs, or video listing with
  thumbnails/titles/authors/durations. The destination requires EPAM corporate SSO
  authentication; no credentials for `access.epam.com` exist anywhere in this project's
  `.env.test` / `.agents/profile.md` § Roles & sample users, and this is a third-party
  property entirely outside Elitea's own codebase (not `EliteaUI`, not `elitea_assistant`) —
  there is nothing to fix on our side and no credential to add safely (this is EPAM's
  internal video portal, not Elitea test data).

## Expected Results
- The Video Library card shows its 5 configured links (confirmed live, matches case text
  exactly).
- Clicking "More..." opens a new tab; the href is configured correctly
  (`https://videoportal.epam.com/channel/DdYPoMVa2X/videos`) and the browser genuinely leaves
  the Elitea app for an `epam.com` host.
- Channel-page identity/tabs/video-listing content (case steps 6–8) — **not verifiable by this
  suite**: EPAM SSO wall, no credentials available. See § Blocked Steps.

## Coverage Map

**Axis 1 — Case coverage**
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | page loads | step 1 | step 1: page header visible | asserted |
| 2 Locate VIDEO LIBRARY card (purple icon, subtitle) | UI state produced | step 2 | step 2: 5 link testids visible (cosmetic subtitle/icon has no testid, scoped out — same reasoning as the sibling family AFS) | asserted *(scoped)* |
| 3 Verify links: Self-Service Agent Publishing, Clearer Shared Credential Setup, Indexing: Completion Summary Report, Notification Center: Inbox-Style Management, More... | condition holds | step 2 | step 2: 5 link testids visible | asserted |
| 4 Click "More..." | control responds | steps 3–4 | step 3: href check; step 4: click + new tab | asserted |
| 5 Redirected to external Video Digital Platform portal | condition holds | step 5 | step 5: final URL host ends `.epam.com` (environment-agnostic form — see Automation Hints for why the literal channel-page landing can't be asserted) | asserted *(scoped)* |
| 6 Channel page shows "Elitea - AI Collaborative Platform" | condition holds | — | — | **blocked** *(EPAM SSO wall, no credentials — § Blocked Steps)* |
| 7 Channel page shows Videos/Playlists tabs | condition holds | — | — | **blocked** *(same reason)* |
| 8 Videos listed with thumbnails, titles, authors, durations | condition holds | — | — | **blocked** *(same reason)* |

**Axis 2 — Analyst additions:**
- href-correctness check before click (step 3) — *added: proves the app-side redirect
  configuration is correct independent of the destination's own auth requirements — isolates
  "our config is right" from "we can't see past EPAM's SSO", which is exactly the honest split
  this case needs.*
- Final-URL-host assertion (step 5) — *added as the concrete, testable proxy for "redirected to
  the external portal" once the literal channel-page landing was confirmed unreachable without
  credentials this suite doesn't have.*

## Cleanup
- None required — no test data created.

## Concrete Handles (discovered during exploration)

| Element | Testid | Provenance |
|---|---|---|
| Help Center page header | `help-center-page-header` | on `automation/testids` ✓ (pre-existing, ELITEA-2227) |
| Video Library card links | `help-center-tour-link-self-service-agent-publishing` / `-clearer-shared-credential-setup` / `-indexing-completion-summary-report` / `-notification-center-inbox-style-management` / `-video-library-more` | `-video-library-more` added THIS session (was colliding `help-center-tour-link-more`, shared fix with the sibling family AFS); the other 4 pre-existing. On `automation/testids` ✓, NOT yet on `main` — human cherry-pick pending. |

```python
TOUR_LINK = '[data-testid="help-center-tour-link-{}"]'  # pre-existing, help_center_page.py
```

## Network Behavior
- Clicking the link navigates the new tab through an unauthenticated redirect chain:
  `videoportal.epam.com/channel/DdYPoMVa2X/videos` → 302 → `access.epam.com/auth/realms/...`
  (EPAM SSO login). Confirmed live via `new_page.url` after `wait_for_load_state()`. No XHR
  from Elitea's own backend involved in this flow.

## Known Defects Found During Exploration
None found on Elitea's side. The EPAM SSO wall is expected corporate-infrastructure behavior
for an unauthenticated automation browser context, not a product defect — not filed.

## Blocked Steps
- **Steps 6–8** (channel-page identity, Videos/Playlists tabs, video-listing content) —
  require an authenticated EPAM SSO session (`access.epam.com`). No credentials for this
  exist in `.env.test` / `.agents/profile.md` § Roles & sample users, and `videoportal.epam.com`
  is a third-party corporate property entirely outside the Elitea codebase — there is nothing
  in `EliteaUI` or `elitea_assistant` to fix, and adding real EPAM SSO credentials to this
  suite is out of scope for a UI regression test (and not something the analyst/implementer
  slot can provision). Engineer/orchestrator: this needs either (a) a decision to accept
  partial coverage permanently (steps 1–5 asserted, 6–8 documented-blocked), or (b) EPAM SSO
  test credentials provisioned by a human with access, at which point steps 6–8 become
  automatable via the same `new_page` handle. Recommend (a) — this is a one-way corporate SSO
  gate, not a transient blocker.

## Automation Hints
- Framework: Playwright + pytest.
- Reuses `automation/pages/help_center_page.py` — `open_resource_link_in_new_tab()` and
  `TOUR_LINK`, no page-object changes needed beyond the shared testid fix (see sibling family
  AFS's § Known Defects for the collision fix, shared by this case).
- New pytest marker: none — `help_center` + priority `p2` (high) + `regression`.
- Separate test function/spec from the family AFS's four cases (materially different step
  count and a partial-block disposition) — same file is acceptable
  (`test_help_center_resource_links.py`) since it shares the page object and testid fix, but
  it is its own `def test_...` , not a row in the family's `pytest.param` table.
- Wait strategy: `new_page.wait_for_load_state("domcontentloaded")` then
  `expect(new_page).to_have_url(re.compile(r"\.epam\.com/"))` — web-first assertion, no
  `sleep`. Do NOT attempt to authenticate through the EPAM SSO gate — that is out of scope
  and would require real corporate credentials.
