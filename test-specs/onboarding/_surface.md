# Exploration digest — Onboarding surface (`/onboarding`)

Handle cache from live runs. **Verify handles as you use them** — this is not a substitute for
executing your own case.

| Field | Value |
|---|---|
| Last verified | 2026-08-24 (batch `onboarding-w3`, cases ELITEA-2237/2238/2239 — slide navigation; before that `onboarding-w2`: ELITEA-2235/2236/2241, then ELITEA-2232) |
| Target | `http://localhost:5173/onboarding` — EliteaUI `automation/testids`, DEV backend |
| Source | `src/pages/Onboarding/Onboarding.jsx`, `src/[fsd]/features/onboarding/ui/{Welcome,OnboardingTour,TourContent,WorkspaceIsReady}.jsx` |

---

## The three states of `/onboarding` (the thing to understand first)

`Onboarding.jsx` renders one of three states, gated only on Redux `user.personal_project_id`
and local state:

| State | Gate | Renders | Whose case |
|---|---|---|---|
| **Welcome** | `!showTour && !user.personal_project_id && user.id` | `Welcome` card, "Sure, let's go!" | ELITEA-2231 (needs the author-details mock) |
| **Tour + provisioning** | `showTour && !thePrivateProjectIsReady` | `OnboardingTour` + `onboarding-progress-footer` ("Configuring Personal project… / about 5 min") | ELITEA-2232 (executed live 2026-08-24 — § The provisioning state) |
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
| `onboarding-tour-next-button` | forward arrow; `disabled` at slide 48 — added 2026-08-24 for ELITEA-2237/2238/2239 (EliteaAI/EliteaUI@f647488d, `automation/testids` only) |
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

- `l2_onboarding-welcome-page_ELITEA-2231.md`
- `l1_onboarding_tips_card_slide_1_of_48_ELITEA-2235.md`
- `l1_onboarding_tips_fullscreen_expand_collapse_ELITEA-2236.md`
- `l2_onboarding_jump_in_now_ELITEA-2241.md`
- `l2_onboarding_provisioning_after_get_started_ELITEA-2232.md`

_(Filename prefixes follow the repo's numeric convention — `l1_` = high, `l2_` = medium,
`l3_` = low. The earlier `lhigh_`/`lmedium_` word forms were renamed 2026-08-24; a
superseded second ELITEA-2231 draft, `lmedium_welcome_page_first_login_ELITEA-2231.md`
— a code-review-only `blocked` analysis — was deleted in the same pass.)_

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


---

## The provisioning state — executed live 2026-08-24 (ELITEA-2232)

The middle state of the three above, reached the only way it can be: install
`OnboardingPage.mock_fresh_user_state()` (nulls `personal_project_id` on `GET /social/author/`,
lead ruling `onboarding-w1` DECISIONS § D3) **before navigating**, go to `/onboarding`, click
`onboarding-welcome-get-started-button`. It is the one state no merged spec asserts — the other
three onboarding specs all assert `onboarding-progress-footer` **absent**.

**What the click actually does** (`Onboarding.jsx:66-85` `handleShowTour`) — worth knowing before
writing any assertion about "provisioning":

1. `sessionStorage.onboarding_state = 'true'` (this is why a reused context skips the Welcome
   card entirely — `showTour` initialises from it at line 36-37; always use a fresh context).
2. Starts a **client-side progress animation only**: `progress` starts at `5` and grows by
   `95/150` per second, capped at 95. Live: `aria-valuenow` 5 → 13 @ +12 s → 16 @ +18 s.
3. Starts a **5 s poll of `GET /api/v2/social/author/`**. Live cadence +4.9 / +9.9 / +14.9 s.

There is **no provisioning API call at all** — provisioning is backend-side, tied to account
creation. The TMS case text says otherwise; filed as clarification **#1756**. Anyone writing
"verify provisioning starts" should assert the *poll start* instead. Careful with the pre-click
baseline: `/social/author/` is fetched **twice during normal page load** (+0.9 s, +1.6 s), so the
"nothing was polling before" window must start after the Welcome card is visible (a ≥7 s quiet
window there is clean, 0 requests).

