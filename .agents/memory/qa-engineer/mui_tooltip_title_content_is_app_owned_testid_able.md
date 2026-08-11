---
name: MUI Tooltip title content is app-owned, testid-able
description: A MUI Tooltip's title JSX is not the #579 third-party exception — you own it, add a data-testid directly
type: feedback
---

## Context

Elitea's `StyledTooltip` (`src/ComponentsLib/Tooltip.jsx`, a thin MUI `Tooltip`
wrapper) is used all over for hover-revealed content — e.g. `Card.jsx`'s
per-card name/description hover tooltip (`role="tooltip"`, ~1s `enterDelay`,
confirmed live for the Skills/Agents/Pipelines shared card component,
ELITEA-2428).

## The gotcha

It is tempting to classify an un-testid'd MUI tooltip as a `#579`
third-party-internal-render-node exception ("MUI renders the popper, I can't
touch it"). **That's wrong when the `title` prop's content is our own JSX.**
MUI's `Tooltip` renders whatever node you pass as `title` verbatim into its
Popper — it does not synthesize or restrict that content. If `title={<Typography
data-testid="...">...</Typography>}` is legal JSX (it is), a `data-testid` goes
directly on that element, same as any other app-owned node. No render-prop
threading needed (contrast with Recharts' custom tooltip, which DOES need
render-prop threading — see `recharts_hover_tooltip_testid_pattern.md`, a
different library with different constraints).

The `#579` exception is for DOM nodes you genuinely can't reach — CodeMirror's
internal per-line divs, ReactFlow's `rf__wrapper` internals. A MUI `Tooltip`'s
`title` content is not that: it's a prop value you wrote.

## The check

Before writing "needs-adding, but see #579" for a tooltip: open the source and
look at what's passed to `title=`. Plain JSX from our own components → testid
it directly. Only escalate to #579 reasoning if the *tooltip trigger itself* is
a third-party-internal node (rare) — the content is almost always ours.

## Where this came from

ELITEA-2428 analysis (batch `skills-remaining-w1`, 2026-08-11) — Skills card
view's description-on-hover tooltip (`Card.jsx`'s `StyledTooltip` wrapping two
app-owned `Typography` nodes). Proposed `entity-card-description-tooltip`.
