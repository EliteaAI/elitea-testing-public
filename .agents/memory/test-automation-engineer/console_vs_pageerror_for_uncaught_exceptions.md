---
name: console vs pageerror for uncaught exceptions
description: page.on("console", ...) never fires for an uncaught JS exception — only page.on("pageerror", ...) does; verify empirically before trusting a console-listener idiom to catch a crash
type: feedback
---

**The finding**: Playwright's `page.on("console", ...)` only fires for explicit
`console.*()` API calls made by page JS. An **uncaught exception** (an unhandled
`throw`, a React error boundary miss, a bare `TypeError` from an unguarded
property read) does **not** reach that event at all — it fires
`page.on("pageerror", ...)` instead. Confirmed empirically (not from docs) with a
throwaway script: launched a page, registered both listeners, `evaluate()`d a
`setTimeout` that reads a property off `undefined` (mirroring the shape of
EliteaUI's real `icon_meta` crash — ELITEA-2094/#684). Result:
`console` listener captured nothing; `pageerror` listener captured the exact
exception message.

**Why it matters for this repo**: this repo has an established
`page.on("console", ...)` idiom used in 6+ test files
(`test_agent_create_button_navigation.py`, `test_agent_management.py`,
`test_credential_search_by_name.py`, `test_credential_create.py`,
`test_mcp_search_by_name.py`, `test_skill_export_import.py`,
`test_pipeline_mcp_node_*.py`) for a generic "no unexpected console errors"
side-channel check. That idiom is fine for catching `console.error(...)` calls
the app itself makes, but it is **silently blind** to an uncaught exception —
if a test (or a reviewer dispatch) asks you to "verify via console listener
that a crash's signature was captured," a console-only listener will report
"no errors captured" even when the crash DID happen, producing a false
"doesn't match the known defect" read. Any check whose target signature
includes an uncaught exception (a `TypeError`, a `ReferenceError`, anything not
wrapped in a try/catch that calls `console.error`) needs `page.on("pageerror",
...)` wired alongside — the console listener alone is not sufficient.

**Applied**: `test_chat_participants_panel.py` Step 9 (ELITEA-2094, PR #688 fix-only
pass) wires both — `console` for the repo's established idiom (catches any
`console.error` the app logs) and `pageerror` because it's the one that actually
catches #684's `icon_meta` TypeError. A live run later confirmed this end-to-end:
one verification run hit a genuine `to_have_url` timeout with a DIFFERENT root
cause (transient post-EliteaUI-merge dev-server instability, confirmed by 3 clean
follow-up runs), and the signature-check code correctly reported "does NOT match
#684 — investigate as a NEW failure" with empty captured signals from both
listeners — proof the discrimination behaves as designed on a real non-matching
case, not just the happy path.

**Reusable check**: before wiring ANY listener-based verification meant to
distinguish "known crash X" from "something else," write a 10-line standalone
script that reproduces X's exception SHAPE (uncaught vs caught-and-logged) and
confirm which Playwright event actually captures it. Don't assume the
established repo idiom transfers to a new target signature just because it's
the pattern used elsewhere.
