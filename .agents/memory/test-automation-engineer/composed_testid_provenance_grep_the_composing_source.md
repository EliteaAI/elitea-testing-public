---
name: Composed testids — a literal two-ref grep proves NOTHING; grep the composing source file
description: For template-composed testids (toolkit-field-${k}-input, testIdPrefix, ${dataTestId}-combobox) the literal never appears in src on EITHER ref — provenance must be checked on the composing component, per ref, and staleness runs BOTH directions
type: feedback
aliases: [composed testid provenance, testIdPrefix provenance, template testid on-main, provenance both directions]
tags: [area/testids, type/provenance]
created: 2026-08-24
updated: 2026-08-24
---

## The trap (ELITEA-1932, PR #1720, fix round 1, 2026-08-24)

The AFS claimed `on-main ✓` for `toolkit-field-client_secret-input-toggle-secret`
/ `-toggle-password`. Both are **composed at three levels**:
`ToolBaseProperty.jsx` emits `` testId={`toolkit-field-${k}-input`} `` →
`SecretField.jsx:342` derives `` testIdPrefix={`${inputProps['data-testid']}-toggle`} ``
→ `src/components/Toggle.jsx` renders `` data-testid={`${testIdPrefix}-${optionValue}`} ``.

**The literal string exists nowhere in `src/` on either ref.** So the canonical
two-ref check (`git grep -- '<testid>' origin/main -- src/`) returns 0 hits on
BOTH — which reads as "not on main" *and* is equally consistent with "the grep
can't see it". Neither the claim nor its refutation is provable that way.
Truth here: `Toggle.jsx` on `origin/main` carries **no testid at all**, and
`SecretField.jsx` on `main` has no `testIdPrefix` line — the wiring is
`automation/testids`-only (`EliteaAI/EliteaUI@5892ae48`, EL-1967).

## The check that works

Find the component that COMPOSES the testid, then grep that file per ref:

```bash
cd ../EliteaUI && git fetch origin
git grep -ln '<stable-fragment>' origin/automation/testids -- src/   # e.g. toolkit-field-  /  testIdPrefix
git show "origin/main:<file>"               | grep -nE 'testid'      # is the WIRING there?
git show "origin/automation/testids:<file>" | grep -nE 'testid'
```

The unit of provenance is **the composition mechanism in its source file**, not
the rendered string. `git log --oneline -S'<prop or fragment>' -- <file>` on
`origin/main..origin/automation/testids` gives the citable SHA.

## Staleness runs BOTH directions — re-verify the "not on main" rows too

Same round: `toolkit-configuration-show-more` and
`toolkit-detail-save-button`/`-discard-button` were carried from the ELITEA-1929
/ 1930 AFS as *"on `automation/testids`"* — the UI team had since promoted both
(`EliteaAI/EliteaUI@ab757380`, `@bf4a13ad`). An under-claiming row is not
harmless: it hides a case that is already deployed-env promotable and invites a
pointless "awaiting human cherry-pick" park. **Verify every row, in both
directions, per fix round** — a copied row from a sibling AFS is a claim, not
evidence.

Related: [[afs_on_main_provenance_claim_needs_two_ref_grep]]
