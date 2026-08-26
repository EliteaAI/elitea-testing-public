---
name: Credentials area backlog (#1394) — 11/14 automated, 3 blocked on a real OAuth identity
description: The credentials surface is done except the SharePoint OAuth completion family, which needs a Microsoft account nobody has provided
type: project
aliases: [credentials backlog, ELITEA-1983, ELITEA-1985, SharePoint OAuth]
tags: [area/credentials, status/blocked]
created: 2026-08-24
updated: 2026-08-24
---

## State

Of the 24 credentials cases, **21 are automated**: 10 before this card, plus 11
delivered under #1394 (wave-01 PR #1704 `a099bc803`, 9 cases; wave-02 PR #1714
`5360fa31e`, ELITEA-1981/1982). TMS back-written, closure record posted, card
parked `Blocked`.

## The 3 that are left, and why they will stay left

ELITEA-1983 (Successful OAuth Completion), ELITEA-1984 (Failed OAuth
Completion), ELITEA-1985 (Reuse After Authorization) all need a **real Microsoft
/ SharePoint identity**, which this environment does not have — `.env.test`
carries `ELITEA_*`, `TEST_USER_*`, `JIRA_*`, `GIT_HUB_TOKEN`, `CONFLUENCE_*`,
`BITBUCKET_*`, `ADO_*`, `POSTMAN_*` and nothing Microsoft.

The observable in each *is* the OAuth token and the state it produces, so faking
it is terminal substitution. **Decision card: #1708** (provide an identity ·
descope to manual · split). Do not re-pick these up until it is answered — an
intake sweep will keep surfacing them.

What IS covered without an identity: the whole Elitea-side surface up to the
authorization hand-off (Login-button gating, the Configuration OAuth dialog's
pre-populated fields off a real `check_connection` 401, Cancel) — ELITEA-1981
and ELITEA-1982 do exactly that, honestly.

## Live debt on this surface

- `test_credential_usage_in_toolkit_flows` (ELITEA-1979) is **red on
  `automation/base` itself** — no linked defect, no soft-assert. Filed #1703. The
  credentials blast radius cannot come back clean until it is triaged.
- Sanctioned-REDs to expect in any credentials blast-radius sweep:
  `test_credential_search_by_name` (#551), `test_credential_duplicate_mismatch_validation` (#1004).
- Product defects filed by this work: #1666, #1713.
- Canon rulings owed: #1705, #1706, #1707. Retracted-and-still-open: #1709, #1710.

Related: [[blast_radius_red_classify_with_a_control_run_on_base]] · [[artifacts_area_backlog_1392]]
