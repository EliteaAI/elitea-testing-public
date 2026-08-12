---
name: Skill test panel shares Chat's response action-button testids
description: SkillTestPanel reuses ApplicationAnswer.jsx (ChatBox's component) — chat-read-out-button/chat-copy-button already testid'd, but SkillDetailPage has no LocatorDescriptor fields for them yet (ChatPage does)
type: project
---

ELITEA-2442 analysis (2026-08-12): the Skill test panel's AI-response action
row (Read aloud speaker icon, Copy to clipboard icon, Regenerate, Delete) is
NOT a separate component — `SkillTestPanel.jsx` renders the exact same
`ChatMessageList` → `ApplicationAnswer.jsx` tree the Agent/Chat `ChatBox.jsx`
uses (same pattern already documented for the model-selector/model-settings
widget under ELITEA-2436). So every testid on that row is already on `main`:
`chat-read-out-button` (aria-label "Read out"), `chat-copy-button`,
`chat-regenerate-button`, `chat-delete-button`.

The catch: `ChatPage` already has `LocatorDescriptor` fields for these
(`read_out_button`, `copy_action_button`, `regenerate_action_button`,
`delete_action_button` — `automation/pages/chat_page.py:460-528`), but
`SkillDetailPage` extends `SkillFormPage`, NOT `ChatPage` — no shared base,
so it has ZERO fields for this row. Any case touching skill-test-panel
response actions needs the implementer to add fresh `LocatorDescriptor`
fields on `SkillDetailPage` mirroring `ChatPage`'s exactly (same testid
strings) — this is page-object wiring work, not an `add-data-testid`
round-trip, since the testids themselves already exist in source.

Also: don't select "Copy to clipboard" by text/role in this area —
`UserMessage.jsx` renders an unrelated same-labelled button with NO
`chat-copy-button` testid on the user's own message row. Testid-scoped
selection is required, not optional convenience.

Voice features (gating whether Read-out even renders) default ON on
localhost: `VOICE_FEATURES_ENABLED` / `VOICE_FEATURES_TEMPORARILY_DISABLED`
in `common/constants.js` default to `true`/`false` respectively when their
env vars are unset (confirmed unset in `EliteaUI/.env`).
