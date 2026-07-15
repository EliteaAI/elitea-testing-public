---
name: Promotability grep false positive from testid prefix collision
description: bare-value grep for promotability can false-positive when the testid being checked is a substring/prefix of another real testid on the same component family — use the exact `data-testid="X"` form in that specific case
type: feedback
---

`promotability_grep_false_negative.md` established: grep the bare testid
value, not the `data-testid="..."` attribute-string form, because
conditional-ternary/prop-forwarding JSX shapes don't emit the literal
attribute string in source.

The opposite failure mode exists too, discovered auditing issue #30
(EliteaUI#544): the bare-value form over-matches when the testid you're
checking is a **substring/prefix of a longer, unrelated, already-shipped
testid** on the same component family. `git grep -- "entity-card"` on
`origin/main` returns a hit — but the only match is
`data-testid="entity-card-name"`, a completely different (already-on-main)
element. A careless read says "entity-card is on main" when it is not.

**Rule of thumb:** before trusting a bare-value grep result during a
promotability check, glance at *what actually matched*
(`git grep -n -- "$t" <ref> -- src/`, not just `-q`). If the match line's
testid isn't character-for-character equal to the one you're checking,
re-run with the exact `data-testid="$t"` form for that specific testid.
This matters most for short/generic base names (`entity-card`,
`skill-tag`) that are also prefixes of compound names in the same file
family (`entity-card-name`, `entity-card-tag-chip`) — exactly the naming
convention this project uses (`{section}-{element}-{type}`), so the
collision risk is structural, not rare.

Net practical guidance: run BOTH forms when auditing (bare-value first for
recall against conditional JSX, then confirm any hit by inspecting the
matched line or re-checking the exact attribute string) rather than
trusting either form alone.
