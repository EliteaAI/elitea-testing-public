---
name: ELITEA-1962 PR #617 R2 — round-1 fix exposed known #518 console flake
description: Moving the console listener before navigate() (round-1's correct fix) makes test_credential_create.py intermittently fail on the pre-existing, already-tracked, OPEN defect elitea-testing-public#518 (CredentialsList.jsx double-refetch race) because the test's console filter only covers #291, not #518
type: feedback
---

## What happened

Reviewing PR #617 (ELITEA-1962, create-credential) round 2, after the implementer
pushed commit `2dc2a785` claiming both round-1 findings fixed (console listener
moved before `list_page.navigate()`; dead `entity_card_tag_chip` field dropped).
Both claims verified TRUE by direct code read (line order + grep). Mechanical
locator-policy grep (`git diff automation/base... | grep get_by_role|...`) also
clean — all 3 hits are the project's sanctioned `page.locator(self.SELECTOR.format(...))`
dynamic-testid pattern, not violations.

But independently re-running `test_credential_create.py` 4× (mandated — don't
trust the implementer's "GREEN 3/3, Reruns: 0 — clean 3/3, no flake" claim)
surfaced **3 of 4 runs FAILED** on the test's own console-error side-channel
assertion (Step 8 / final check), not on any functional step. The credential
still gets created and appears correctly in the list every time (functional
flow unaffected) — only the `assert not console_messages` check fails.

## Root cause

`automation/pages/credentials_list_recovery.py` documents a pre-existing, OPEN,
already-filed defect **elitea-testing-public#518**: `CredentialsList.jsx`'s
mount effect calls `onRefetch()` twice unconditionally on `/credentials/all`,
and the second call throws "Cannot refetch a query that has not been started
yet" (RTK Query), tripping React Router's default error boundary. Documented
reproduction rate ~60% (my 4 runs: 3/4 = 75%, consistent). The project already
built a recovery helper (`recover_from_credentials_list_crash()`, wired into
`CredentialsListPage.navigate()`) that detects the "Unexpected Application
Error!" text and reloads — this recovers the FUNCTIONAL flow fine.

But recovery happens AFTER the crash's console messages already fired. Round-1
correctly required the test's `page.on("console", _on_console)` listener to
register BEFORE `list_page.navigate()` (so it doesn't miss the initial page-load
window) — and that fix is 100% correct in isolation. The side effect: the
listener now also captures the #518 crash's console spam on the ~60-75% of runs
where it fires, and `test_credential_create.py`'s own filter
(`_is_known_291_warning`) only covers issue #291 ("missing key prop"), not #518.

This exact filter-per-known-defect pattern already exists in the sibling
`test_credential_search_by_name.py` (`_is_known_291_warning` +
`_is_known_554_warning`) — the fix is additive: add a third
`_is_known_518_warning()` matching "Cannot refetch a query that has not been
started yet" / the CredentialsList.jsx error-boundary text, same idiom,
referencing #518. Not defect-masking — #518 is already tracked, already
functionally worked around by the page-object layer; the test just needs to
apply the suite's own established noise-filtering convention to it.

## Durable lesson

**Any new test that (correctly) registers a console listener before its first
`/credentials/all` navigation is now exposed to #518's ~60% flake rate**, until
it adds the matching filter. Every future credential test touching
`CredentialsList.jsx` (via `CredentialsListPage.navigate()` OR
`CredentialDetailPage.open_credential_by_name()`, both call the recovery
helper) needs to check whether its console assertion accounts for #518 —
grep sibling `_is_known_29
1_warning`/`_is_known_554_warning` precedent before
writing a fresh one. A round-1 finding that's correctly fixed can still create
a NEW downstream failure mode — always independently re-run after a "both
fixed" claim, don't just diff-review the fix.

Also re-confirmed the existing `git worktree add`/`remove` gotcha
(`git_worktree_can_leave_main_checkout_on_wrong_branch.md`): this session's
worktree cycle again left the main checkout on the PR's branch
(`tests/ELITEA-1962-create-credential`) instead of `automation/base` — restored
via plain `git checkout automation/base` (safe, no conflicts). Third confirmed
occurrence of this pattern in this repo.

## Resolution (R3, commit `85da0567`) — CONFIRMED not just theoretically fixed

The implementer's round-3 fix added `_is_known_518_warning()` exactly as
recommended above (2 message shapes: raw RTK error text, React's error-boundary
companion anchored on `<CredentialsList>`) plus `_is_known_554_warning()`
(exact-URL match, not blanket-404) — both narrow, matching #518/#554's own
filed root-cause text verbatim. R3-reviewer (fresh session, isolated `git
worktree`) independently re-ran the test 8× (5 required + 3 bonus): 8/8 GREEN.
One bonus run with `-s --log-cli-level=WARNING` caught `credentials_list_recovery.py`'s
"Recovering from known CredentialsList crash (elitea-testing-public#518) —
reloading" firing LIVE mid-run — the test still passed. This is the strongest
verification available short of forcing the race deterministically: the filter
was proven to catch a genuine real-time #518 occurrence, not just green on a
sample that happened to avoid the race. Verdict: APPROVED, merged.

**Reusable technique**: when reviewing a console-filter fix for an
intermittent, already-tracked defect, don't stop at N clean re-runs — run at
least one pass with `-s --log-cli-level=WARNING` (or the project's equivalent
verbose/live-log flag) so any known-defect recovery-path log line that fires
mid-run is visible. A clean run tells you the filter didn't cause a false
failure; a clean run WITH the defect's own recovery log visible tells you the
filter actually did its job against a live occurrence.
