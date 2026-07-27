---
name: Killed background run orphans test data
description: Interrupted/backgrounded pytest runs bypass Python `finally` cleanup entirely (SIGKILL), leaving real orphaned entities with the test's fixed literal names — a recurring false-positive source for any lookup that excludes "this run's data" by id only
type: feedback
---

## What happened (ELITEA-1790)

A background `pytest` invocation appeared to vanish with an empty output
file (no error, no exit code recorded). It had actually run far enough to
create 5 skills (via UI) before the underlying process was killed — likely
because the shell session backing a backgrounded Bash tool call was reset/
torn down between tool calls, which took the child pytest/Chromium process
down with it (SIGKILL-equivalent). Because the kill was hard, the test's
`finally:` cleanup block never ran, so the 5 skills (fixed literal names:
`elitea-1790-skill-2` .. `-skill-6`) were left in the project indefinitely.

On the next (successful, foreground) run, a test step that looked up "the
6th distinct skill in the project" filtered `all_skills` by **id** only
(`s["id"] not in skill_ids`, where `skill_ids` was *this* run's own 5 freshly
created ids). The orphaned same-named skill from the killed run passed that
id filter (different id, same name) and got picked as the "6th" skill. The
subsequent `is_skill_attached(sixth_skill_name)` check is **name-based, not
id-based** (Playwright's `get_by_text(name, exact=True)` scoped to the
Skills section) — so it matched *this* run's own freshly attached
same-named skill and returned `True`, producing a false-positive "6th skill
is attached" failure that had nothing to do with the product.

## The general lesson

Any exclusion filter meant to isolate "this run's own test data" from
"everything else in a shared environment" must exclude by **every axis the
downstream check will match on**, not just the axis convenient to filter by
(id). If the downstream verification is name-based, the exclusion must also
be name-based (or the test data must use per-run-unique names in the first
place). This class of bug only surfaces when a prior run's cleanup failed to
run — which for pytest with `finally`-based cleanup, happens on *any* hard
kill (background timeout death, host process reset, OOM, manual `kill -9`),
not just assertion failures (which DO still run `finally`).

## Practical takeaways

1. **When a backgrounded test run "vanishes" with a 0-byte output file and
   no process in `ps aux`,** don't assume it never started — it may have
   run partially and been hard-killed mid-flight, leaving orphaned entities
   behind under the test's fixed names. Check the environment directly
   (a one-off script using the project's existing API client class, e.g.
   `SkillAPI(browser_cookies=[])` which falls back to the bearer token in
   `.env.test` when no browser cookies are passed — no live browser session
   needed) before assuming a clean slate.
2. **Any "find the Nth pre-existing X, not one of the M I just created"
   lookup should exclude by both id AND by the test's own naming pattern**
   (e.g. a `startswith("elitea-<TMS-ID>-skill-")` guard), not id alone —
   cheap insurance against exactly this class of false positive, and it
   costs nothing when the environment is actually clean.
3. **Prefer foreground execution with output redirected to a file** (`cmd >
   /tmp/x.log 2>&1; echo $? > /tmp/x.done`) over relying on the harness's
   auto-backgrounding for anything with real side effects (data creation),
   so a kill is visible immediately rather than silently orphaning state.
