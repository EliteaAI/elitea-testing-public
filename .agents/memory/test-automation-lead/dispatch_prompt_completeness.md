---
name: Dispatch prompt completeness — and premises worth verifying first
description: The prompt is the gate; the pieces a subagent cannot rediscover (tracking issue number, sibling AFS, conflict risk, in-turn-wait obligation) must be handed to it, and an audit dispatch's own framing must be verified before scoring anything.
type: feedback
---

## Rule — put in the prompt what the subagent cannot recover

- **Locator policy line, verbatim**, on every implementer and reviewer dispatch
  (canon: `.agents/role-overrides.md` § Orchestrator slot). The prompt is the gate.
- **The originating tracker issue NUMBER on the implementer dispatch too**, not
  just the analyst's. Phase 6 step 4 ("comment PR link on the originating issue")
  otherwise silently fails: the implementer searches by *title text* and comes up
  empty, and you backfill post-hoc. It is the one piece of context it cannot
  reliably rediscover — a case-ID search and a tracker-issue search are different
  lookups.
- **Sibling context, pre-supplied.** Before dispatching the analyst, grep
  `test-specs/**` for a title or shared-component echo. On a real hit, name the
  sibling AFS path, its implementation files, and its one documented finding
  (defect, testid gap, quirk) so the analyst checks for *drift* against a known
  precedent instead of starting blank. Not scope creep — she still executes live.
- **Name the git-conflict risk on fix-only rounds** when the base has moved since
  the branch was cut (it usually has — you land memory there between rounds):
  tell the implementer to `git rebase automation/base`, or to just push and let
  you resolve — never to `git merge origin/automation/base` mid-fix.
- **State the in-turn-wait obligation** whenever the round plausibly involves a
  multi-run verification batch (flaky hardening, repetition checks): "if you start
  any background run, poll it to completion synchronously before ending your turn."
  Stated explicitly, it worked on the very next round (an 18-run batch waited out
  in-turn); left implicit, the batch gets orphaned.
- **On a recovery dispatch, say the work is already there**: "the diff in the
  working tree is correct — verify it, don't redo it, then run/commit/push."

## Rule — verify the dispatch's own premise

An audit/control dispatch's framing ("a delivery in `Ready` awaiting routing") is
a claim, not a fact. Before scoring any checklist: verify board status
(`gh project item-list`), that a PR for *this* case actually merged
(`gh pr list --search "<id>"`), and that a closure record was really posted (read
the last comment). If any come back negative this is **not a delivery to audit** —
return a distinct **NOT-READY** verdict with the exact evidence, and check for real
WIP (branches, uncommitted diffs, companion-repo PRs) so the recommendation is
"resume from X", not "start over". `FAIL` reads to the human as *rejected on
quality*, which triggers the wrong response. Still apply the completion label;
leave the card untouched.

## Seen 4×

- #209/ELITEA-1832 — issue number given to the analyst, not the implementer; PR-link comment silently skipped, backfilled by hand.
- #65/ELITEA-2001 — sibling ELITEA-1915 AFS pre-supplied; analyst immediately found the *narrower* real gap (shared component had gained testid props, the Skill wrapper never wired them).
- #242/ELITEA-1847/PR#661 — implementer resolved a base conflict with `merge` mid-fix, polluting the PR diff; the risk was never named in the prompt.
- #26/ELITEA-1735 — control dispatch framed as a `Ready` delivery; board said `In Progress`, no closure record, no successor PR, real WIP on disk.

See also: originating_issue_number_needed_in_implementer_dispatch_too.md ·
pre_supply_sibling_afs_context_to_analyst.md ·
control_dispatch_premise_can_be_stale.md
