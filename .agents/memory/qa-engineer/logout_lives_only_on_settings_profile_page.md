---
name: Log out lives only on the Settings → Profile page
description: The app's ONLY logout control is a button on /settings/profile; the sidebar user menu (UserButton.jsx) is dead code
type: reference
aliases: [logout, log out, sign out, UserButton, user menu, settings drawer logout]
tags: [area/settings, type/ui-inventory]
created: 2026-08-24
updated: 2026-08-24
---

## Where logout is (and the three places it is not)

Verified live 2026-08-24 (localhost:5173, EliteaUI `automation/testids`) while
analysing ELITEA-2252/2253/2254.

**The one control:** `<BaseBtn variant="secondary" startIcon={<LogoutIcon/>}>Log out</BaseBtn>`
in the content pane of `/settings/profile` —
`src/[fsd]/features/settings/ui/profile/Profile.jsx:73-80`. Label is `Log out`
**with a space**.

**Not in the Settings drawer.** `SettingsDrawer.jsx` renders only
`SETTINGS_TABS_CONFIG` tabs; PERSONAL ends at **Notifications**. A whole-document
text scan on `/settings/tokens` found 0 `Log out` nodes.

**Not in the app-shell sidebar.** `src/[fsd]/widgets/sidebar-root/ui/button/UserButton.jsx`
*does* contain a DotMenu with `Preferences` + `Logout` — but it is **dead code**:
`grep -rn "UserButton" src/` finds no importer, and no user `data-tour` node renders
live (17 sidebar tour targets, none of them the user). **This is the trap**: reading
the source for "where is logout" lands on UserButton.jsx and looks authoritative.
Never target it, never add a testid to it.

⇒ Logging out from any Settings sub-page costs **one drawer click** (→ Profile),
then the button. Any case claiming logout is reachable "without extra navigation"
is describing a UI that does not exist (clarification #1772).

Related: [[clicking_log_out_is_unobservable_and_destructive_on_localhost]]
