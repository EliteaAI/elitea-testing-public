---
name: Secrets page React render-loop defect fires on plain mount
description: SecretsContent.jsx triggers "Maximum update depth exceeded" on every /settings/secrets navigation, before any interaction — filed #1203, sibling of #538 not a dupe
type: feedback
---

## The defect (elitea-testing-public#1203)

Navigating to `/settings/secrets` (via `SecretsPage.navigate()` — plain
`page.goto()` + wait for the row) reliably triggers a React console warning
(17-46 occurrences observed per mount across runs):

```
Warning: Maximum update depth exceeded. This can happen when a component
calls setState inside useEffect, but useEffect either doesn't have a
dependency array, or one of the dependencies changes on every render.
```

Stack trace pins `SecretsContent.jsx`. Confirmed via a standalone repro
script (`page.goto()` + wait for `secret-row`, zero clicks/typing) — errors
are already present in `capture_console_errors()`'s buffer before any
interaction happens. 100% reproducible (3/3 across 2 full pytest runs + 1
isolated script) with a properly authenticated `page` fixture (proper
`auth_state`/DEV-token session).

**Sibling of #538** (Agent Instructions field — `Maximum update depth
exceeded` fires only on TYPING, not on navigation) — same warning class,
different trigger/component. Don't conflate: #538's isolation notes
explicitly say "does NOT fire on plain page navigation/load" — #1203 is the
opposite (fires on navigation alone, before typing). Different object +
different trigger = sibling, not duplicate, per the dedup rule.

**Gotcha — a raw unauthenticated Playwright script will NOT show this.** My
first repro attempt used a hand-rolled `sync_playwright()` script without
wiring `auth_state`/`VITE_DEV_TOKEN` and saw zero errors — misleading, since
that page never actually reached the authenticated Secrets view. Always
reproduce via the project's own `page` fixture (or an equivalent that wires
`auth_state`) before concluding "not reproducible" — an unauthenticated
diff can silently mask a defect that only manifests on the real data-loaded
page.

Soft-asserted via `soft_failures`/`pytest.fail()` (see
`agent_instructions_react_render_loop_quirk.md` for the generic pattern) —
filter unexpected console errors from the known signature so a genuinely
NEW error still hard-fails.

**Round-2 finding — `_is_known_defect_1203()`'s `"SecretsContent.jsx" in text`
check is occasionally too strict.** Across 3 verification reruns of the
merged spec, 2 correctly reached the intended `pytest.fail()` soft path
("Known defect https://…/1203: … 18 occurrence(s)"), but 1 hard-failed at
the earlier `assert not unexpected_errors` line instead — that run's single
captured `ConsoleMessage.text` lacked the stack-trace suffix entirely (short
form, ~250 chars, no `SecretsContent.jsx`), vs the normal long form (~4600
chars, full component stack, `args_len == 2`). Root cause not fully pinned
down (Playwright's `.text` concatenation of `console.error(fmt, stackArg)`
args appears to occasionally drop the second arg) — reproduces at the
`page.goto()` level too (ad-hoc script: 0/1/1 errors across 3 bare
navigations, i.e. the underlying warning's occurrence-count AND arg
completeness are both somewhat non-deterministic per mount, not just the
count). Not fixed as of fix-round-2 (out of that round's named-finding
scope) — if the batch hardening gate's 3x reruns hit the short-text branch,
harden the filter to match on the message-text prefix alone (already
unique enough: `"Warning: Maximum update depth exceeded. This can happen
when a component calls setState inside useEffect"`) instead of requiring
the component-name suffix.

**Fixed in fix-round-3** (as the reviewer's next-round blocking finding, per
the pattern above — flagging without fixing only postponed it one
round-trip). `_is_known_defect_1203()` now matches
`"Maximum update depth exceeded" in text` alone, no stack-suffix
requirement. Regression-pinned by
`tests/unit/test_secret_create_inline_known_defect_1203_matcher.py`
(long-form-with-stack / short-form-no-stack / unrelated-error). Live re-run
after the fix hits the correct `pytest.fail()` soft-known-defect line.

(from ELITEA-2336)
