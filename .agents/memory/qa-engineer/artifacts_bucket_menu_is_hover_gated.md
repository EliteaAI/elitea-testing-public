---
name: Artifacts bucket 3-dot menu is hover-gated
description: bucket-menu-<name>-menu-button exists in the DOM but is invisible until its row is hovered
type: reference
aliases: [bucket menu not visible, artifacts bucket 3-dot, element is not visible bucket menu]
tags: [area/artifacts, type/quirk]
created: 2026-08-28
updated: 2026-08-28
---

## The quirk

`[data-testid="bucket-menu-<name>-menu-button"]` is **present in the DOM at all times** but rendered
invisible until its bucket row is hovered. A direct click fails with Playwright's
`element is not visible` after exhausting retries — and because the locator *resolves*, the error
looks like a timing problem rather than a hover gate.

Fix: hover `[data-testid="artifacts-bucket-row-<name>"]` first, then click the menu button.

Contrast: the per-file **preview** icon in the file table is **not** hover-gated (see #994) — don't
generalise this to the whole Artifacts surface.

## Menu contents (2026-08-28, project 471)

Bucket-level: **Upload files · Rename · Pin to top · Share · Manage permissions**.
File-preview overflow (`file-preview-overflow-menu-menu-button`): **Copy Content · Download · Delete**.

Related: [[positive_control_for_absent_ui_claims]]
