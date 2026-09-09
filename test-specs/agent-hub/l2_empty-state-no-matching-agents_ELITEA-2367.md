# Test Case: Agent Hub — empty state when no agents match filter or search

## Metadata
- **TMS ID**: ELITEA-2367
- **Linked Story**: none (case `requirements: []`)
- **Priority**: l2 (case priority: high)
- **Environment Explored**: local (`http://localhost:5173/elitea-catalog`, EliteaUI `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` — on localhost, `auth_state`/`VITE_DEV_TOKEN` skips explicit Keycloak login
- **Analyst**: qa-engineer (analyst slot)
- **Status**: **extend-existing** — AMENDED 2026-09-09 (drift re-analysis, card #2079). The case is merged and automated (`tests/ui/agent_hub/test_empty_state.py`); one assertion in its Step 6 went stale against a product change and must be REPLACED in place. See § Drift Re-analysis (2026-09-09) below — it supersedes the original Step 5 filter-rail assertion, the Axis-1 row for case element 5, the Axis-2 step-5 bullet, and the chip rows of § Concrete Handles. Everything else in this AFS re-verified live on 2026-09-09 and still holds. Zero product defects; no bug filed; one `question` card (#2100) raised for an unrelated canon gap surfaced en route.
- **Original status (2026-08-10, still true for steps 1-4)**: ready-for-automation — case executable end-to-end; all steps verified live; empty state renders correctly with consistent layout and no broken UI elements.
- **AFS-path note**: amended in place per dispatch (card #2079) rather than emitted as a second `lextend_*` file — one case, one AFS. A downstream audit grepping `lextend_` will not see this unit; it is tracked by card #2079.

## Preconditions
- User is logged in to the Elitea platform (`${TEST_USER}` / dev-auth on localhost).

## Test Data

### reuse-existing
- `${TEST_USER}` — see `.agents/profile.md` § Roles & sample users.

(No other test data required — case searches for a non-existent term; search is case-insensitive substring match so any unique nonsense string works.)

## Test Steps

1. Navigate to Agent Hub (`/elitea-catalog`).
   - **Verify**: URL is `/elitea-catalog`; page title is `"ELITEA Catalog - <project name>"`.
   - **Verify**: `catalog-page-heading` visible with text "Welcome to ELITEA Catalog!"
   - **Verify**: zero console errors during page load.
2. Search for a term that matches no agents (e.g., "xyznonexistent" or any unique string guaranteed not to appear in agent names/descriptions).
   - **Verify**: search input accepts the typed term; the search request fires (backend query completes within ~500ms per the 300ms debounce + network overhead).
3. Verify the "No agents found" message is displayed in the main content area.
   - **Verify**: text "No agents found" visible in the content area (center-aligned, MuiTypography-headingMedium).
   - **Verify**: element is a SPAN within a MuiBox container; no CSS display:none or visibility:hidden; computed opacity is 1.
4. Verify a helper message appears.
   - **Verify**: text "Try adjusting your search terms" visible below "No agents found" (MuiTypography-bodyMedium).
   - **Verify**: element is a SPAN; visible and not hidden.
5. Verify the layout remains consistent with no broken UI elements.
   - **Verify**: page heading (`catalog-page-heading`) still visible and readable.
   - **Verify**: search input (`catalog-search-input`) still visible with the search term populated; clickable and focusable.
   - **Verify**: the agent category filter rail is still rendered and intact. **SUPERSEDED 2026-09-09 — do NOT assert a hardcoded chip count.** The assertion shape is specified in § Drift Re-analysis § The Step-5 filter-rail assertion below: head+tail visibility of the frontend-constant chips, plus an exact-count and set-membership invariant derived from the page's OWN `agent_categories` response.
   - **Verify**: Agents/Skills tabs still visible and functional.
   - **Verify**: zero console errors during empty state render; no exceptions in the dev tools.
   - **Verify**: no agent cards present in the main content area (query for `[data-testid^="catalog-agent-card-"]` returns zero matches).

## Expected Results
- Empty state displays correctly when no agents match the search or filter.
- "No agents found" and "Try adjusting your search terms" messages render and are accessible.
- All major UI elements (heading, search, tabs, filter rail) remain visible and functional.
- Zero console errors; layout is clean and consistent.
- No broken/collapsed/hidden elements; spacing and alignment are correct per the app's design system.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Agent Hub | Target page/section loads successfully | step 1 | URL `/elitea-catalog`; page title includes project name; `catalog-page-heading` visible; zero console errors | asserted |
| 2 Search for a non-matching term | Operation completes successfully; state updates and confirmation shown | step 2 | search input accepts typed term; backend request fires (~500ms after keystroke sequence completes) | asserted |
| 3 "No agents found" message displayed | Condition holds as described | step 3 | text "No agents found" visible in SPAN element; computed opacity 1; no display:none/visibility:hidden | asserted |
| 4 Helper message appears | Condition holds as described | step 4 | text "Try adjusting your search terms" visible; element rendered, not hidden | asserted |
| 5 Layout consistency, no broken UI | Condition holds as described | step 5 (assertion shape amended 2026-09-09) | `catalog-page-heading` visible; `catalog-search-input` visible with the term retained; Agents/Skills tabs visible with `aria-selected` intact; filter rail intact per the § Drift Re-analysis invariant (head+tail chip visibility + response-derived exact count and set membership); zero agent cards; zero console errors | asserted |

Disposition legend: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.

### Axis 2 — Analyst additions

- `step 1` verifies zero console errors during initial page load (regression guard).
- `step 2` notes the 300ms search debounce + network latency (total ~500ms expected wait before backend responds); the search request is verified to have fired.
- `step 3` documents the exact element structure: SPAN with MuiTypography-headingMedium, inside MuiBox-root container; no testid on either element.
- `step 4` similarly documents the helper text element structure: SPAN with MuiTypography-bodyMedium.
- `step 5` explicitly checks that the category filter rail remains rendered and laid out — confirming the empty state is NOT a full-page overlay that hides navigation; layout breadth consistency is the case's actual point. **AMENDED 2026-09-09:** the original wording ("11 chips") pinned a number that appears nowhere in the case text and that mixes product STRUCTURE with product DATA; it broke on the first legitimate product change. Replaced by the structure/data-split invariant in § Drift Re-analysis. The analyst addition itself (assert the rail survives the empty state) is retained and still grounded — it is the only reading of case Step 5 that has teeth.

## Cleanup

None — read-only empty state verification, no state created.

## Concrete Handles (discovered during exploration)

| Element | Recommended Locator | Fallback | Provenance |
|---|---|---|---|
| Catalog page heading | `LocatorDescriptor(testid="catalog-page-heading")` — pre-existing, `AgentHubPage.page_heading` | none (testid-only policy) | on-automation/testids (pre-existing, ELITEA-2075, confirmed live 2026-08-10) |
| Search input | `LocatorDescriptor(testid="catalog-search-input")` — pre-existing, `AgentHubPage.search_input` | none | on-automation/testids (pre-existing, ELITEA-2075, confirmed live) |
| "No agents found" message | `LocatorDescriptor(testid="catalog-no-results-title")` — pre-existing `AgentHubPage.no_results_title`. | none (testid-only policy) | **on-main ✓** (verified 2026-09-09, fresh fetch — the `needs-adding` state recorded in 2026-08-10 was resolved; testid live-confirmed rendering "No agents found", computed opacity 1) |
| "Try adjusting your search terms" helper | `LocatorDescriptor(testid="catalog-no-results-description")` — pre-existing `AgentHubPage.no_results_description`. | none | **on-main ✓** (verified 2026-09-09, fresh fetch; live-confirmed rendering "Try adjusting your search terms") |
| Category filter chips | `AgentHubPage.AGENT_CATEGORY_FILTER_CHIP_PREFIX` = `[data-testid^="catalog-agent-category-filter-chip-"]` (enumerate all) and `AgentHubPage.CATEGORY_FILTER_CHIP` = `[data-testid="catalog-agent-category-filter-chip-{}"]` (one by slugified label). Both are existing class-level constants — **no new locators needed.** | none (testid-only policy) | **on-main ✓** — verified 2026-09-09 after `cd ../EliteaUI && git fetch origin`. ⚠️ See § Drift Re-analysis § Provenance-grep false negative: the canon closure-record grep reports these as absent. They are NOT absent — the testid is composed at runtime in `CategoryRail.jsx:26` from a `chipTestIdPrefix` prop supplied at `AgentsTab.jsx:246` / `SkillsTab.jsx:247`, both present on `origin/main`. |
| Agents / Skills tabs | `LocatorDescriptor(testid="catalog-agents-tab")` / `("catalog-skills-tab")` — pre-existing `AgentHubPage.agents_tab` / `.skills_tab`; selection state via `aria-selected` (MUI Tabs' own attribute, `is_agents_tab_selected()`). | none | on-main ✓ (verified 2026-09-09, fresh fetch) |

## Network Behavior
- `GET /api/v2/elitea_core/public_applications/prompt_lib/?query=<search term>&...` fires when search term is typed; debounce 300ms, network ~150–200ms (total ~500ms end-to-end after keystroke sequence). Response includes empty `results: []` array when no match. No 4xx/5xx observed.

## Known Defects Found During Exploration

**Minor gap (not a product defect, noted for future automation):** The empty state messages ("No agents found" and "Try adjusting your search terms") render via `Category.NoResultsMessage.jsx` and currently carry NO testids. This is a minor testid absence (case text doesn't require these elements by name, and accessibility text fallback exists for this read-only empty-state use case), but future cases targeting this empty state for more granular assertions should add testids `catalog-no-results-title` and `catalog-no-results-description` to `Category.NoResultsMessage.jsx` component. No product bug filed for this (it's a test-infrastructure gap, not a functional defect).

Zero functional defects found. Layout integrity confirmed; all assertions pass.

## Blocked Steps

None — all 5 case steps reproducible and verified.

## Automation Hints

- Framework: Playwright + pytest (this project), Playwright MCP tools available.
- **Reuse `AgentHubPage` page object** (`automation/pages/agent_hub_page.py`, ELITEA-2075) for navigation, search input, and page-heading references. Add a new method `verify_empty_state()` or `search_and_verify_no_results(term)` that:
  1. Types the search term into `search_input` (use framework's search action/wait helpers, not raw `type()`).
  2. Waits for the "No agents found" text to appear using `page.get_by_text("No agents found")` or a locator wrapper pending testid addition.
  3. Asserts the text is visible, heading is still visible, filter rail is still visible, and zero agent cards are present.
- **Search term:** use any unique string not matching real agent names (e.g., "xyzabc123", "no-agents-here", "zzzznotreal"). Server-side search is case-insensitive substring match, so any nonsense guarantees zero matches.
- **Wait strategy:** the framework's `expect_response` / `wait_for_response` to `public_applications/prompt_lib/` request with `query=<term>` (debounce 300ms + network latency); or simply wait for text "No agents found" to appear (cleaner, end-to-end).
- **Assertion on empty-card-count:** `document.querySelectorAll('[data-testid^="catalog-agent-card-"]').length === 0` or use Playwright's locator count: `page.locator('[data-testid^="catalog-agent-card-"]').count()` must equal 0.
- Marker suggestion: `@pytest.mark.p2` (medium/high priority), `@pytest.mark.regression`, feature marker `agent_hub`.
- **Minor testid workaround for now:** the empty-state-text elements lack testids. Spec assertions can use `page.get_by_text("No agents found")` and `page.get_by_text("Try adjusting your search terms")` as fallback, with a TODO comment noting the testid gap for future additions. Alternately, wait on `AgentHubPage` to land the testid-addition, then add the locators as class fields per standard practice.

## Relation to Other Cases

- **ELITEA-2350/2351** (agent hub page loads): predecessor cases covering the initial populated state; this case extends the coverage to the empty state.
- **ELITEA-2352/2353** (category filter): sibling cases exercising the filter rail; if a future case combines "filter + empty state", reuse both the search navigation pattern from this case and the filter-chip interaction from ELITEA-2352.
- **ELITEA-2363** (search behavior): sibling case covering search mechanics in detail (debounce, substring match); this case reuses those findings and adds the empty-state verification.

## Automation-Friendly Spec Summary

**Covered:** empty state rendering when search matches zero agents; layout consistency; all major elements remain functional. **Not covered (not in case scope):** empty state via category filter (case text says "OR", but only search was tested here; implementer should test filter path too if needed for coverage; see Hints for guidance). **Testid gaps:** two messages lack testids (documented, not blocking; fallback text locators provided). **Framework ready:** testid-only locator policy applies; two pre-existing testids reused; no blocking implementation gaps.

---

# Drift Re-analysis (2026-09-09) — card #2079

Amendment by the analyst slot after the merged spec went RED on DEV CI (run
34331579791) and reproduced locally on pristine `automation/base`:

```
tests/ui/agent_hub/test_empty_state.py:96
assert chip_count == 11, f"Expected 11 filter chips visible (2 Featured + 9 Categories), found {chip_count}"
E   AssertionError: Expected 11 filter chips visible (2 Featured + 9 Categories), found 12
```

Everything below was executed live against `http://localhost:5173/elitea-catalog`
(EliteaUI `automation/testids`, DEV backend) on 2026-09-09.

## 1. What the 12th chip is — VERDICT: legitimate product feature, NOT a defect

The rail renders 12 chips. Enumerated live (label — testid), in DOM order:

| # | Section | Label | testid | `data-selected` | visible |
|---|---|---|---|---|---|
| 1 | Featured | Trending | `catalog-agent-category-filter-chip-trending` | false | ✓ |
| 2 | Featured | My Liked | `catalog-agent-category-filter-chip-my-liked` | false | ✓ |
| 3 | Featured | **New** ← the 12th chip | `catalog-agent-category-filter-chip-new` | false | ✓ |
| 4 | Categories | Business Analyst | `…-business-analyst` | false | ✓ |
| 5 | Categories | DevOps | `…-devops` | false | ✓ |
| 6 | Categories | Development | `…-development` | false | ✓ |
| 7 | Categories | Elitea | `…-elitea` | false | ✓ |
| 8 | Categories | Epam | `…-epam` | false | ✓ |
| 9 | Categories | Knowledge & Documentation | `…-knowledge-documentation` | false | ✓ |
| 10 | Categories | Project Management | `…-project-management` | false | ✓ |
| 11 | Categories | Quality Assurance | `…-quality-assurance` | false | ✓ |
| 12 | Categories | Other | `…-other` | false | ✓ |

The extra chip is **"New"**, a third **Featured** entry. It is neither a duplicate
nor an erroneous render — every testid is distinct, every chip is visible, and the
two section headings ("Featured", "Categories") both render exactly once.

**Root cause, traced in source and confirmed on `origin/main`:**

- `EliteaAI/EliteaUI@18170f71` — *"feat: [EL-6238] show entity count on Catalog page
  and highlight the new ones (#927)"*, **2026-09-07**, merged to `main`.
- It added `export const NEW_CATEGORY = 'New';` to
  `src/[fsd]/features/agent-hub/lib/constants/agentHub.constants.js`, injected it into
  `AgentHubHelpers.buildAllCategories()` (`agentHub.helpers.js`), and bumped
  `CatalogBody.jsx`'s `const FEATURED_COUNT = 3; // Trending, My Liked, New` from 2 to 3.

So the rail went 2+9 → **3 Featured + 9 Categories = 12**. This is intended product
behaviour shipped two days before the CI failure. **No bug filed** — filing one would
be reverse-masking a correct product against a stale test artifact. A dedup pass over
all 300 `bug`-labelled issues (real-time list API, not `--search`) found no existing
issue for this area, so nothing to cross-link either.

**The TMS case text is NOT stale either** — it never mentions a count. So there is also
no case-text CLARIFICATION to file. The only stale artifact is the assertion, and it was
an Axis-2 analyst addition, authored by this AFS. This amendment retires it.

## 2. Is case Step 5 still satisfied? — YES

Case Step 5 reads, in full: *"Verify the layout remains consistent with no broken UI
elements."* The count `11` and the enumeration "2 Featured + 9 Categories" appear
**nowhere in the case text**; they were an Axis-2 analyst addition (recorded as such in
this AFS's own Coverage Map). So the question was never *"is 11 or 12 the right number"*
— it is *"what does the case actually demand of the filter rail here, and what shape
states that without re-breaking on every product-data change."*

Live, the layout is fully consistent in the empty state: the rail renders both sections,
all 12 chips are visible and clickable, and nothing is collapsed, clipped or overlaid.
Step 5 holds.

## 3. Why a hardcoded count is the WRONG shape — the structure/data split

The original assertion conflated two things that change for completely different reasons:

| Part of the rail | Source | Changes when | Should a test pin it? |
|---|---|---|---|
| **Featured chips** (Trending, My Liked, New) | **Frontend constants** — `agentHub.constants.js`, injected by `buildAllCategories()`, sliced by `FEATURED_COUNT` in `CatalogBody.jsx` | the UI team deliberately ships a feature | **YES** — product *structure*; a red test is the correct, informative signal |
| **Category chips** (Business Analyst … Other) | **Backend data** — `GET /api/v2/elitea_core/agent_categories/prompt_lib/{PUBLIC_PROJECT_ID}`, live-confirmed returning 9 `{name, is_default}` rows | an admin adds/removes/renames a category tag on DEV, at any time, with no code change | **NO** — product *data*; pinning it makes the spec a tripwire on someone else's content |

`assert chip_count == 11` pinned both halves with one number, so a routine data change and
a deliberate feature change were indistinguishable — and the failure message named neither.
**Bumping 11 → 12 would repeat the mistake**: it re-pins the data half, and the very next
category tag added on DEV turns this spec red again with the same uninformative message.
So no, a hardcoded product-data count is not the right shape, and this amendment does not
adopt one.

## 4. The Step-5 filter-rail assertion — the specified shape

Four assertions, made **in the empty state** (i.e. after this AFS's step 4), replacing the
single `assert chip_count == 11`:

**Oracle.** Capture the categories response the page's OWN load fires — wrap
`agent_hub.navigate()` in `page.expect_response(...)` matching
`**/elitea_core/agent_categories/prompt_lib/**`. RTK-Query caches per page session, so a
fresh `goto` fires it exactly once (live-confirmed). Then:

```
api_names        = {c["name"] for c in body["categories"]}          # live: 9 names, incl. "Other"
FEATURED_LABELS  = ("Trending", "My Liked", "New")                  # frontend constants, see below
expected_labels  = set(FEATURED_LABELS) | api_names                 # live: 12
```

- **A — exact count.** `expect(chips).to_have_count(len(expected_labels), timeout=10_000)`
  where `chips = agent_hub.get_visible_category_filter_chips()` (existing method, existing
  `AGENT_CATEGORY_FILTER_CHIP_PREFIX` constant). Catches a **duplicated** or **dropped**
  chip, which set-equality alone cannot.
  *Keep the auto-retrying `expect()`, not a one-shot `.count()`* — the rail's categories
  fetch settles a beat after the content grid, a race already documented in
  `test_catalog_default_agents_tab.py`'s own Step 5 comment.
- **B — set membership.** Rendered chip label set `== expected_labels`. The failure message
  must name the delta both ways — `missing: {...}` and `unexpected: {...}` — so the next
  drift is triaged in seconds instead of a session (the concrete cost this amendment paid).
- **C — head visibility.** Each of the three `FEATURED_LABELS` chips individually
  `expect(...).to_be_visible()`, addressed by exact testid through the existing
  `CATEGORY_FILTER_CHIP` template constant (`…-trending`, `…-my-liked`, `…-new`).
- **D — tail visibility.** The `Other` chip (`…-other`) `expect(...).to_be_visible()`.
  `Other` is the other frontend constant — `buildAllCategories()` strips it from the sorted
  middle and re-appends it last — so it is the deterministic **end** of the rail.

**Why C and D are load-bearing, not decoration.** Playwright's `to_have_count` matches
*attached* elements, including hidden ones. A collapsed or `display:none` rail would satisfy
A and B on its own. C+D pin the rail's **head and tail** as genuinely visible, so a rail that
is collapsed, hidden, clipped or emptied fails — which is exactly the constraint case Step 5
carries. A+B+C+D together also cost **zero new locators**: all four use constants already on
`AgentHubPage`.

**What each real-world change now does:**

| Change | Result | Correct? |
|---|---|---|
| Admin adds/removes a category tag on DEV | **passes** — `api_names` moves with it | ✓ the tripwire this amendment removes |
| UI team adds a 4th Featured bucket | **fails**, naming `unexpected: {'<name>'}` | ✓ a real structural change, worth one informed red |
| Rail collapsed / hidden / emptied | **fails** at C or D | ✓ the case's actual point |
| A chip rendered twice, or one dropped | **fails** at A (and B for a drop) | ✓ strictly stronger than the old shape |
| Backend returns a category the rail never renders | **fails** at A and B | ✓ new coverage the old shape had no way to express |

### Fidelity — compliant, and NOT a declared improvisation

Deriving the expected set from the response the product itself fetched is the pattern
`.agents/testing.md` § Fidelity policy prescribes by name: *"Capture the real response and
assert the UI against it. The response is the oracle, not a payload you wrote."* — and its
worked row *"assert the invariant: `rendered_count == len(body["items"])`"* is this
assertion almost verbatim. Nothing is fabricated, injected or replaced; the test only
**reads** a real response.

- **No § Fidelity Declaration row is owed** — there is no substitution, transit or terminal.
- **Not a declared improvisation** — the canon has an explicit, named shape for this; no
  canon gap is being filled, so § Declared-improvisation protocol does not engage.
- ⚠️ **Implementer note:** use `page.expect_response` (passive observation). Do **not** reach
  for `page.route` — the reviewer's mechanical provenance grep must return 0 hits, and a
  `route.fulfill` here would be a textbook terminal substitution.
- Locator policy: testid-only, satisfied — all four assertions run through existing
  class-level `LocatorDescriptor` fields and `[data-testid=` template constants. **No new
  locators, no new testids, and no `get_by_role`/text handles are introduced.**

### `FEATURED_LABELS` — why pinning these three is legitimate

They are not product data; they are `TRENDING_CATEGORY` / `MY_LIKED_CATEGORY` /
`NEW_CATEGORY` in `agentHub.constants.js`, assembled in a fixed order by
`buildAllCategories()`. The API cannot change them. Spec them as a **named page-object
constant with a source pointer in its comment** (`agentHub.constants.js` +
`CatalogBody.jsx`'s `FEATURED_COUNT`), so the next UI-team change to the Featured rail is a
one-line, obviously-correct edit rather than an archaeology exercise. That is the whole
difference between this and the `11` it replaces: the constant now names *what* it pins and
*where that truth lives*.

## 5. The other 7 case elements — re-verified live 2026-09-09, all still hold

Full clean pass: fresh `goto` → type `xyznonexistent123` into `catalog-search-input` → empty
state. No self-inflicted requests in this pass (see the caveat below).

| Case element | Observed live | Verdict |
|---|---|---|
| 1 Navigate to Agent Hub | URL `http://localhost:5173/elitea-catalog`; title `ELITEA Catalog - Private`; `catalog-page-heading` = "Welcome to ELITEA Catalog!", visible | ✓ holds |
| 2 Search term matching no agents | `catalog-search-input` accepted the term; value retained as `xyznonexistent123`; grid emptied | ✓ holds |
| 3 "No agents found" | `catalog-no-results-title` visible, text exactly `No agents found`, computed opacity `1` | ✓ holds |
| 4 Helper message | `catalog-no-results-description` visible, text exactly `Try adjusting your search terms` | ✓ holds |
| 5 Layout — heading | still visible with unchanged text | ✓ holds |
| 5 Layout — search input | still visible, term retained, interactive | ✓ holds |
| 5 Layout — tabs | `catalog-agents-tab` visible `aria-selected="true"`; `catalog-skills-tab` visible `aria-selected="false"` | ✓ holds |
| 5 Layout — filter rail | 12 chips, **all** visible, both section headings render once each | ✓ holds (assertion shape amended above) |
| 5 Layout — zero agent cards | `[data-testid^="catalog-agent-card-"]` → **0** (6 before the search) | ✓ holds |
| 5 Console cleanliness | **0 errors, 0 warnings** across the whole flow | ✓ holds |

Only the filter-rail assertion shape drifted. Nothing else regressed.

⚠️ **Exploration caveat worth keeping (cost a false alarm during this analysis).** An earlier
pass showed 2 console errors — both **self-inflicted**, not product errors: calling `fetch()`
on `/api/v2/...` from `browser_evaluate` is unauthenticated, gets 302'd to
`https://dev.elitea.ai/forward-auth/auth_oidc/login`, and is **cross-origin** from
`http://localhost:5173`, producing a CORS error plus `net::ERR_FAILED`. Same localhost
topology already documented for `/socket.io/` in `.agents/testing.md`. **Read the response
off the captured network request instead** (`browser_network_request … part=response-body`),
never re-issue it from the page — and always re-verify console cleanliness on a pass with no
analyst-injected requests, as was done here.

## 6. Provenance-grep false negative — canon gap, question card filed

The closure-record verification block in `.agents/workflow.md` § Closure record reports both
chip-testid prefixes as **absent from `origin/main` and from `automation/testids`**. That is
**wrong** — they are on both. Stage 1 finds the line; stage 2's filter
`grep -iE '(data-testid|testid[[:space:]]*[:=])'` discards it, because the wiring reads:

```
src/[fsd]/features/agent-hub/ui/AgentsTab.jsx:246:  chipTestIdPrefix="catalog-agent-category-filter-chip"
src/[fsd]/features/skill-hub/ui/SkillsTab.jsx:247:  chipTestIdPrefix="catalog-skill-category-filter-chip"
src/[fsd]/shared/ui/category/CategoryRail.jsx:26:   data-testid={chipTestIdPrefix ? `${chipTestIdPrefix}-${slugifyCategory(category)}` : undefined}
```

In `chipTestIdPrefix=`, `testid` is followed by `Prefix=`, not by `[:=]` — so the filter drops
it. This is a **third** shape in the same family the doc has already patched twice (`-i` for
`buttonTestId=`, `[:=]` for `testId:`), and it is exactly the false-negative class that writes
a wrong "not on main" row into a closure record. Filed as **question card #2100** (a
regression of the closed #553, same family). Until it is fixed, on this surface **read the
stage-1 hits rather than counting them**.

## 7. Transferable disposition — for sibling card #2099 (`test_catalog_default_agents_tab.py`)

Verified live in the same session, so the sibling needs no re-exploration:

- The Skills tab drifted **identically**: `catalog-skill-category-filter-chip-*` also renders
  **12** chips, same third Featured entry "New". `SkillsTab.jsx:74` calls
  `SkillHubHelpers.buildAllCategories()`, which injects `SkillHubConstants.NEW_CATEGORY` exactly
  as the agent-hub helper does, through the same shared `CatalogBody.jsx` / `CategoryRail.jsx`
  with the same `FEATURED_COUNT = 3`.
- So **both** of that spec's hardcoded assertions are stale, not one:
  `expect(agent_chips).to_have_count(11)` at its Step 5 **and**
  `expect(skill_chips_after).to_have_count(11)` at its Step 8.
- Same disposition applies verbatim, per tab: **do not bump 11 → 12.** Derive the expected set
  from that tab's own categories response and assert A+B+C+D. The skills side needs its own
  oracle request (skill-scoped `entity_coverage`), captured the same way.
- **Its cross-tab `to_have_count(0)` assertions are NOT affected and must stay exactly as they
  are** — `expect(skill_chips).to_have_count(0)` on the Agents tab and
  `expect(agent_chips_after).to_have_count(0)` on the Skills tab assert *absence* of the other
  tab's prefix. Absence is structural, carries no product data, and is that spec's primary
  content-switch signal. Live-confirmed still true: on the Skills tab, skill chips = 12 and
  agent chips = **0**. Leave them alone.
