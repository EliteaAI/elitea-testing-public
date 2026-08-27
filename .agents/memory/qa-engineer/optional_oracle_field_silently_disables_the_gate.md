---
name: An optional per-config oracle field silently disables the gate
description: A "populate only from live capture" field is a hole for every config that lacks it — check EVERY entry, not the two that were captured
type: feedback
---

Pattern to challenge on sight: a repair replaces a bad oracle with a **per-config
optional field** (`ToolkitConfig.tool_output_success_pattern`, `expected_shape`,
`success_matcher`, …) populated "only from live capture, never inferred". The
reasoning is honest and usually right. The defect is in the *fallback*: an unset
field is implemented as **skip the check + `logger.warning`**, i.e. a silent pass.

Review move: enumerate EVERY entry in the config registry, not the ones the
analyst captured, and for each ask *"does this entry actually RUN, and if it does,
what happens on a genuine failure?"* Look for the gate that keeps it off:
a `skip_reason`, a missing credential env var, a marker. An entry with **no
gate and no captured pattern** is a false-GREEN channel.

Worked case (ELITEA-1140/#1817, 2026-08-27): `github` + `jira` got captured
patterns; `gitlab` + `bitbucket` were harmless (unconditional `skip_reason`);
`confluence` had **neither** — and its `CONFLUENCE_API_KEY` is wired in three GHA
workflows, so it runs. A failed confluence tool call satisfied every remaining
assertion. The prior (bad) guard had caught that failure by accident, so the
repair was a net loss of detection on that one param.

"Classify nothing" is the right POLICY; implementing it as "assert less and pass"
is the bug. Make the gap loud instead — an explicit skip/xfail naming the missing
capture and a filed issue — so an uncaptured config can never report green.
