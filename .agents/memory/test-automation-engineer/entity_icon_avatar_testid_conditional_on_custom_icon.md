---
name: EntityIcon avatar testid only exists for a custom-uploaded icon
description: chat-participant-avatar (PARTICIPANT_AVATAR) is absent whenever the entity has no custom icon image — use chat-participant-icon for an unconditional icon-presence check
type: feedback
---

## What

`EntityIcon.jsx` renders one of two branches:
- `icon?.url && !icon?.component` → an `<img>` carrying `imgTestId` (e.g.
  `chat-participant-avatar` in `ParticipantItem.jsx`).
- otherwise (`!icon?.url && !icon?.component`) → a generic `<EntityTypeIcon>`
  fallback SVG with **no testid at all**.

So `PARTICIPANT_AVATAR` (`chat-participant-avatar`) only exists in the DOM for
a participant that has a custom-uploaded icon image. An agent using the
default/generic icon (common — e.g. this account's "AA" agent) has NO element
matching that testid; `get_participant_avatar()` times out waiting for it.

## Fix pattern

`EntityIcon`'s own outer container `Box` already supports a `data-testid` prop
(`dataTestId` destructured from `props['data-testid']`) that renders
UNCONDITIONALLY regardless of which branch fires. Added
`data-testid="chat-participant-icon"` on that container in
`ParticipantItem.jsx` (distinct testid value from the img-only
`chat-participant-avatar`, so no locator collision) — page-object constant
`PARTICIPANT_ICON` + method `ChatPage.get_participant_icon(row)`.

Use `get_participant_icon()` for a generic "does this row show an icon" check;
reserve `get_participant_avatar()` for when the participant is KNOWN to carry
a custom icon image specifically.

Same shared `ParticipantItem.jsx` component backs both the EXPANDED
PARTICIPANTS panel row and the collapsed participants-popover row
(`CollapsedParticipantsDropdown.jsx` imports it) — this fix benefits both
surfaces.

## Where

`EliteaAI/EliteaUI@dd44ce90` (`automation/testids`) —
`src/[fsd]/features/chat/participants/ui/ExpandedParticipants/ParticipantItem.jsx`.
`automation/pages/chat_page.py` — `PARTICIPANT_ICON`, `get_participant_icon()`.
Origin: ELITEA-2207/2469 implementation, 2026-08-19.
