---
name: Cleanup flag must be set at the mutating call, not after its assertions
description: A restore-in-finally guard flag set after post-mutation assertions leaks shared state whenever one of those assertions flakes
type: feedback
aliases: [cleanup flag, default_changed, finally restore, teardown guard]
tags: [area/test-design, type/review-pattern]
created: 2026-08-29
updated: 2026-08-29
---

## The pattern

Specs that mutate shared project state guard their `finally` restore with a boolean
(`default_changed = True`). The flag must be assigned on the line **immediately after
the call that performs the mutation** — not after the assertions that verify it.

Seen in settings-w10 (ELITEA-2400, `test_vector_storage_edit.py`): the transit create
(`save_and_return_to_list()`) reassigns the section default as a side effect, but
`default_changed = True` sat three assertions later. Any flake in
`card_for_model(...).to_have_count(1)` or the card-count assert skips the restore while
the `finally` still deletes the configuration — i.e. the project's default vector
storage is deleted without being restored. The sibling specs in the same PR
(ELITEA-2399/2401) set the flag on the very next line, so the asymmetry is the tell.

## Review heuristic

For every `finally`-restore guard flag, ask: *what is the widest window between the
mutation and the flag?* Everything in that window is a path that leaks. Same reasoning
applies to `body_completed` — but that one is deliberately late, because it gates an
assertion rather than a restore.

Related: [[settings_ai_providers_vector_storage_project_and_default_traps]]
