---
name: Verify handles against main, not the working tree
description: A handle greps green locally because localhost serves automation/testids; a main-targeted spec must be verified against origin/main or it ships a DEV-only red
type: feedback
---

## The trap

Localhost:5173 serves EliteaUI **`automation/testids`**, which carries every testid the
team ever added. GHA runs against dev.elitea.ai, which serves **`main`**. So a handle that
exists only on `automation/testids`:

- passes every local run, every time
- fails on DEV, always
- and **no amount of local evidence reveals it** — the dev server had it the whole time

For a spec targeting `main`, that turns "green locally" into actively misleading evidence.

## The rule

> A handle verified against the **working tree** is verified against `automation/testids`.
> A spec targeting **`main`** must be verified against **`main`**.

```bash
cd ../EliteaUI && git fetch origin          # non-optional
FILTER='(data-testid|testid[[:space:]]*[:=])'
git grep -- "$t" origin/main -- src/ | grep -qiE "$FILTER" && echo YES || echo NO
```

## How it got past me (ELITEA-0500, 2026-08-28)

I specced a settle condition keyed on `chat-stop-generation-button`
(`main:NO`, `testids:YES` — `src/ComponentsLib/Chat/UserInput.jsx:531`). It would have
fixed one DEV red by shipping a different one.

**Root cause, and the reusable lesson:** the handle entered via the AFS **step table**
without a row in § Concrete Handles — so it bypassed the provenance check that every other
handle in the spec passed. The table was right; the handle just never reached it.

> **Any handle named in a step row must also appear in the handles table.** A provenance
> discipline only protects the handles that actually go through it.

## Design consequence worth reusing

The replacement needed no settle signal at all:
`expect(messages_container.nth(idx)).to_contain_text(answer, timeout=90_000)` — web-first
auto-retry against a fixed index. A mid-turn narration cannot satisfy it **by
construction** rather than via a transient-string blocklist. Prefer an auto-retrying
assertion over inferring "the turn is done"; it is stronger AND needs fewer handles.
