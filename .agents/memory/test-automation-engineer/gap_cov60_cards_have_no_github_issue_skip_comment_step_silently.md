---
name: cov60 GAP-* campaign cards have no GitHub tracker issue — Task Completion step 4 is a correct no-op, not a skipped obligation
description: GAP-0xx cards (cov60 coverage-gap campaign) live only on the local .agents/automation-board/ ledger, unlike ELITEA-XXXX cases which get a GitHub issue on board #9 at intake. Searching gh issue list for "GAP-020" (or any GAP-0xx id) returns zero hits — this is expected, not a gap in tracking. Don't invent an issue reference or treat the missing comment-PR-link step as an error.
type: feedback
---

`.agents/profile.md` § Status reporting says "Comment PR link on the
originating issue: yes" — but that policy presumes an originating issue
exists. The cov60 GAP-* cards (coverage-gap campaign, e.g. GAP-020/054/073/
077/...) are generated straight onto the batch board
(`.agents/automation-board/batches/cov60/cases/GAP-<n>/source.md` +
`batch.md`'s `Cases` list) and never get a GitHub issue filed for them the
way `ELITEA-<id>` cases do via the normal tms-folder intake
(`.agents/test-automation.yaml` § intake). Confirmed for GAP-020:

```bash
GITHUB_TOKEN= gh issue list --state all --limit 300 --json number,title \
  | grep -i "gap-020"
# (no output)
```

**What this means for the implementer's Task Completion Protocol (step 4,
"Comment PR link on the originating issue"):** there is nothing to comment
on for a GAP-* card — skip it silently, exactly per the seed-governance
principle ("skip the ones it doesn't [apply]"), not as an omission to flag.
Don't fabricate an issue number or search `--search` (index lag risk anyway,
per the dedup-rule precedent) hunting for one that doesn't exist.

**Also relevant:** the back-write destination for these cards is different
from the standard onetest MCP TMS back-write — it's a "local-file backwrite"
against the board/case source file, which is explicitly the orchestrator's
post-merge job (batch clerk owns `.agents/automation-board/`), not
something the implementer performs or needs to wire.

Cross-reference: the cov60 foundation-pass commit (`534de62a`, see the
09:35 daily-log entry on 2026-07-24) already built the shared page-object
grounding + testids for GAP-020/054/073/077's surfaces (Settings/
Analytics/Hubs/Notifications) — check the relevant page object FIRST before
assuming Phase-2 exploration or `add-data-testid` work is needed for any of
these four cards; GAP-020 needed zero new locators, only the dedicated spec
file.
