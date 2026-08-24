# Exploration digest — Onboarding surface (`/onboarding`)

Handle cache from live runs. **Verify handles as you use them** — this is not a substitute for
executing your own case.

| Field | Value |
|---|---|
| Last verified | 2026-08-24 (qa-engineer, batch `onboarding-w2`, cases ELITEA-2235/2236/2241) |
| Target | `http://localhost:5173/onboarding` — EliteaUI `automation/testids`, DEV backend |
| Source | `src/pages/Onboarding/Onboarding.jsx`, `src/[fsd]/features/onboarding/ui/{Welcome,OnboardingTour,TourContent,WorkspaceIsReady}.jsx` |

---

## The three states of `/onboarding` (the thing to understand first)

`Onboarding.jsx` renders one of three states, gated only on Redux `user.personal_project_id`
and local state:

| State | Gate | Renders | Whose case |
|---|---|---|---|
| **Welcome** | `!showTour && !user.personal_project_id && user.id` | `Welcome` card, "Sure, let's go!" | ELITEA-2231 (needs the author-details mock) |
| **Tour + provisioning** | `showTour && !thePrivateProjectIsReady` | `OnboardingTour` + `onboarding-progress-footer` ("Configuring Personal project… / about 5 min") | ELITEA-2232-ish |
| **Tour + ready** | `showTour && thePrivateProjectIsReady` | `OnboardingTour` + `WorkspaceIsReady` ("Jump in now!") | ELITEA-2235 / 2236 / 2241 |

`showTour` initialises to `hasClickedGetStarted || !!user.personal_project_id`, and the effect at
`Onboarding.jsx:130-134` sets `thePrivateProjectIsReady = true` whenever `user.personal_project_id`
is truthy.

**⇒ An ordinary authenticated user (who has a personal project) navigating to `/onboarding`
lands directly in the tour+ready state — no mock, no substitution, no fixture.** That is the
honest route for every tips-card / banner case. The first-login route (`personal_project_id:
null`) can NEVER show the workspace-ready banner: with it null the page stays in the provisioning
state. Do not mock `/social/author/` for tips-card cases.

Navigate to `/onboarding` **directly**. Root `/` redirects there only for a user *without* a
personal project; for the standard test user root lands on `/chat`.

---

## Confirmed testids (live 2026-08-24)

### Page shell — `Onboarding.jsx`
| testid | Notes |
|---|---|
| `onboarding-page-container` | full-screen wrapper |
| `onboarding-page-logo` | ELITEA wordmark, **above** the card (not inside it) |
| `onboarding-progress-footer` | present ONLY in the tour+provisioning state |
| `onboarding-progress-status-label` | "Configuring Personal project..." |
| `onboarding-progress-estimated-time` | "about 5 min" |
| `onboarding-progress-bar` | MUI LinearProgress |

### Tips card — `OnboardingTour.jsx` / `TourContent.jsx`
| testid | Notes |
|---|---|
| `onboarding-tour-container` | card wrapper |
| `onboarding-tour-tip-content` | **one markdown node** carrying tip title + description + Quick Action — no per-part testids possible (markdown-rendered DOM) |
| `onboarding-tour-page-indicator` | `"{currentStep} / 48"` — 48 = `onboardingTips.length` |
| `onboarding-tour-prev-button` | `disabled` at slide 1 |
| *next button* | **no testid** — add if a case navigates forward |
| *slide image* | **no testid** — requested as `onboarding-tour-tip-image` (ELITEA-2236 AFS) |
| *expand icon* | **no testid** — `aria-label="View tour in full screen"`; requested as `onboarding-tour-fullscreen-button` |
| *fullscreen dialog / title / X* | **no testids** — requested as `onboarding-tour-fullscreen-{dialog,title,close-button}` |

