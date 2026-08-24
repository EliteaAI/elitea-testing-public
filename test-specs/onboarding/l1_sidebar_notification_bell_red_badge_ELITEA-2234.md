# ELITEA-2234: Onboarding — bell notification icon shows red badge/dot on first login

**TMS ID:** ELITEA-2234
**Priority:** high
**Status:** `ready-for-automation`
**Type:** UI
**Feature:** onboarding (surface: **sidebar header**, not the `/onboarding` page)
**Analysed:** 2026-08-24 · live, `http://localhost:5173/chat` (EliteaUI `automation/testids`, DEV backend)
**Cluster:** analysed in ONE live session with ELITEA-2233 (sidebar-header family). **Separate AFS each** — see § Why not a family AFS.
**Surface digest:** `test-specs/onboarding/_surface.md` § The sidebar header
**Clarification filed:** case-text drift on steps 5-7 — see § Known case-text drift

---

## Summary

The notification bell lives in the sidebar header (`SidebarBody.jsx` → `Buttons.NotificationButton`,
right of the ELITEA logo). Its red badge is **not a separate DOM node**: `BellIcon.jsx` renders an
extra `<circle cx=12 cy=3 r=3 fill="#D71616"/>` **inside the bell SVG** when its `hasMessages` prop
is true. `hasMessages` is driven by the product's own query
`GET /api/v2/notifications/notifications/prompt_lib/{personal_project_id}?only_new=true&only_total=true`
— `setHasMessages(!!data?.total)` (`NotificationButton.jsx:63`), plus a live socket event
(`sioEvents.notifications_notify`) that flips it to true.

Clicking the bell opens a **MUI Popover** (`NotificationList.jsx`, `id="notificationList"`) headed
"Notifications", listing the unread notifications; the header's X (`aria-label="Close notifications"`)
closes it.

Live-confirmed 2026-08-24 on the standard test user (personal project **399**): red dot present,
popover opens with 5 unread items, X closes it, and the red dot **survives** opening/closing
(the popover does not auto-mark-as-read).

---

## Preconditions

- Standard authenticated user (`auth_state`; on localhost login is skipped via `VITE_DEV_TOKEN`).
- **Sidebar EXPANDED.** `SidebarBody.jsx:236` renders the bell as
  `{!sideBarCollapsed && <Buttons.NotificationButton />}` — in the collapsed sidebar the bell does
  not exist at all. Default state on a fresh context is expanded
  (`sidebar-collapse-toggle-button[data-collapsed="false"]`, live-confirmed); assert it rather than
  assume it.
- **≥1 unread notification on the user's PERSONAL project.** This is the case's own premise
  ("first login" ⇒ the project-created notification). See § Test-data dependency — it is the one
  real risk in this case and is handled by reading the product's own count, not by fabricating it.
- Route: any authenticated route renders the sidebar; this AFS uses `/chat` (the default landing).
- ~~The first-visit interactive-tour prompt blocks the sidebar~~ — **does not fire on the suite's entry path**; see § Entry-path quirk (amended at implementation).
- **ZERO substitution.** No route mock, no injected state, no API seeding. Every asserted value is
  produced by the product.

### Entry-path quirk (analysis-time) — **amended at implementation, 2026-08-24**

