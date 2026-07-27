---
name: Promotability must cover every testid dependency, not just this case's own PR
description: A closure record's promotability row must list every testid the test actually uses as a potential blocker — including ones reused from an unrelated, still-in-flight case — not only the testids this case's own draft PR added
type: feedback
---

Self-caught during a control-audit of my own delivery (issue #64, ELITEA-1971,
2026-07-15). The test used `ENTITY_CARD_SELECTOR` (`entity-card`), a testid the
implementer correctly identified as "already existing, no new testid needed" —
true in the sense that this case didn't need to add it. But "already existing"
was checked against `automation/testids` (the integration branch), not `main`.
Ground truth: `entity-card` was added by an *unrelated, still-open* case
(EL-1740 / EliteaUI#544), so it is exactly as un-promoted as this case's own
new testids (EliteaUI#562).

The closure record I posted named only EliteaUI#562 as the promotion blocker.
That's wrong — the case is ALSO blocked on #544, a dependency with zero
connection to this case's own PR. This is the same shape as the #35/#36/#37
false-promotability-row failure this control loop exists to catch, just
arriving via a *reused* testid instead of a *new* one.

**Rule going forward:** the promotability check (`.agents/workflow.md` §
Closure record) must enumerate EVERY testid the test's page-object diff
references — not just the ones the case's own testid PR touches — and check
each independently against `origin/main`. A testid being "pre-existing" on
`automation/testids` does NOT mean pre-existing on `main`; it only means some
other case (open or merged) put it there first. Every "no new testid needed"
claim in a PR/AFS still needs its own main-vs-testids row in the verification
block, sourced by finding which commit/PR actually introduced it
(`git log -p origin/automation/testids -- <file>` grepped for the testid
string) so the true blocking PR can be named.

**Recurrence (control-audit, issue #78, ELITEA-1974, 2026-07-15/16):** exact
same shape, exact same unrelated blocker PR (`EliteaUI#544`, still open) —
this time the reused dependency was `entity-card` again, in a *different*
case's delivery, caught during an independent control audit rather than
self-caught by the deliverer. The closure record named only the case's own
`EliteaUI#569` as the blocker. Confirms this isn't a one-off slip: any
Credentials/Mcp/Skills/Applications/Toolkits list-page case that reuses the
shared `Card.jsx` `entity-card` testid inherits the SAME #544 blocker until
that sibling case's testid PR merges — worth checking for on every future
case in this family, not just re-deriving from scratch each time.

**Third recurrence (control-audit, issue #83, ELITEA-1963, 2026-07-16):**
same `entity-card`/`EliteaUI#544` blocker, third case in the family, and this
time the delivering session's own closure record HAD already done real
diligence — it correctly caught and disclosed two OTHER reused-testid
blockers (`EliteaUI#562`, `EliteaUI#554`) that neither of the prior two
deliveries surfaced — and still mis-marked the `entity-card` row as "already
fully promoted." Lesson sharpened: partial diligence on a promotability table
does not earn partial credit on the audit — every row is an independent hard
claim, and getting 2 of 3 rows right while the 3rd is flatly wrong is still a
FAIL. `EliteaUI#544` (EL-1740) remains open as of this recurrence; its own
canon question `#277` has now also crossed the 24h unanswered threshold —
worth escalating since resolving/merging #544 removes this blocker from an
entire case family at once instead of relitigating it per-case.

**Fourth recurrence + new gotcha (delivery, issue #94, ELITEA-1929,
2026-07-16):** this test's testid dependencies spanned its own draft
(`EliteaUI#572`) AND an unrelated upstream case's draft (`EliteaUI#554`,
ELITEA-1922 — the Remote-MCP-form fields), same shape as above. New wrinkle:
several of the upstream testids are **schema-driven via JS template
literals** — e.g. `` `toolkit-field-${k}-checkbox` `` in
`ToolBaseProperty.jsx`, `` `toolkit-type-card-${itemKey}` `` in
`CategoryItemCard.jsx` — so there is no literal `data-testid="toolkit-field-
enable_caching-checkbox"` string anywhere in the source; only the template
pattern exists, and the concrete value only materializes at render time from
a schema key. A `data-testid="<id>"` literal-quote grep reports **not
found even on the branch that genuinely has the code** — this is a
different failure mode than the earlier single-vs-double-quote gotcha
(`'data-testid': 'x'` vs `data-testid="x"`), which was purely a
quoting-style miss. Fix: when a literal-quote grep comes back empty on
BOTH `main` and `automation/testids` for a testid the implementer/AFS
claims exists, don't conclude "missing everywhere" — retry with a
bare-substring `git grep -- "<id>"` (no `data-testid=` anchor, no quote
assumption) before treating it as a real gap; if that also finds nothing,
grep for the base id with the trailing dynamic segment stripped (e.g.
search `toolkit-field-` and `-checkbox` separately) to catch the
template-literal case.

**`EliteaUI#544` (the `entity-card`/`entity-card-name` blocker) is now
RESOLVED (delivery, issue #139, ELITEA-1991, 2026-07-17):** first case in
this family since the four recurrences above where `entity-card` AND
`entity-card-name` both checked `main:YES` on a fresh `git fetch` — the
long-standing shared-blocker for the whole Credentials/Mcp/Skills/
Applications/Toolkits list-page family has been merged/cherry-picked to
`main` at some point between 2026-07-16 and 2026-07-17. **Do not keep
treating `entity-card`/`entity-card-name` as an automatic blocker for new
cases in this family** — but do NOT skip the per-case check either:
promotability facts age in both directions (a blocker can clear, a
previously-clear testid can regress if `main` and `automation/testids`
diverge). Always re-derive fresh via `git fetch` + `git grep` per case;
this entry records the historical shape of the blocker and its resolution
date, not a standing exemption.

**Fifth recurrence-adjacent gotcha (same delivery, issue #139,
ELITEA-1991):** the `generate-skill-open-button`/`generate-skill-*`/
`skill-*` family false-negatived on a literal `data-testid="x"`-quoted grep
the same way `entity-card` and the ELITEA-1929/ELITEA-1911 families did,
but via yet another mechanism: `buttonTestId="generate-skill-open-button"`
is a **prop passed at the call site** (`GenerateSkillButton.jsx`), forwarded
down to a child component that applies it as the actual `data-testid`
attribute elsewhere in the tree — not a template literal, not an
object-property shorthand, just plain prop-drilling. Same fix applies:
bare-substring `git grep -- "<id>"` (no quote/attribute anchor at all)
catches all three variants (template literals, object-property shorthand,
prop-drilling) uniformly. At this point the literal-quoted-attribute grep
should be treated as unreliable BY DEFAULT for this codebase's promotability
checks — always run the bare-substring form first, and only fall back to
the anchored form as an extra confirmation, never as the sole check.

**Sixth variant — the listed rows can themselves be incomplete, even when
every listed row is individually true (control-audit, issue #162,
ELITEA-1955, 2026-07-18):** all prior recurrences above were about a
row being *wrong* (false "already promoted," or false-negative from a grep
gotcha). This one is different: the closure record's 10-row table was 100%
accurate for every row it listed, but the table itself dropped a real,
genuinely-used dependency — `agent-toolkit-card`/`toolkit_card`, asserted
at the test's Step 2 (`count()==0`) and consumed by `is_toolkit_attached()`
at Step 8 — that never appeared in the table at all. Ground truth happened
to be benign (`main:YES testids:YES`, no risk), so it didn't flip the
promotability verdict this time, but the near-perfect table (9-10 correct
rows) gave no visible signal that anything was missing. **Lesson: don't
just re-verify the rows a closure record lists — independently re-derive
the FULL testid-usage set from the test's own page-object call chain (every
`LocatorDescriptor` field and UPPER_CASE selector constant actually reached
by a method the test calls) and diff that set against the table's rows, on
every audit, even when every listed row checks out clean.** A table that's
right about everything it says can still be silently short one row.
