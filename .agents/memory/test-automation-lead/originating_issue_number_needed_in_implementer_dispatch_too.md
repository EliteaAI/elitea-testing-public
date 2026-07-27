---
name: Originating issue number needed in implementer dispatch too
description: pass the tracking-issue number to the implementer dispatch, not just the analyst's, or Phase 6 step 4 (comment PR link) silently gets skipped
type: feedback
---

On #209/ELITEA-1832 I named the originating tracker issue (#209) in the
analyst dispatch prompt (for defect filing) but not in the implementer
dispatch prompt. The implementer's own Phase 6 step 4 ("comment PR link on
the originating story/issue") requires it to find that issue itself — it
searched via the dedup rule (`gh issue list ... --json title`) and came up
empty, because it was searching by title text, not the number I already
had in hand. It correctly reported the gap rather than skipping silently
("Note for the lead: no existing GitHub tracking issue found") — but that
still left me to backfill the PR-link comment post-hoc instead of it
happening as part of the implementer's own handoff.

**Fix:** every implementer dispatch template should carry the originating
issue number explicitly, the same way the analyst dispatch already does —
even though the canonical template in the orchestration playbook doesn't
list it as a per-case parameter for that slot. Cheap to add, and it's the
one piece of context the implementer cannot reliably rediscover on its own
(a case ID search and a tracker-issue search are different lookups).
