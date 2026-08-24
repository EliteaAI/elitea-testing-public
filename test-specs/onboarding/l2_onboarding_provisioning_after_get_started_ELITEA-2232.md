# ELITEA-2232: Onboarding — clicking "Sure, let's go!" starts the account-status poll and shows the tips card 1/48 with the "Configuring Personal project..." progress footer

**TMS ID:** ELITEA-2232
**Priority:** medium
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding
**Analysed:** 2026-08-24 · live, `http://localhost:5173` (EliteaUI `automation/testids`, DEV backend)
**Surface digest:** `test-specs/onboarding/_surface.md`
**Clarification filed:** #1756 (case-text drift on step 9 + under-specified precondition — read it before implementing)

---

## Summary

From the first-login Welcome card, clicking **"Sure, let's go!"** replaces the card with the
**onboarding tips card** positioned at **1 / 48**, renders the **progress footer**
("Configuring Personal project..." / "about 5 min" / a determinate progress bar), and starts a
**5-second poll of `GET /api/v2/social/author/`** which was not running before the click. No
sidebar and no project dropdown exist while that state is on screen. When the poll finally sees a
non-null `personal_project_id`, the footer unmounts and the sidebar appears **on `/onboarding`
itself** with the entity menu and `Project: Private` in the project selector.

This is the **third** onboarding state pair. The two already automated:
`test_onboarding_welcome.py` (ELITEA-2231) stops *before* the click; `test_onboarding_tips_card.py`
(ELITEA-2235) starts *after* provisioning is already done. **Nothing merged asserts the
provisioning state at all** — every existing onboarding spec asserts
`onboarding-progress-footer` is *absent*. This case is the only one that asserts it present.

---

## Preconditions

- Authenticated user (localhost: `auth_state` fast-path via `VITE_DEV_TOKEN`, no Keycloak login).
- **First-login state:** `user.personal_project_id` must be **null** — this is what renders the
  Welcome card (`Onboarding.jsx:158`) and what keeps the page in the *tour + provisioning* state
  after the click (`Onboarding.jsx:182`). No account in this environment is in that state
  naturally, so it is established by the existing
  `OnboardingPage.mock_fresh_user_state()` route mock — see § Fidelity Declaration.
- Fresh browser context (the product writes `sessionStorage.onboarding_state`; a leftover `'true'`
  makes `showTour` initialise to `true` and skips the Welcome card entirely —
  `Onboarding.jsx:36-37`). The suite's per-test context satisfies this; do not reuse a context
  across this spec and the other onboarding specs.
- No test data, no seeding, no cleanup.

---

## Fidelity Declaration

| # | What is substituted | Transit or terminal | Authority / what the system still produces |
|---|---|---|---|
| 1 | `GET /social/author/` response has `personal_project_id` forced to `null` (all other fields byte-identical, fetched live via `route.fetch()`) | **Transit** | Establishes the case's own stated precondition — the first-login account state — which no available account has. Every asserted observable in steps 1-10 is then *rendered by the product* from that state: the tour card, the counter, the tip text, the footer copy, the progress value, the poll cadence, the absent sidebar. Sanctioned mechanism: lead ruling, batch `onboarding-w1` DECISIONS § D3 (already merged in `test_onboarding_welcome.py`). |
| 2 | The mask is **released mid-test** so the next poll receives the *unmodified* backend response | **Transit** (timing control) | Reaches step 11. Once released, the app's completion path runs on a **100 % genuine backend payload** — the real `personal_project_id`, the real project list, the real sidebar and the real project name. Nothing asserted in step 11 was authored by the test. This is the "delay a real response so a transient state is observable" shape (`.agents/testing.md` § Fidelity policy) applied in reverse: the real ready-state is withheld for a few seconds so the provisioning state can be observed, then delivered unaltered. |

**Coverage boundary (state it in the docstring):** this spec verifies the **UI contract of the
provisioning state and of the transition out of it**. It does **not** verify that the backend
actually provisions a personal project for a brand-new account — that is an API/e2e concern with
a ~5-minute real wait and no available fresh account. Do **not** "improve" this by asserting any
value the mock authored; the mock authors exactly one field (`personal_project_id: null`) and no
assertion reads it.

