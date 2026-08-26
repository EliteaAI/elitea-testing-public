---
name: ELITEA-1865 Context Management panel is not an Artifacts feature
description: Artifacts file-preview has no Context Management panel; those fields live in the context-budget widget (Chat/Pipelines/Applications) and Settings > Memory
type: project
aliases: [context management panel, context budget, ELITEA-1865, artifacts preview cancel button]
tags: [area/artifacts, type/case-text-drift]
created: 2026-08-23
updated: 2026-08-23
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

## Two side-facts worth keeping

- The Artifacts preview panel has **no Cancel button** — the pair is
  Save + Discard. Any artifacts case text saying "Cancel" for this panel is drifted.
- Three case labels ("Context Window", "Summarized Link Count",
  "Attribute: Clause & Format") exist nowhere in EliteaUI source — a strong
  smell that a case was authored from a hallucinated/foreign screenshot, not
  from the product. Worth grepping EliteaUI source for a case's distinctive
  labels BEFORE booting a browser: it cost ~2 minutes here and settled the case.

Related: [[no_playwright_mcp_use_sync_playwright_script]] · [[artifact_bucket_fixture_delete_silently_fails_404]]
