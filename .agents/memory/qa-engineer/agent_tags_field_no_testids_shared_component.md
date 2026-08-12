---
name: Agent Tags field has no testids (shared component, pipeline-only wired)
description: Agent Tags input/chips are testid-less by design; add via ApplicationEditForm.jsx's existing isFromPipeline ternary, using function-form chipTestId/chipDeleteTestId for per-tag addressability
type: reference
---

`ApplicationEditForm.jsx` (shared by Agent + Pipeline forms) already threads
`inputTestId`/`chipTestId` into its `<TagEditor>` call site, but only for the
Pipeline branch (`isFromPipeline ? 'pipeline-tags-input' : undefined`) — the
Agent branch is intentionally `undefined`, per an explicit code comment
("canon #511 scope discipline: no case exercises Agent's Tags yet"). ELITEA-
1878/1879 (2026-08-06) are the first cases to touch Agent Tags, so this gap
needs closing via `add-data-testid`.

Key facts for whoever implements:
- `AutoCompleteDropDown.jsx` (the component underneath `TagEditor`) already
  supports `chipTestId`/`chipDeleteTestId` as **either a static string or a
  function of the option** (`typeof x === 'function' ? x(option) : x`). The
  Pipeline form only uses the static form (one shared testid for every
  chip); Agent should use the function form
  (`option => \`agent-tags-chip-${option.name}\``) because Agent cases need
  to address specific tags individually (verify two named tags persist,
  delete one named tag among several) — a single static testid would force
  brittle `.nth()` positional indexing.
- `chipDeleteTestId` (the delete-icon testid) is a SEPARATE prop from
  `chipTestId` — needed only by cases that actually remove a tag
  (ELITEA-1879), not by add-only cases (ELITEA-1878). Per canon #511 scope
  discipline, don't wire it unless a case's implementation actually calls
  it.
- No network request fires on chip add or chip delete — pure client-side
  Formik state (`TagEditor`'s `onChangeTags` → `setFieldValue`). Only Save
  (`agent-save-button` → `PUT .../application/prompt_lib/{proj}/{id}` →
  `201`) persists. Reload correctly reflects the saved tag set — confirmed
  live, no functional defect on add-multiple or remove-one-keep-others.
- Full AFS: `test-specs/agents/l2_add-and-save-multiple-tags-persist-after-reload_ELITEA-1878.md`,
  `test-specs/agents/l2_remove-tag-from-agent-removal-persists-after-reload_ELITEA-1879.md`.
