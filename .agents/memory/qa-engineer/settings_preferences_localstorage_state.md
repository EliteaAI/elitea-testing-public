---
name: /settings/preferences stores its state in localStorage, not on the account
description: Voice + Sound Notifications need NO teardown — unlike the persona/context-management family on the shared user record
type: project
aliases: [preferences, voice personalization, sound notifications, elitea_voice_config, teardown]
tags: [area/settings, type/test-data]
created: 2026-08-29
updated: 2026-08-29
---

`/settings/preferences` keeps both its sections client-side:

| Section | localStorage key | Shape |
|---|---|---|
| Voice Personalization | `elitea_voice_config` | `{voiceName, voiceId, rate, volume}` |
| Sound Notifications | `elitea_ui.sound_notifications` | `{enabled, volume}` |

A pytest browser context is fresh per run, so these specs need **no read-before-write, no
restore, and they pollute nothing**. That is the opposite of the neighbouring
`/settings/ai-personality` and `/settings/memory` families, whose values live on the shared
`${TEST_USER}` record and MUST be restored in teardown.

Two consequences worth remembering:
- A "fresh profile" defect is therefore fully deterministic in pytest — e.g.
  EliteaAI/elitea-testing-public#1965 (blank Voice dropdown) fires on **every** run.
- Sound Notifications' toggle **unmounts** its volume slider *and* its Preview Sound button
  (`{config.enabled && …}`) — `to_have_count(0)`, never `to_be_disabled()`. Third distinct
  hide mechanism on this surface; the section body stays visible, which is how you tell an
  unmount from an accordion collapse.

Related: [[mui_slider_drag_vs_keyboard]]
