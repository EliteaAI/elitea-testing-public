---
name: onetest_coverage_tool_is_aggregate_only
description: automation_coverage MCP tool's reports/coverage.md has no per-case rows — can't confirm one case's TMS link with it
type: reference
---

`mcp__onetest-tms__automation_coverage` writes `reports/coverage.md` in the TMS repo
(`onetest-ai-tm-Elitea`), but that file is **summary-only**: a Metric table + a
Coverage-by-priority table, no per-case listing at all. Grepping it for a specific
TMS case ID (e.g. `ELITEA-2023`) or a specific `automation_test_id` string returns
nothing, even when that case correlates fine.

`correlate_results` (the tool that actually links a case to a live CI run) also
does NOT accept a raw pytest `reports/junit.xml` as its `automated` argument — it
expects a different launch-JSON shape and throws `JSONDecodeError` on junit XML.

**The per-case verification that actually works** (and is the one
`.agents/test-automation.yaml` § `backwrite_on_done` specifies as canon) is the
manual Form-C self-check one-liner against the fresh local `reports/junit.xml`:

```bash
t="tests.ui.<pkg>.<module>.<Class>.<method>"
grep -qi "classname=\"${t%.*}\".*name=\"${t##*.}\"" reports/junit.xml && echo MATCH || echo NO-MATCH
```

Run `build_index` after editing a case file (mandatory — index.json is not
auto-rebuilt) and treat that self-check, not `automation_coverage`'s aggregate
numbers, as the closure-record evidence for one case's back-write.
