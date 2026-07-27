---
name: Inline get_by_test_id in a new page-object method missed by file-scoped reviewer grep
description: A new page-object method can carry an inline get_by_test_id() call (banned per role-overrides.md) that survives 4 review rounds because the reviewer's own mechanical grep was scoped to the test file, not automation/pages/
type: feedback
---

Control-audit of #212 (ELITEA-1808, PR #643) found a genuine item-1 violation
that 4 fresh review rounds all missed: a brand-new page-object method,
`ArtifactsPage.get_file_row_text()`, called
`self.page.get_by_test_id("artifacts-file-row").filter(has_text=filename).first`
inline in its method body — a literal string, not a class-level
`LocatorDescriptor` field and not an UPPER_CASE `[data-testid="…"]` constant
reference. `.agents/role-overrides.md` bans this explicitly in TWO places:
Reviewer slot ("get_by_test_id included: inline Playwright calls are also
banned — locators are class-level LocatorDescriptor fields") and Implementer
slot ("inline `get_by_test_id(f"…")` is NOT the compliant shape").

**Why it survived 4 rounds.** Round 2's reviewer DID run exactly the right
grep pattern — "`page.locator(`, `.locator(`, `get_by_test_id(`,
`getByTestId(`, `css=`, `xpath=`" — but scoped it to **the test/spec file
only** ("I grepped the entire current test file for..."). The violation lives
in `automation/pages/artifacts_page.py`, which nobody re-ran that grep
against, because round 1's original finding (a raw `page.locator()`
constructed directly in the SPEC file) primed every subsequent round to
treat "is anything constructed in the test file" as the check, when the
canon's actual scope is "any non-testid handle ADDED in `automation/pages/`
**or** `automation/tests/`" — both directories, always, not just whichever
one the last finding happened to live in.

**Compounding factor — self-cited tech debt as justification.** The new
method's own docstring says it reads the row "via the existing
testid-anchored row locator... the same pattern the legacy `download_file`
already uses" — i.e. it explicitly leans on one of the ~350 pre-policy raw
handles already in the file (tracked debt, issues #25/#42) as its own
rationale. This is the exact anti-pattern `.agents/role-overrides.md` names
by name: "The surrounding code is NOT precedent... never cite existing code
to justify a new raw handle." A docstring citing an existing bad pattern as
its own justification is worth treating as a stronger tell than an unexplained
raw handle — it means the author saw the tech debt and chose to extend it
rather than route around it.

**Audit technique going forward:** when running the item-1 mechanical grep,
don't stop at classifying each hit as compliant/non-compliant by itself —
separately ask "does this hit sit in a BRAND-NEW method/file, or an existing
one?" (`git show <base>:<path> | grep <method-name>` — absent in the base
commit means wholly new). New methods get zero benefit of the doubt from
surrounding-file precedent, whatever their own docstring claims. And when
checking whether a reviewer's own grep evidence actually covers this PR's
full diff, check WHICH FILES they say they grepped, not just which patterns —
a reviewer narrating "the test file" when the canon's scope is "pages/ or
tests/" is a scope gap even when the command syntax itself was exactly right.
