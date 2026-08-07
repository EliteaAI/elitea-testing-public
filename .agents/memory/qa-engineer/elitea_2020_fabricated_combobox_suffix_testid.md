---
name: ELITEA-2020 fabricated "-combobox" suffix testid on VERSION selector
description: agent-version-selector-trigger-combobox does not exist anywhere in EliteaUI; the real, working testid is agent-version-selector-trigger (no suffix) — verify a "two testids render" claim by grepping BOTH strings before trusting it
type: feedback
---

Reviewing ELITEA-2020 (PR #1305), the AFS / `_surface.md` digest / page-object
docstring all claimed `ApplicationVersionSelect.jsx`'s VERSION selector
"renders TWO testids": the outer `agent-version-selector-trigger` (called a
"non-interactive wrapper") and an inner `agent-version-selector-trigger-combobox`
(the actual `role="combobox"` element, claimed as "confirmed live"/"on-main ✓").

**This is false.** Repo-wide `git grep` for the literal string
`agent-version-selector-trigger-combobox` returns **zero hits** on both
`origin/main` and `origin/automation/testids`, whole repo (not just `src/`).
Source trace: `ApplicationVersionSelect.jsx:228` passes
`testId="agent-version-selector-trigger"` → `VersionSelect.jsx` threads it to
`SingleSelect.jsx:658` as `data-testid={dataTestId}`, applied verbatim to a
**single** MUI `<Select>` root (which itself carries `role="combobox"` per
`SelectInput.js:472` — same element, not two). No `-combobox`-suffixing logic
exists anywhere in the codebase (`git grep -n "\-combobox"` also zero hits).

**Independent confirmation**: `AgentDetailPage` (merged, exercised across
ELITEA-1888/1889/1890/1891/1892) already reads this exact shared component's
version text via `get_by_test_id("agent-version-selector-trigger")` (no
suffix) — `automation/pages/agent_detail_page.py:761-768`,
`test-specs/agents/_surface.md:66-67`. That page object works today.

**Effect if shipped as-is**: `PipelineDetailPage.version_selector` (testid
`...{-combobox}`) resolves via Playwright's `get_by_test_id()`, which does an
EXACT string match — zero elements match, so `get_version_display()` times
out. The daily-log's "GREEN 3/3" claim for this PR is inconsistent with this
source evidence; the discrepancy needs to be resolved by an actual run, not
assumed away.

**Lesson**: a "confirmed live via DOM query" / "renders TWO testids" claim
about a shared component is exactly the kind of thing to verify with a
repo-wide grep for the SPECIFIC literal string claimed — not just the base
testid — before trusting it into an AFS Concrete-Handles row or a
`_surface.md` digest entry. When another page object already exercises the
same shared component, cross-check against it first — it's often the fastest
way to catch a fabricated variant.
