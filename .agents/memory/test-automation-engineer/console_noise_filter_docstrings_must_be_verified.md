---
name: Console-noise filter docstrings must be tracker-verified, not copied
description: Credentials specs copy forward "already-filed, OPEN #N" console filters — #518/#554 have been CLOSED since 2026-08-11, and #518's filter masks a crash of the component under test
type: feedback
aliases: [is_known_518_warning, is_known_554_warning, console noise filter, CredentialsList crash filter, prompt_lib 404]
tags: [area/credentials, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The fact (verified 2026-08-22, `gh issue view`)

The credentials suite (`test_credential_create.py`, `test_credential_delete.py`,
`test_credential_search_by_name.py`) carries two copy-forward console-noise
filters whose docstrings assert the issues are **OPEN**. Both are CLOSED:

- **#518** — "Cannot refetch a query that has not been started yet" /
  `<CredentialsList>` error-boundary crash — CLOSED `COMPLETED` 2026-08-11,
  NOT REPRODUCIBLE after 22 attempts. Its signature is a crash of the very
  component every credentials spec renders, so a copy of this filter is
  **masking**: a crash regression ships green. Removed from ELITEA-1966 /
  ELITEA-1973 in PR #1668 fix round 1; both specs run green without it.
- **#554** — empty-projectId `.../toolkits/prompt_lib/` 404 — CLOSED 2026-08-11,
  verdict "local UI / test-client artifact, not a backend defect". Keeping the
  filter is defensible as a local-environment allowance; the "OPEN" wording is not.

## The move when writing a new spec

Before copying any `_is_known_<N>_warning()` from a neighbour, run
`env -u GITHUB_TOKEN gh issue view <N> --repo EliteaAI/elitea-testing-public
--json state,stateReason`. Closed-as-not-reproducible ⇒ do not copy; a filter
whose signature names the component under test is masking regardless of state.
Three merged specs doing it is convention, not authority
(`role-overrides.md` § precedent is not authority).

`automation/tests/unit/test_credentials_console_filters_scope.py` pins this for
the two ELITEA-1966/1973 specs: it fails if `_is_known_518_warning` reappears in
either module, and if the retained #554 filter ever widens past its URL shape.