### Workspace-ready banner — `WorkspaceIsReady.jsx`
| testid | Notes |
|---|---|
| `onboarding-workspace-ready-title` | "Your Elitea workspace is ready!" |
| `onboarding-workspace-ready-jump-in-button` | "Jump in now!" · computed `background-color: rgb(106, 232, 250)` (dark theme) · navigates to `/chat` |

### Welcome state — `Welcome.jsx` (ELITEA-2231, for reference)
`onboarding-welcome-{card,illustration,title,greeting,body-text,secondary-text,get-started-button}`.

**Provenance:** every `onboarding-*` testid above is on `origin/automation/testids` only —
**not yet on `origin/main`** (verified 2026-08-24 with `git fetch` + two-stage grep). `sidebar-toggle`
and `project-selector-trigger` ARE on main. `sidebar-menu-item-*` is a dynamic testid
(`SidebarBody.jsx:272`), `automation/testids` only.

---

## Quirks worth knowing

1. **Duplicate testids while the fullscreen dialog is open.** `OnboardingTour` keeps the embedded
   `TourContent` mounted and renders a second copy inside the `Dialog`. So
   `onboarding-tour-tip-content` / `-page-indicator` / `-prev-button` each resolve to **2 visible
   nodes** in that state → unscoped `to_be_visible()` is a strict-mode violation. Scope with
   class constants: `'[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="…"]'`.
   Closing the X unmounts the dialog entirely (no `keepMounted`) — counts return to 1.
2. **Visiting `/onboarding` arms an interactive tour on the NEXT page.**
   `handlePersonalProjectReady()` → `markTourPending(FIRST_ELITEA_TOUR_ID)` writes
   `localStorage["interactive-tour:first-elitea:pending"]="true"`; `useProposePendingTour` consumes
   it on the next page and opens the **first-visit prompt** ("New here? … Skip / Start!"). It fires
   on **every** run of this flow, ignoring `prompt-seen`.
3. **That prompt blocks the page.** It is a modal with `InteractiveTourBackdrop`; the backdrop
   intercepts pointer events, so the sidebar is *visible but not clickable* until Skip / Start! /
   Escape. Any spec that interacts with `/chat` after "Jump in now!" must dismiss it first.
   Its Skip/Start buttons and card have **no testids** — requested as
   `interactive-tour-first-visit-{prompt,skip-button}` (ELITEA-2241 AFS).
   The `interactive-tour-complete-title` / `-icon` testids that DO appear inside it come from the
   shared `TourCardHeader` and are mis-scoped — don't bind to them.
4. **Known console error on that path:** `MUI: The modal content node does not accept focus.`
   — deterministic when the first-visit prompt opens (4/4), 0 errors on a control navigation
   straight to `/chat`. Filed as **#1753**; filter it (with the ticket comment) rather than
   asserting a bare "no console errors" after "Jump in now!".
5. `/onboarding` itself is clean: 0 console errors across 4 loads and 2 fullscreen open/close
   cycles.
6. Slide state is component-local `useState` — a fresh context always starts at `1 / 48`; no
   reset, no cleanup, no test data anywhere in this surface.

---

## Page objects

- `automation/pages/onboarding_page.py` — **Welcome state only** (ELITEA-2231), including
  `mock_fresh_user_state()` (author-details route mock). Do not use that mock for tips-card cases;
  extend the page object (or add a sibling) for the tour + banner locators.
- Specs: `automation/tests/ui/onboarding/test_onboarding_welcome.py` (ELITEA-2231).

## Related AFS

- `l2_onboarding-welcome-page_ELITEA-2231.md`, `lmedium_welcome_page_first_login_ELITEA-2231.md`
- `lhigh_onboarding_tips_card_slide_1_of_48_ELITEA-2235.md`
- `lhigh_onboarding_tips_fullscreen_expand_collapse_ELITEA-2236.md`
- `lmedium_onboarding_jump_in_now_ELITEA-2241.md`

---

## Resolved/added during ELITEA-2235 / 2236 / 2241 implementation (test-automation-engineer, 2026-08-24)

