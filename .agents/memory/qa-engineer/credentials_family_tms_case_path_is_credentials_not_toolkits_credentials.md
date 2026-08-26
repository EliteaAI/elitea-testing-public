---
name: Credentials-family TMS cases live in credentials/, not toolkits-credentials/
description: allure.issue links for the ELITEA-1976/1977 toolkit-credential family point at a folder+slug that does not exist; the real path is credentials/ELITEA-<id>_credential-<title-slug>.md
type: feedback
aliases: [allure.issue credentials link, ELITEA-1976 dead link, ELITEA-1977 dead link, toolkits-credentials TMS path]
tags: [area/credentials, type/traceability]
created: 2026-08-22
updated: 2026-08-22
---

## The fact

The AFS/spec feature folder in this repo is `test-specs/toolkits-credentials/`,
but the **TMS** folder is `credentials/`, and the case filename keeps the
`credential-` prefix from the case title:

```
../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/credentials/
  ELITEA-1976_credential-create-private-credential-from-toolkit-flow.md
  ELITEA-1977_credential-create-project-credential-from-toolkit-flow.md
```

Both `test_credential_create_private_from_toolkit_dropdown.py` (MERGED,
ELITEA-1976) and `test_credential_create_project_from_toolkit_dropdown.py`
(ELITEA-1977, PR #1675) `@allure.issue(...)` a
`toolkits-credentials/ELITEA-<id>_create-…-from-toolkit-dropdown.md` URL —
wrong folder *and* wrong slug, so both links 404. The merged one owes a sweep.

## Derive it, never guess it

```bash
find ../onetest-ai-tm-Elitea/tests -iname "*ELITEA-<id>*"
```

Fourth confirmed occurrence of this class — see also
[[allure_issue_tms_link_path_drift]], [[allure_issue_tms_link_filename_must_be_verified]],
[[allure_issue_link_slug_can_drift_from_real_tms_filename]]. Standing reviewer
stance (unchanged): report it, do not block — it is report-traceability, not
test correctness.
