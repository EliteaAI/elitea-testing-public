---
name: An AFS-named testid can be real but belong to the WRONG component — verify importers, not just that the string exists
description: The ELITEA-2166 AFS named "agent-version-selector-trigger" for the chat composer's version button. That testid IS real and DOES exist — but on ApplicationVersionSelect.jsx (the agent detail page's own tab bar), a component with zero importers outside that page. The composer's actual version button (VersionSelector.jsx, chat-input-only) had no testid at all. `document.querySelector` alone can't catch this; only tracing the component tree (grep importers) does.
type: feedback
---

## What happened

AFS § Concrete Handles claimed: "Composer version-selector button (shows
version name) → `agent-version-selector-trigger` → on-main ✓ → Confirmed
via `ApplicationVersionSelect.jsx`." This looked verified — the testid
genuinely exists in the codebase, wired correctly, on-main. But it's wired
onto `ApplicationVersionSelect.jsx`, which `grep -rln
"ApplicationVersionSelect" src/` showed is imported ONLY by
`ApplicationTabBar.jsx` / `SkillTabBar.jsx` — components that render on the
agent/skill DETAIL page's own tab bar, not the chat composer.

Live-checking the actual chat composer (after opening the canvas, saving,
closing it) confirmed: `document.querySelector('[data-testid="agent-
version-selector-trigger"]')` → **null** in the composer. The visible
"base" text button in the composer is rendered by an entirely different
component, `VersionSelector.jsx` (`chat/ui/chat-input/`), used ONLY by the
composer's own `AgentEditorPanel.jsx` — and it carried **no testid at
all**.

## Why the AFS's claim looked solid but wasn't

The analyst's exploration likely found the right VISUAL element (a button
showing "base") and then grepped the codebase for a plausible-sounding
testid name (`*version-selector-trigger*`), found ONE real hit, and
attributed it without checking WHICH component instance the visual element
actually came from. Both components serve conceptually the same purpose
("pick a version") and even use similar Button/Menu-based implementations
— an easy mix-up when working from a name search rather than the render
tree.

## The check that catches this

Don't stop at "does this testid string exist somewhere in the codebase" —
confirm the testid's OWNING component is actually rendered on the surface
you're testing:

```bash
grep -rln "ApplicationVersionSelect" src/ | grep -v "ApplicationVersionSelect.jsx"
# -> only ApplicationTabBar.jsx / SkillTabBar.jsx (agent/skill DETAIL page)
# -> NOT the chat composer -> AFS's claim is for the wrong surface
```

Then, once you know the visual element's REAL owning component (traced via
`AgentEditorPanel.jsx`'s own imports, or by locating the un-testid'd
element's ancestor chain live via `el.parentElement` walk + `outerHTML`),
add the testid there instead of reusing the wrong name — a fresh, correctly-
scoped testid (`chat-version-selector-trigger`), not a repurposed one.

## Same session, same underlying lesson: absence checks need the SAME rigor

A companion gap in the same case: the AFS needed to assert "Invite Users"
is ABSENT from the composer's `+` menu for a Private project. The item
had literally zero testid (unlike its `*-menuitem` siblings), so a
testid-only "is absent" check was impossible until a testid was added
directly to the (conditionally-rendered) `MenuItem`. The lesson pairs with
the above: when the AFS's own Concrete Handles table says "on-main ✓" for
something you're about to assert, verify BOTH (a) the testid exists at all
in the live DOM for the surface under test, not just anywhere in the
source, AND (b) if you need to assert absence, that a testid-only
mechanism to prove absence actually exists (it usually doesn't for
truly-optional elements — that's new `add-data-testid` work, not a
locator you can build around).

## Actionable pattern

Before trusting an AFS's Concrete Handles row for a composer/canvas/shared-
surface element:
1. `grep` the testid string across the whole EliteaUI source — confirm
   which component(s) render it.
2. `grep -rln "<ComponentName>" src/ | grep -v "<ComponentName>.jsx"` — list
   every importer. If the surface you're testing isn't one of them, the
   AFS's claim is for a different (even if visually similar) element.
3. Live-verify via `playwright-cli`/`browser-verify`
   `document.querySelector('[data-testid="..."]')` on the ACTUAL page under
   test, not just "the testid exists in the codebase somewhere."
4. If it resolves to `null` live despite existing in source, trace the
   REAL element's ancestor chain and add a fresh, correctly-scoped testid —
   declare the improvisation (role-overrides.md's canon-gap protocol)
   rather than silently reusing the wrong name.

## Addendum (docs-only fix round, PR #710, orchestrator's own diff check): declaring an improvisation is NOT the same as amending the AFS

Both gaps above (`chat-version-selector-trigger`, `invite-users-menuitem`)
were correctly declared as improvisations — in the commit message, in the
PR description, and in the test file's own module docstring. All three
said the right thing. But the AFS itself (`test-specs/chat-interface/
l2_create-agent-via-chat-canvas_ELITEA-2166.md`) was never touched —
`git log --all -- <that path>` showed only the original analyst commit.
The Concrete Handles table still named the wrong testid/component for the
version selector and had no row at all for `invite-users-menuitem`. The
orchestrator caught this on its own diff check, not a reviewer round.

The mistake: treating "I explained this in three other places" as
equivalent to "I amended the one place (the AFS) that's the durable,
re-readable contract per the Phase 2 amend-in-PR rule." A commit message
and a PR description are read once, at review time, then archived; the
AFS is what the NEXT implementer/reviewer opens when this spec is touched
again. If it still says the wrong thing, the next reader inherits the
mistake with none of the context that corrected it.

**Fix habit going forward:** the moment a Run Report or PR description is
about to declare an improvisation/canon-gap, treat that as the trigger to
open the AFS file itself in the SAME commit (or immediately after) and
correct the specific row/step/bullet that named the old handle — not just
narrate the fix elsewhere. A quick self-check before calling a round done:
`grep <old-handle-name> test-specs/**/*.md` should return nothing (or only
the amendment's own "corrected from X" historical note), the same way
`git diff <file> | grep '^-[^-]'` is the self-check for additive-only.
