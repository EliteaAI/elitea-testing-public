---
name: Gate on the environment the repair is FOR — an env-specific guard gated only on localhost leaves its central risk unverified
description: #2074 added a deployed-env gateway-error guard and gated it 3x via localhost; the duplicate card #2116 ran it on dev.elitea.ai and only then was the review's own unfalsified concern actually settled
type: feedback
aliases: [gate environment mismatch, deployed env gate, localhost gate insufficient, env-specific guard, where to gate a repair]
tags: [area/test-repair, area/ci, type/gate]
created: 2026-09-09
updated: 2026-09-09
---

## The shape

A repair whose *mechanism* is environment-specific must be gated on that
environment. Gating it somewhere cheaper proves the test still passes; it does
not exercise the thing that was built.

`.agents/testing.md` already says some specs *cannot* be gated on localhost
(the publish-wizard `user_token` case). This note is the weaker, far more common
sibling: the spec runs fine on localhost, so nobody notices the gate never
touched the repair's actual subject.

## Worked case — #2074 / #2116 (ELITEA-1740)

#2074 repaired a *diagnosability* failure: a full-page gateway 500 served in
front of the app on `dev.elitea.ai` sailed through `BasePage.navigate()` and
surfaced ~64 s later as `'skill-a-…' should be visible in the grid`, naming the
Skills feature for an infra fault. The fix: `SkillsListPage.navigate()` raises on
a non-OK top-level `Response`.

The gate was **3x at ~55 s against the DEV backend via `localhost:5173`**, plus a
3/3 pre-change reproduction. Green, honest, and it never once executed the guard
on a deployed env — where `APP_PREFIX=/app` changes the navigation URL.

That mattered, because the review had attached an explicit concern it could not
settle statically (carried to **#2089**): `response.ok` is False for anything
outside 200-299, so a legitimate non-2xx main-frame navigation would make the
guard raise on a *healthy* load. Unfalsifiable by inspection — and the only place
it could be falsified was the env nobody ran.

On the duplicate card: **3/3 PASSED on `https://dev.elitea.ai`** (90.63 s w/ one
cold-start rerun, 55.49 s, 55.03 s), guard never fired, all 5 steps green. The
concern is now settled empirically. Zero lines of code to do it.

## The test to apply

Ask of any repair: **what environment does the mechanism I added respond to?**

- guard against a *gateway/proxy/CDN* behaviour -> deployed env, always
- guard against *deploy-time config* (`APP_PREFIX`, auth mode, same-vs-cross-origin) -> deployed env
- a locator/assertion/wait change on app DOM -> localhost is fine

If the answer is "deployed", one extra invocation on the deployed env is worth
more than the 2nd and 3rd localhost runs combined, because it is the only run
that can *disagree*.

## Deployed-env cold start is its own flake — do not read it as the guard firing

DEV run 1 reran once. It was **not** the guard and not the feature: allure showed
status `broken`, **zero steps recorded**, dead in the auth fixture's very first
navigation.

```
playwright._impl._errors.TimeoutError: Page.goto: Timeout 15000ms exceeded.
Call log:
  - navigating to "https://dev.elitea.ai/", waiting until "domcontentloaded"
```

Root URL, before Step 1 - a precondition failure upstream of every assertion,
first-connection cold start against the deployed env. Never a member of a
sanctioned-RED set; response is re-run, and `--reruns=2` absorbs it. When
triaging a deployed-env run, check the step count first: **zero steps means the
test never started**, so nothing about the repair is implicated.

Related: [[a_duplicate_card_is_where_you_pay_the_originals_evidence_gap]] (item 1
of its value menu is this note's action) ·
[[two_fix_cards_can_cite_the_identical_ci_run]]
