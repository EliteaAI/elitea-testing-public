---
name: Known defect #518 fires in 3 console message shapes; verify a probabilistic-defect filter actually fired
description: CredentialsList.jsx's double-onRefetch() crash (#518) logs THREE distinct console.error message shapes for one underlying error (React error-boundary companion message doesn't repeat the original text); a single-substring filter silently misses two of them. Plus the general technique for proving a filter for a probabilistic (~60-75%) known defect was genuinely exercised, not just lucky non-reproduction.
type: feedback
---

## #518's three console message shapes (same gotcha class as #611)

`CredentialsList.jsx`'s double-`onRefetch()` crash (elitea-testing-public#518,
~60-75% reproduction on any flow landing on `/credentials/all`) logs THREE
separate `console.error` calls for the SAME underlying error, confirmed live
via a temporary `msg.location`/`msg.text` debug print (added, used once,
reverted — never leave debug prints in the committed diff):

1. `"Error handled by React Router default ErrorBoundary: Error: Cannot
   refetch a query that has not been started yet.\n    at ..."`
2. `"React Router caught the following error during render Error: Cannot
   refetch a query that has not been started yet.\n    at ..."`
3. `"The above error occurred in the <CredentialsList> component:\n\n
   at ..."` — React's error-boundary companion message. This one does
   **NOT** repeat the original error text at all, so a filter matching only
   `"Cannot refetch a query that has not been started yet"` (shapes 1+2)
   silently misses shape 3 and still fails the console-cleanliness
   assertion. Confirmed by an actual re-run: my first-pass filter (single
   substring) still FAILED on a live #518 occurrence.

Fix: OR two conditions — the original-error substring, AND
`"above error occurred" in text and "<CredentialsList>" in text` (anchor on
the component name in React's boundary message, not just the phrase, same
technique already established for #611 in
`publish_unpublish_wizard_implementer_quirks.md`).

**General rule**: any known-defect console filter written against a single
observed message string should be treated as unverified until re-run against
a LIVE occurrence of that defect — React (and RTK Query, and error
boundaries generally) frequently log the same root cause in multiple
message shapes, and a filter that only catches the shape you happened to see
first will look correct in code review and still flake in CI.

## #554 (toolkitTypes 404 race) also leaks from CredentialsList's OWN mount, not just search

Previously only confirmed leaking from `test_credential_search_by_name.py`'s
repeated create-credential navigations and from an unrelated agent-detail
page (see `publish_unpublish_wizard_implementer_quirks.md`). Now confirmed a
THIRD, independent leak point: `test_credential_create.py`'s Step 1
`CredentialsListPage.navigate()` — a plain, single `/credentials/all` load,
no search, no repeated navigation. `CredentialsList.jsx` itself fires a
`useListCredentialTypesQuery` for its own "Types" filter panel, and the
project-id race that #554 documents can hit that entry point too (or, more
likely given the URL, the shared toolkit-types query is present somewhere in
the same page tree). Confirmed via `msg.location.url ==
'.../elitea_core/toolkits/prompt_lib/'`, not text alone — **before adding a
filter for what looks like #554, always confirm the URL**, per the
project's own established "don't blanket-filter any 404" rule. Any new test
whose Step 1 is a bare `CredentialsListPage.navigate()` should budget for
this noise source too, not just #518.

## Verifying a probabilistic filter actually did something (not just luck)

#518 only reproduces ~60-75% of the time. 5 green consecutive runs of a test
with a NEW filter for it is necessary but not sufficient evidence the filter
works — if #518 didn't fire in any of the 5 runs, the green result proves
nothing about the filter. Ran one supplementary 6th run with
`-s --log-cli-level=WARNING` specifically to check whether
`credentials_list_recovery.py`'s own log line
(`"Recovering from known CredentialsList crash (elitea-testing-public#518)
— reloading"`) appeared — it did, and the test still passed, which is the
actual proof the filter was exercised against a live occurrence rather than
avoided it by chance. Cheap, non-destructive, worth doing whenever verifying
a fix for a probabilistic defect (don't just count green runs — check the
defect's own recovery/detection log fired at least once across the sample).

From ELITEA-1962, PR #617 review round 2.
