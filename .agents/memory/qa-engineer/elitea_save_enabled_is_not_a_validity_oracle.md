---
name: Toolkit create form — Save enabled proves dirtiness, not validity
description: shouldDisableSave = isLoading || !formik.dirty; a to_be_enabled() assertion says nothing about required fields
type: feedback
aliases: [to_be_enabled, save button enabled, formik dirty, toolkit form validation, credential auto-select]
tags: [area/toolkits, type/oracle-strength]
created: 2026-09-10
updated: 2026-09-10
---

## The fact

`CreateToolkitToolTabBar.jsx` gates Save on `isLoading || !formik.dirty` — there is a
`//@todo` in the source saying validation is not wired in. Measured live 2026-09-10:

- Form renders empty → Save DISABLED.
- The credential **auto-selects** ~0.8–1.0 s later (the newest saved credential of the
  type) → the form is dirty → **Save ENABLED with Toolkit Name empty and the required
  Repository field empty.**
- Clicking Save in that state fires **no request at all**, shows **no error anywhere**,
  and leaves both buttons enabled.

## Why it matters for a repair

`expect(save_button).to_be_enabled()` is the right assertion on the **credential** form
(#1897 R2 — there it genuinely gates on the required set). It does **not** transfer to
the **toolkit** form: it is satisfied by any dirty form, valid or not. The only honest
oracle for "the toolkit was created" is the `POST …/tools/prompt_lib/{project}` 201 and
the resulting `/toolkits/all/{id}` navigation.

Corollary: a required field silently skipped by a fill helper does not surface as a
disabled Save. It surfaces two steps later as "did not navigate", naming the wrong
subsystem.

Origin: #2123 / ELITEA-1141.
