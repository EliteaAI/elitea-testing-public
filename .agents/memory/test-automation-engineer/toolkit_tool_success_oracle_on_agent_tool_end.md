---
name: Toolkit tool success/failure is only visible in agent_tool_end.tool_output
description: Judge a toolkit tool call on the agent_tool_end frame's tool_output, never on chat text — DOM/events/finish_reason are identical on 401 and success
type: project
---

**Elitea publishes no structural marker for a FAILED toolkit tool execution.**
Verified live 2026-08-27 (ELITEA-1140 / card #1817, github 401 vs jira success):
identical DOM + testids, identical Socket.IO event sequence, `finish_reason:
"stop"` on both, and a recursive key-path diff of the two `agent_tool_end`
frames found **zero** differences. The only error-ish keys anywhere on the wire
(`chat_message_sync.meta.error` / `.is_error`) read `""` / `false` **even on a
genuine 401**.

The one discriminating value: `agent_tool_end.response_metadata.tool_output`.

Two traps this closes:

1. **Never scan free text for `"error"`.** A tool's *success* payload
   legitimately contains it — this repo's own branch list carries
   `tests/ELITEA-1980-credential-error-states`. That is what broke CI on a
   passing run (GHA 32931571484).
2. **Never scan the chat message at all.** It is LLM prose: three real 401s
   produced three phrasings, none containing the literal the old guard hunted
   (`"authorization error"` — the model writes *"authentication error"*), and
   all three contained `"branches"`, i.e. they SATISFIED
   `chat_response_keywords` while the toolkit was provably broken. Deleting a
   bad guard without replacing it turns false-RED into silent false-GREEN.

The shape that works — `automation/utils/toolkit_output.py`:
`find_tool_end_frames(frames, tool_name, toolkit_display_name)` (exactly one
frame ⇒ the tool really ran; nothing else in a chat test proves that) +
`tool_output_matches_success(output, anchored_regex)` against a **captured**
per-toolkit success shape (`ToolkitConfig.tool_output_success_pattern`; empty =
never captured ⇒ classify nothing, and the helper raises rather than pass).

⚠️ **Populate such a pattern only from a live capture.** The first github
pattern (`^Branches in \S+:`) was *inferred* from the chat text and was
**refuted** by capture — the real `list_branches_in_repo` output is a JSON array
of `{"name","protected"}`; the prose was narration (which even miscounted 102
for 100). Shipping the inference would have re-created the same false-RED one
layer down, on the wire.

Anonymous GitHub auth (credential `data` with `base_url` only, no token) is a
working honest source of a github-toolkit success on a public repo while #1673's
`GIT_HUB_TOKEN` stays expired — useful for CAPTURE probes; swapping the fixture
to it would change what the case verifies (human decision).
