---
name: Pipeline YAML-view CodeMirror squash quirk + vacuous-substring fix technique
description: get_yaml_content() returns a single no-newline string in this env (pipeline-yaml-lines testid matches 0), so yaml.safe_load() can't parse it — use the entry_point-style regex extraction instead; also a worked example of proving a bare-substring YAML assertion isn't vacuous before shipping it
type: feedback
---

## The quirk: `PipelineDetailPage.get_yaml_content()` can return NO newlines at all

`get_yaml_content()` (`automation/pages/pipeline_detail_page.py`) tries to read
CodeMirror's per-line `.cm-line` divs (via the `pipeline-yaml-lines` testid)
and join them with `"\n"`. When that selector matches 0 elements — confirmed
live 2026-07-24 in this project's env — it falls back to
`self.yaml_editor.text_content()`, which concatenates EVERY descendant text
node with **zero separators**. The result looks like:

```
entry_point: LLM 1nodes:  - id: LLM 1    type: llm    input:      - input    input_mapping: ...
```

`PipelineDetailPage.get_entrypoint_node_id()` already documents and works
around this (it's the ONLY existing caller that reads structured content out
of `get_yaml_content()`'s output) with a regex:

```python
re.search(r"entry_point:\s*(.+?)(?=\s*[a-z_]+:|\n|$)", yaml_text, re.DOTALL)
```

**`yaml.safe_load()` will NOT parse this squashed text** — it's not valid
YAML without the newlines/indentation. If you're tempted to "just parse it
structurally" (the obvious-sounding fix for a vacuous substring check), you
have to either fix `get_yaml_content()` itself (a shared-caller page-object
method — out of scope for a narrow fix-round) or reuse/extend the same
regex-extraction idiom. I added a small local helper,
`_yaml_node_field(yaml_text, field_name)`, generalizing the `entry_point:`
extraction to any top-level node field. Verified (in isolation, before
touching the test) that the SAME regex correctly handles both the squashed
form (live-captured) and a hand-built newline-separated form — the `.+?`
non-greedy capture combined with the `\s*[a-z_]+:` lookahead naturally skips
past embedded newlines rather than stopping at the first one, so it's robust
to either rendering.

## The generalizable lesson: a bare substring check on a YAML/text dump is often vacuous

`assert "input" in yaml_text` looks like it proves the Input select wrote
something — but if ANY other field's value also happens to contain that
literal substring (here: the TASK f-string placeholder `{input}` from a
DIFFERENT, already-typed field), the assertion passes regardless of whether
the thing you're actually testing worked. The fixture's pre-seeded empty
state (`input: []`) makes this a REAL regression class, not a theoretical
one: a broken `select_llm_node_input()` would leave `input: []` and the test
would still go green.

**Before shipping a substring-based text assertion, ask: does any OTHER
value in this same blob already guarantee the substring, independent of the
thing under test?** If yes, either (a) anchor to a more specific pattern that
only the real value produces (case-sensitivity mattered here too — the
collision was capitalized "Input:" from "User Input:", the real field is
lowercase "input:" — case-sensitive `re.search` with no `re.IGNORECASE` flag
was enough on its own to dodge it, but I still extracted the actual field for
a fully structural proof), or (b) extract just that field's own value and
assert on it directly.

**Verify a fix like this isn't itself vacuous** by simulating the exact
regression (comment out / skip the call under test), rerunning, and confirming
the NEW assertion actually fails — then revert and confirm the real green
run. Five minutes of extra verification, and it's the only way to be sure the
fix isn't just a differently-shaped tautology.

(From ELITEA-2004, PR #1012, fix round R2 — reviewer finding on
`test_pipeline_llm_node_configure_system_task_chat_history.py:160`/`:226`.)
