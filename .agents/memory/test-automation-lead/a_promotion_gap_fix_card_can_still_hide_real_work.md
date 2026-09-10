# A promotion-gap [FIX] card can still hide real work — look one method away

**Learned:** 2026-09-10, card #2168 (ELITEA-2363, `test_agent_hub_search_bar_filters_in_real_time`).
**Complement of:** `a_fix_card_can_have_no_work_in_it.md` (which is the "stop, it's a duplicate" case).

## The trap

Triage said "already repaired": the card's exact 3/3 CI signature
(`expect_response … Timeout 15000ms`, `agent_hub_page.py:575`) was fixed by PR #2097 / `8dd8a8e44`
five hours before the CI run that produced the card — whose title *names ELITEA-2363*. CI runs
`main`; the repair lives on `automation/base` (443 commits ahead). Clean promotion gap, and the
obvious move is to label it `duplicate` and close.

**That would have shipped a known hazard.** `.agents/testing.md` had explicitly left one `#1847`
`networkidle` site open — `AgentHubPage.clear_search()` — and **this spec is its sole caller**
(Step 6). The byte-identical shape in `search()` took a *sibling spec* red 3/3 **in the very same
CI run** that produced my card. So the card's spec had a proven-live, one-method-away hazard that
nobody owned, and promoting the "already fixed" repair would have carried it to `main` intact.

## The heuristic

When a [FIX] card turns out to be a promotion-gap duplicate, before closing it ask **three** things:

1. **Same spec, same class, same run** — did any *other* test in that CI job fail on a mechanism
   that also exists on my spec's path? (Grep the job log for sibling failures, not just mine.)
2. **Did a previous card knowingly defer something in this spec?** Grep `.agents/testing.md` and the
   AFS/`_surface.md` for "left open", "sibling site", "out of scope" naming my spec or page object.
3. **Is the deferred thing reachable from a method only my spec calls?** If yes, it is in-scope work
   for this card, not scope creep — declare the extension and do it.

Two of the three held here, and the delivery went from a paperwork closure to a real repair
(PR #2200) that also made the gate ~30% faster.

## Also true, and worth saying in the closure record

Delivering a repair to `automation/base` does **not** clear the CI red — the intake will re-file the
identical card on every subsequent nightly until a human promotes. Say so explicitly, name the human
as owner, and log the occurrence on #1938 rather than filing a new question card.
