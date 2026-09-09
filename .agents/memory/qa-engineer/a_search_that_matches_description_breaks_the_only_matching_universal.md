---
name: A search that matches description breaks the "only matching results" universal
description: Elitea dashboard search filters on name AND description — assert established names, never "every result contains the term"
type: feedback
aliases: [search matches description, only matching pipelines shown, dashboard search universal assertion]
tags: [area/pipelines, type/assertion-design]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

A TMS case that says *"only pipelines containing X are shown"* invites the
strongest-looking assertion: `all(X.lower() in n.lower() for n in visible_names)`.
On Elitea dashboards (shared `SearchBar.jsx` + `useLoadApplications`) that is a
**false-red generator**, because the backend `query` param matches the entity's
**description** as well as its name.

Proven live 2026-09-10 (ELITEA-2023 repair, board `#2119`): two pipelines whose
names contain no `ELITEA-2023` but whose descriptions do, both appeared when
searching `ELITEA-2023`.

## What to assert instead

The specific names the test itself established: `match_name in visible`,
`nonmatch_name not in visible`. Ambient-proof, and it is the only shape that is
correct on a project you do not control.

## Corollary for preconditions

A "non-matching" precondition entity must avoid the search term in **name AND
description**. A clean name alone is not enough.

Related: [[a_positive_assertion_guarding_an_absence_only_by_ordering_is_fragile]]
