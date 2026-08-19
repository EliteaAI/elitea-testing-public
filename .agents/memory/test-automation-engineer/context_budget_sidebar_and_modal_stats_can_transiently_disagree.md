---
name: Context Budget sidebar and modal stats can transiently disagree
description: context-budget-* (sidebar) and context-modal-stat-* (Edit context settings dialog) can briefly show different tokens/percentage off the same conversation — don't assert cross-panel equality unless the case requires it.
type: feedback
---

`ContextBudgetProgress.jsx` (sidebar `context-budget-percentage`) and
`ContextBudgetStats.jsx`'s `ContextStats` (modal `context-modal-stat-percentage`)
both render straight off a `stats`/`utilizationPercentage` prop with no math of
their own — same formula, same source shape. But they are populated via TWO
SEPARATE subscriptions to the conversation's stats, not one shared read. Confirmed
live (ELITEA-2217 implementation): reading the sidebar's percentage immediately
before clicking "Edit context settings", then reading the dialog's own percentage
a moment later with NO message sent in between, showed two different values off
the identical underlying conversation (114% vs 136% in one capture). Each panel
was internally self-consistent (its own tokens/max/percent agreed with each
other) — it's only the two panels against each other that can transiently drift.

Also: sidebar's tokens text carries a trailing `" tokens"` word suffix
(`context-budget-tokens` → `"5 391 / 5 000 tokens"`) that the modal's own stat
(`context-modal-stat-tokens` → `"5 391 / 5 000"`) does not — strip the suffix
before any string comparison between the two, don't assert exact string equality.

**Don't add a cross-panel equality assertion unless the case text actually asks
for it** — it introduces a real, reproducible flake source that has nothing to do
with what most cases (e.g. ELITEA-2216/2217/2218) actually need to prove: each
panel's OWN internal consistency (tokens/max/percent agreeing with itself, a
toggle's own checked state) is the correct scope. If a future case explicitly
requires sidebar/modal parity, that's new ground — flag it to the analyst/lead
rather than assuming it always holds.
