---
name: Absence-of-never-rendered-control is not a #579 case
description: A get_by_text() absence handle for a control the product never renders at all is a canon gap, not the #579 exception — first-party JSX has no third-party subtree to invoke, and there is no JSX node to add a testid to.
type: feedback
aliases: [drawer_logout_controls, 579 exception misapplied, absence assertion no testid, declared improvisation absence]
tags: [area/locator-policy, area/settings]
created: 2026-08-26
updated: 2026-08-26
---

## What happened

`settings_drawer_page.py::drawer_logout_controls()` (ELITEA-2242/2243/2244) used
`self.settings_drawer.get_by_text(LOGOUT_LABEL_PATTERN)` to assert NO "Log out"
control exists in the Settings drawer (case-text drift, clarification #1772 — the
case assumed a Log out drawer item that the live product never renders).

First-round docstring cited this as the `.agents/testing.md` #579 sanctioned
exception (scoped raw handle for a testid that "genuinely can't be placed").
Reviewer correctly rejected it: #579 has exactly two shapes — third-party widget
subtree, third-party editor-library internal nodes — and the Settings drawer is
first-party EliteaUI JSX we own. Per `.agents/testing.md`, a missing testid on
first-party JSX is normally "work to do" (`add-data-testid`), not a stop+flag case.

## Why #579 genuinely doesn't close this gap

The AFS asserts absence of a control that is **never rendered at all** — there is
no JSX node to add a testid to. `add-data-testid` has no target. The canon's
absence-assertion rulings (#511 extension, same-element conditional pairs #277)
both presuppose a testid that exists on *some* branch (an alternate/untested
render). Neither covers "the branch was never authored in the first place."

## Resolution taken

Kept the same technique (`get_by_text` scoped off the real `settings_drawer`
testid parent — bounded blast radius, same discipline #579 requires) but
re-labelled the docstring as a **DECLARED IMPROVISATION**
(`.agents/role-overrides.md` § Declared-improvisation protocol) rather than a
false #579 citation, and flagged it for a lead canon ruling (a likely #579-sibling
clause: "assert absence of a control with no live JSX branch to testid"). Same
pattern exists on the sibling `SettingsProfilePage.drawer_logout_controls`
(ELITEA-2252) — also unresolved by canon there.

## Rule of thumb

Before citing #579 for ANY raw handle: ask "is the parent's *subtree* third-party
(a widget/editor library), or is this first-party JSX where the specific node just
isn't rendered on this branch?" Only the former is #579. The latter — asserting
the absence of a control with zero live JSX to testid — is a canon gap: declare it
explicitly, don't cite an inapplicable exception to make it look sanctioned.

Related: [[custom_handle_testid_prop_not_579_exception]] · [[mui_simple_select_auto_id_is_not_a_579_exception]]
