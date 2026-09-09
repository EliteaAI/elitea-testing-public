---
name: Verify a wait's oracle by reading the JSX prop chain, not the testid
description: A static reviewer can prove a new completion-wait is live-updating (not a snapshot) by tracing the attribute's prop chain in EliteaUI source.
type: feedback
aliases: [inert wait, completion oracle, data-status, wait oracle, soft wait review]
tags: [area/review, type/technique]
created: 2026-09-09
updated: 2026-09-09
---

## The check

When a PR replaces a wait with "wait until `data-X` on testid Y reaches Z", the
testid's existence proves nothing. Two failure shapes look identical in a diff:

- the attribute is rendered from a **live prop** the socket updates -> the wait
  is real;
- the attribute is a **snapshot captured at mount/open** -> the wait can never
  be satisfied, and you have swapped one inert wait for another.

Statically distinguishable in ~2 greps, no execution needed: find the JSX that
renders the attribute, then walk *upward* to who owns the value.

Worked case (PR #2091, ELITEA-2448): `RunStatus.jsx:15-16` renders
`data-testid="pipeline-run-details-status-badge"` + `data-status={status}`;
`RunStateDialog.jsx:98` passes `<RunStatus status={data.status} />`;
`RunStateNode.jsx` renders that dialog as a **sibling that stays mounted**,
passing its own live `data` prop, keyed on the stable run-node id. So the badge
re-renders in place as the socket updates the node -> the panel can be opened
mid-run and the wait is genuine.

Also confirm the literal the test waits for is the product's constant, not a
guess: `flowEditor.constants.js` `PipelineStatus.Completed === 'Completed'`.

## The mirror check: does the new wait actually raise?

Same review, other half. A helper that logs a WARNING and returns is not a
wait. Read the `except` path: `PlaywrightTimeoutError -> raise AssertionError`
is a wait; `try/except: pass` or `logger.warning(...)` + fallthrough is not.
A "repair" that swaps an inert wait for another inert wait is the original bug.

Related: [[soft_helpers_cannot_fail_and_hide_the_real_failure]]
