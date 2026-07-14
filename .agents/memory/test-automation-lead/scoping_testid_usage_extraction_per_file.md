---
name: Scope testid-usage extraction per file, not globally
description: When enumerating "every testid a case's diff/test uses" for a closure record, build the field→testid map per source file — a global dict lets a later file's same-named field silently overwrite an earlier one
type: feedback
---

## The bug

Writing a one-off script to answer "which testids does this test actually
touch?" (needed for the closure record's promotability table when the test
calls through 6-7 page-object files), the natural first pass built ONE
dict across all files:

```python
class_fields = {}
for fname in files:
    for m in re.finditer(r'(\w+)\s*=\s*LocatorDescriptor\(testid="([^"]+)"', open(fname).read()):
        class_fields[m.group(1)] = m.group(2)   # BUG: same key, different files, silently overwrites
```

Two page objects both have a field named `save_button` (e.g.
`SkillFormPage.save_button -> "skill-save-button"` and
`AgentFormPage.save_button -> "agent-save-button"`). Whichever file is
processed last wins the dict slot — the earlier file's mapping silently
vanishes. The script still runs and produces plausible-looking output; it's
just wrong for every field name reused across more than one page object,
and nothing errors to flag it.

## The fix

Build the field→testid map **fresh per file**, and check that file's own
called methods against only its own map:

```python
for fname, methods in files_methods.items():
    src = open(fname).read()
    class_fields = {}                       # <-- scoped inside the loop
    for m in re.finditer(r'(\w+)\s*=\s*LocatorDescriptor\(testid="([^"]+)"', src):
        class_fields[m.group(1)] = m.group(2)
    # ...then walk this file's AST using only this file's class_fields
```

## The broader technique (worth reusing)

For a closure record's "every testid the case's diff uses" table, hand-
tracing every method a test calls (across many files) is too slow to do by
memory or plain grep — a small one-off AST script is the right tool:
1. List the exact method names the test file actually calls, per page-object
   file (from reading the test's own call sites — not "every method in the
   file").
2. Per file, parse with `ast`, build that file's own
   `field -> testid` map from `LocatorDescriptor(testid="...")` assignments
   AND `'[data-testid="...` UPPER_CASE template constants.
3. For each called method's `FunctionDef` node, regex the function's own
   source segment for `self.<field>` references against that file's map,
   PLUS inline `get_by_test_id("...")`/`get_by_test_id(f"...")` literals
   (pre-existing tech-debt code sometimes still calls this directly instead
   of through a class field — don't miss those).
4. Cross-check a sample of the candidate list by reading the actual method
   bodies — the script produces a strong candidate set, not a source of
   truth to blindly trust.

Then verify each candidate testid against freshly-fetched `origin/main` and
`origin/automation/testids` (`git fetch origin` first, non-optional — see
the promotability-grep-false-negative memory for the bare-value-vs-attribute-
string gotcha on the grep pattern itself).

## Worked example

Issue #27 (ELITEA-1736) rework closure record: this technique surfaced 6
testids not yet on `main` (`skill-instructions-editor-content`,
`agent-skills-counter`, `agent-add-skill-button`, `agent-skills-section`,
`chat-switch-participant-button`, `skill-mention-list`/
`skill-mention-item-{name}`), spanning 3 separate draft PRs
(EliteaUI#526, #540, #541) — two of which were shared dependencies from
sibling cases' reworks, not owned by this case at all. A naive "just check
this PR's own diff" approach would have missed all but one of them.
