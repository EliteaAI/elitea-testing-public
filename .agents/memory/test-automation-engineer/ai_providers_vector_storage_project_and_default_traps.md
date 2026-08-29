---
name: Vector Storage — wrong project by default, and creation assigns the default
description: The automation lands on project 399 (no vector storages), and creating a vector storage silently makes it the section default — both invalidate an AFS precondition.
type: feedback
aliases: [vector storage, pgvector, isLastInSection, ai_providers_seeded_project_id, seeded project]
tags: [area/settings, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The automation lands on project 399, not 400

The acting test user's default project is **399 (`Private`)**, whose Vector Storage
section is EMPTY. Analysts explore on **400 (`UI Testing`)**, which carries the
deliberate permanent seed `Autotest PGVector Seed`. **A card count cannot tell the two
apart** — both have 12 LLMs and the same 3 shared embedding models. Only
`GET /configurations/models/{id}?section=vectorstorage` distinguishes them
(399 → `total: 0`, 400 → `total: 1`).

This matters because `CredentialsControls.jsx`'s `isLastInSection` makes the FIRST
vector storage in a project **permanently undeletable through the UI**, and Vector
Storage has no shared configurations to pad the count — so a spec that lands on 399 and
creates one leaves irreversible residue in shared state.

Fix used: `settings.ai_providers_seeded_project_id` (default `"400"`) +
`BasePage.ensure_project_selected()`, which waits on the two project-scoped GETs a
switch fires (`project-info`, `auth/permissions`) rather than `networkidle` (`#1847`).
Plus an explicit guard: if the section is empty at test start, FAIL LOUDLY.

## Creating a Vector Storage configuration ASSIGNS it as the section default

Measured: default `autotest_pgvector_seed` before the create, `autotest_pgvector_<run>`
straight after, with **no selection made**. The OPPOSITE of the LLMs section, where the
new model must be assigned explicitly. Two consequences:

1. Every spec that creates one has mutated the project default and owes a restore
   BEFORE the delete (deletion is additionally blocked while only one remains).
2. A "set a different one as default" case must restore the pre-existing default in
   SETUP, or its selection step is a no-op against a config that is already default.

Not filed as a defect — no case asserts it either way, and it is plausibly intended for
a section that requires a default. Recorded in
`test-specs/settings-ai-providers/_surface.md`.

Related: [[ai_provider_form_schema_remount_and_select_traps]]
