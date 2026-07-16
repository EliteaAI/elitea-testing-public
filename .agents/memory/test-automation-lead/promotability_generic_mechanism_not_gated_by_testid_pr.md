---
name: Promotability — a testid can be genuinely on main via a generic runtime mechanism even when literal grep finds it nowhere
description: before concluding a testid is "not found on either branch" or "blocked on a draft PR," check whether it's constructed generically at runtime from a pre-existing, undiffed shared component — that mechanism can already be live on main even though the literal composed string never appears in source
type: feedback
---

Hit while verifying promotability for ELITEA-1889 (issue #67, PR #558). The test uses
`delete-agent-menuitem`. A bare-value grep for that exact string came back **zero hits
on BOTH `origin/main` and `origin/automation/testids`** — the pattern that normally means
"not sourced from any pending testid work, investigate further" (see
`promotability_grep_false_negative.md`), but this time both branches came back empty,
which looks like neither branch has it at all.

Traced it to the actual source: `src/components/DotMenu.jsx` renders
`data-testid={testId ? \`${testId}-menuitem\` : undefined}`, and the caller passes
`testId: item.key` where the menu item's `key` field is `'delete-agent'` (defined in
`DeleteApplicationButton.jsx`). Neither file has **any diff** between `main` and
`automation/testids` — this generic `key`→`testId`→`${testId}-menuitem` composition
mechanism is pre-existing, shared infrastructure, unrelated to any of the testid work in
flight. It was never introduced by any draft PR; it's just constructed at runtime from a
value that isn't a literal string anywhere near the `data-testid` attribute, so no grep
form (attribute-string or bare-value) can find the *composed* result in source — only the
two separate pieces (`testId ? ... : undefined` and `key: 'delete-agent'`) exist as text,
in two different files, joined only by a prop pass-through and a template literal at
render time.

**The check that actually resolves this:** `git diff origin/main origin/automation/testids
--stat -- <owning-file>`. If the file has **zero diff** between the two branches, the
mechanism it contains is pre-existing and promotable regardless of whether a literal-string
or bare-value grep for the *final* testid string finds anything — there's nothing pending
to promote because nothing about that file changed. Only trust a "genuinely missing"
verdict when the owning file **does** show a diff, and only then trace that diff (via
`git log -S`) to its owning draft PR.

**Escalating check order for a testid that grep can't find on either branch:**
1. Bare-value grep (defeats attribute-string false negatives from conditional/prop-forwarding JSX — already documented).
2. If still empty on both branches: find the file that plausibly renders the element (via UI-team naming convention, sibling component search, or asking the analyst/implementer where they found it), then `git diff main...testids --stat` on that exact file.
3. Zero diff on that file → pre-existing generic mechanism, already promotable, not gated by any draft PR — don't report it as an open dependency.
4. Non-zero diff → read the actual render logic (template literals, prop defaults, spread props) to find how the composed value forms, then `git log -S` on the real substring that IS literal text in the diff.

Don't stop at "grep found nothing anywhere" and either (a) wrongly report it as blocked-on-unknown, or (b) skip it from the promotability table entirely. Read the source.
