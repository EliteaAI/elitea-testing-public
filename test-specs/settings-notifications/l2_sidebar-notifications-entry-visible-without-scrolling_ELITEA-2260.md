# Test Case: Notification entry in sidebar is always visible without scrolling

## Metadata
- **TMS ID**: ELITEA-2260
- **Linked Story**: batch `settings-w02` (campaign EliteaAI/elitea-testing-public#1398)
- **Priority**: l2 (case priority: medium)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend), viewports 1728x861 AND 1366x768 (the headless test viewport, `automation/conftest.py:310`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot, 2026-08-26
- **Status**: ready-for-automation

## Preconditions
- User is logged in (`auth_state` fixture).
- **Surface**: "the sidebar" in this case means the **Settings drawer**, whose
  `PERSONAL` group the case names explicitly — not the app's left rail.
  Source of truth: `SettingsDrawer.jsx`, `SETTINGS_TABS_CONFIG` in
  `src/[fsd]/pages/settings/index.jsx` (see `test-specs/settings-navigation/_surface.md`).

## Test Data
### reuse-existing
- `${TEST_USER}` — no data requirements; the drawer's contents are config-driven.

## Test Steps
1. Log in — covered by `auth_state` (localhost bypass via `VITE_DEV_TOKEN`).
2. Navigate to a Settings sub-page **other than Notifications**, so the assertion is not
   trivially satisfied by the active tab: `${BASE_URL}/settings/profile`
   (`SettingsDrawerPage.navigate("/settings/profile")`).
   - **Verify**: page title starts with `"Settings: profile"`; `settings-drawer` and
     `settings-drawer-menu` are visible.
3. Locate the Notifications entry in the drawer's PERSONAL group.
   - **Verify**: `settings-nav-item-notifications` is visible and its text is
     `"Notifications"`; `data-active` is `"false"` (we are on Profile).
   - **Verify (PERSONAL group membership)**: the entry appears AFTER
     `settings-section-header-personal` in the drawer menu's DOM order, and after every
     item of the PROJECT group — asserted via
     `SettingsDrawerPage.nav_item_ids_in_order()` plus the two section headers'
     bounding-box vertical order.
   - **Verify (no scrolling required)**: the drawer menu is not scrolled and does not
     need to be — `settings-drawer-menu`'s `scrollHeight <= clientHeight` and
     `scrollTop == 0` — AND the Notifications entry's bounding box lies entirely inside
     both the menu's visible box and the browser viewport.
     Confirmed live at 1366x768: `scrollHeight == clientHeight == 617`, `scrollTop == 0`,
     entry box `top 630 / bottom 662` inside the menu box `top 61 / bottom 678`.
4. Look for an unread-count badge next to "Notifications" — **case-text drift, see the
   table below.**
   - **Verify (live contract)**: the drawer entry renders its label ONLY — its text is
     exactly `"Notifications"`, with no digits and no additional text node. This is the
     product's actual contract and it fails loudly if a count is ever added to (or
     silently removed from) the drawer.
   - **Verify (where the unread indication actually lives)**: the app sidebar header's
     bell (`sidebar-notifications-bell-icon`) exposes `data-has-messages`, the product's
     own boolean unread indicator — asserted here only as *present as an attribute*
     (either value), so this spec proves the indicator exists on the surface that owns
     it without duplicating ELITEA-2234, which already asserts its `"true"` state and
     the popover behaviour (`tests/ui/onboarding/test_sidebar_notification_badge.py`,
     merged on `automation/base`).
5. Assert no unexpected console errors across the flow.

## Expected Results
- On any Settings sub-page, the PERSONAL group's Notifications entry is rendered and
  fully visible without scrolling the drawer, and carries no unread count (the unread
  indication is a boolean red dot on the app sidebar bell instead).

## Coverage Map

### Axis 1 — every original case element
| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as any user | authenticated, lands on expected page | step 1 | `auth_state` fixture + step 2's title assertion | setup |
| 2 Navigate to any Settings sub-page | page loads | step 2 | `step 2`: title + drawer visible | asserted |
| 3 "Notifications" visible in PERSONAL section without scrolling | condition holds | step 3 | `step 3`: entry visible + text + PERSONAL DOM-order membership + `scrollHeight <= clientHeight`, `scrollTop == 0`, box inside menu and viewport | asserted |
| 4 Any unread count badge displayed next to "Notifications" | condition holds | step 4 | `step 4`: live contract asserted (label-only, no count) + the real unread indicator asserted on `sidebar-notifications-bell-icon` | asserted-with-drift *(see drift table)* |
| Preconditions: "User is logged in" | — | § Preconditions | `auth_state` fixture | setup |
| Expected Final State: unread count badge displayed next to "Notifications" | condition holds | step 4 | same as element 4 | asserted-with-drift |

