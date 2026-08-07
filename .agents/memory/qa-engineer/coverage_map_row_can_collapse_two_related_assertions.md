---
name: Coverage Map row can collapse two related assertions into one check
description: A Coverage Map row claiming "aria-invalid AND no helper text" may be honestly satisfied by asserting only aria-invalid — verify via source JSX whether both are keyed off the same boolean before flagging a gap
type: project
---

## What happened (ELITEA-1900, PR #1290 — reviewer slot)

AFS step 4 / Coverage Map row 4 says: "asserted where: `aria-invalid == "false"`,
no error helper text". The implementation (`test_agent_name_character_limit.py`
Step 4) only asserts `not form_page.is_name_invalid()` (reads `aria-invalid`) —
no separate check for helper-text DOM absence.

At first glance this looks like a per-step-assertion gap (AFS Coverage Map
promises two things, code delivers one). Reading the live source resolved it:
`CreateAgentForm.jsx` wires both props off the identical condition —

```jsx
error={formik.touched?.name && Boolean(formik.errors.name)}
helperText={formik.touched?.name && formik.errors.name}
```

— and the AFS's own "Known Defects" section already established that no
length-based validation rule sets `formik.errors.name` at all (only the
required-empty case does). So `aria-invalid === "false"` and "no helper text
rendered" are causally the same fact in this component, not two independent
observables. Checking one is a sound proof of both, same shape as
`ArtifactsPage.is_bucket_name_invalid` precedent.

## Reviewer action item

Before flagging "Coverage Map claims two things, code asserts one" as a gap:
grep the component's JSX for the `error=`/`helperText=` (or equivalent) props
of the field in question. If both are keyed off the identical boolean
expression, a single-attribute assertion is NOT under-testing — it's the
correct minimal proof. Only block when the two conditions can genuinely
diverge (independent error sources, e.g. one prop checks length and another
checks emptiness).