**Analysis observed:** landing on `/chat` opened the interactive-tour **first-visit prompt** ("New
here? … Skip / Start!"), a modal with `InteractiveTourBackdrop` whose backdrop intercepts pointer
events — a plain `bell.click()` failed Playwright actionability with
`<div class="MuiBox-root …"> intercepts pointer events`.

**Amended (implementer, ELITEA-2234/2233 implementation):** that prompt **cannot fire on the
suite's entry path**, and no dismissal step is implemented. `NewChat.jsx:104` is the only caller of
`useProposePendingTour`, and that hook returns immediately unless
`localStorage["interactive-tour:first-elitea:pending"] === "true"` — a flag written **only** by
`/onboarding`'s `handlePersonalProjectReady()`
(`[fsd]/features/interactive-tours/lib/hooks/useProposeTour.hooks.js`). The analysis session had
visited `/onboarding` in the same browser profile; the suite has not: on localhost `auth_state`
returns an **empty storage state** (`fixtures/session_fixtures.py:110`) and `conftest.py` builds a
**fresh context per test**, so the flag can never be set when the spec navigates straight to `/chat`.
Confirmed by the implementation run: prompt absent, **0 console errors**.

The `#1753` console filter is kept anyway (one message, ticket-linked) so the assertion stays honest
if a future entry path does arm the prompt — it costs nothing and masks nothing.

---

## Test-data dependency (read this before implementing)

The red dot is a function of real account state. **Do not fabricate it** (a `route.fulfill` of the
notification count would be a terminal substitution — the badge IS the case's observable).

The honest, deterministic shape is `.agents/testing.md` § *How to test a NONDETERMINISTIC producer*:
**capture the product's own count response and assert the UI against it.**

```python
with page.expect_response(lambda r: "only_total=true" in r.url and "notifications" in r.url) as resp:
    page.goto(...)                     # or reload
unread_total = resp.value.json()["total"]      # the ORACLE — produced by the system
```

Then:

- `assert unread_total > 0` — the case's precondition, asserted **as a precondition** with an explicit
  message ("ELITEA-2234 needs ≥1 unread notification on personal project N"). If DEV ever has zero,
  this fails LOUDLY and goes back to the lead. **Never `pytest.skip`** — a silent skip deletes the case.
- `expect(bell_icon).to_have_attribute("data-has-messages", "true")` — the product rendered the badge
  for that same real count.

Live evidence that the dependency is safe in practice: the DEV account carries a continuous supply of
`only_new` notifications generated by the artifacts suite's own bucket-retention notices (5 unread at
analysis time, timestamps spread over ~20 h). Nothing in the merged suite clicks "Mark all as read".

**Fallback if it ever does go to zero** (implementer, only on a real failure, and declare it):
`PUT /api/v2/notifications/notifications/prompt_lib/{pid}` with `{"ids": "all", "is_seen": false}`
(`api/notifications.js:50-58`) marks existing notifications unread again — a *transit* precondition
via the suite's `APIClient` (Bearer). **Unverified by this analysis** (an in-page `fetch` without the
app's Bearer token is redirected to OIDC and dies on CORS — that is the ONLY reason it is unverified,
not a product problem). Do not build it speculatively.

---

## Coverage Map

