---
name: EliteAImage alt prop silently dropped
description: EliteAImage.jsx ignores its caller's alt prop, always renders alt="elitea" on the <img>
type: feedback
---

`src/components/EliteAImage.jsx` destructures only `image`, `style`, and
`data-testid` from its props — a caller-passed `alt` prop (e.g.
`EntityIcon.jsx` passes `alt="Preview"` when rendering an agent/pipeline
icon with a URL) is silently dropped. The rendered `<img>` always carries
the component's own hardcoded `alt="elitea"`, regardless of what the caller
asked for.

Confirmed live (ELITEA-2361, 2026-08-11): a Catalog agent's avatar in the
chat Participants panel renders `<img alt="elitea" ...>` even though
`EntityIcon` passed `alt="Preview"` down the chain. Not a defect worth
filing (visually inert, no accessibility regression reported) — just a trap
for a future analyst who reads `EntityIcon.jsx`'s `alt="Preview"` and
expects that string to show up in the DOM. Any assertion on this avatar's
`alt` text should target `"elitea"` (the actual rendered value), not
whatever alt text the call site appears to pass.

Also: `EntityIcon` accepts an `imgTestId` prop (threaded to `EliteAImage`'s
`data-testid`) for exactly this situation — when an avatar `<img>` needs its
own testid distinct from the icon's outer `Box` wrapper's `data-testid`.
Used this for `chat-participant-avatar` (`ParticipantItem.jsx`'s normal card
branch) — see `ChatPage.PARTICIPANT_AVATAR` / `get_participant_avatar()`.
