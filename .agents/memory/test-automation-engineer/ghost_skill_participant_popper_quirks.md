---
name: Ghost skill mention popper + participants popper quirks (implementer)
description: get_by_role("paragraph", ...) never matches Playwright's role tree even when Chromium's own a11y snapshot labels a <p> "paragraph" — use a p+has_text filter instead; participants-popper ancestor depth is div[3] from the "Agents" heading (not div[2]); Escape-dismiss leaves the literal "~" in the input, so re-typing "~" without clearing first produces "~~" and the popper never reopens (from ELITEA-1793)
type: feedback
---

## Context

Implementing ELITEA-1793 ("Ghost skill not shown after Agent participant
removed") — a `defect-found` AFS with a confirmed, deterministic (2/2)
product defect (issue #51: the "Mention skill" popper retains a removed
agent's skill). Three implementer-side (infrastructure) gotchas surfaced
while writing `ChatPage.open_participants_popover()` /
`remove_agent_participant()` / `open_mention_skill_popper()` that the
analyst's manual/live-tool exploration couldn't have caught the same way:

## 1. `get_by_role("paragraph", ...)` matches 0 elements, even when the live a11y tree shows role "paragraph"

`playwright-cli snapshot` (and any accessibility-tree dump) will show a
plain `<p>` element as `paragraph [ref=...]: Agents` — but calling
`page.get_by_role("paragraph", name="Agents", exact=True)` in real
Playwright code returns **0 matches**, confirmed live via `run-code`. The
snapshot's "paragraph" role label does not correspond to a role Playwright's
`getByRole` engine recognizes/matches for a bare `<p>`. Don't trust the
snapshot's structural-role labels (paragraph, generic, etc.) as if they were
`getByRole`-queryable ARIA roles — only roles from the real ARIA spec
(button, menuitem, dialog, heading, ...) are reliably queryable that way.
For a `<p>` with no other distinguishing attribute, fall back to
`page.locator("p").filter(has_text=re.compile(r"^Agents$"))` — a CSS-tag +
exact-text filter — and document why (locator ladder tier 5, last resort).

## 2. Popper container ancestor depth must be verified live, per popper — don't assume the same depth as a different popper

The "Mention skill" popper's container is `ancestor::div[2]` from its
heading (existing code, `send_message_with_skill_mention`). The "Agents"
participants popper's container is **`ancestor::div[3]`** from its heading
— a different depth, confirmed by walking both the heading and a
participant-row element's ancestor chains to their first common ancestor
via a `run-code` snippet:
```js
function ancestors(node){ const arr=[]; let c=node; while(c){ arr.push(c); c=c.parentElement; } return arr; }
const common = rowAncestors.find(a => headingAncestors.includes(a));
```
Guessing "it's probably the same div[N] as the other popper in this file"
is a real trap — verify per-popper via this technique before writing the
locator, not by pattern-matching an existing method.

## 3. Escape-dismissing the mention popper leaves the literal "~" in the input — retyping "~" without clearing first breaks the trigger

Per the AFS itself: dismissing the "Mention skill" popper via Escape does
NOT clear the composer input — the literal `~` character remains. If a
later step types `~` again without clearing first, the input ends up
`~~`, which does **not** re-trigger the popper (confirmed live: screenshot
showed literal `~~` in the composer with no popper open, causing a
false-negative 10s timeout). `open_mention_skill_popper()` now does
`Control+a` + `Backspace` before every `press_sequentially("~")` so the
trigger is always a single fresh `~` regardless of prior composer state.

## Reusable pattern

`ChatPage.open_participants_popover()` returns the `ancestor::div[3]`
container from the `p`-tag-filtered "Agents" heading; participant rows are
reached via `popper.get_by_text(agent_name, exact=True).first` then
`ancestor::div[2]` from THAT text node (different depth again — verified
separately, since it's measuring from the row's inner text node up to the
row itself, not from the popper heading down to the container).
`ChatPage.open_mention_skill_popper()` always clears-then-types `~`. Both
new methods are additive on `chat_page.py` (existing methods/callers
untouched — verified via `git diff | grep -E '^-[^-]'` empty).
