---
name: An oracle that is a substring of the identifier it accompanies proves nothing
description: content-assertion tautology — check the "real oracle" is not already implied by the indicator assertion
type: feedback
---

# The oracle-substring tautology

Found reviewing ELITEA-1140 / elitea-testing-public#1816 (2026-08-27), reviewer slot.

`test_toolkit_parameterized.py::TestToolkitTestSettings` asserts two things about the
same string:

```python
assert cfg.test_tool_result_indicator in result_text   # the tool KEY
assert cfg.test_tool_result_content   in result_text   # "the only real oracle"
```

The second is supposed to catch the `✅`-with-an-error-body class (`✅ list_branches_in_repo
(0.213s) Failed to list branches: 401 {"message": "Bad credentials"}` — the checkmark means
the tool RAN, not that the call SUCCEEDED). It only does that when `content` is not already
implied by `indicator`:

| param | indicator | content | catches ✅-with-401? |
|---|---|---|---|
| github | `list_branches_in_repo` | `"main"` (with quotes) | **yes** |
| jira | `list_projects` | `project` | **no** — substring of the key |
| confluence | `list_pages_with_label` | `page` | **no** — substring of the key |

So two of the three params carry an oracle that is satisfied by the result header line
alone. The AFS's own verified-result table even records it (`✅ (page, via list_pages…)`),
and the code comment still says "this content assertion is the only real oracle in this
test" — true for github, false for the other two.

**Reviewer move, generalised:** whenever a test asserts `A in text` and `B in text` against
the SAME captured string, check whether `B in A`. If it is, the second assertion adds
nothing and the failure mode it was written for is uncovered — regardless of how strongly
the comment above it argues otherwise. A good oracle for a tool run is a value from the
tool's PAYLOAD that cannot appear in its name (a branch name, a quoted id, a count key).

Pre-existing here (the old code compared against `page.locator("main").text_content()`,
which was weaker still), so it did not block the repair — raised as an Important
non-blocking finding.
