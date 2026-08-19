---
name: Modal stat display shares component but not testids with sidebar panel
description: ContextStrategyModalContent's Tokens/Messages/Summaries stats use a DIFFERENT component than the sidebar Context Budget panel, and only Summaries inherited a testid for free.
type: feedback
---

Context Budget has TWO places that render Tokens/Messages/Summaries stats, and
they are NOT the same component, even though an AFS/analyst pass can easily
assume they are (same visible labels, same underlying `stats` object):

- **Sidebar panel** (`ContextBudgetExpanded.jsx` → `ContextBudgetStatsDisplay.jsx`)
  — carries `context-budget-tokens` (in `ContextBudgetProgress.jsx`),
  `context-budget-messages-count`, `context-budget-summaries-count`
  (`STAT_VALUE_TESTIDS` dict in `ContextBudgetStatsDisplay.jsx`).
- **"Edit context settings" modal** (`ContextStrategyModalContent.jsx` →
  `ContextBudgetStats.jsx`'s `ContextStats` component) — a DIFFERENT
  component, only ever mounted inside this modal. Before ELITEA-2216 it had
  **zero testids** on Tokens/Messages — plain `<Typography>` values with no
  `data-testid` at all.

The one exception: **Summaries** in the modal DOES render with
`context-budget-summaries-count` already — not because `ContextBudgetStats.jsx`
wired it, but because Summaries always renders through the shared
`SummaryDetailsButton.jsx`, which hardcodes that testid unconditionally
regardless of which parent calls it. This makes it easy to assume "if
Summaries works, Tokens/Messages must too" — they don't; check each value's
render path independently, don't infer from a sibling in the same array.

If a case needs to assert the MODAL's own stat display (not just the sidebar
panel before/after opening it), grep `ContextBudgetStats.jsx` for
`data-testid` before assuming the AFS's "pre-existing, no new testid work
needed" claim covers all three values — it may only be true for Summaries.

Testids added for this gap (ELITEA-2216, EliteaAI/EliteaUI@69b103b2):
`context-modal-management-toggle` (the modal's own "Context Management"
Switch — also had no testid), `context-modal-stat-tokens`,
`context-modal-stat-messages`.

**Round 2 (same case, fix round 1, EliteaAI/EliteaUI@3ce289af): the SAME
pattern recurs WITHIN a single stat value.** `context-budget-tokens` /
`context-modal-stat-tokens` cover only the fraction text (`"0 / 6 400
tokens"` / `"0 / 6 400"`) — the percentage suffix next to it
(`{utilizationPercentage}%`, in `ContextBudgetProgress.jsx` line ~29 for the
sidebar and `ContextBudgetStats.jsx`'s `item.suffix` render for the modal)
is a SEPARATE sibling `<Typography>` with no testid of its own in either
place. An AFS/PR claim that "the tokens testid reads `X / Y` + `Z%`" is
describing two DOM nodes as if they were one read — verify against the JSX,
don't trust the phrasing. New testids: `context-budget-percentage`
(sidebar), `context-modal-stat-percentage` (modal). General principle: when
one visible "value" is actually rendered as N sibling text nodes (value +
unit, value + percent, value + suffix), each node needs its own testid if
the case asserts it — don't assume a compound-looking Concrete-Handles row
maps to one handle. See also
`.agents/memory/qa-engineer/afs_single_handle_claim_may_hide_a_sibling_untested_value.md`
(reviewer-side account of the same incident) and this repo's
`afs_concrete_handles_table_can_undercount_verify_clauses.md`.
