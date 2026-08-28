---
name: Porting a case to main must diff its docs against the source branch
description: On a port PR, diff the AFS and _surface.md against the SOURCE branch — the greps cannot see a doc that reverted to the stale contract
type: feedback
---

**Symptom.** A PR that ports an already-reviewed repair from `automation/base` to `main`
resolves the doc conflicts by "keeping both sides". The code files are byte-identical to
base (verifiably faithful). The AFS and `_surface.md` are not — they silently keep `main`'s
side and drop most of base's amendment.

**Why every existing gate misses it.** The three mechanical greps only scan `automation/`.
Triangulation compares test ⇄ AFS ⇄ case — and a *reverted* AFS makes the TEST look wrong,
so triangulation fires in the wrong direction. The N×-green gate is indifferent to markdown.
Nothing in the pipeline diffs docs against the branch they were ported FROM.

**The check that catches it (cheap, two commands):**

```bash
# 1. code fidelity — must be EMPTY
git diff origin/automation/base:<path/to/spec.py> $HEAD:<path/to/spec.py>

# 2. doc union — every '<' line is content the port DROPPED
diff <(git show origin/automation/base:<afs.md> | grep -E '^#{1,4} ') \
     <(git show $HEAD:<afs.md>                  | grep -E '^#{1,4} ')
```

Run it on the AFS **and** `_surface.md`. Line counts are the tell: HEAD ≈ main's count +
a small delta, when base's version is much larger, means the amendment did not travel.

**What the loss actually costs.** On PR #1929 the AFS's `## Expected Results`,
§ Test Steps and Coverage Map Axis 1 all reverted to the pre-EL-6128 contract
("only Chat Message available; Schedule/Webhook absent") — the exact assertion the
port exists to replace — presented as current, with base's strikethrough marking gone.
A later analyst or `adjust-automated-test` run would triangulate the shipped test against
that AFS and "repair" it back, re-creating the original failure.

**Second shape, same PR:** a digest section ADDED by the port asserted a root cause
(config-panel remount) that the SAME PR's code docstring explicitly refutes, and described
an implementation the PR deletes. Check that a ported digest paragraph agrees with the code
shipping beside it — `grep -c "<phrase>"` on `origin/main` proves whether the section is new
content (0) or inherited staleness.

**Also:** `gh pr review --request-changes` is rejected when the keyring account authored the
PR ("Can not request changes on your own pull request"). Post via `gh pr comment` instead.

**The mirror-image trap, found on the fix round (PR #1929, round 3).** The correct repair for
a doc-loss blocker is usually to take the source branch's file **wholesale** — a cherry-pick
applies one commit's *delta*, not the file state produced by the ~15 commits that built it.
But wholesale import brings across every sentence that is true *there* and false *here*.

On #1929 the restored AFS's § Shipped implementation record described the old
`open_trigger_select` (3 s probe, `count() == 0`, one re-click) and its since-disproven
config-panel-remount root cause. True on `automation/base`, which still runs that code;
false on the fix branch, which had just deleted it.

**So a cross-branch doc restore needs a second pass:** grep the restored file for text
describing CODE the restoring branch changed.

```bash
# strings the branch's own docstrings refute, or that name deleted symbols
for s in "<old mechanism phrase>" "<deleted constant>" "<deleted guard>"; do
  printf '%-38s : %s\n' "$s" "$(git show $HEAD:<restored.md> | grep -c "$s")"
done
```

And do not let byte-identity-with-source become the invariant. **"No dropped content" is the
invariant**; identity is only the usual way to achieve it. A one-paragraph, branch-local
"superseded by PR #N" addendum is the right resolution, and the two files legitimately differ
until the code change itself reaches the source branch.

## The two directions, and the one command each

A cross-branch port can lose truth in **both** directions, and neither is visible to the three
mandatory greps (they scan `automation/` only). Confirmed across PR #1929, where all three
blockers were of this class and the code was sound throughout:

| Direction | What happens | Catch it with |
|---|---|---|
| **Dropped** — the port kept `main`'s side | The AFS reverts to a superseded contract; triangulation then indicts the *test* | `diff <(git show <src>:<doc> \| grep -E '^#{1,4} ') <(git show $HEAD:<doc> \| grep -E '^#{1,4} ')` — every `<` is dropped |
| **Imported** — the fix took the source file wholesale | Text true on the source branch, false here, because this branch changed the code it describes | `grep -c` the restored file for old mechanism phrases **and deleted/renamed symbol names** |

Run the second sweep in two halves. Refuted *prose* (`remount`, `3 s probe`, the old guard's
name) and dangling *symbols* — for every page-object identifier the doc names, check it still
exists on this branch. A doc naming a deleted symbol is the same defect wearing different clothes.

Both blockers on #1929 were mirror images of each other: fixing the dropped one by taking the
source file wholesale is exactly what imported the other.
