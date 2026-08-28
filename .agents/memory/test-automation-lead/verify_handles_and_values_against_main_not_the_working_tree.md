---
name: Verify handles AND values against main, not the working tree
description: localhost serves automation/testids, so a main-targeted spec must be provenance-checked against origin/main — and the check must cover backend-config values, not just testids
type: feedback
aliases: [main provenance check, green locally red on DEV, chat-stop-generation-button, backend config literal, working tree is not main]
tags: [area/workflow, type/promotion, type/review]
created: 2026-08-28
updated: 2026-08-28
---

## The rule

> A handle or value verified against the **working tree** is verified against
> `automation/testids`. A spec targeting **`main`** must be verified against `origin/main`.

The dev server on `localhost:5173` runs `automation/testids`, which carries every testid the
team ever wrote — merged *and* unpromoted. So an IC exploring live UI cannot tell the two apart,
and a green local run **cannot** detect the difference. On a `main`-targeted repair this produces
the exact failure the card was opened to fix: green on localhost, red on `dev.elitea.ai`.

## Two doors, and only one of them is guarded

**Door 1 — an EXISTING testid that lives only on `automation/testids`.**
Distinct from [[a_new_testid_inside_a_ci_red_fix_is_self_defeating]], which covers *adding* one.
Here nobody added anything: the analyst picked a handle the dev server already served, so it
looked pre-existing and safe. Worked case (ELITEA-0500 / #1888): the corrected-oracle design
hinged on `chat-stop-generation-button` — `main:NO`, `testids:YES`, and the only one of eight
handles that missed. Every "did we add a testid?" check passes; the trap is invisible to all of them.

**Door 2 — a LITERAL that comes from backend config, not from source.**
The provenance discipline is testid-shaped and therefore structurally blind to this. Same card:
`expect(...).to_contain_text("10 left")` cleared the locator grep, the provenance grep, the
testid table and a green run — but `10` traces to `useChatConfig.js` → `data.chat_max_upload_count`,
a per-project backend value whose source-tree literal is only a client-side fallback. Different
env, different number, red. Raised as canon card **#1916**.

Both doors have the same tell and the same fix: **trace the thing to its origin**, then assert a
*relationship* rather than a value — the auto-retrying indexed assertion instead of a settle
signal, the counter **delta off a runtime baseline** instead of its endpoints.

## What I do about it as orchestrator

- Before dispatching an implementer on a `main`-targeted repair, run the two-stage promotability
  grep from `.agents/workflow.md` § Closure record **myself**, after `cd ../EliteaUI && git fetch origin`,
  and put the result in the dispatch prompt as a hard constraint. On #1888 that one check killed the
  specced design before a line was written.
- Do not accept an AFS's "all handles `on-main ✓`" — it is written against the working tree.
  The analyst's own post-mortem: the bad handle entered via the **step table** with no row in
  § Concrete Handles, so it bypassed the provenance check every other handle passed.
- Ask of any literal asserted against rendered UI: **constant or config?** Require the source
  pointer. A green local run is not evidence either way.

Related: [[promoted_test_fixes_branch_from_main]] · [[a_new_testid_inside_a_ci_red_fix_is_self_defeating]] · [[promotability_dependency_set]] · [[closure_record_discipline]]
