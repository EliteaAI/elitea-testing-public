---
name: Chat module carries near-duplicate case ID pairs
description: chat-interface TMS cases recur under different IDs with only test-data literals changed — check _surface.md / grep case titles before assuming ready-for-automation
type: feedback
---

The `chat-interface` TMS module (`onetest-ai-tm-Elitea/tests/automated-full-regression-ui/chat/`)
has at least one confirmed instance of the same underlying flow being carried
by two separate case-ID ranges with near-identical text: ELITEA-2118/2119/2120
("Folder Creation — default name saved / custom name saved / cancel
discards") and ELITEA-2133/2134 ("Folder Creation with Custom Name via CHATS
Header Icon" / "Folder Creation Cancel Discards New Folder"), differing only
in the literal test-data folder name used.

**Before classifying a fresh chat-interface case as `ready-for-automation`:**
1. Read `test-specs/chat-interface/_surface.md` — its section headers name the
   flow, not just the case ID, so a duplicate flow under a new ID is
   findable by reading the flow descriptions, not just grepping the ID.
2. If a match looks likely, still RE-EXECUTE the new case live with its OWN
   literal test data before writing the AFS — don't assume equivalence from
   the earlier session's run. (Confirmed necessary both times: values
   differed, and re-running caught nothing new either time, but the
   assumption itself is never free.)
3. The merged-target rule still applies: if the covering spec is only on
   this batch's OWN trunk (not yet `origin/automation/base`), route
   `extend-existing`, never `already-covered` (that verdict is terminal and
   needs a base-merged target).
4. A zero-gap duplicate case is NOT `already-covered`-eligible when the
   target is trunk-only — it becomes a tag-only `extend-existing` (a second
   `@allure.issue` decorator, no test-body change). See
   `lextend_chat-folder-creation-cancel-discard-tag-only_ELITEA-2134.md` for
   the worked AFS shape.

Worth a `grep -i "folder\|duplicate" test-specs/chat-interface/_surface.md`
(or the equivalent for whatever flow the new case describes) before diving
into live exploration — it can save the whole exploration pass if the answer
is already written down.
