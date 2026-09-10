---
name: Closure grep is line-scoped — a multi-line JSX data-testid expression reads as absent
description: 4th false-negative shape; `data-testid={` on one line and the value on the next defeats stage 2 — add `-C1`, and tell it apart from a composed template by whether stage 1 hit at all
type: feedback
aliases: [multiline testid, data-testid on its own line, ternary testid absent, stage 2 context, closure record false negative, -C1]
tags: [area/promotability, type/convention]
created: 2026-09-10
updated: 2026-09-10
---

## The gap

`.agents/workflow.md` § Closure record filters stage 1's hits with a **line-scoped**
grep. When the attribute spans lines, the value's line carries neither `data-testid`
nor `testid[:=]`, so a testid that IS on `main` is reported absent:

```jsx
// EliteaUI ImportWizardModal.jsx:106-108
      data-testid={
        importSucceedData || forkedData ? 'agent-import-complete-dialog' : 'agent-import-preview-dialog'
      }
```

Hit live on #2147/ELITEA-1901: two of fifteen testids printed `main:no testids:no`
while both were present on both refs. The section exists to stop exactly this kind of
false row (#19), so the miss is silent and lands in the record as fact.

## The fix — one flag

```bash
git grep -n -C1 -- "$t" origin/main -- src/ | grep -qiE "$FILTER"
```

## Telling the two "no" causes apart — do this BEFORE reaching for a fix

| Stage 1 | Meaning | Move |
|---|---|---|
| **hits**, stage 2 drops them | multi-line attribute (this note) | add `-C1`, then read the hit |
| **nothing at all** | runtime-composed template | grep the literal **prefix** the template contributes |

Same run produced one of each: `agent-import-complete-list-agents` had zero stage-1
hits because the source is ``data-testid={`agent-import-complete-list-${key}`}``.
Applying the wrong remedy to either leaves the row wrong.

**A `no` row is not evidence until you know which of the two you are looking at.**
Reported on canon card #2100 (which already tracks shapes 1-3: `-i`, `[:=]`,
`<part>TestIdPrefix=`).

Related: [[closure_grep_must_catch_testid_colon_prop_form]] · [[promotability_grep_false_negative]] · [[promotability_grep_false_positive_prefix]] · [[closure_record_narrative_can_fail_on_template_shape_alone]] · [[dynamic_testid_promotability_grep]]
