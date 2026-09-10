# Four cards from ONE run id is a different bug from the promotion gap

**Learned:** 2026-09-10 (working #2181, ELITEA-2022 — six open cards for one case)

## The move that separated them

When a FIX card looks like a duplicate storm, **map every sibling card to the `Run ID:`
in its body and to its `created_at`**. One API call each; it splits one apparent problem
into two with different fixes:

| Card | Created | Run ID |
|---|---|---|
| #2062 | 09-09 07:41Z | 34309196977 |
| #2139 | 09-09 19:55Z | 34331579791 ← delivered the repair |
| #2171 | 09-10 04:51Z | **34436416962** |
| #2181 | 09-10 08:45Z | **34436416962** |
| #2198 | 09-10 09:56Z | **34436416962** |
| #2216 | 09-10 11:51Z | **34436416962** |

- **Across runs** (#2062 → #2139 → #2171): the same true red re-detected each nightly,
  because `main` never got the repair. NOT duplicate filings. Only promotion stops them.
  (This is the taxonomy already in `a_cross_run_fix_card_is_not_a_duplicate_filing.md`.)
- **Within one run** (#2171/#2181/#2198/#2216): the intake **re-processed run
  34436416962 four times**, hours apart, filing a fresh card each pass. Pure artifact.

## Why it generalises

It was not case-specific. The same run filed ~3 cards for *every* failing test —
ELITEA-2024 as #2170/#2180/#2197/#2215, ELITEA-1899 as #2183/#2192/#2213, ELITEA-2453 as
#2182/#2199/#2217, ELITEA-2363 as #2168/#2188/#2209. **~3-4x inflation across the run.**

**Confirmed by direct count 2026-09-10 (working #2197):** ELITEA-2024's cluster is
**FOUR** from run `34436416962` (#2170 as well), on top of #2118 (run 34331579791,
delivered the repair) and #2138 — **six cards, one case, zero code delta after the
first.** The prediction above was made before #2197 was worked and held exactly.

Find them in one call:
`gh api "search/issues?q=repo:OWNER/REPO+<run-id>+in:body&per_page=30"`

## The point for #2157

Dedup on `(run_id, test node id)` needs **no knowledge of code state** and would have
collapsed 4 cards into 1 — a smaller change than the already-fixed-on-`automation/base`
check, removing more noise. Recommended ordering: (a) `(run_id, node id)` dedup,
(b) open-ELITEA-id dedup, (c) message-string / ancestry check against `automation/base`.

**Do not report a duplicate cluster as one number.** "Six cards" hides that three of them
are honest re-detections a dedup must NOT swallow.
