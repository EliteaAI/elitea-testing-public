---
name: Chat folder-rename dedup — already-covered pattern
description: ELITEA-2123/2127 duplicated ELITEA-2459's merged special-chars/leading-space test verbatim — dedup via lcovered_ AFS, zero new code
type: project
---

ELITEA-2123 ("...Validation Tooltip for Invalid Input", data `"Folder$$%%"`)
and ELITEA-2127 ("...First Character Cannot Be a Space") both landed as
`already-covered` traceability AFS files pointing at
`test_folder_rename_checkmark_special_chars_and_leading_space_invalid`
(ELITEA-2459, merged `origin/automation/base`@`5cc8647c`) — the covering test's
Step 2/Step 3 used the IDENTICAL literal test data these two later TMS cases
ask for. Zero implementation needed; only two `lcovered_*.md` AFS files.

Lesson for future chat-folder / chat-conversation-rename cases: the
`ConversationNameRegExp` validation family (folder rename, conversation
rename) has now spawned near-duplicate TMS cases across a wide ID range
(2118-2120, 2121, 2130, 2133-2134, 2457, 2458, 2459, now 2123/2127) — before
classifying ANY new case on this family, `grep -n "special char\|leading
space\|first character\|tooltip" test-specs/chat-interface/_surface.md` first.
Chances are good it's already-covered or a one-line extend, not fresh work.

Verified live (not just source-cited) that "coverage judgments stand on your
own execution" applies to `already-covered` dedup verdicts too, not only to
`ready-for-automation`/`extend-existing` — drove both scenarios live this
session via `browser_fill_form` (works around the folder-name-editor's known
"append not replace" bare-`Control+a` race, same trap `ChatPage.set_folder_name()`'s
docstring warns about) before writing either lcovered_ file.
