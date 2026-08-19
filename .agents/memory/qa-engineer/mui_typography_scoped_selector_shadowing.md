---
name: MUI Typography scoped-selector shadowing
description: A raw 'p, span' scoped selector for content reads can be shadowed by a sibling Typography — scope tighter or add a testid
type: feedback
---

## What happened (ELITEA-2206 review, PR #1598)

`NewParticipantCard.jsx` renders THREE `Typography` elements as descendants of
the card's outer testid'd `Box`: `nameText` (no `component` override),
`typeText` (`component="span"`), and — only when `participant.project_id ==
PUBLIC_PROJECT_ID` — a `"Public"` label `Typography` (also no `component`
override), added as a THIRD sibling **after** `bodyContainer` (which holds
`nameText`+`typeText`). None of the three declare a MUI core variant
(`body1`/`body2`/etc.) — they use project-custom variant tokens
(`headingSmall`, `bodySmall` from `typographyVariants.js`), which have no
`variantMapping` override in this codebase, so MUI's Typography falls back to
rendering them all as `<span>`.

The implementation added `HASH_SEARCH_ITEM_SUBTITLE = 'p, span'` and read
`item.locator(HASH_SEARCH_ITEM_SUBTITLE).last.text_content()` **scoped to the
whole card**, not to `bodyContainer`. The docstring assumed only 2 elements
match ("`.last` reads the type, not the name") — true for non-Public cards,
**false** for Public-labeled ones: the Public-label span becomes the new
`.last`, so the subtitle read returns `"Public"` instead of `"agent"`/
`"pipeline"` for any Agent-Hub-sourced card. Live data on this account
includes Public-labeled AGENTS ("Business Analyst"), so this is a real,
data-dependent false-negative risk (a `next(subtitle == "agent")` search can
silently skip legitimate matches, or — with a paginated/relevance-limited
result page — find none at all).

## Lesson

A "scoped content-extraction read" off an already-testid'd parent is only as
safe as the scope actually excludes every OTHER element the same tag-selector
could match. Scope to the tightest real DOM container the source confirms
(here: `bodyContainer`, a `styles.bodyContainer`-sxed inner `Box` — no testid
existed on it either, which is exactly why this pattern is a policy violation
in the first place, not just a bug: `.agents/testing.md` § Locator policy
requires scoped sub-selectors to be `[data-testid="…"]` only). When a case's
own steps need to read specific card content (subtitle, icon, badge text),
request the testid on that specific child via `add-data-testid` rather than a
raw CSS tag selector scoped to an ancestor — the ancestor's DOM can gain new
sibling text nodes (exactly what the conditional "Public" chip is) without
ever being a testid/policy violation on its own end, silently poisoning the
"last matching node" assumption.

Also: `.claude/rules/mui-patterns.md`'s own preamble (2026-07-14 note)
explicitly disclaims its raw-selector examples (`_extract_message_body()`
etc.) as "legacy illustration, not license" for new code — citing that
function as a sanctioned precedent for a NEW raw-selector page-object
constant is citing a document against its own express caveat. Check the
cited file's preamble before trusting an in-repo "precedent" comment.