**Exiting the state.** Releasing the mock (`clear_author_details_mock()`) lets the next poll see
the real `personal_project_id`; the footer unmounts and `WorkspaceIsReady` appears — within 5 s,
no sleep needed, `expect(...).to_be_visible(timeout=20_000)` covers it.

**The sidebar renders on `/onboarding` itself once the project is ready** — this surprised the
analysis and matters for ELITEA-2232 step 11: `MainSidebar` returns null only when
`isOnboardingPage && !user.personal_project_id`, so the moment the id is truthy the full app
sidebar appears *beside the onboarding page*, no navigation required.

| Observable, ready state on `/onboarding` | Value |
|---|---|
| `sidebar-toggle`, `project-selector-trigger` | visible (both **on-main ✓**) |
| `project-selector-trigger` text | `P\nProject:\nPrivate` |
| `sidebar-menu-item-*` | fills in **progressively**: `skills` + `applications` at t+0, the full nine (`chat`, `agents`, `pipelines`, `skills`, `toolkits`, `mcps`, `credentials`, `applications`, `artifacts`) by ~3 s. Anchor on one item with auto-waiting `expect`; never assert the list length. |
| project dropdown option row | **no testid** — requested as dynamic `project-selector-option-{label}` on `SidebarProjectSelect.jsx` `customRenderOption` (ELITEA-2232 AFS) |
| console errors, whole flow | **0** — quirk 4's `#1753` MUI focus error needs the first-visit prompt, which only appears after "Jump in now!" navigates to `/chat`. Stay on `/onboarding` and the console assertion needs no filter. |

**Absence handles during provisioning** (all confirmed count 0): `sidebar-toggle`,
`project-selector-trigger`, `onboarding-workspace-ready-title`, `onboarding-welcome-card`.


---

## Resolved/added during ELITEA-2232 implementation (test-automation-engineer, 2026-08-24)

Attributed implementation-time facts — the analyst's behavior/scope claims above are unchanged.

**The project-dropdown option testid now EXISTS.** `project-selector-option-{label}` was added to
`SidebarProjectSelect.jsx`'s `customRenderOption` (EliteaAI/EliteaUI@bb8b9adc, pushed to
`automation/testids`; **not yet on `main`** — human cherry-pick pending, same as every other
`onboarding-*` testid here). Attribute-only addition on the existing `<Box>` — no new DOM node,
no hook, no render-prop change. Live value for the standard test user:
`project-selector-option-Private`.