Attributed implementation-time facts — the analyst's behavior/scope claims above are unchanged.

**The seven "needs-adding" testids now EXIST** on `EliteaAI/EliteaUI` `automation/testids`
(commit EliteaAI/EliteaUI@3ba7967d, pushed; **not yet on `main`** — human cherry-pick pending,
same as every other `onboarding-*` testid here):

| testid | File |
|---|---|
| `onboarding-tour-fullscreen-button` | `OnboardingTour.jsx` |
| `onboarding-tour-fullscreen-dialog` | `OnboardingTour.jsx` — **on the Dialog's PAPER via `slotProps.paper`** |
| `onboarding-tour-fullscreen-title` | `OnboardingTour.jsx` |
| `onboarding-tour-fullscreen-close-button` | `OnboardingTour.jsx` |
| `onboarding-tour-tip-image` | `TourContent.jsx` |
| `interactive-tour-first-visit-prompt` | `FirstVisitPrompt.jsx` (TourCard root) |
| `interactive-tour-first-visit-skip-button` | `FirstVisitPrompt.jsx` (Skip button) |

**Why the dialog testid is on the paper, not on `<Dialog>`.** MUI spreads a `data-testid` passed
to `<Dialog>` onto the Modal **root**, which is `position: fixed; inset: 0` for *every* dialog —
so a bounding-box "is this fullscreen?" assertion against it passes even with `fullScreen`
removed. The paper is the element MUI resizes for `fullScreen`, and carries `role="dialog"`.
Dialog-scoping is unaffected (header, `DialogContent` and the second `TourContent` are all
descendants of the paper).

**`page.viewport_size` is `None` in the suite's default HEADED mode** (`conftest.py` uses
`no_viewport=True` when `HEADLESS=false`; headless pins 1366x768). Any "compare a box to the
viewport" assertion on this or any other surface must handle that — ELITEA-2236 asserts
origin-anchoring + coverage of `onboarding-page-container` + larger-than-the-embedded-card
unconditionally, and adds the exact viewport equality only when `viewport_size` is set.

**Feature-scoped testids pass cleanly through the shared `TourCard` / `BaseBtn`** — both spread
`...rest` onto their MUI root, so the testid is hardcoded at the FEATURE call site
(`FirstVisitPrompt.jsx`), never inside the shared component. No `testId` prop plumbing needed.

**Page objects (shipped).** The tour/banner locators went into the EXISTING
`automation/pages/onboarding_page.py` (`OnboardingPage`), not a sibling: a sibling would have had
to re-declare `onboarding-page-container` / `-page-logo` / `-progress-footer` /
`onboarding-welcome-card`, which this project's "one testid, one file" convention forbids. The
ELITEA-2231 Welcome locators and `mock_fresh_user_state()` are byte-identical (additive-only).
Dialog-scoped selectors ship as class constants `DIALOG_TIP_CONTENT` / `DIALOG_TIP_IMAGE` /
`DIALOG_PAGE_INDICATOR` with accessor methods `dialog_tip_content()` / `dialog_tip_image()` /
`dialog_page_indicator()`.

**First-visit prompt page object:** `components/interactive_tour.py` → `FirstVisitPromptCard`
(`prompt`, `skip_button`, `wait_for()`, `click_skip()`). It lives with the other interactive-tour
overlays, not in the onboarding page object — the prompt mounts on whatever route is next.

**Specs (shipped, one per case):**
`automation/tests/ui/onboarding/test_onboarding_tips_card.py` (ELITEA-2235),
`test_onboarding_tips_fullscreen.py` (ELITEA-2236),
`test_onboarding_jump_in.py` (ELITEA-2241). All three green first run, 0 reruns, 24.3 s total.
Quirks 1-6 above all confirmed live by the implementation run — including the deterministic
first-visit prompt and the #1753 console error, which the ELITEA-2241 spec filters by that ONE
message with a `# Known defect: #1753` comment.
