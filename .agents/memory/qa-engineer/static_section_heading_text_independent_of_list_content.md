---
name: Static section-heading text is independent of the list it labels
description: A dropdown/popper title Typography ("Users") renders unconditionally — asserting it in popper_text proves the popover opened, never that the list under it is populated.
type: feedback
---

Companion shape to `passing_assertion_may_prove_nothing.md` (the "vacuous
assertion" family) — specific enough to warrant its own note.

## Pattern

A component renders a static section title (`<Typography>Users</Typography>`)
followed by a separately-fed list (`<UserMenu options={users} .../>`). A test
asserts `"Users" in popper_text` (or similar substring-in-container-text
check) to prove "the section shows its items." This assertion is **vacuous**:
the heading string is unconditional JSX, present whether `users` is `[]` or
populated. An empty/broken participant fetch still renders the "Users"
heading and still passes the check — the exact regression the case's
"PARTICIPANTS USERS section shows participants" wording asks to catch.

## Tell

The container being asserted against combines a static label with dynamic
content, and the assertion string is exactly the static label (not a piece
of the dynamic content). Read the component source — if the label
`Typography` sits outside the conditional/mapped block that renders the
list, the assertion can never fail on an empty list.

## Fix

Assert against the dynamic content directly — a per-item testid if one
exists (`chat-participant-row-{id}` in `UserMenu.jsx`), or a specific known
value (participant name / owner) inside the container text. A sibling test
covering the SAME popper (`test_team_users_mention_and_remove_participants.py`,
ELITEA-2168) already does this correctly — `assert name in popper_text` for
each expected participant — so a "matches sibling convention" check would
have caught this had the reviewer diffed against the established idiom
instead of judging the assertion in isolation.

## Seen

- PR #1562/ELITEA-2188 (`test_public_conversation_green_icon.py` Step 7) —
  `open_participants_popover(section="users")` asserted only
  `"Users" in popper_text`; `UsersParticipantDropdown/index.jsx` renders
  `<Typography sx={styles.title}>Users</Typography>` unconditionally, ABOVE
  the `<UserMenu options={users} .../>` that actually lists participants.
  Sibling ELITEA-2168 test on the same popper asserts specific participant
  names — the stronger, already-established idiom was available and unused.
