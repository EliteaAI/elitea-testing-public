---
name: Creating a configuration can silently become the section default
description: In some Elitea AI-Providers sections a create auto-assigns the new item as default — which turns a later "select a different one" step into a vacuous no-op
type: feedback
aliases: [auto default on create, transit create default, no-op selection, select fires no request]
tags: [area/settings, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## The behaviour is per-section, and it is not documented anywhere in the product

Measured live on Settings -> AI Providers:

| Section | Creating a configuration... |
|---|---|
| **Vector Storage** | auto-assigns it as the section default |
| **TTS** | auto-assigns it as the section default (confirmed 2026-08-30) |
| **LLMs** | does **not** — must be assigned explicitly |

## Why it matters more than it looks

A case whose step says *"select a **different** model"* is usually automated by creating a
second configuration as transit. If the create silently made that configuration the
default, the "select a different one" step re-selects what is **already** selected, which:

1. **fires no request at all** — so a helper that waits on the POST hangs its full
   timeout; and
2. asserts nothing — the case passes while the product performed no change.

Both failure modes are silent in opposite directions (a hang, or a vacuous green).

## The shape that works

Transit setup must **read the default back after the create** and put the pre-existing
one back **before** the case's own step runs. Teardown must likewise restore the default
**before** deleting the transit configuration — deleting one that the project default
still points at leaves the project pointing at something gone, from a spec that still
reports green.

Never assume either direction: read the persisted default from the product's own
`GET .../configurations/models/{project_id}?...&section={param}` response.

Related: [[mui_accordion_summary_testid_is_not_a_scope]]
