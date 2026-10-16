---
name: VoiceButton focus-steal on Skill instructions clear
description: clearing a Skill's Instructions editor mounts a fresh chat test-panel whose VoiceButton.stop() steals focus mid-type, breaking every Save/Save-As-Version flow that edits an EXISTING skill
type: feedback
---

## What happened (issues #2445/ELITEA-1738, #2447/ELITEA-2440, 2026-10-15/16)

CI reported `Locator.click: Timeout ... waiting for
get_by_test_id("skill-save-as-version-button")` with the button resolved and
`disabled`/`Mui-disabled`. Looked like a locator/UI-drift problem; it is not.

**Root cause, traced live + in `EliteaUI` frontend source (`origin/main`):**

1. Any "replace Skill instructions" flow — including this suite's own
   `SkillFormPage.fill_instructions()` (`select_text()` + Backspace + type) —
   necessarily passes through an **empty-instructions intermediate state**.
2. The instant Instructions is empty, `hasUnsavedRunChanges(values,
   initialValues)` (`skillRunSettings.helpers.js`) becomes true (differs from
   the saved `initialValues`), which flips `SkillRunPane`'s `showsTestPanel`
   and swaps the right-hand panel from `SkillRunPanel` to a **freshly-mounted
   `SkillTestPanel`** → a brand-new `NewChatInput`.
3. `NewChatInput.jsx` has `useEffect(() => { voiceButtonRef.current?.stop()
   }, [conversationId])` — fires on this mount too (not just a real
   stop-recording event). `VoiceButton.jsx`'s `handleStopRecording`
   unconditionally does `inputRef.current?.focus()` with no guard for
   "was anything actually recording" — stealing keyboard focus from the
   CodeMirror instructions editor to the new chat test-panel's message
   textarea, ~300-400ms after the editor empties.
4. Whatever text the test/user types next lands in the **chat input**, not
   Instructions. Instructions stays empty ("Instructions are required" inline
   error), so both Save and Save As Version stay disabled — exactly the
   "button never becomes clickable" CI timeout.

Confirmed via a `HTMLElement.prototype.focus` monkeypatch logging stack
traces in a bare `playwright.sync_api` script: the focus-stealing call
resolves to `VoiceButton.jsx:handleStopRecording` → `inputRef.current.focus()`.
Reproduced identically with `select_text()`+Backspace+type, `Ctrl+A`+Backspace,
and separately confirmed an ATOMIC `select_text()`+`keyboard.insert_text()`
(no empty intermediate state visible to React) and APPEND-only edits
**still** trigger it — any transient empty-instructions state is enough,
however briefly.

Filed `elitea-testing-public#2451` (bug, DEV-verified, both code pointers,
embedded evidence screenshot). Neither #2445's nor #2447's test/page-object
needed any change — both are already correct and will go green once #2451
ships.

## Rule going forward

Before diagnosing ANY "Save As Version button won't enable" / "Save stays
disabled" timeout on a Skill test that **edits an existing skill's
instructions** (as opposed to filling a brand-new skill's form once): check
whether the test clears Instructions at any point first. If so, this is the
likely cause — verify via a quick `HTMLElement.prototype.focus` stack-trace
instrumentation (see the repro technique above) or just check
`document.activeElement` right after the clear step; don't assume it's a
locator/timing issue and don't adjust the test. Until #2451 ships, this
affects every current and future skill-instructions-edit test using
`fill_instructions()`/`fill_instructions_markdown()` on an existing skill —
treat a fresh red of this exact shape as the SAME bug, not a new one; link
#2451 rather than re-diagnosing or re-filing.
