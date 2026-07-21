---
name: Positional assertion with wrong comparison target survives invert-sanity-check
description: A bounding-box assertion can be non-tautological (fails when inverted) yet still test the wrong relationship — proving a structural layout fact instead of the claimed list-ordering fact. Invert-and-verify only rules out tautology, not scope mismatch.
type: feedback
---

## Where

PR #698 / ELITEA-2132 ("Chat – Folder Creation via CHATS Header Icon"), round-3
independent review, `automation/tests/ui/chat/test_folder_creation.py` Step 3
(lines ~178-200), `automation/pages/chat_page.py::get_conversation_group_header()`.

## What happened

Round 2 caught that the original case's step-3 clause — "New folder entry
appears **at top of folder list**" — had a Coverage Map row marked `asserted`
with no real positional check in code (only value + focus were asserted).
The round-2 fix added a genuine bounding-box comparison: the new-folder
input's bottom edge (`y + height`) must be `<=` the "Today" conversation
date-group heading's top edge (`y`). The implementer explicitly
sanity-checked it wasn't tautological — temporarily inverted the comparison,
confirmed a real `AssertionError` fired, then reverted. This is good
practice and it DID prove the check isn't a no-op.

But live DOM inspection (creating a folder, then creating a SECOND folder,
and reading both elements' `getBoundingClientRect()`) showed something the
invert-check couldn't catch: the "Folders" section (`data-tour="chat-folders"`)
and the conversation date-groups section are **separate sibling containers**
in the DOM — the Folders block unconditionally precedes the Conversations
block, regardless of how many folders exist or their internal order. Proof:
created folder A (id 5), then folder B (id 6) — B rendered at `y=56`, A at
`y=97`, confirming the product DOES prepend new folders to the top of the
folder list (correct behavior). But the merged assertion never compares a
new folder against an existing sibling folder — it only compares against the
conversations section, which is a **structurally fixed layout fact**,
unrelated to folder insertion order. A regression that started **appending**
new folders to the bottom of the folder list instead of prepending them
would still pass this test, because the folder-vs-conversation-section
ordering would be unaffected.

## The lesson

"Sanity-check by inverting the comparison and confirming it fails" proves
the check isn't a **tautology** (always-true regardless of state). It does
**not** prove the check tests the **right relationship** claimed by the
Coverage Map row. A bounding-box/positional assertion needs a second,
independent question asked at review time: *if the specific behavior this
row claims were regressed, would this exact comparison actually change
value?* Answering that requires understanding the DOM/layout structure
(here: two sibling containers, not one ordered list), not just flipping the
inequality operator.

## Applies to

Any AFS/Coverage-Map row whose "Asserted where" is a positional/bounding-box
check, especially ones added specifically to close a prior round's
"over-claim" finding — the fix can look thorough (real DOM comparison,
negative-case sanity-checked, clear code comment) while still not closing
the original gap, if the comparison target is structurally decoupled from
the claimed behavior. Verify by directly manipulating the compared-against
sibling (e.g., create a second real folder) and confirming the check's
result actually depends on it.
