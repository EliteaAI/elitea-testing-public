---
name: Composer agent chip is three sibling controls, not one combined element
description: AgentEditorPanel.jsx's ButtonGroup renders chat-switch-participant-button (avatar+name), chat-version-selector-trigger (version text), and chat-participant-settings-button (settings icon) as three adjacent sibling <Button>s — not one "AgentName vX" chip. Confirms canon #511's framing for this surface specifically.
type: feedback
---

Confirmed live (ELITEA-2362, 2026-08-11): once an agent/pipeline participant is
active in a chat, the composer (message-input area, bottom of `/chat`) renders
`AgentEditorPanel.jsx`'s `ButtonGroup` with exactly these testid-carrying
children, in DOM order:

1. `chat-switch-participant-button` (`ChatPage.switch_participant_button`) —
   accessible name "Switch Agent"/"Switch Pipeline". Contains the avatar
   `<img>` (now `chat-switch-participant-avatar` — see below) + a `Typography`
   with `participantDetails?.name`.
2. `chat-version-selector-trigger` (`ChatPage.chat_version_selector_trigger`,
   ELITEA-2166) — text = `selectedVersion?.name` (e.g. "skills-v3.0") when not
   in small-view.
3. `chat-participant-settings-button` (`ChatPage.chat_participant_settings_button`,
   wired ELITEA-2362) — accessible name "agent settings menu"/"agent settings
   menu"; renders a `SettingIcon`, or "Editing…"/"Viewing…" text ONLY while
   `isActiveParticipantBeingEdited` is true (not the fresh-chat default state).

The avatar `<img>` inside control #1 had **no testid** until ELITEA-2362 added
`imgTestId="chat-switch-participant-avatar"` to `AgentEditorPanel.jsx`'s
`EntityIcon` call (EliteaAI/EliteaUI@91746dfc, `automation/testids`, not yet on
`main`). `EntityIcon` already supported the `imgTestId` prop (threaded to
`EliteAImage`'s `data-testid`) — same mechanism ELITEA-2361 used for
`chat-participant-avatar` in the Participants-panel row, but these are TWO
DIFFERENT physical elements (composer chip vs. panel row) that happen to share
the same underlying `useParticipantEntityIcon` hook and rendering logic.
`EliteAImage` always renders `alt="elitea"` regardless of what `EntityIcon`
passes as `alt` (see `eliteaimage_alt_prop_silently_dropped.md`).

`chat-version-selector-trigger` and `chat-participant-settings-button` were
BOTH already present in source on `automation/testids` (from an earlier,
unrelated ELITEA-2166 rework) but only `chat-version-selector-trigger` had
ever been wired into `ChatPage` as a `LocatorDescriptor` before this case —
`chat-participant-settings-button` sat unreferenced until ELITEA-2362's Test
Outline actually called for it (canon #511: a testid isn't "referenced" until
a test's executed path uses it).

Do not assume a combined "AgentName vX" locator exists anywhere on this
surface — always target the specific one of the three controls the assertion
needs.