### Axis 1 — TMS case elements

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| P | Precondition: "User is logged in to the Elitea platform" | authenticated session | framework `auth_state` | `expect(sidebar_toggle).to_be_visible()` | **asserted** (transit) |
| 1 | Log in to private project for the **first time**; land on the expected landing page | authenticated, on landing page | `page.goto("/chat")` (no prompt dismissal — see § Entry-path quirk, amended) | `expect(page).to_have_url(re.compile("/chat"))` + `expect(sidebar_toggle).to_be_visible()` | **asserted, scope-amended** — "first login" is **not reproducible** for a standard user and is not what the product gates on: the badge reflects the *unread count* at any login (`NotificationButton.jsx:63`), not a first-session flag. Asserting the live contract per the reverse-masking guard; drift filed as a clarification |
| 2 | Locate the bell (notification) icon in the top-right area of the sidebar header | control located, no error | `sidebar-notifications-button` (**added** EliteaAI/EliteaUI@1d512ae2) | `expect(notifications_button).to_be_visible()` + geometry: its box is right of `sidebar-toggle` and inside the header row (live: bell x=172-200 y=16-44 vs logo x=8-52 y=8-52) | **asserted** — position asserted as `bell.x > logo.right`, not as pixel constants |
| 3 | Verify the bell icon is visible | bell visible | `sidebar-notifications-bell-icon` (**added** EliteaAI/EliteaUI@1d512ae2) | `expect(bell_icon).to_be_visible()` | **asserted** |
| 4 | Verify red badge/dot is displayed above the bell icon | red dot rendered | `sidebar-notifications-bell-icon` + state attribute `data-has-messages` (**needed**) | `expect(bell_icon).to_have_attribute("data-has-messages", "true")`, tied to the real `unread_total > 0` read from the product's own response | **asserted** — the badge is an SVG `<circle>` INSIDE the bell, so it cannot carry its own testid (its *presence* flips with state, which `.agents/testing.md` § Locator policy outlaws). State goes on a `data-*` attribute of the stable element, per the PR #581 ruling |
| 5 | Click the red dot; a modal opens with "Project was successfully created" | modal/popover opens showing the notification | `sidebar-notifications-button` clicked; `sidebar-notifications-popover` + `-popover-title` + `-mark-all-read-button` (**all needed**) | `open_notifications()` (clicks the bell **inside** `expect_response` on the popover's own list fetch, then waits for the paper) → `expect(popover).to_be_visible()` + `expect(popover_title).to_have_text("Notifications")` + `expect(mark_all_read_button).to_be_visible()`, each with an explicit `timeout=UI_ELEMENT_TIMEOUT` | **asserted, text-amended** — live the popover is headed **"Notifications"** and lists the account's actual unread items; **"Project was successfully created" is a first-login-only message this account no longer has.** Asserting it would be reverse-masking. The "≥1 item is listed" meaning is carried by `sidebar-notifications-mark-all-read-button`, which `NotificationList.jsx:141` renders **only** when `notifications.length > 0`. Drift filed as a clarification. Note it is a **Popover, not a modal** — no backdrop, closes on outside click too |
| 6 | Click the "X" button | control responds | `sidebar-notifications-close-button` (**testid needed**; today only `aria-label="Close notifications"`) | `close_button.click()` | **asserted** |
| 7 | Verify Notifications modal closes | popover gone | `sidebar-notifications-popover` | `expect(popover).to_have_count(0)` | **asserted** — live-confirmed; MUI unmounts the Popover (no `keepMounted`) |
| Final | Notifications modal closes | as step 7 | same | same | **asserted** |

### Axis 2 — coverage beyond the case (each with its reason)

| Observable | Reason | Assertion |
|---|---|---|
| The badge state matches the product's **own** unread count from `?only_new=true&only_total=true` | This is what makes the case honest rather than a screenshot of whatever the account happened to contain: the assertion pins the badge to the number the product itself computed. A regression that renders the dot unconditionally, or drops it while unread items exist, fails here | `unread_total = response.json()["total"]; assert unread_total > 0` then `to_have_attribute("data-has-messages", "true")` |
| The red dot **survives** opening and closing the popover | Live-confirmed (`fill="#D71616"` still present after the X). Viewing is not reading — a product change that silently marked everything seen on open would be a real behaviour change this case would otherwise miss | re-assert `to_have_attribute("data-has-messages", "true")` after step 7 |
| Sidebar is expanded (`sidebar-collapse-toggle-button[data-collapsed="false"]`) | The bell does not render in the collapsed sidebar; without this the "bell not visible" failure mode is ambiguous | `expect(collapse_toggle).to_have_attribute("data-collapsed", "false")` |
| No error-level console messages, **excluding** the known `#1753` MUI focus error | Side channel. The `#1753` error is deterministic on the first-visit prompt path (digest quirk 4) and already ticketed | filter that one message; `# Known defect: #1753` |

---

## Concrete Handles Reference

| Element | Handle (testid-only) | Provenance (verified 2026-08-24, `git fetch origin` in ../EliteaUI) |
|---|---|---|
| Sidebar logo / toggle (header anchor) | `sidebar-toggle` | **on-main ✓** |
| Sidebar collapse toggle | `sidebar-collapse-toggle-button` | on `automation/testids` — verified live at implementation ✓ |
| Bell button (clickable container) | `sidebar-notifications-button` | **ADDED** EliteaAI/EliteaUI@1d512ae2 (`automation/testids`, pushed) |
| Bell SVG + badge state | `sidebar-notifications-bell-icon` + `data-has-messages="true|false"` | **ADDED** EliteaAI/EliteaUI@1d512ae2 |
| Notifications popover paper | `sidebar-notifications-popover` | **ADDED** EliteaAI/EliteaUI@1d512ae2 |
| Popover header title | `sidebar-notifications-popover-title` | **ADDED** EliteaAI/EliteaUI@1d512ae2 |
| Popover X close button | `sidebar-notifications-close-button` | **ADDED** EliteaAI/EliteaUI@1d512ae2 |
| "Mark all as read" (renders only when ≥1 item) | `sidebar-notifications-mark-all-read-button` | **ADDED** EliteaAI/EliteaUI@1d512ae2 |
| ~~First-visit tour prompt + Skip~~ | ~~`interactive-tour-first-visit-prompt` / `-skip-button`~~ | **not used** — the prompt cannot fire on the suite's entry path (see § Entry-path quirk, amended) |

**Live-captured values (2026-08-24, standard test user, personal project 399):**

| Observable | Value |
|---|---|
| Badge circle inside the bell SVG | `<circle cx="12" cy="3" r="3" fill="#D71616">` (present) |
| Bell container box | x=172 y=16 w=28 h=28 (right of the logo button, x=8..52) |
| Popover root | `div#notificationList`, paper `.MuiPopover-paper` |
| Popover header text | `Notifications` |
| Popover content (live) | 5 unread bucket-retention notices + `Mark all as read` + `View all` |
| X button | `<button aria-label="Close notifications">` |
| After X | `#notificationList` removed from the DOM |
| Badge query | `GET /api/v2/notifications/notifications/prompt_lib/399?only_new=true&only_total=true&limit=1&offset=0` → 200 |

**Two different project ids — do not conflate.** The **badge** query uses
`user.personal_project_id` (`NotificationButton.jsx:20`); the **popover** query uses
`useSelectedProjectId()` (`NotificationList.jsx:31`). For the standard test user both are 399 today.
If a future case switches projects, the badge can legitimately disagree with the popover list.

---

## Testids to add (EliteaUI, `automation/testids`, `add-data-testid` skill)

All four are **attribute-only** additions on elements that already exist — no new DOM node, no hook,
no render-prop change (zero-functional-impact check passes).

1. `src/[fsd]/widgets/sidebar-root/ui/button/NotificationButton.jsx` — on the existing `<Box>`
   (line ~68, the one that already carries `data-tour`):
   ```jsx
   data-testid="sidebar-notifications-button"
   ```
   and on the `<BellIcon>` call, **at the feature call site** (BellIcon does
   `const { hasMessages, ...rest } = props` and spreads `{...rest}` onto its `<svg>`, so both
   attributes land on the SVG without touching the shared icon component):
   ```jsx
   <BellIcon hasMessages={hasMessages}
             data-testid="sidebar-notifications-bell-icon"
             data-has-messages={hasMessages ? 'true' : 'false'} />
   ```
   **Do NOT** put a testid on the `<circle>`: its presence flips with state, which
   `.agents/testing.md` § Locator policy forbids. State belongs on a `data-*` attribute.
2. `src/[fsd]/widgets/sidebar-root/ui/NotificationList.jsx`:
   - `sidebar-notifications-popover` — on the Popover's **paper**, via
     `slotProps={{ paper: { sx: styles.popoverPaper, 'data-testid': 'sidebar-notifications-popover' } }}`.
     **Not on `<Popover>` itself** — MUI spreads it onto the Modal root, which is
     `position: fixed; inset: 0` for every popover (the w2 lesson, digest § dialog testid).
   - `sidebar-notifications-popover-title` — on the header `<Typography>` ("Notifications").
   - `sidebar-notifications-close-button` — on the header X `<BaseBtn>` (BaseBtn spreads `...rest`,
     so hardcoding at this feature call site is correct; no `testId` prop plumbing needed).
   - `sidebar-notifications-mark-all-read-button` — on the "Mark all as read" `<BaseBtn>`.

Naming: `{section}-{element}-{type}` with section = `sidebar-notifications` (the call site's section).
Uniqueness verified 2026-08-24: `git grep` on `origin/automation/testids -- src/` returns **0 hits**
for every name above.

Commit subject must use `[EL-2234]`, not `[ELITEA-2234]` — EliteaUI's commitlint hook rejects the
latter (digest, w1).

---

## Known case-text drift (clarification, NOT a product defect)

| Case says | Live product | Handling |
|---|---|---|
| Step 1 "Log in … for the first time" | The badge is a function of the unread count at ANY login, not a first-session flag | Assert the live contract (badge ⇔ unread count) |
| Step 5 "a modal opens with **'Project was successfully created'**" | A **Popover** headed **"Notifications"** listing the account's unread items. The project-created notice is a genuine first-login artifact this long-lived account no longer has among its unread set | Assert popover + header + ≥1 item; do not assert that string |
| Steps 5-7 "modal" | MUI **Popover** — no backdrop; also closes on outside click / Escape | Wording only |

Filed as a case-text clarification issue (`question` label) per `.agents/profile.md` § Bug filing —
the #40 pattern. **No product defect was found in this case.**

---

## Why not a family AFS (ELITEA-2234 + ELITEA-2233)

Both live in the sidebar header and were analysed in one session, so they share the entry path, the
prompt-dismissal step and (soon) the page object. But they differ in **steps**, not in data:
ELITEA-2234 clicks a control, opens a popover and closes it (7 steps, 2 interactions); ELITEA-2233 is
a 4-step read-only inspection of a different element with no interaction at all. Merging them into one
parameterized spec would make two unrelated observables share assertions — the merge test in
`test-case-analysis` § Cluster dispatches says keep them separate. One branch, one PR, two specs.

---

## Suggested test location

`automation/tests/ui/onboarding/test_sidebar_notification_badge.py`
(`TestSidebarNotificationBadge::test_bell_shows_red_badge_and_notifications_popover`)

New page object: `automation/pages/sidebar_header_page.py` (`SidebarHeaderPage`) — shared with
ELITEA-2233. Not `onboarding_page.py`: this surface is the persistent app sidebar, not `/onboarding`.
Reuse `components/interactive_tour.py` → `FirstVisitPromptCard` for the prompt dismissal.

Markers: `@pytest.mark.p1`, `@pytest.mark.regression`, `@pytest.mark.ui`.

---

## Blocked Steps

None.

## Known Defects

None found. (`#1753` — MUI focus console error on the first-visit tour prompt — is pre-existing,
already filed, and only filtered here.)

---

## Evidence

- `test-results/screenshots/ELITEA-2234-step-05-notifications-popover-open.png` — bell with red badge, green
  logo dot, and the open Notifications popover in one frame.

---

## Implementation amendment (test-automation-engineer, 2026-08-24)

- **Shipped:** `automation/tests/ui/onboarding/test_sidebar_notification_badge.py`
  (`TestSidebarNotificationBadge::test_bell_shows_red_badge_and_notifications_popover`) +
  new page object `automation/pages/sidebar_header_page.py` (`SidebarHeaderPage`, shared with
  ELITEA-2233). Green first run, 0 reruns.
- **Entry path simplified** — no first-visit-prompt dismissal (see § Entry-path quirk, amended).
- **Test data at implementation time:** the product's own unread-count probe returned a non-zero
  `total` and the bell rendered `data-has-messages="true"`, exactly as specced. The precondition is
  asserted loudly (never `pytest.skip`).
- **The `PUT … {"ids": "all", "is_seen": false}` fallback was NOT built** — the AFS said build it only
  on a real failure, and there was none.
- Everything else implemented as specced; every Coverage-Map row is asserted.
