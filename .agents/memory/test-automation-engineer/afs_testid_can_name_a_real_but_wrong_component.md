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

## Addendum (ELITEA-2020 fix round 1, PR #1305, reviewer Finding 1) — SUPERSEDED, see round-2 correction below

A fourth variant was claimed here, one notch worse than the others: that
`PipelineDetailPage.version_selector`'s originally-recorded
`agent-version-selector-trigger-combobox` testid was **wholly fabricated**
— not a wrong-component mix-up, a wrong-STRING invention — on the strength
of `git grep -n "agent-version-selector-trigger-combobox" origin/main --
src/` (and `origin/automation/testids`) returning **zero hits**, whole
repo, and a source trace claiming `SingleSelect.jsx` has "no `-combobox`-
suffix derivation logic anywhere."

**This verdict was itself wrong — corrected 2026-08-07, review fix round 2
(reviewer re-review + implementer fix-round-2 cross-check).** The
`-combobox` variant IS real:
`SingleSelect.jsx:661` (`../EliteaUI`, `automation/testids` ref) reads
`SelectDisplayProps={dataTestId ? { 'data-testid': \`${dataTestId}-combobox\` } : undefined}`
— a genuine second `data-testid`, applied via MUI's `SelectDisplayProps`
prop onto the nested `role="combobox"` display div (confirmed against
`node_modules/@mui/material/Select/SelectInput.js:472,486` — a different
DOM node from the outer wrapper). The shared component really does render
TWO `data-testid`-bearing elements, one nested in the other — the
*original* AFS claim ("renders TWO testids") was accurate all along.

**Why the round-1 grep still returned zero hits despite the testid being
real — this is the actual, corrected lesson**: `` `${dataTestId}-combobox` ``
is a template literal evaluated at RENDER TIME, so the fully-concatenated
string `agent-version-selector-trigger-combobox` NEVER appears as a literal
anywhere in source. Grepping for the exact concatenated string is checking
the wrong thing — it will read as "zero hits, doesn't exist" for ANY
dynamically-suffixed testid, real or not. The correct check is to grep for
the *mechanism* or the literal suffix fragment instead:
`git grep -n -- "-combobox" <ref> -- src/` (the substring `-combobox` DOES
appear literally in the template) or `git grep -n "SelectDisplayProps"
<ref> -- src/`. This is the exact "dynamic testid" shape
`.agents/testing.md` § Locator policy already documents for data-
parameterized testids — just parameterized by the BASE TESTID rather than
by test data, which is why a plain literal-string check missed it.

**And the finding is ref-specific, not absolute**: `git grep -n --
"-combobox" origin/automation/testids -- src/` → 1 hit
(`SingleSelect.jsx:661`). `git grep -n -- "-combobox" origin/main -- src/`
→ 0 hits (re-verified 2026-08-07 with a fresh `git fetch origin` on both
refs, round 2). The `SelectDisplayProps` line is on `automation/testids`
only, not yet promoted to `main` — a `needs-adding`→`on-automation/testids
only (awaiting human promotion to main)` PROVENANCE case
(`.agents/role-overrides.md` § Analyst slot), not a non-existent testid.
"Zero hits on both `main` and `automation/testids`" (as round 1 claimed)
was also simply false as a factual matter, independent of the template
issue — a single `git grep` across "both refs" collapsed into one claim
without pasting each ref's output separately is exactly the anti-pattern
the closure-record two-stage-grep discipline exists to catch.

**Why `agent-version-selector-trigger` (no suffix) was still the right
fix, for a different reason than round 1 gave**: `AgentDetailPage` already
reads this exact shared component via `version_selector_trigger` (no
suffix) — merged, exercised across ELITEA-1888/1889/1890/1891/1892 — and
that testid is confirmed on BOTH `main` and `automation/testids`, unlike
the `-combobox` variant. DOM `textContent` on the outer wrapper already
includes the inner `-combobox` div's descendant text, so reading the
no-suffix testid returns "base" correctly either way. The page-object
OUTCOME from round 1 was correct; only its stated JUSTIFICATION
("fabricated", "does not exist", "zero hits on both refs") was false —
and that false justification shipped into 4 permanent artifacts (this
memory entry, the AFS, `_surface.md`, and the page-object docstring) as
verified fact, exactly the "improvisation declared but the AFS/digest
never actually corrected to the TRUE state" failure this file's own
"Addendum (docs-only fix round, PR #710)" above warns about — except here
the correction itself, not just the omission, was the defect.

**Fix habit, restated for THIS specific failure mode**: before declaring a
claimed testid "fabricated" / "does not exist" from a grep-zero-hits
result, ask whether the claimed string could be a `<base>-<suffix>` or
`<prefix>-<base>` TEMPLATE CONSTRUCTION rather than a literal — if so,
grep for the KNOWN-REAL base string plus the suffix/prefix fragment or a
template-construction pattern (`` `${ ``, `SelectDisplayProps`, or the
project's documented dynamic-testid mechanisms), not just the exact
concatenated form — and check EACH ref separately, pasting both outputs,
never collapsing "checked both, zero on either" into one unverified claim.

## Addendum (ELITEA-2370 fix round 1, reviewer dispatch): two files with the IDENTICAL basename `SkillCard.jsx`, only one wired into the surface under test

A fifth variant, this time in a REVIEWER's fix instruction rather than an
AFS row — same failure class, different origin. The reviewer's dispatch
named a specific, real, already-pushed fix: "`skill-card-{id}` on `EliteaUI
src/[fsd]/features/skill/ui/SkillCard.jsx:48`" as the handle to use for a
Catalog-page Skills-tab content-visibility assertion. That testid IS real,
IS on `main` and `automation/testids`, and IS named exactly as claimed —
every surface-level check passes. But `features/skill/ui/SkillCard.jsx` is
imported ONLY by `ApplicationSkills.jsx` (an agent's attached-skills list on
the agent detail page) — confirmed via `grep -rln "SkillCard" src/` +
reading each hit's import path. The Catalog's Skills tab
(`EliteaCatalog.jsx` → `SkillsTab.jsx` → `SkillCategorySection.jsx`) imports
a DIFFERENT, unrelated component that happens to share the exact same
filename one directory over: `features/skill-hub/ui/SkillCard.jsx` — which
had NO testid at all.

**Why this is a sharper version of the same trap**: prior addenda involved
same-STRING-different-component or same-string-different-REF collisions.
Here the collision is same-BASENAME-different-directory — `grep -rln
"SkillCard" src/` alone still returns both files with no signal to prefer
one, because both are legitimately named `SkillCard.jsx`. The disambiguator
is the RELATIVE import (`import SkillCard from './SkillCard'` inside
`skill-hub/ui/SkillCategorySection.jsx` resolves to the sibling file in
`skill-hub/ui/`, not the one in `skill/ui/`) — a check that requires reading
the importer's own directory, not just the imported filename.

**Actionable pattern, restated for basename collisions**: when a fix/AFS
names `<Component>.jsx` as the owner of a handle, `find src -iname
"<Component>.jsx"` (not just `grep`) BEFORE trusting the path — if more than
one file shares the basename, trace which one the surface's actual import
chain resolves to (`grep -rn "SkillCard" <surface-entry-point>.jsx` then
read that import's relative/aliased path literally) before adding to or
reusing either file's testid. Two components can legitimately have the same
name in an FSD-style `features/<domain>/ui/` layout — the directory is part
of the identity, not decoration.
