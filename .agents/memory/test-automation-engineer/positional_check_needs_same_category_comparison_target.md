---
name: Positional assertions need a same-category comparison target, not just a non-tautological one
description: When a review finding says a bounding-box/positional assertion "proves the wrong fact" (not "proves nothing"), the fix is to seed a real sibling instance of the SAME thing under test to compare against — not a stronger version of the same structurally-decoupled comparison. Worked resolution for ELITEA-2132/PR #698 round 3, companion to qa-engineer's detection-side entry.
type: feedback
---

## Where

PR #698 / ELITEA-2132 ("Chat – Folder Creation via CHATS Header Icon"),
fix-only round 3, `automation/tests/ui/chat/test_folder_creation.py` Step 3.
Companion to the qa-engineer curated entry "Positional assertion with wrong
comparison target survives invert-sanity-check" (same PR, detection side —
read that one for the finding; this one is the resolution).

## The pattern

Round 2 fixed a "no real assertion" finding by comparing the new-folder
entry's bounding box against the "Today" conversation date-group heading —
non-tautological (invert-and-verify correctly failed), reviewed as solid at
the time. Round 3's review showed it proved the wrong thing: the Folders
and Conversations sections are separate sibling DOM containers, Folders
*always* first regardless of folder count/order — so the check only proved
layout separation, immune to a real prepend-vs-append regression, because
the test never had a second folder to compare against (cleanup runs after
every test, so it was always comparing "the only folder" against something
structurally unrelated).

**The fix was not "make the existing comparison stronger."** It was:
identify that the claimed behavior ("new folder prepends to the top of the
*folder list*") can only be tested against another member of that same
list — so seed one. Concretely: create a real baseline folder via the exact
UI flow the case itself exercises (no new API client needed — reusing the
existing create-folder flow twice was simpler and lower-risk for a
single-round fix), then compare the new editor's box against *that folder's
own row*, not a heading from an unrelated section.

## Judgment calls worth remembering

1. **Reuse the case's own UI flow to seed comparison data, rather than
   building new API infra**, when it's a single fix-only round and the
   flow is already fully exercised elsewhere in the same test. The AFS's
   own Automation Hints had recommended a `FolderAPI` client for exactly
   this kind of need — but for a one-round fix, "click the same button
   twice" was the lower-risk, lower-footprint choice. Don't over-invest in
   infra a fix-only round doesn't need.
2. **Drop the superseded check, don't keep it as belt-and-suspenders.**
   The stronger folder-vs-folder comparison fully supersedes the weaker
   folder-vs-heading one; keeping the old `conversation_id` fixture +
   `get_conversation_group_header()` call around "just in case" would have
   doubled the seeded state (a conversation AND two folders) for zero
   marginal test-strength. When a new check strictly supersedes an old one,
   remove the old one's *usage* — but leave a harmless, already-additive
   page-object method in place (deleting working code is out of a
   fix-only round's scope; a future case may still want it).
3. **Verify the exact mechanism live, before writing any code**, whenever
   the fix involves an assumption about product behavior you haven't
   personally observed — here: "can two folders share the identical
   default name with no conflict?" and "does clicking create-folder a
   second time really open a NEW second editor above the first, now-
   collapsed folder?" Both were confirmed via a `playwright-cli` session
   (open, click, confirm, click again, `eval` the real `getBoundingClientRect()`
   values) BEFORE writing the test code — cheap (a few minutes) and turns
   "I assume this works" into "I watched it work," consistent with the
   project's Phase-2-Explore discipline.
4. **Independent-DOM-check the leak surface proportionally to what you
   added.** Doubling the seeded-folder count (baseline + case's own) means
   the out-of-band leftover check has to independently verify BOTH ids
   were cleaned, every run — including the asymmetric case (a negative/
   sanity run that fails before the second folder is even created, so only
   one id needs cleanup, and the `if folder_id:` / `if baseline_folder_id:`
   independent guards both have to be shown working, not just one of them).
