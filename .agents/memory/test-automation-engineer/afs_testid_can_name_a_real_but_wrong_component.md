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

## Addendum (ELITEA-2167 fix-only round, PR #988, reviewer Finding 3): the SAME string can be real on `main` — for a DIFFERENT component

A second variant of this exact lesson, this time hitting the `on-main ✓`
PROVENANCE column instead of a "does the DOM resolve" check. The AFS/test
docstring claimed `chat-participants-badge-button` /
`chat-participants-popper` were `on-main ✓`, reused as-is from an existing
`ChatPage` field. **The string genuinely IS on `main`** — `git grep` finds
it — so a shallow "does this testid exist on main" check passes. But it's
on `main` in `CollapsedPerticapantsList.jsx` /
`CollapsedParticipantsDropdown.jsx` (the Agents-participants flavor), a
DIFFERENT component from the one this test's `section="users"` flow
actually renders through: `UsersParticipantDropdown/index.jsx`. That
component's copy of the same two testid strings only exists on
`automation/testids` (added via a dedicated commit,
EliteaAI/EliteaUI@7ecc041d) — `main` has never seen it.

## Addendum (ELITEA-2369, implementer's OWN new-testid work order): the AFS can name the wrong CALL SITE for a shared-component testid prop, not just the wrong existing testid

A third variant — this time on a `testid needed:` work order the AFS asked
the implementer to add, not a "reuse this existing testid" claim. The AFS's
Concrete Handles table named `src/pages/NewChat/ChatConversationStarters.jsx`
as the call site to wire a new `testId` prop onto the shared
`EllipsisTextWithTooltip` component (`src/components/ConversationStarters.jsx`),
for "starter tiles shown in the chat area right after Start Chat, before any
message is sent." That component genuinely imports `EllipsisTextWithTooltip`
— but live exploration (adding the testid, running the test, getting a
0-match timeout) showed this case's ACTUAL flow renders through a DIFFERENT
component, `src/pages/NewChat/NewConversationView.jsx` (the "Hello,
{user}! What can I do for you today?" landing view), which ALSO imports
`EllipsisTextWithTooltip` directly. `ChatConversationStarters.jsx` turned out
to be consumed only by `src/[fsd]/features/chat/ui/chat-box/ChatBox.jsx` — an
embedded/agent-participant chat surface this case never reaches.

**How this was caught:** the testid was correctly ADDED (compiled, served by
Vite, confirmed via `curl localhost:5173/src/...` showing the new prop), but
the test still timed out waiting for it — 0 matches on a screen that
visibly showed the 4 starter tiles in the screenshot. That mismatch (visible
tiles, zero testid matches) is the signal: the RIGHT visual element is
rendering, through a component OTHER than the one that got the testid.
`grep -rln "ChatConversationStarters" src --include="*.jsx"` showed only
`ChatBox.jsx` as a consumer — confirming this was a different flow, not a
caching/HMR issue.

This is the identical failure mode as the original lesson above
("the testid string exists somewhere ≠ it exists for the component you're
testing"), just discovered through promotability/provenance verification
(`git grep <string> origin/main -- src/`) rather than through a live DOM
`document.querySelector`. **The fix is the same discipline, restated for
this check specifically**: when a Concrete Handles row says "reused as-is,
on-main ✓" for a testid whose NAME happens to already exist elsewhere in
the codebase, `git grep -n "<testid-string>" origin/main -- src/` and
confirm the MATCHING FILE is the actual component this test's code path
renders — not just that the grep returns a hit. A hit in the wrong file is
a false positive that produces a false "already promotable" claim in the
closure record (the exact class of error `.agents/workflow.md`'s closure-
record verification exists to catch). Caught this round by a fresh
reviewer session re-deriving provenance from scratch rather than trusting
the original implementer's claim — the same "verify importers/owners, not
just string existence" muscle, applied one level up the stack.

## Addendum (ELITEA-2020 fix round 1, PR #1305, reviewer Finding 1): a variant strain — the testid doesn't exist AT ALL, not even for the wrong component

A fourth variant, one notch worse than the others: `PipelineDetailPage
.version_selector` was wired to `agent-version-selector-trigger-combobox`,
claimed in the AFS/`_surface.md`/page-object docstring as "confirmed live,
renders TWO testids — the outer wrapper (`agent-version-selector-trigger`)
and an inner `-combobox`-suffixed one on the actual `role="combobox"`
element." Both the AFS and the digest treated this as `on-main ✓`. It was
**wholly fabricated** — not a wrong-component mix-up, a wrong-STRING
invention. `git grep -n "agent-version-selector-trigger-combobox"
origin/main -- src/` (and `origin/automation/testids`) returns **zero
hits**, whole repo. Source trace: `ApplicationVersionSelect.jsx:228` passes
`testId="agent-version-selector-trigger"` → `VersionSelect.jsx:176` applies
it as a SINGLE `data-testid={testId}` on the `SingleSelect` root — that
root already carries `role="combobox"` natively (MUI `<Select>`), so "outer
wrapper vs inner combobox" was never two elements to begin with. There is
no `-combobox`-suffix derivation logic anywhere in `SingleSelect.jsx`.

**What made this catchable without a live DOM check**: `AgentDetailPage`
already reads this exact shared component via `version_selector_trigger`
(testid `agent-version-selector-trigger`, no suffix) — merged, exercised
across ELITEA-1888/1889/1890/1891/1892. Any claim of a second,
differently-suffixed testid on the SAME shared component should have been
cross-checked against the sibling page object that already uses it, before
trusting a "confirmed live via DOM query" note at face value. The
reviewer caught this statically (no browser) purely from the grep +
source trace — proving the "two testids render" claim never needed a live
session to falsify, only the discipline of grepping the SPECIFIC literal
string claimed, not just the base testid.

**Fix habit, restated once more**: when an AFS/digest claims a shared
component "renders N testids" with a specific literal string per element,
grep EACH literal string individually — `git grep -n
"<exact-string>" origin/main -- src/` per string, not one grep for a
prefix that happens to match several. A prefix match (`agent-version-
selector-trigger*`) would have "confirmed" the fabricated suffix too by
matching the real base testid as a substring hit.