**⚠ Extension beyond D3 — flag for the lead.** D3 sanctioned *installing* the author-details
mock. Substitution #2 (releasing it mid-test to observe the completion transition) is a new
application of the same mechanism and is declared here per `.agents/role-overrides.md`
§ Declared-improvisation protocol. If the lead rules it out, steps 1-10 remain fully automatable
as specced and step 11 becomes a `blocked` row — the rest of the spec does not depend on it.

---

## Entry path (how the implementer reaches the screen)

```
context (fresh) → OnboardingPage.mock_fresh_user_state()   # before any navigation
                → navigate("/onboarding")
                → onboarding-welcome-card visible           # ELITEA-2231's screen
                → [quiet window: assert NO author-details poll]
                → click onboarding-welcome-get-started-button
                → onboarding-tour-container + onboarding-progress-footer  # THIS case's screen
                → [poll observation window]
                → clear_author_details_mock()               # substitution #2
                → onboarding-workspace-ready-title + sidebar on /onboarding
```

Navigate to `/onboarding` **directly** — with the mock installed root `/` also redirects there,
but the direct navigation is one hop and is what the merged ELITEA-2231 spec does.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| Pre | User is logged in | Authenticated session | `auth_state` (localhost dev token) | fixture | **ready** |
| Pre* | *(implied)* first-login user, no personal project | Welcome card renders | `mock_fresh_user_state()` | § Fidelity Declaration #1 | **ready** — clarification #1756 § 2 asks the TMS case to state this precondition |
| 1 | Click "Sure, let's go!" on the Welcome page | Completes without error, produces the expected UI state | `onboarding-welcome-get-started-button` click | `expect(tour_container).to_be_visible()` after the click; no error-level console message | **ready** |
| 2 | Welcome card is replaced by the onboarding tips slide view | Card gone, tour shown | `onboarding-welcome-card` (absence) + `onboarding-tour-container` | `expect(welcome_card).to_have_count(0)` **and** `expect(tour_container).to_be_visible()` | **ready** — both halves matter: "replaced" is a *count-0* + *visible* pair, not just visibility |
| 3 | ELITEA logo shown at the top center of the page | Wordmark visible | `onboarding-page-logo` | `expect(page_logo).to_be_visible()` | **ready** — this case says "of the **page**", which is exactly right (`Onboarding.jsx:150-155`, above the panel) |
| 4 | First slide title "Tip 1: Welcome to ELITEA" | Title present | `onboarding-tour-tip-content` | `to_contain_text("Tip 1: Welcome to ELITEA")` | **ready** — steps 4-6 share one markdown node (§ Handles note 1) |
| 5 | Slide description (verbatim, see § Expected values) | Description present | `onboarding-tour-tip-content` | `to_contain_text(_EXPECTED_TIP1_DESCRIPTION)` | **ready** — captured verbatim live |
| 6 | Quick Action "Click the ELITEA logo (top-left) to explore all available menus." | Quick-action present | `onboarding-tour-tip-content` | `to_contain_text("Quick Action: Click the ELITEA logo (top-left) to explore all available menus.")` | **ready** — rendered text drops the markdown `**` around `Quick Action:` |
| 7 | Slide counter shows "1 / 48" | Counter is exactly `1 / 48` | `onboarding-tour-page-indicator` | `to_have_text("1 / 48")` | **ready** |
| 8 | Progress bar at the bottom with label "Configuring Personal project..." and "about 5 min" | Footer + label + time + bar visible | `onboarding-progress-footer`, `-status-label`, `-estimated-time`, `-progress-bar` | `to_be_visible()` on the footer + `to_have_text("Configuring Personal project...")` + `to_have_text("about 5 min")` + `to_be_visible()` on the bar | **ready** — **the only merged assertion of this footer in the suite** (the other 3 onboarding specs assert it absent) |
| 9 | Provisioning begins only now — after the click — and was not running before | see disposition | `GET **/api/v2/social/author/` request counting around the click | before: 0 requests in a ≥7 s quiet window after the Welcome card settles; after: ≥2 requests within 12 s | **ready, REWRITTEN — case-text drift, clarification #1756 § 1.** The click issues **no** provisioning call; `handleShowTour()` (`Onboarding.jsx:66-85`) starts a 5 s poll of `GET /api/v2/social/author/`. Live cadence measured: **+4.9 s / +9.9 s / +14.9 s**, zero such requests in the pre-click window. The poll-start *is* the observable "it begins only now"; asserting a provisioning call would assert something that does not exist. |
| 10 | No sidebar navigation and no project dropdown while the project is still loading | Both absent | `sidebar-toggle`, `project-selector-trigger` | `expect(...).to_have_count(0)` for both, while the footer is visible | **ready** — confirmed live (`MainSidebar.jsx` returns null when `isOnboardingPage && !user.personal_project_id`). Case wording carries a double negative (#1756 § 3); the behaviour is unambiguous. |
| 11 | After loading completes, a private project appears in the left-menu dropdown with sidebar entities displayed | Footer gone; sidebar + project dropdown present, showing the private project | `onboarding-progress-footer` (absence), `sidebar-toggle`, `project-selector-trigger`, `sidebar-menu-item-*`, `project-selector-option-Private` (**needs adding**) | `expect(progress_footer).to_have_count(0)`; `to_be_visible()` on toggle + selector; `expect(project_selector_trigger).to_contain_text("Private")`; `expect(sidebar_menu_item("chat")).to_be_visible()`; open the dropdown → `expect(project_option("Private")).to_be_visible()` | **ready** — reached via § Fidelity Declaration #2. All values from the real backend response. |
| Final | Private project on the left-menu dropdown with sidebar entities displayed | as step 11 | same | same | **ready** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| Progress bar is a *determinate* MUI bar that **advances** | Step 8 only asks that a bar is *visible* — a frozen or indeterminate bar would pass that while telling the user nothing. `Onboarding.jsx:71-73` increments `progress` by `95/150` every second from a start of `5`. Measured live: `aria-valuenow` 5 → 13 after 12 s → 16 after 18 s. | `expect(progress_bar).to_have_attribute("role", "progressbar")`; capture `aria-valuenow` right after the click, assert it is at its baseline (`5 <= initial <= 12`), then after a ≥6 s wait assert `int(later) > int(initial)`. **Amended at implementation (2026-08-24):** the AFS originally specified exact equality with `"5"`. The read happens after the footer's visibility assertion, i.e. inside — but not reliably at the start of — the product's first 1 s interval tick, so exact equality is a stopwatch race against the 3× merge gate while carrying no extra meaning. The bounded form asserts the same observable (the bar starts at its documented baseline and then moves); shipped value observed live: `5`. |
| Previous-slide button is **disabled** | Independent proof the card is really at the FIRST slide — a rendering bug could print `1 / 48` while the position is wrong (`TourContent.jsx: disabled={currentStep === 1}`). Same rationale as ELITEA-2235's Axis 2. | `expect(tour_prev_button).to_be_disabled()` |
| `onboarding-workspace-ready-title` is **absent** during provisioning | The provisioning state and the ready state are mutually exclusive in `Onboarding.jsx:182/213`; asserting the banner's absence is what proves the page is genuinely in the *provisioning* state and not merely rendering a footer. | `expect(workspace_ready_title).to_have_count(0)` while the footer is visible |
| `sessionStorage.onboarding_state == "true"` after the click | The click's only persisted side effect (`Onboarding.jsx:68`); it is what makes a page refresh resume the tour instead of re-showing the Welcome card. Cheap, and it distinguishes "the click was handled" from "React re-rendered for another reason". | `page.evaluate("sessionStorage.getItem('onboarding_state')") == "true"` |
| No error-level console messages across the whole flow | Standard side channel. Verified clean live: **0 error messages** over the full run (mask → click → poll → release → sidebar). | `assert not console_errors` |

**Note on the console check:** the `#1753` MUI focus error documented in `_surface.md` § quirk 4
fires only on the first-visit interactive-tour prompt, which appears after **"Jump in now!"**
navigates to `/chat`. **This spec must not click "Jump in now!"** — step 11's observable is fully
satisfied on `/onboarding` (the sidebar renders there once the project is ready). Keeping the spec
on `/onboarding` keeps the console assertion clean and unfiltered, and leaves the jump-in flow to
ELITEA-2241 where it belongs.

---

## Handles Reference

Provenance verified 2026-08-24 after `cd ../EliteaUI && git fetch origin`, two-stage grep per
`.agents/workflow.md` § Closure record.

| Element | testid | Provenance | Source |
|---|---|---|---|
| Welcome card (presence → absence) | `onboarding-welcome-card` | on-`automation/testids` only (awaiting human promotion to main) | `Welcome.jsx:12-15` |
| "Sure, let's go!" button | `onboarding-welcome-get-started-button` | on-`automation/testids` only | `Welcome.jsx:59-67` |
| ELITEA wordmark | `onboarding-page-logo` | on-`automation/testids` only | `Onboarding.jsx:150-155` |
| Tips-card wrapper | `onboarding-tour-container` | on-`automation/testids` only | `OnboardingTour.jsx` |
| Tip markdown block (title + description + quick action) | `onboarding-tour-tip-content` | on-`automation/testids` only | `TourContent.jsx` |
| Slide counter | `onboarding-tour-page-indicator` | on-`automation/testids` only | `TourContent.jsx` |
| Previous-slide button | `onboarding-tour-prev-button` | on-`automation/testids` only | `TourContent.jsx` |
| Progress footer | `onboarding-progress-footer` | on-`automation/testids` only | `Onboarding.jsx:182-212` |
| "Configuring Personal project..." label | `onboarding-progress-status-label` | on-`automation/testids` only | `Onboarding.jsx:188-194` |
| "about 5 min" | `onboarding-progress-estimated-time` | on-`automation/testids` only | `Onboarding.jsx:195-201` |
| Progress bar | `onboarding-progress-bar` | on-`automation/testids` only | `Onboarding.jsx:204-209` |
| Workspace-ready title (absence, then presence) | `onboarding-workspace-ready-title` | on-`automation/testids` only | `WorkspaceIsReady.jsx` |
| Sidebar toggle (absence, then presence) | `sidebar-toggle` | **on-main ✓** | `SidebarBody.jsx:221` |
| Project dropdown trigger (absence, then presence) | `project-selector-trigger` | **on-main ✓** | `SidebarProjectSelect.jsx:94` |
| Sidebar entity menu items | `sidebar-menu-item-{value}` (dynamic) | on-`automation/testids` only | `SidebarBody.jsx:272` (`testId={...}` prop) |
| Project option inside the open dropdown | `project-selector-option-{label}` (dynamic) | **ADDED at implementation** — EliteaAI/EliteaUI@bb8b9adc, on-`automation/testids` only (awaiting human promotion to main) | `SidebarProjectSelect.jsx` `customRenderOption` |

### The one testid to add — **DONE** (EliteaAI/EliteaUI@bb8b9adc, `automation/testids`)

`SidebarProjectSelect.jsx`'s `customRenderOption` renders each project row with **no testid**, so
step 11's "appears on left-menu dropdown" cannot be asserted on the option itself. Add it via the
`add-data-testid` skill, at the **feature call site** (the render function lives in
`SidebarProjectSelect.jsx`, not in the shared `ProjectSelect`, so nothing feature-scoped leaks
into a shared component):

```jsx
<Box
  data-testid={`project-selector-option-${option?.label}`}
  sx={optionStyles.optionRow}
>
```

Dynamic testid → the compliant page-object shape is a **class-level template constant**
(`.agents/testing.md` § Locator policy):

```python
PROJECT_SELECTOR_OPTION = '[data-testid="project-selector-option-{}"]'
```

Live value for the standard test user: `project-selector-option-Private` (trigger text reads
`P / Project: / Private`). It is an attribute-only addition — no new DOM node, no new hook, no
render-prop change (zero-functional-impact check clean).

### Handles notes

**Note 1 — steps 4/5/6 share one node.** `TourContent.jsx` renders the tip as a single
`<Markdown>` inside `onboarding-tour-tip-content`; heading, description and Quick-Action paragraph
have no testids of their own (that DOM is produced by the markdown renderer, not by app JSX).
Assert the three strings with `to_contain_text` on the one node — decomposition, not a dropped
step. Same treatment as the merged ELITEA-2235 spec.

**Note 2 — the sidebar entity menu fills in progressively.** Immediately after the ready
transition only `sidebar-menu-item-skills` and `-applications` are in the DOM; the full set
(`chat`, `agents`, `pipelines`, `skills`, `toolkits`, `mcps`, `credentials`, `applications`,
`artifacts`) is complete within ~3 s. Use Playwright's auto-waiting `expect(...).to_be_visible()`
on a specific item (`sidebar-menu-item-chat` is a good anchor) — **never** snapshot the item list
and assert its length, which is what makes this look flaky.

**Note 3 — page object.** `automation/pages/onboarding_page.py` (`OnboardingPage`) already has
every locator this case needs except the project-dropdown option and the sidebar entity item, plus
`mock_fresh_user_state()` / `clear_author_details_mock()`. Extend it (do not create a sibling —
"one testid, one file"), adding: the `PROJECT_SELECTOR_OPTION` / `SIDEBAR_MENU_ITEM` template
constants with accessor methods, and an action that clicks the Get-Started button. Keep every
ELITEA-2231/2235/2236/2241 locator byte-identical.

---

## Expected values (verified live 2026-08-24)

| What | Exact value |
|---|---|
| Button label | `Sure, let's go!` |
| Slide counter | `1 / 48` |
| Tip title (substring) | `Tip 1: Welcome to ELITEA` |
| Tip description | `ELITEA is your AI-powered workspace where you create intelligent agents, automate workflows with pipelines, and chat with powerful AI models. Everything you need is organized in the left sidebar for easy access.` |
| Quick action | `Quick Action: Click the ELITEA logo (top-left) to explore all available menus.` |
| Progress status label | `Configuring Personal project...` (three ASCII dots, not `…`) |
| Estimated time | `about 5 min` |
| Progress bar initial `aria-valuenow` | `5` (grows ≈ 0.63/s: 13 @ +12 s, 16 @ +18 s, capped at 95) |
| Poll endpoint | `GET http://localhost:5173/api/v2/social/author/` |
| Poll cadence after the click | +4.9 s, +9.9 s, +14.9 s (5 s interval; **zero** in the pre-click window) |
| Pre-click author-details calls | 2, both during initial page load (+0.9 s, +1.6 s) — the quiet window must start **after** the Welcome card is visible |
| `sessionStorage.onboarding_state` after click | `"true"` |
| Ready-state banner title | `Your Elitea workspace is ready!` |
| Project selector trigger text (after ready) | `P\nProject:\nPrivate` — assert `to_contain_text("Private")` |
| Console errors, whole flow | **0** |

---

## Suggested test shape

New spec file `automation/tests/ui/onboarding/test_onboarding_provisioning.py`, class
`TestOnboardingProvisioning`, one test
`test_get_started_starts_provisioning_poll_and_shows_tips_with_progress_footer`.
Markers: `p2` (medium), `onboarding`, `regression`, `ui`. `allure.step("Step N — ...")` per case
step, with steps 4-6 inside one step block if the implementer prefers (keep the numbering).

Request counting for step 9 — count on the page's own `request` event, no interception:

```python
author_polls: list[float] = []
page.on("request", lambda r: author_polls.append(time.monotonic())
        if "/social/author/" in r.url else None)
```

Take a marker index before the quiet window and before the click; assert 0 new entries across the
quiet window and ≥2 new entries within 12 s of the click. **No `sleep()` for the ready
transition** — after `clear_author_details_mock()` use
`expect(workspace_ready_title).to_be_visible(timeout=20_000)` (the poll fires at most 5 s later).
The two deliberate fixed waits (the pre-click quiet window and the progress-advance window) are
*observation windows*, not waits-for-a-condition — there is nothing to wait *for* (the assertion
is that nothing happened / that a number moved), so `page.wait_for_timeout()` is the correct tool
there and should be commented as such.

---

## Blocked Steps

None.

## Known Defects

None. One **clarification** filed: **#1756** (case text claims the click triggers provisioning;
precondition under-specified; step 10 double negative). No product defect was found — the product
is correct in every observed respect.

---

## Evidence

- `automation/test-results/screenshots/ELITEA-2232-step-00-welcome.png` — Welcome card, pre-click
- `automation/test-results/screenshots/ELITEA-2232-step-02-tour-provisioning.png` — tips card 1/48 + "Configuring Personal project..." footer
- `automation/test-results/screenshots/ELITEA-2232-step-11-ready-with-sidebar.png` — ready state: footer gone, sidebar + `Project: Private`
- `automation/test-results/screenshots/ELITEA-2232-step-11-project-dropdown.png` — project dropdown open, `Private` listed
- `automation/test-results/screenshots/ELITEA-2232-step-11-final.png` — full sidebar entity menu on `/onboarding`
