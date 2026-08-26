# Test Case (FAMILY): Help Center — resource card link redirects to the correct external page

## Metadata
- **TMS ID**: ELITEA-2220, ELITEA-2221, ELITEA-2222, ELITEA-2224 (family — `family_afs=true`,
  same `afs_path` for all four; see `.claude/skills/test-case-analysis/SKILL.md` §
  "Merge cases that differ only in DATA")
- **Linked Story**: none
- **Priority**: l3 (case priority: medium, all four members)
- **Environment Explored**: local (`http://localhost:5173`, `automation/testids` build) for
  the launch side; destination pages explored live on their real external hosts
  (`docs.elitea.ai`)
- **User set**: `${TEST_USER}` — via the `auth_state` fixture (localhost bypasses Keycloak via
  `VITE_DEV_TOKEN`; no login steps needed)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Why these four are ONE family (and ELITEA-2223 is not)
All four exercise the *identical* flow — navigate to Help Center, locate a resource card,
verify its listed links, click one named link, verify it opens the right external URL in a
new tab, verify that page loads. They differ only in DATA: which card, which link, which
destination, and (ELITEA-2221) whether the destination currently loads correctly. ELITEA-2223
("Video Library More...") was kept as its own AFS/spec because it has EXTRA steps the other
four don't (channel-page identity, Videos/Playlists tabs, video-listing content) and hits an
external SSO auth wall none of these four do — a genuine STEPS difference, not just a data
difference (test-case-analysis SKILL.md's merge test: "differ only in data → family; differ in
steps → separate").

## Preconditions
- User is authenticated (`auth_state` fixture; localhost skips login via `VITE_DEV_TOKEN`).
- No seeded state required — the resource cards' link configuration is static backend/CMS
  data (`useGetResourcesConfigQuery`), unaffected by user actions.

## Test Data
### reuse-existing
- (none required — no data inputs; the resource link config is read-only backend data)

## Test Steps (shared shape — see Parameter Table for per-case values)

1. Navigate to `${BASE_URL}/help-center` (via `navigate("/help-center")`).
   - **Verify**: `help-center-page-header` testid visible, text "Help Center".
2. Locate `{CARD_TITLE}` card and verify its listed links are present (proxy for "card
   located + links displayed" — see § Automation Hints for why a link-testid check, not a
   card-title testid, is the chosen verification): for each slug in `{CARD_LINK_SLUGS}`,
   verify `help-center-tour-link-{slug}` is visible.
3. Verify the link to click (`help-center-tour-link-{CLICK_SLUG}`) has `href="{EXPECTED_HREF}"`
   (confirms the app is correctly *configured* to redirect to the right destination,
   independent of whether that destination currently resolves).
4. Click `help-center-tour-link-{CLICK_SLUG}` (`target="_blank"` — opens a new tab/page via
   `page.expect_popup()`/`context.expect_page()`).
   - **Verify**: a new page/tab opens at exactly `{EXPECTED_HREF}`.
5. On the new page, verify the target page loads without errors:
   - **ELITEA-2220, ELITEA-2222, ELITEA-2224** (expect_ok=True): assert the page title
     matches the expected live-confirmed title substring.
   - **ELITEA-2221** (expect_ok=False — confirmed live defect): `expect.soft()` the
     CORRECT expected title pattern (`Release Notes - 2.0.2`) with
     `# Known defect: EliteaAI/elitea-testing-public#1492` — confirmed live this currently
     fails (docs.elitea.ai returns HTTP 404, title "Page Not Found").
6. **ELITEA-2224 only** (case-text CLARIFICATION — see § Automation Hints): the destination
   (`https://docs.elitea.ai/`) is the general docs homepage, not a dedicated "tutorials list"
   page as the case text implies. Verify the honest live-contract form instead: the
   destination's "Pages" navigation exposes MORE linked topics than the 3 non-"More..." links
   shown in the Tutorials card preview (Course / How to create an Agent / How to create a
   Pipeline).

## Expected Results
- Each card shows its configured links (confirmed live, matches case text exactly for all
  four cases — see Parameter Table).
- Clicking the named link opens a new tab at the href shown on the link.
- ELITEA-2220 → `docs.elitea.ai/getting-started/chat-quick-start`, title "Quick Start - ELITEA
  Documentation" — loads correctly.
- ELITEA-2221 → `docs.elitea.ai/release-notes/rn-2-0-2` — **HTTP 404** (confirmed live,
  isolated to this one link; the other three Release Notes links — 2.0.1, 2.0.0, 2.0.0B2 — all
  load correctly). Known defect, filed.
- ELITEA-2222 → `docs.elitea.ai/archive/create-agent`, title "Create Your First Agent - ELITEA
  Documentation" — loads correctly.
- ELITEA-2224 → `docs.elitea.ai/` (general docs homepage, not a dedicated tutorials list —
  case-text clarification), title "Welcome to ELITEA Documentation - ELITEA Documentation" —
  loads correctly, nav exposes more linked topics than the 3-link card preview.

## Parameter Table

| TMS ID | Card | Link slugs shown on card (all must be `visible`) | Slug clicked | Expected href | expect_ok | Expected title substring | Known defect |
|---|---|---|---|---|---|---|---|
| ELITEA-2220 | Documentation | `getting-started`, `how-to-guides`, `integrations`, `migration-update` | `getting-started` | `https://docs.elitea.ai/getting-started/chat-quick-start` | True | `Quick Start` | — |
| ELITEA-2221 | Release Notes | `release-2-0-2-latest`, `release-2-0-1`, `release-2-0-0`, `release-2-0-0b2` | `release-2-0-2-latest` | `https://docs.elitea.ai/release-notes/rn-2-0-2` | **False** | `Release Notes - 2.0.2` (correct-expected; currently 404) | `EliteaAI/elitea-testing-public#1492` |
| ELITEA-2222 | Tutorials | `course-ai-based-elitea-platform`, `how-to-create-an-agent`, `how-to-create-a-pipeline`, `tutorials-more` | `how-to-create-an-agent` | `https://docs.elitea.ai/archive/create-agent` | True | `Create Your First Agent` | — |
| ELITEA-2224 | Tutorials | `course-ai-based-elitea-platform`, `how-to-create-an-agent`, `how-to-create-a-pipeline`, `tutorials-more` | `tutorials-more` | `https://docs.elitea.ai/` | True | `Welcome to ELITEA Documentation` | — (extra check: nav link count > 3) |

## Coverage Map

**Axis 1 — Case coverage** (one sub-table per member; each row disposition covers that
member's own case text).

### ELITEA-2220
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | page loads | step 1 | step 1: page header visible | asserted |
| 2 Locate DOCUMENTATION card (blue icon, subtitle) | UI state produced | step 2 | step 2: all 4 link testids visible (icon-color/subtitle text has no testid — cosmetic, scoped out, see Automation Hints) | asserted *(scoped)* |
| 3 Verify links: Getting Started, How-To Guides, Integrations, Migration & Update | condition holds | step 2 | step 2: 4 link testids visible | asserted |
| 4 Click "Getting Started" | control responds | steps 3–4 | step 3: href check; step 4: click + new tab | asserted |
| 5 Redirected in new tab | condition holds | step 4 | step 4: new page URL == href | asserted |
| 6 Target page loads without errors | condition holds | step 5 | step 5: title contains "Quick Start" | asserted |

### ELITEA-2221
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | page loads | step 1 | step 1: page header visible | asserted |
| 2 Locate RELEASE NOTES card (orange icon, subtitle) | UI state produced | step 2 | step 2: all 4 link testids visible (cosmetic subtitle/icon scoped out) | asserted *(scoped)* |
| 3 Verify links: Release 2.0.2 (latest), 2.0.1, 2.0.0, 2.0.0B2 | condition holds | step 2 | step 2: 4 link testids visible | asserted |
| 4 Click "Release 2.0.2 (latest)" | control responds | steps 3–4 | step 3: href check; step 4: click + new tab | asserted |
| 5 Redirected to release notes page for 2.0.2 | condition holds | step 4 | step 4: new page URL == configured href (URL/config is correct) | asserted |
| 6 Target page loads without errors | condition holds | step 5 | step 5: `expect.soft()` — **fails today**, confirmed live 404, filed `#1492` | asserted *(sanctioned RED — known defect)* |

### ELITEA-2222
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | page loads | step 1 | step 1: page header visible | asserted |
| 2 Locate TUTORIALS card (green icon, subtitle) | UI state produced | step 2 | step 2: all 4 link testids visible (cosmetic subtitle/icon scoped out) | asserted *(scoped)* |
| 3 Verify links: Course, How to create an Agent, How to create a Pipeline, More... | condition holds | step 2 | step 2: 4 link testids visible | asserted |
| 4 Click "How to create an Agent" | control responds | steps 3–4 | step 3: href check; step 4: click + new tab | asserted |
| 5 Redirected to correct tutorial page | condition holds | step 4 | step 4: new page URL == href | asserted |
| 6 Target page loads without errors | condition holds | step 5 | step 5: title contains "Create Your First Agent" | asserted |

### ELITEA-2224
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Help Center | page loads | step 1 | step 1: page header visible | asserted |
| 2 Locate TUTORIALS card | UI state produced | step 2 | step 2: all 4 link testids visible | asserted |
| 3 Click "More..." at bottom of card | control responds | steps 3–4 | step 3: href check; step 4: click + new tab | asserted |
| 4 Redirected to a page listing all available tutorials | condition holds | step 4 (+ CLARIFICATION) | step 4: new page URL == href; step 6: nav exposes more linked topics than the 3-link preview | **clarification** *(live product routes to the general docs.elitea.ai homepage, not a dedicated tutorials-list page — case text hypothesis vs live-contract, see Automation Hints; asserted the honest live-contract form)* |
| 5 Page loads without errors, displays more tutorials than the card preview | condition holds | step 5, 6 | step 5: title "Welcome to ELITEA Documentation"; step 6: nav link count > 3 | asserted |

**Axis 2 — Analyst additions (all four members):**
- href-correctness check on the link BEFORE clicking (step 3) — *added: isolates "is the app
  correctly configured to redirect" from "does the destination currently resolve" — this is
  exactly what makes ELITEA-2221's defect diagnosable as a destination-content issue, not a
  redirect-mechanism issue.*
- (nothing else added beyond each case)

## Cleanup
- None required — no test data created; the resource link config is static read-only backend
  data.

## Concrete Handles (discovered during exploration)

All handles below are **pre-existing testids** (added by the already-merged ELITEA-2227
implementer) except the two disambiguated `-more` slugs, which this session added (see
§ Known Defects — the `help-center-tour-link-more` collision).

| Element | Testid | Provenance |
|---|---|---|
| Help Center page header | `help-center-page-header` | on `automation/testids` ✓ (pre-existing, ELITEA-2227) |
| Documentation card links | `help-center-tour-link-getting-started` / `-how-to-guides` / `-integrations` / `-migration-update` | on `automation/testids` ✓ (pre-existing) |
| Release Notes card links | `help-center-tour-link-release-2-0-2-latest` / `-release-2-0-1` / `-release-2-0-0` / `-release-2-0-0b2` | on `automation/testids` ✓ (pre-existing) |
| Tutorials card links | `help-center-tour-link-course-ai-based-elitea-platform` / `-how-to-create-an-agent` / `-how-to-create-a-pipeline` / `-tutorials-more` | `-tutorials-more` added THIS session (was colliding `help-center-tour-link-more`); the other 3 pre-existing. On `automation/testids` ✓, NOT yet on `main` — human cherry-pick pending. |

**Dynamic testid template** (pre-existing, `automation/pages/help_center_page.py`):
```python
TOUR_LINK = '[data-testid="help-center-tour-link-{}"]'
# usage: page.locator(HelpCenterPage.TOUR_LINK.format("getting-started"))
```

## Network Behavior
- No XHR to wait on for the click/redirect itself — the link is a plain `<a target="_blank">`;
  Playwright's `context.expect_page()` around the click is the correct wait primitive (no
  `sleep`).
- The Help Center page itself fires `useGetResourcesConfigQuery` on load (pre-existing,
  unrelated) — no action needed.

## Known Defects Found During Exploration
- **[BUG] `EliteaAI/elitea-testing-public#1492`** — ELITEA-2221's "Release 2.0.2 (latest)"
  link (`href="https://docs.elitea.ai/release-notes/rn-2-0-2"`) 404s. Confirmed live: the
  other 3 Release Notes links (2.0.1, 2.0.0, 2.0.0B2) all load correctly; the docs site's own
  404 page suggests the actual latest is `/release-notes/rn-2-0-5`. Isolated to this one
  entry — the resources CMS "latest" config is stale. Filed, dedup-checked (no existing match
  in `elitea-testing-public` bug list).
- **`help-center-tour-link-more` testid collision (fixed, not filed as a separate bug — this
  is testid infrastructure, handled as `add-data-testid` work, same authority as "missing
  testid" per `.agents/testing.md`).** Both the Video Library card's and the Tutorials card's
  generic "More..." links slugified to the identical `data-testid="help-center-tour-link-more"`
  — two elements matched by one locator, page-wide. Fixed on `EliteaAI/EliteaUI`
  `automation/testids` by prefixing the generic "More..." title's slug with the card's
  category (`video-library-more` / `tutorials-more`); every other card's link testids
  (including the already-merged sidebar/chat tour links) are byte-identical — see the commit
  body for the Step 5.5 grep evidence.

## Blocked Steps
None — all four cases executed end-to-end live.

## Automation Hints
- Framework: Playwright + pytest (per `.agents/testing.md`).
- Extend the existing `automation/pages/help_center_page.py` — reuse
  `open_resource_link_in_new_tab(slug)` unchanged (additive, no signature change) and the
  existing `TOUR_LINK` class constant.
  **Amended during implementation (fix round 1, ELITEA-2220 family):** the claim below this
  line originally read "the family test reads `HelpCenterPage.TOUR_LINK.format(slug)` directly
  ... per the same pattern the ELITEA-2227 implementer already established" — that precedent
  does not exist. ELITEA-2227's own spec (`test_help_center_sidebar_tour.py`) never constructs
  a `TOUR_LINK`-based locator directly; it exclusively calls the page-object method
  `open_resource_link_in_new_tab()`. Per `.claude/rules/ui-tests.md` / `.claude/rules/page-objects.md`
  (locators live only as page-object class fields, never constructed in spec files), the
  correct — and now actual — implementation adds `HelpCenterPage.resource_link(slug) -> Locator`
  (same style as `ai_providers_page.py`'s `card_for_model()` / `agent_form_page.py`'s
  `get_tag_chip()`: a method wrapping a dynamic-testid class constant) and the spec calls
  `help_center.resource_link(slug)` for both the "links displayed" loop and the pre-click href
  check. `open_resource_link_in_new_tab()` now calls `self.resource_link(slug)` internally
  instead of duplicating the locator construction.
- **Family spec**: ONE parameterized test function
  (`test_resource_card_link_redirects_to_external_page`), one `pytest.param` row per TMS case,
  `id=` tagged with the case id. New pytest marker: none needed — reuse `help_center` +
  priority `p2` (medium) + `regression`.
- **Why a link-testid check, not a card-title testid, for "Locate the X card"**: `ResourceCard`
  has no testid on its title/subtitle Typography today (confirmed — only the individual link
  `<Link>` elements carry testids). Case step 2's expected result is the generic
  boilerplate "Action completes without error and produces the expected UI state" (all 5 TMS
  cases in this batch share near-identical templated wording), not a hard requirement to
  assert the icon color or subtitle text. Verifying that card's own link testids are visible
  is a strictly *stronger* signal that the correct card rendered (a link testid can only
  resolve if the card whose config produced it is mounted) than a bare title-text match would
  be, at zero new-testid cost. Adding 4-5 new `ResourceCard` title testids purely to check
  cosmetic copy is disproportionate scope creep for cases whose actual crux is "click link →
  verify redirect" (canon #511 — scope discipline: add only what the test needs).
- **ELITEA-2221 known-defect pattern**: follow the existing `expect.soft(locator_or_page,
  "Known defect: #N — …")` convention (see
  `automation/tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py`
  for the precedent) — soft-assert the CORRECT expected title, not a weakened one. This keeps
  the test honestly red on that one row until `#1492` is fixed (sanctioned RED, single-cause,
  linked, deterministic — `.agents/testing.md` § Merge gate exception) while the other 3 rows
  stay green.
- **ELITEA-2224 case-text drift is a CLARIFICATION, not a bug** (reverse-masking guard,
  `test-automation-implementation` § Hard Rules → 2): the case text implies "a page listing
  all available tutorials"; the live product's "More..." link is configured to the general
  `docs.elitea.ai` homepage (same as every other doc site's generic nav-based structure — not
  a dedicated tutorials index). Asserting the case-text hypothesis (a literal "tutorials list"
  page) would fail on a non-defect. Asserted the honest live-contract form instead: page loads
  + its "Pages" nav (`get_by_role("navigation", name="Pages").get_by_role("link")`, a
  third-party-site locator — NOT subject to the testid-only policy, which governs only our own
  `EliteaUI`/`elitea_assistant` locators) exposes strictly more linked topics than the 3-link
  card preview.
- New-tab handling: identical to ELITEA-2227's established pattern —
  `with page.context.expect_page() as new_page_info: <click>`, already encapsulated in
  `open_resource_link_in_new_tab()`.
- Wait strategy: `expect(new_page).to_have_title(...)` (web-first assertion, auto-retries) —
  no `sleep`.
