---
name: ELITEA-1865 Context Management panel is not an Artifacts feature
description: Artifacts file-preview has no Context Management panel; those fields live in the context-budget widget (Chat/Pipelines/Applications) and Settings > Memory
type: project
aliases: [context management panel, context budget, ELITEA-1865, artifacts preview cancel button]
tags: [area/artifacts, type/case-text-drift]
created: 2026-08-23
updated: 2026-08-28
---

## The fact

TMS case ELITEA-1865 files a "Context Management settings panel" under the
`artifacts` module, claiming it opens with a file preview. Verified live
2026-08-23: **zero** matches for every one of its ~14 field labels anywhere on
the Artifacts page. The Artifacts preview panel renders only
`"<bucket>/<file>\nSave\nDiscard"` plus close + 3-dot menu.

The real panel is `src/[fsd]/widgets/context-budget/ui/ContextStrategyModalContent.jsx`
(`label="Context Management"`), consumed only by Chat participants, Pipelines
ChatPanel and Applications ConfigurationTab. A near-identical form at
Settings → Memory is already covered by ELITEA-2374.

Returned `blocked`; clarification `EliteaAI/elitea-testing-public#1695`.

## RE-CONFIRMED 2026-08-28 after a human bounce — and how to survive one

A human ruled on #1695 *"Panel is expected to be in place. Double check UI."* and the case
came back for re-analysis. **Verdict unchanged**, but the bounce happened because the first
pass produced a *negative observation* rather than *disproof*. What the second pass added:

- **The `afa` bucket the case names does not exist** (11 buckets in project 471, none named
  `afa`). The first pass used a fixture bucket, which left "maybe the real bucket carries
  state" open — that gap alone justified the bounce. **Always check the object the case
  literally names, or prove it is absent.**
- **Positive control**: the identical label probe on `/settings/memory` returns
  `Context Management 3 · Max Context Tokens 1 · Preserve Recent Messages 1 · Summarization 2
  · Target Summary Tokens 1`. Same method, same session — proves the zeros are absence, not a
  broken probe. See [[positive_control_for_absent_ui_claims]].
- **Closed affordance list**: `PreviewHeader.jsx` renders exactly 7 things and no feature flag
  exists under `features/artifacts/` or `pages/Artifacts/`; both 3-dot menus were opened
  (preview: Copy Content/Download/Delete; bucket: Upload files/Rename/Pin to top/Share/Manage
  permissions), and 1920x1200 shows no right-hand drawer.

Disproof posted as issue comment 5451524815 on #1695.

## Two side-facts worth keeping

- The Artifacts preview panel has **no Cancel button** — the pair is
  Save + Discard. Any artifacts case text saying "Cancel" for this panel is drifted.
- Three case labels ("Context Window", "Summarized Link Count",
  "Attribute: Clause & Format") exist nowhere in EliteaUI source — a strong
  smell that a case was authored from a hallucinated/foreign screenshot, not
  from the product. Worth grepping EliteaUI source for a case's distinctive
  labels BEFORE booting a browser: it cost ~2 minutes here and settled the case.

Related: [[positive_control_for_absent_ui_claims]] · [[artifacts_bucket_menu_is_hover_gated]] · [[artifact_bucket_fixture_delete_silently_fails_404]]
