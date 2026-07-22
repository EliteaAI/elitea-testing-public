---
name: Orphan testid vs. wired-but-uninvoked testid
description: When auditing item 2's blanket-testid clause, distinguish a testid with zero consuming code from one wired into a real (just uncalled) method — only the latter is genuinely ambiguous enough to need a fresh question
type: feedback
---

The team ruling (2026-07-14) behind checklist item 2 says "testids on elements
the test never touches = FAIL." Two shapes both violate the letter of that
rule, but they carry very different weight when deciding whether to solo-FAIL
or file a `question`:

1. **Wired-but-uninvoked** (`#511`'s shape) — the testid is passed through to
   a real, callable page-object method that genuinely exists in the diff, but
   that specific method is never called by *this* case's test. There's a
   plausible "reusable page-object scaffolding" argument (the object may
   already serve multiple cases). Genuinely murky — worth a `question` if no
   existing one covers it.

2. **Orphan** (issue #65's `close_button`/`cancel_button` shape) — the
   testid is declared as a `LocatorDescriptor` field (or base-class
   placeholder) but **no method anywhere in the diff ever references it** —
   not even an uncalled one. There's no scaffolding argument because there's
   no scaffold. This is the plain-wording case the rule was written for.

**Practical rule:** grep for `<field_name>\.` (a method actually touching the
attribute) across the whole diff, not just `<field_name> =` (the declaration).
Zero hits anywhere = orphan = solo-FAIL, no question needed — especially if an
open question already exists for the *murkier* wired-but-uninvoked shape and
recommends "no carve-out" (as #511 does): an orphan is a fortiori covered by
that same recommendation, so don't file a third overlapping question for a
case that's strictly clearer-cut than the one still open.

## Case history

- Issue #85 (ELITEA-1907, PR #543/EliteaUI#570): `generate-agent-resource-section-title-`
  declared, never referenced. Orphan shape, solo-FAIL.
- Issue #94 (ELITEA-1929, PR #548/EliteaUI#572): `toolkit-detail-discard-button`
  declared as `detail_discard_button`, never referenced by any test/page-object
  method (`grep -rn 'detail_discard_button' automation/ --include='*.py'`
  matched only its own definition). The AFS had speculatively grouped
  "Save/Discard" together in its testid-gap note, but the implemented case
  only exercised Save — worth watching for: an AFS that names a *pair* of
  elements in its gap note doesn't mean both need testids if the case only
  touches one. Orphan shape, solo-FAIL, sibling (`toolkit-detail-save-button`)
  in the same PR was correctly wired and used — the FAIL is per-testid, not
  per-PR, don't let one compliant sibling launder an orphan one.

### Wired-but-uninvoked (#511's shape) — case history, building toward a ruling

- Issue #60/#511 (ELITEA-1922, PR #292/EliteaUI#554): `toolkit-form-view-toggle`
  wired into `McpFormPage.switch_to_form_view()`, method never called by the
  test. Original case that opened the still-unanswered canon question.
- Issue #298 (ELITEA-2095, PR #693, control-audited 2026-07-21): `chat-participants-
  badge-users` wired into the pre-existing generic `is_participants_badge_visible(
  section=...)`/`open_participants_popover(section=...)` (parameterized, reused by
  sibling cases with other `section` values), but `section="users"` is never called
  anywhere in `test_open_conversation_today_section.py`. Second real-delivery
  instance of the exact shape — and this time the closure record **proactively
  disclosed it** rather than it being caught cold by audit. Did not file a
  duplicate question; flagged as a second occurrence in the #298 verdict comment
  instead, per the practice below. Judged the rest of #298's delivery clean (PASS).
- Both instances are self-disclosed/wired into reused, parameterized page-object
  scaffolding — not silent, not orphaned. The "no carve-out" recommendation on
  #511 is still just a recommendation, not a human ruling; #511/#277 are both
  now multiple days old and unanswered — worth prioritizing given they're
  recurring in real deliveries, not just a theoretical edge case anymore.
  **RESOLVED 2026-07-22:** Aliaksandr ruled option 1 on #511 (no carve-out).
  Wired-but-uninvoked is now a plain solo-FAIL, same bar as orphan. See
  [[canon_ruling_511_referenced_means_on_test_code_path]] for the full
  ruling and the tuned instructions. #277 (structural locator-disambiguation
  pair) is still open — do NOT extend this ruling to that shape.
- Issue #317 (ELITEA-2114, PR #696, control-audited 2026-07-21, one day after
  #298): `chat-conversation-menu-make-public-menuitem` /
  `chat-conversation-menu-share-menuitem` — 2 of 7 NEW menu-item testids this
  same PR added, wired into the real (also new, same-PR) `get_conversation_menu_item()`/
  `CONVERSATION_MENU_ITEM` mechanism, but never invoked with those two keys
  anywhere in the diff (only `rename/move-to/playback/pin/delete` are exercised).
  Distinct from #298's shape in one way — here the generic method AND the
  uninvoked testids were born in the same PR, not a pre-existing method reused
  from elsewhere — but the AFS's own § Concrete Handles table self-disclosed it
  ("only 5 of 7 render for a Private-project conversation"), so still cleanly
  wired-but-uninvoked, not orphan. Third real-delivery instance in 2 days. Did
  not file a duplicate question; flagged in the #317 verdict comment. #511 is
  now 6 days unanswered with 3 real occurrences piled up behind it — the
  strongest case yet for prioritizing a human ruling.
