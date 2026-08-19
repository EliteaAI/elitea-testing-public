---
name: MUI Portal dialog + shared testid — .first reads the wrong node
description: A testid shared between a Portal-rendered MUI Dialog and an always-mounted background panel resolves .first to the background node, not the dialog's
type: feedback
---

## The pattern

`StyledDialog` (MUI `Dialog`, no `disablePortal`) mounts its content via React
Portal, appended to `document.body` **after** any already-mounted page content
in DOM order. If a shared component renders the SAME hardcoded `data-testid`
both inside such a dialog and in an always-mounted panel behind it, a
`.first` read taken while the dialog is open resolves to the **background
panel's** node, not the dialog's own — the assertion silently re-checks
something the test already checked, instead of the modal's OWN copy of the
value.

Confirmed instance (ELITEA-2217 fix-round-1, PR #1606): the "Edit context
settings" dialog's Summaries stat is rendered by `SummaryDetailsButton.jsx`,
which hardcoded `data-testid="context-budget-summaries-count"` — the exact
same testid the always-mounted `ContextBudgetStatsDisplay.jsx` sidebar panel
uses (also via `SummaryDetailsButton`). `chat.get_context_budget_summaries_count()`
(`.first.text_content()`) called while the dialog was open resolved to the
sidebar's node.

## The fix pattern (mirrors ELITEA-2216's tokens/messages/percentage stats)

Give the shared component an **optional `testId` prop** (default = the
existing/background testid, so every other caller is unaffected), and wire
the modal's call site to a dialog-unique testid
(`context-modal-stat-<name>`, mirroring `context-modal-stat-tokens` /
`-messages` / `-percentage`). Zero-functional-impact, additive-only —
no new hooks/DOM nodes, just a prop threading through an existing render path.

## Regression guard worth adding

Assert `.count() == 1` on BOTH the shared/background testid and the new
modal-unique testid while the dialog is open — a regression back to the
hardcoded/shared shape shows up as `count() == 2` on the shared testid.

## Where else to check

The SAME `SummaryDetailsButton` shared-testid shape (unscoped
`context-budget-summaries-count` read while a dialog is open, byte-identical
comment wording) exists in the already-merged ELITEA-2216 test
(`test_context_management_disabled.py`) and in ELITEA-2218's
`test_context_auto_summarization.py` — check both when next touched; they
carry the same latent false-pass risk this fix closed for ELITEA-2217.
