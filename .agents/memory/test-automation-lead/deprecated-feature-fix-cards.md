# [FIX] card whose test targets a DEPRECATED feature → question card, not a repair (2026-09-16)

When a `[FIX]` card's root cause is a deliberate product deprecation that removes the case's
**subject** (not just a menu count / locator), no repair preserves what the case verifies.
Worked pair: #2317 (ELITEA-2030, menu lists N types — adjustable, expected-result change declared
via #2323) vs #2319 (ELITEA-2036, "add a Custom node" — subject gone → #2326 question, card Blocked).

Tells: the commit adds the type to `deprecated.constants.js` `DeprecatedNodes` (Custom joined Loop /
LoopFromTool / Tool on EL-6616). Precedent for retiring an AUTOMATED TMS case: none as of
2026-09-16 (all `status: deprecated` cases are manual) — ask the human delete-vs-deselect.
Until the human answers, the nightly re-files a `[FIX]` duplicate every run — dedupe, don't approve.