**EliteaUI commitlint rejects `[ELITEA-NNNN]` in a commit subject.** The husky `commit-msg` hook
enforces `[EL-XXXX]` (`function-rules/subject-empty`: *"subject must container ticket number -
[EL-XXXX]"*). Use `test: [EL-2232] …`, not `test: [ELITEA-2232] …`, for every testid commit in
that repo — the first form fails the hook and the commit is rejected outright.

**Page object (shipped, additive-only).** The provisioning locators went into the EXISTING
`automation/pages/onboarding_page.py`: `progress_status_label` / `progress_estimated_time` /
`progress_bar` as `LocatorDescriptor` fields, plus class-level dynamic-testid template constants
`PROJECT_SELECTOR_OPTION` / `SIDEBAR_MENU_ITEM` with accessors `project_selector_option(label)` /
`sidebar_menu_item(value)`, and actions `click_get_started()` / `open_project_selector()`. Every
ELITEA-2231/2235/2236/2241 locator is byte-identical (0 removed lines in the diff).

**Spec:** `automation/tests/ui/onboarding/test_onboarding_provisioning.py` (ELITEA-2232) — green
first run, 0 reruns, 31.0 s.

**Timings confirmed by the implementation run** (all as the analyst measured): the ≥7 s post-
Welcome quiet window is clean (0 `/social/author/` requests); the click yields ≥2 polls within
12 s; `aria-valuenow` reads `5` immediately after the click and has advanced after 6 s; releasing
the mock brings up `WorkspaceIsReady` + the sidebar within the 20 s allowance; 0 console errors
across the whole flow, no filter needed (the `#1753` MUI focus error needs the first-visit prompt,
which only appears after "Jump in now!" — this spec deliberately stays on `/onboarding`).

**Progress-bar start value: assert a bound, not an exact number.** The AFS's `aria-valuenow == "5"`
was amended to `5 <= initial <= 12` at implementation — the read lands inside, but not reliably at
the start of, the product's first 1 s interval tick, so exact equality is a stopwatch race against
the 3× merge gate while asserting nothing extra. Observed value on the shipped run: `5`.


---

## Resolved/added during ELITEA-2237 / 2238 / 2239 analysis + implementation (test-automation-engineer, 2026-08-24)

Attributed implementation-time facts — the analyst's behavior/scope claims above are unchanged.

**The last missing tips-card testid now EXISTS.** `onboarding-tour-next-button` was added to the
forward `IconButton` in `TourContent.jsx` (EliteaAI/EliteaUI@f647488d, pushed to
`automation/testids`; **not yet on `main`** — human cherry-pick pending, same as every other
`onboarding-*` testid here). Attribute-only addition on the existing element — no new DOM node,
no hook, no render-prop change. The tips card now has a complete testid inventory.

**The duplicate-testid trap (quirk 1) extends to BOTH nav arrows.** While the fullscreen dialog is
open, `onboarding-tour-prev-button` and `onboarding-tour-next-button` each resolve to **2 visible
nodes**, exactly like the tip content / image / indicator. Confirmed live. The page object now
ships `DIALOG_PREV_BUTTON` / `DIALOG_NEXT_BUTTON` alongside the existing dialog-scoped constants,
plus `CARD_PAGE_INDICATOR` / `CARD_TIP_CONTENT` for reading the EMBEDDED copy while the dialog is
open (scoped into `onboarding-tour-container`; the dialog's paper is not a descendant of it).

**Slide state is shared between the two copies.** `currentStep` is lifted into `OnboardingTour`, so
navigating inside the dialog moves the embedded card too — live-observed as both indicators reading
`2 / 48` simultaneously — and the slide reached in the dialog survives collapsing it. This is the
only machine-checkable reading of ELITEA-2239's prose step 9 ("consistent with the collapsed card
view").

**Navigation facts measured live (2026-08-24):**

| Fact | Value |
|---|---|
| Clicks from `1 / 48` to `48 / 48` | exactly **47** |
| Slide 2 | `Tip 2: Navigate the Sidebar` · image `sidebar-navigation.png` |
| Slide 3 | `Tip 3: Switch Between Projects` · image `project-selector.png` |
| Slide 48 | `Tip 48: View Message Execution Details` · image `message-details.png` |
| Prev @ slide 1 / Next @ slide 48 | `disabled=true`, computed `color: rgb(104, 108, 118)` (theme `text.disabled`), `pointer-events: none` |
| Opposite arrow at each boundary | ENABLED (Next @ 1, Prev @ 48) |
| Console errors over the full 1 → 48 walk + a fullscreen navigation cycle | **0** — no filter needed on `/onboarding` (quirk 5 holds) |

**`pointer-events: none` on the disabled arrows ⇒ `click(force=True)` is mandatory** for the
"click the inactive arrow and verify nothing happens" steps (ELITEA-2238 steps 3 and 8). A plain
`.click()` times out on Playwright's actionability check and reads like a product failure. Forcing
dispatches a real mouse click at the control's position — the product's own handler ignores it, and
the asserted observable (counter unchanged) is still produced by the product.

**Dev-server HMR gotcha on this machine (cost ~4 turns).** After editing JSX under `../EliteaUI/src`,
Vite served the NEW module (`curl .../TourContent.jsx?t=<epoch>` showed the testid) while the
already-open browser page kept the OLD one — a plain re-`goto` of the same URL did not pick it up.
A cache-busted navigation (`/onboarding?r=1`) did. If a freshly-added testid "does not match any
elements", check the served module with a `?t=` query before suspecting the edit.

**Specs (shipped, one per case):**
`automation/tests/ui/onboarding/test_onboarding_tips_navigation.py` — three test classes,
one per case (ELITEA-2237 forward navigation, ELITEA-2238 arrow boundaries, ELITEA-2239 fullscreen
navigation). One file rather than three because all three share ONE subject (arrow navigation) and
the same entry path; the w2 wave's one-file-per-case shape was for three genuinely different
screens.


---

## The sidebar header — added by ELITEA-2234 / ELITEA-2233 analysis (qa-engineer, 2026-08-24, batch `onboarding-w4`)

These two "onboarding" cases are **not on `/onboarding` at all** — their subject is the persistent
app sidebar header (`src/[fsd]/widgets/sidebar-root/ui/SidebarBody.jsx`), which renders on every
authenticated route. Executed live on `/chat`.

### Layout (live boxes, 2026-08-24, expanded sidebar)

| Element | Box | Source |
|---|---|---|
| Logo `IconButton` (`sidebar-toggle`, **on-main ✓**) | x=8 y=8 44×44 | `SidebarBody.jsx:218-236` |
| Socket status dot (inside the logo button) | x=44 y=8 8×8 — top-**right corner**, `top:0 right:0` | `SidebarBody.jsx:229-235` |
| Notification bell container | x=172 y=16 28×28 | `NotificationButton.jsx:68` |

### Socket status dot — ONE element, colour is the whole state machine

`useSocketIcon()` → Redux `settings.socketConnected` → `socketStatus` `'connected'|'disconnected'`;
`isSocketIconVisible` is hardcoded `true`. Colour: `icon.fill.success` `#2BD48D` =
**`rgb(43, 212, 141)`** vs `icon.fill.error` `#D71616` = `rgb(215, 22, 22)`.
MUI's `<Tooltip title={...}>` clones the title onto the child as **`aria-label="Elitea is connected"`**
— readable without hovering. DOM count of the element: **1**, so "no red dot" is provable by a
count+colour pair, not just by absence.

### Notification bell — the badge is an SVG circle, not a DOM node

`BellIcon.jsx` renders `<circle cx=12 cy=3 r=3 fill="#D71616">` **inside** the bell `<svg>` when its
`hasMessages` prop is true. `hasMessages` = `!!data?.total` from
`GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?only_new=true&only_total=true`
(`NotificationButton.jsx:63`) plus the `notifications_notify` socket event.
⇒ the badge can only be located by a **state attribute on the bell**, never by a testid on the circle
(presence-flipping testids are outlawed). Requested shape:
`sidebar-notifications-bell-icon` + `data-has-messages`.

**Two different project ids:** the badge query uses `user.personal_project_id`; the popover query
uses `useSelectedProjectId()`. Both are **399** for the standard test user today.

**Bell only exists in the EXPANDED sidebar** — `{!sideBarCollapsed && <Buttons.NotificationButton />}`.
The socket dot exists in both states.

### Notifications popover (`NotificationList.jsx`)

MUI **Popover** `id="notificationList"` (not a modal, no backdrop; outside click / Escape also close
it). Header "Notifications" + X `aria-label="Close notifications"`; body = unread items; footer
"Mark all as read" (**rendered only when `notifications.length > 0`** — a clean "the list is
non-empty" observable) and "View all". Live: 5 unread bucket-retention notices from the artifacts
suite. **Opening the popover does NOT mark anything read** — the red badge survives open→close
(confirmed live).

### Testids requested by this wave (all `needs-adding`, all attribute-only, 0 grep hits on `origin/automation/testids`)

`sidebar-socket-status-indicator` + `data-socket-status` · `sidebar-notifications-button` ·
`sidebar-notifications-bell-icon` + `data-has-messages` · `sidebar-notifications-popover` (on the
Popover **paper** via `slotProps`, per the w2 Dialog lesson) · `sidebar-notifications-popover-title` ·
`sidebar-notifications-close-button` · `sidebar-notifications-mark-all-read-button`.
`BellIcon` and `BaseBtn` both spread `...rest` onto their root, so every testid is hardcoded at the
**feature call site** — no shared-component pollution, no `testId` prop plumbing.

### Quirks (new, live-confirmed)

7. **The first-visit interactive-tour prompt fires on `/chat` too, and BLOCKS the sidebar.** Quirk 3
   above is not `/onboarding`-specific: landing on `/chat` in this browser profile opened the "New
   here?" prompt and a `bell.click()` failed with `<div class="MuiBox-root …"> intercepts pointer
   events`. Dismiss with `components/interactive_tour.py` → `FirstVisitPromptCard.click_skip()`
   (`interactive-tour-first-visit-prompt` / `-skip-button`) before ANY sidebar interaction. It also
   emits the known `#1753` MUI focus console error — filter that one message.
   The prompt is per-section (`localStorage["interactive-tour:<section>:prompt-seen"]`).
8. **You cannot call the Elitea API from inside the page.** An in-page `fetch('/api/v2/...')` (even
   same-origin, `credentials: 'include'`) is redirected to `dev.elitea.ai/forward-auth/auth_oidc/login`
   and dies on CORS — the app's requests carry a Bearer token the page context doesn't reproduce.
   Cost 3 turns during this analysis. For API preconditions use the suite's `automation/api/`
   `APIClient` (Bearer from `.env.test`), never `page.evaluate` + `fetch`.
   Corollary: those CORS errors land in the console log and can be mistaken for product errors.

### AFS produced

- `l1_sidebar_notification_bell_red_badge_ELITEA-2234.md` (clarification **#1764**)
- `l2_sidebar_logo_socket_status_green_dot_ELITEA-2233.md` (clarification **#1765**)

Both `ready-for-automation`, ZERO substitution. Suggested shared page object:
`automation/pages/sidebar_header_page.py` (`SidebarHeaderPage`) — **not** `onboarding_page.py`.

---

## Resolved/added during ELITEA-2234 / ELITEA-2233 implementation (test-automation-engineer, 2026-08-24)

Attributed implementation-time facts — the analyst's behavior/scope claims above are unchanged.

**The seven sidebar-header testids now EXIST** on `EliteaAI/EliteaUI` `automation/testids`
(**not yet on `main`** — human cherry-pick pending, same as every other testid in this batch).
All are attribute-only additions on elements that already existed: no new DOM node, no hook, no
render-prop change, nothing removed.

| testid | File | Commit |
|---|---|---|
| `sidebar-socket-status-indicator` + `data-socket-status` | `SidebarBody.jsx` | EliteaAI/EliteaUI@2c0ac201 |
| `sidebar-notifications-button` | `button/NotificationButton.jsx` | EliteaAI/EliteaUI@1d512ae2 |
| `sidebar-notifications-bell-icon` + `data-has-messages` | `button/NotificationButton.jsx` (at the call site — `BellIcon` spreads `...rest` onto its `<svg>`) | EliteaAI/EliteaUI@1d512ae2 |
| `sidebar-notifications-popover` | `NotificationList.jsx` — on the Popover's **paper** via `slotProps.paper` | EliteaAI/EliteaUI@1d512ae2 |
| `sidebar-notifications-popover-title` | `NotificationList.jsx` | EliteaAI/EliteaUI@1d512ae2 |
| `sidebar-notifications-close-button` | `NotificationList.jsx` (`BaseBtn` spreads `...rest`) | EliteaAI/EliteaUI@1d512ae2 |
| `sidebar-notifications-mark-all-read-button` | `NotificationList.jsx` | EliteaAI/EliteaUI@1d512ae2 |

**Quirk 7 is CORRECTED for the pytest suite: the first-visit prompt CANNOT fire on a direct
`/chat` entry.** `NewChat.jsx:104` is the only caller of `useProposePendingTour`, and that hook
returns immediately unless `localStorage["interactive-tour:first-elitea:pending"] === "true"` — a
flag written **only** by `/onboarding`'s `handlePersonalProjectReady()`
(`[fsd]/features/interactive-tours/lib/hooks/useProposeTour.hooks.js`; there is no other
`useProposeTour` call site in `src/`). The analysis session saw the prompt because that same browser
profile had visited `/onboarding` earlier. The suite cannot inherit it: on localhost `auth_state`
returns an **empty storage state** (`fixtures/session_fixtures.py:110`) and `conftest.py` creates a
**fresh context per test**. Confirmed by the ELITEA-2234/2233 run — no prompt, **0 console errors**
on `/chat`. Quirk 7 remains true for any spec that reaches `/chat` *through* `/onboarding`
(ELITEA-2241's path).

**The bell's badge oracle.** `GET …/notifications/notifications/prompt_lib/{personal_project_id}
?only_new=true&only_total=true&limit=1&offset=0` fires on every app load; capturing it with
`page.expect_response` around the navigation yields the exact `total` the badge is computed from
(`SidebarHeaderPage.navigate_and_get_unread_total()`). It shares its URL prefix with the notification
CENTRE's list fetch — `only_total=true` selects the count probe, `sort_by=created_at` selects the
list (`NotificationCenterPage` keys off the latter for the opposite reason). The DEV account still
had unread items at implementation time; the `is_seen: false` re-arm fallback the AFS sketched was
NOT needed and was NOT built.

**Page object (shipped): `automation/pages/sidebar_header_page.py` (`SidebarHeaderPage`)** — the
persistent app-shell sidebar header, deliberately not `onboarding_page.py`. Holds the logo anchor,
the socket dot (plus the three class-level scoped/state-filtered constants), the bell and the whole
notifications popover, `navigate_and_get_unread_total()`, `open_notifications()` and
`close_notifications()`. `sidebar-collapse-toggle-button` is inherited from `BasePage`;
`sidebar-toggle` is pre-existing app-shell chrome already declared in `chat_page.py` /
`onboarding_page.py`.

**Specs (shipped, one per case):**
`automation/tests/ui/onboarding/test_sidebar_notification_badge.py` (ELITEA-2234),
`test_sidebar_socket_status_indicator.py` (ELITEA-2233). Both green on the first run, 0 reruns,
20.7 s for the pair.

---

## The project dropdown + full sidebar after provisioning — executed live 2026-08-24 (ELITEA-2240)

The *content* of the ready state, which no merged spec asserted (ELITEA-2232 asserts its skeleton
only: sidebar present, trigger reads `Private`, ONE entity item, the `Private` row exists).

| Observable, dropdown open on `/onboarding` | Value (standard test user, DEV backend) |
|---|---|
| Option rows | 5 — `Private` + team projects `Bugs & Features`, `Elitea Development`, `Elitea Testing Team`, `UI Testing` |
| Row testids | outer MUI `MenuItem` = `select-option-{projectId}` (**numeric, env-specific — do not bind**); inner Box = `project-selector-option-{label}` (bind to this one) |
| Selected row | `aria-selected="true"` + `Mui-selected` + a `<CheckedIcon/>` `<svg>` in `.MuiListItemIcon-root` — **the icon has NO testid** (requested generic `select-option-selected-icon` on the shared `SingleSelectMenuItem.jsx`; option-row selection state requested as `data-selected` on the existing `project-selector-option-*` Box, ELITEA-2240 AFS) |
| Entity menu | exactly **9** `sidebar-menu-item-*`: chat, agents, pipelines, skills, toolkits, mcps, credentials, applications, artifacts. Label of `toolkits` is **"Toolkits & Indexes"** |
| Settings / Catalog | **not** menu items — separate bottom-section buttons `sidebar-settings-button` (`SettingsButton.jsx:27`) and `sidebar-agent-hub-button` (`AgentHubButton.jsx:38`, label "Catalog"). Both `automation/testids` only |
| Project-list endpoint (the oracle) | `GET /api/v2/projects/project/default/1?check_public_role=true` → array of `{id, name, …}`; the personal project (`id == personal_project_id`, raw name `project_user_659`) renders as `Private`; **no public-project entry**, so the mapping to rows is 1:1 |

**⚠ The dropdown fills PROGRESSIVELY, exactly like the entity menu.** At the instant
`onboarding-workspace-ready-title` appears the dropdown lists **only `Private`**; the team rows
arrive a few seconds later when the project-list query resolves. Auto-wait per option; never
snapshot the option list, never assert its length.

**Provisioning-state absence re-confirmed first-hand** (mask `personal_project_id: null`, click
"Sure, let's go!"): `sidebar-toggle` 0, `project-selector-trigger` 0, `sidebar-menu-item-*` 0,
`sidebar-settings-button` 0, `sidebar-agent-hub-button` 0 — the sidebar does not exist, it is not
merely empty. So ELITEA-2240's step 2 ("click the project dropdown, no project listed, limited
sidebar items") is unexecutable as written → clarification **#1767**. Mask release → ready banner in
**1.8 s**. 0 console errors across the whole flow.

**Menu items are permission-filtered per selected project** (`SidebarBody.jsx` `sections` memo,
`PERMISSION_GROUPS`) — that is the mechanism behind a "limited sidebar" on routes where the sidebar
does render without a project.

**Related AFS:** `lextend_private_and_team_projects_in_dropdown_after_provisioning_ELITEA-2240.md`
(`extend-existing` on `automation/tests/ui/onboarding/test_onboarding_provisioning.py:324-350`).
