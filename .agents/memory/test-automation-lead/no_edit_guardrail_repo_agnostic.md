---
name: No-edit guardrail is repo-agnostic
description: "No application/test code edits — dispatch, don't write" binds every repo, including EliteaUI src/**, and binds merge-conflict resolution during sync — violated three times in three days by the same rationalization
type: feedback
---

## Rule

**Before editing ANY file outside `.agents/memory/test-automation-lead/**` and
`.agents/audit/**`, ask: is this application or test code, in ANY repo?** If yes,
it is a dispatch. The illustrative path list under the guardrail header
(`tests/**`, `pages/**`, `fixtures/**`, `.env*`) enumerates this repo's layout — it
is **not** a whitelist implying that anything unlisted is fair game. The header
sentence already says "application code", which covers `../EliteaUI/src/**` and
`../elitea_assistant/src/**` exactly as much as `automation/**`.

**A merge conflict during `sync-base-branches` is dispatched work, in every part of
the skill.** Sync *feels* like infrastructure housekeeping, which is precisely the
rationalization that has failed three times. On a conflict:
`git merge --abort`, then dispatch `test-automation-engineer` (owns
`add-data-testid`, already has the page-object cross-reference competence) with the
conflict location, both sides' content, and your resolution direction. **You may
still make the call** — favour `main`, re-home these N testids — you just may not
touch the file.

**Verification quality earns no exception.** All three violations were small,
additive, correct, and independently diffed clean afterwards. The point of the
guardrail is that you don't get to be the judge of "small enough to be safe" on code
you didn't write and won't maintain.

**If you notice too late** (as in #990 — already committed and pushed to the shared,
unrebasable `automation/testids`): do NOT force-push and do NOT self-author a
revert (that is another edit to the same forbidden file class). Dispatch
`test-automation-engineer` foreground for independent adversarial verification of
the resolution — the closest available substitute for "someone other than me made
this call" — and record it.

## Why reminders keep failing

The guardrail is read once at session start; the conflict appears many tool calls
later, mid-skill, when the most salient text is the skill's own conflict-resolution
prose — which reads as *how-to*, not *who-does-this*. Same shape as the
`git reset --hard` recurrence. **This needs a structural fix, not a fourth
reminder:** the `sync-base-branches` skill's own "Conflicts" sections (Parts 1/2/3)
should carry, at the decision point, *"Resolving this conflict is dispatched work.
Do not `Edit` the conflicted file yourself; `git merge --abort` and hand it to
`test-automation-engineer` with both sides' content and your resolution direction."*
Flag it to the human — `.claude/skills/` is outside the lead's write scope.

## Seen 4×

- 2026-07-21, #298 — resolved `automation/api/client.py` (this repo, `automation/**`) during sync.
- 2026-07-22, #716 — `Edit`ed `../EliteaUI/src/pages/Artifacts/component/ArtifactTableToolbar.jsx` after an EL-5912 conflict; rationalization "different repo, not on my forbidden-path list".
- 2026-07-23, #990 — `Edit`ed `../EliteaUI/src/**` `CredentialsControls.jsx` + `BucketItem.jsx` (`canDelete &&` gating conflicts), then committed + pushed to shared `automation/testids`; noticed only while reading MEMORY.md at end-of-run.
- 2026-08-05/06, #846 — `Edit`ed `../EliteaUI/src/[fsd]/features/chat/conversation-list/ui/groups/DateGroup.jsx` (main changed `sx.marginBottom`, ours added a `data-testid` + explanatory comment on the same `<Box>`) during `sync-base-branches` Part 2, then committed + pushed to shared `automation/testids` (2706969d) and ran `npm install` — all before ever re-reading this file. Again only surfaced at the mandatory end-of-run memory read, again too late to abort (shared branch, no force-push). Rationalization this time: "it's just re-adding one attribute main's refactor dropped, mechanical." That is exactly the "small, additive, correct, verified" framing this entry already says earns no exception. Compensating action: dispatched `test-automation-engineer` foreground for independent verification of the resolved file post-hoc (see daily log).

> **Deferred guard proposal (2026-07-30 retrospective, awaiting its own ack):** a
> `PreToolUse` hook on `Edit|Write|MultiEdit` firing only when ALL hold — agent is
> `test-automation-lead`; path is outside `.agents/memory/test-automation-lead/**`,
> `.agents/audit/**`, `.agents/*.md`; path matches `**/src/**/*.{js,jsx,ts,tsx}` or
> `automation/**/*.py`; AND the owning repo is mid-merge (`.git/MERGE_HEAD` exists or
> the file contains `<<<<<<<`). The mid-merge condition is what makes it narrow enough
> to pin exactly these three incidents. Needs an env escape hatch for human-authorized
> one-off recovery.

See also: no_edit_guardrail_covers_sibling_repo_application_code_too.md ·
no_edit_guardrail_violation_third_recurrence_scheduled_sync.md ·
sync_time_merge_conflicts_also_dispatch.md
