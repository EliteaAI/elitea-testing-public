---
name: New Bucket 56-char Save is unclickable (layout shift on blur)
description: At exactly 56 chars the character counter unmounts on mousedown, shifting Save 16px up, so no click event fires — blur first, then click.
type: reference
aliases: [56 character bucket name save, artifacts save does nothing, character counter layout shift, issue 1080]
tags: [area/artifacts, type/product-defect]
created: 2026-08-23
updated: 2026-08-23
---

## Symptom

Creating an artifact bucket whose name is exactly **56 characters** (the declared
maximum): a single click on Save does nothing — no request, no toast, no error, form
stays open. 55 characters works. Tracked as `EliteaAI/elitea-testing-public#1080` (OPEN).

## Root cause (found 2026-08-23, ELITEA-1818/1819 analysis)

`CreateBucket.jsx:247` renders `Text.CharacterCounter` only while
`isFocused('name') && name.length === 56`. It sits in normal flow and occupies 16 px.

1. `mousedown` on Save → Name field blurs → counter unmounts → Save button moves **up 16 px**
2. `mouseup` lands on a different element → the browser emits **no `click`** → `onSave` never runs

Instrumented listeners captured `["mousedown"]` only. Bounding box: `y=267` focused →
`y=251` blurred. `elementFromPoint(old centre)` after blur = the form `<div>`.

Real users hit this identically (a pointer doesn't move between down and up), which is why it
reads as "frozen" rather than "broken" — a second click works.

## What to do about it

- **Automation that must create a 56-char bucket:** `bucket_name_input.press("Tab")` (blur),
  *then* click Save → POST 200. Ordinary user gesture, not a substitution — but declare it.
- **A case whose step says "click Save":** soft-assert the correct single-click behaviour with
  `# Known defect: #1080` and reach later steps via the blur-then-click. Sanctioned-RED.
- **Same pattern elsewhere:** `CreateAgentForm.jsx`, `CreateSkillForm.jsx`,
  `ApplicationEditForm.jsx` use the same focus-gated `CharacterCounter` — suspect the same
  shift at their max name/description lengths before trusting a Save click.

Related: [[artifact_bucket_fixture_delete_silently_fails_404]] (#636 cleanup leak).
Digest: `test-specs/artifacts/_surface.md` § ELITEA-1818/1819.
