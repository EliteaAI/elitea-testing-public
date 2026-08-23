---
name: /artifacts/create-bucket serves BOTH the New Bucket and Edit bucket forms
description: A URL-only assertion never proves which bucket form opened — assert artifacts-bucket-form-heading's text
type: reference
aliases: [create-bucket route, New Bucket form opens, Edit bucket heading, bucket form heading]
tags: [area/artifacts, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

`EliteaUI` renders the bucket form at the single route `/artifacts/create-bucket`
for BOTH modes; `CreateBucket.jsx` switches on `currentBucket` to render the
heading `New Bucket` vs `Edit bucket` (and to set `disabled={!!currentBucket}` on
the Name field). So

```python
assert "/artifacts/create-bucket" in page.url   # says NOTHING about which form
```

satisfies a case step that reads *"the New Bucket form opens"* even if the Edit
form (or an empty form) rendered instead.

**The discriminating handle already exists** — `artifacts-bucket-form-heading`,
wrapped as `ArtifactsPage.get_bucket_form_heading_text()`. Assert the heading
text alongside the route for any "which form opened" step, in either direction.

Found while reviewing ELITEA-1812 / ELITEA-1816 (PR #1679): the same AFS pair
states the route-is-ambiguous fact for the Edit step (and asserts the heading
there) while leaving the Create step on the URL alone — the inconsistency is easy
to miss because both halves read as reasonable in isolation.

Related: [[bucket_name_lowercasing_is_backend_and_edit_name_is_disabled]]
