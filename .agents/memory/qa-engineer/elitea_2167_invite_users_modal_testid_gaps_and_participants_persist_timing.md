---
name: ELITEA-2167 Invite Users modal — testid gaps, defects, and participant-persist timing
description: Chat Team-project "Add users" (Invite Users) modal is new page-object surface — full testid-gap cluster, a new MINOR defect (#719, sx-on-raw-svg), a re-confirmed BaseModal a11y defect (#694), and the network fact that invited users persist only at first-message-send, not at Add-click.
type: reference
---

## Context

ELITEA-2167 (chat — Team project — create conversation, add/cancel/close users
via Invite Users) — `test-specs/chat-interface/l2_team-invite-users-add-cancel-close_ELITEA-2167.md`.
`AddNewUserModal.jsx` ("Add users" dialog, reached via composer `+` →
`invite-users-menuitem`, Team projects only) had no prior page-object
coverage — `ChatPage.open_add_teammate_dialog()` only detects that the dialog
opened, it does not drive search/select/cancel/close.

## Testid-gap cluster (all confirmed absent on both `main` and `automation/testids`)

- Dialog container (`role="dialog"` only, no `data-testid`)
- X-close button (`aria-label="Close"` only)
- Search combobox ("Search users..." accessible name only)
- Per-option search-result row (dynamic) — **mechanical fix available**:
  `AutoCompleteDropDown.jsx`'s `renderOption` already supports a
  `getOptionTestId` prop (`data-testid={getOptionTestId ? getOptionTestId(option) : undefined}`)
  — `UserSearchSelect.jsx` simply doesn't pass one.
- Selected-user chip (only a positional `data-item-index`, not a stable
  per-user id — reordering/removal shifts the index)
- Cancel button, Add button (role/text only)
- Conversation-list multi-person icon — untagged `<div class="css-nguu07">`
  wrapper; confirmed via a live negative control (empty for a single-owner
  conversation "HI Chat", non-empty once 2+ users are participants) that this
  really is a participant-count indicator, not decorative chrome present on
  every row.

## Network behavior — participants persist at SEND, not at Add-click

Selecting users in the modal and clicking **Add** only updates client-side
state (`AddNewUserModal.jsx`'s `localUsers`) and the badge count — **no
network call fires yet**. The actual persistence happens only when the first
message is sent (which also creates the conversation itself), in this order:
`POST .../conversations/prompt_lib/{proj}` (201) → `PATCH
.../entity_settings/.../{id}` → `PUT .../conversation/.../{id}` → `POST
.../participants/prompt_lib/{proj}/{id}` (this is the one that actually
persists the invited users) → `POST .../select_conversation/.../{id}`. Do not
assert a participants-persistence network call right after Add — it hasn't
happened yet for a brand-new, not-yet-created conversation.

## Defects

- **#719 (NEW, MINOR)** — `AutoCompleteDropDown.jsx:425`'s
  `<CheckedIcon sx={styles.checkIconSx} />` forwards MUI's `sx` prop onto a
  raw imported SVG component (`@/assets/checked-icon.svg?react`, not an MUI
  `SvgIcon`), so `sx` lands as an invalid attribute straight on the `<svg>`
  DOM node — React logs "Invalid value for prop `sx` on <svg> tag" on every
  user selection, and the intended theme-driven checkmark size/fill silently
  never applies. Shared-component blast radius: any other picker built on
  `AutoCompleteDropDown` inherits the same bug.
- **#694 (re-confirmed, not re-filed)** — `AddNewUserModal.jsx` renders via
  the same `Modal.BaseModal` already found broken in #694 (stale
  `id="variables-dialog-title"` on the actual title vs hardcoded
  `aria-labelledby="alert-dialog-title"` in `BaseModal.jsx`). Cross-referenced
  via a comment on #694 rather than a duplicate ticket — confirms the defect's
  blast radius spans at least two distinct modals (delete-confirmation +
  Invite Users), both built on the same shared component.

## Test-data note

Case's literal example user "Admin Bot" does not exist in this environment
(searching "ad" returns "Aliaksandr Valadzko" / "Levon Dadayan" / "Vladyslav
Variushkin" — substring matches, no "Admin Bot"). "Hrach Sargsyan" (the
case's other example) DOES exist and was used verbatim. Same pattern as
ELITEA-2166's "echo" agent-name collision check — verify case-literal names
exist live before depending on them; substitute a real user and note it,
don't block.

## MUI overlay-interception recurrence

Same gotcha as `.claude/rules/mui-patterns.md` documents elsewhere: after
selecting a user, the `MuiAutocomplete-popper` results dropdown stays open
and intercepts clicks on Cancel/Add/Close underneath it
(`TimeoutError: ... subtree intercepts pointer events`). Fix: `Escape` to
dismiss the dropdown (closes the popper without closing the dialog) before
clicking any of those three buttons — every time, not just once.