### Axis 2 — additions beyond the case
| Addition | Why it is grounded |
|---|---|
| `data-active == "false"` on the Notifications entry | Proves the visibility assertion is not trivially satisfied by the entry being the ACTIVE tab — the case says "any Settings sub-page". |
| PERSONAL-group DOM-order membership | The case says "in the PERSONAL section"; without an order check, "visible somewhere in the drawer" would pass a regression that moved it into PROJECT. |
| No unexpected console errors | Suite-wide convention. |

### Case-text drift (filed, not masked)
| Case text | Live product (verified 2026-08-26, two viewports) | Handling |
|---|---|---|
| "Verify any unread count badge is displayed next to 'Notifications'" (in the Settings drawer's PERSONAL section) | The Settings drawer renders **no badge of any kind, next to any item**: `SettingsDrawer.jsx` renders `icon + label` and nothing else; the drawer's full innerText contains no digit and the DOM has zero `MuiBadge` nodes inside `settings-drawer`. The product's unread indication is a **boolean red dot** (not a count) on the app sidebar header's bell — `BellIcon`'s extra `<circle fill="#D71616">`, exposed as `sidebar-notifications-bell-icon[data-has-messages]`. | NOT a product defect — nothing is broken; the case describes a control that was never built on this surface, and the real indication exists elsewhere. Per `.agents/role-overrides.md` § interaction-discovery ladder (step 6: read the source — decisive) this is a **case-text clarification**, and per the settings-navigation digest's standing instruction the occurrence is **commented on the existing clarification EliteaAI/elitea-testing-public#1772** (the settings-drawer drift card for this cluster) rather than filed as a duplicate. The spec asserts the live contract per `.agents/testing.md` § reverse-masking guard. |

## Cleanup
None — read-only navigation.

## Concrete Handles (discovered during exploration)

Provenance verified with `cd ../EliteaUI && git fetch origin` on 2026-08-26.

| Element | Recommended Locator | Provenance |
|---|---|---|
| Settings drawer root | `LocatorDescriptor(testid="settings-drawer")` | pre-existing on `automation/testids` — `EliteaAI/EliteaUI@e1e031a1`, not yet on `main` |
| Drawer menu container (scroll subject) | `LocatorDescriptor(testid="settings-drawer-menu")` | same commit |
| Notifications nav item | `SettingsDrawerPage.SETTINGS_NAV_ITEM.format("notifications")` → `[data-testid="settings-nav-item-notifications"]` (existing class constant) | same commit |
| PERSONAL / PROJECT group headers | `SettingsDrawerPage.SETTINGS_SECTION_HEADER.format("personal"/"project")` | `EliteaAI/EliteaUI@529e2e4d` (added for ELITEA-2242), not yet on `main` |
| Sidebar bell icon (unread indicator) | `SidebarHeaderPage`'s existing `sidebar-notifications-bell-icon` descriptor | pre-existing (ELITEA-2234), on `automation/testids` |

**No new testid is needed for this case.**

## Network Behavior
- No case-specific requests; `/settings/profile` and the drawer are client-rendered from
  `SETTINGS_TABS_CONFIG`. The unread-count probe (`only_new=true&only_total=true`) fires
  on mount and feeds the bell's `data-has-messages`.

## Known Defects Found During Exploration
None (the badge gap is case-text drift, see above — not a defect).

## Blocked Steps
None.

## Automation Hints
- Suite: `automation/tests/ui/settings/` — where the sibling drawer specs live
  (`test_settings_sidebar_item_navigation.py`); markers `ui`, `admin`, `p2`, `regression`.
- Reuse `SettingsDrawerPage`; add only additive helpers for the scroll/geometry read.
- The "without scrolling" geometry must be evaluated at the framework's HEADLESS
  viewport (1366x768) — confirmed to hold there.
