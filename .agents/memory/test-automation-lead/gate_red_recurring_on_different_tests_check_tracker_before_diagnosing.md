---
name: A gate red with an identical generic signature on DIFFERENT tests each run = check the tracker before diagnosing
description: "Failed to load resource: 404" hit 2 unrelated tests across repeated gate runs — was already root-caused and filed as #554, with an established codebase-wide filter pattern; grep the tracker before spending time re-diagnosing
type: feedback
---

## What happened (2026-08-07, #1277 agents-batch1-1277)

Two separate full-scope gate attempts each surfaced exactly ONE red, same
generic signature (`Failed to load resource: the server responded with a
status of 404 (Not Found)`, always in pairs), but on a DIFFERENT test each
time (`test_add_multiple_tags_persist_after_reload` ELITEA-1878, then
`test_nested_agent_with_mcp_tool_output` ELITEA-1951 — completely unrelated
code paths). Isolated re-runs of the first failing test came back 3/3 clean.
That pattern — same generic signature, different unrelated tests, clean in
isolation — is the fingerprint of an environment/infra-level race, NOT a bug
in either test's own logic.

**Before spending time trying to network-capture/root-cause it from
scratch: `gh issue list --label bug` and grep the console-message text.**
This exact signature was already filed as #554 (an RTK-Query `toolkitTypes`
timing race, empty-projectId, cosmetic/console-only, root-caused down to the
exact source line) — and, more importantly, the codebase ALREADY has an
established filter convention for it in 5+ other test files
(`_is_known_554_warning`, matching `"404" in msg.text and
"elitea_core/toolkits/prompt_lib/" in (msg.location or {}).get("url", "")`).
`msg.location` DOES carry the failing resource's URL — Playwright's
`ConsoleMessage.text` alone looks like it doesn't (no URL in the visible
text), which is what makes this pattern non-obvious without checking
`.location` explicitly.

## The fix, once matched

Dispatch a fix-only implementer to apply the SAME precedented filter to the
batch's own affected tests (and defensively to every OTHER new/changed test
with a similar `assert not console_messages` shape near an agent/pipeline
detail page — cheap insurance, matches the pattern's "any page mount" reach).
This is NOT masking: the filter is narrowly scoped to one exact, already-open,
already-documented, functionally-inert signature — every OTHER console error
still fails the test. Landed on the batch trunk directly (no new branch/PR —
same pattern as any fix-only dispatch mid-batch), then re-gate.

## Rule of thumb

A recurring gate red whose signature is identical but whose LOCATION moves
between unrelated tests across attempts is very likely shared/environmental,
not per-test. Check the tracker (`gh issue list --label bug --state all`,
keyword-match the message text) before diagnosing from first principles —
the answer, and often an existing filter to reuse, may already be sitting
in 5 other files in the same repo.
