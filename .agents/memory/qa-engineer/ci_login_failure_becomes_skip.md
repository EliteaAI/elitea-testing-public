---
name: A DEV CI login failure turns a test into SKIP, so the job goes green
description: "SKIPPEDLogin failed:" in the dev-stable logs — a green CI job can mean the test never ran; never read job conclusion as a pass
type: project
aliases: [login failed skip, green job test never ran, dev-stable skip, CI false green]
tags: [area/ci, type/anti-pattern]
created: 2026-08-27
updated: 2026-08-27
---

## What was observed

Chasing ELITEA-1790 (#1811) I checked whether the test had ever passed on DEV CI.
Run **32999476644** (2026-08-26 18:23Z) reported the `dev-stable - skills` job as
**success** — but its log reads:

```
tests/ui/skills/test_agent_max_five_skills_limit.py::TestAgentMaxFiveSkillsLimit::test_max_five_skills_attach_limit SKIPPEDLogin failed:
```

The job was green because the test **never ran**. Had I taken the green at face value
I would have concluded the failure was intermittent and mis-triaged the whole case.

## The rule

**A green `dev-stable` job is not evidence a specific test passed.** When a CI result is
load-bearing for a verdict, pull the job log and grep for the node id plus its
`PASSED|FAILED|SKIPPED` verdict:

```bash
env -u GITHUB_TOKEN gh run view --repo EliteaAI/elitea-testing-public --job <id> --log \
  | grep -E "<test_name> (PASSED|FAILED|SKIPPED)"
```

A run on a feature branch is also not a `main` datapoint — check `headBranch`.

## Standing concern (flagged, not filed)

Auth failure silently degrading to SKIP is a green-masking pattern in the harness
itself: an environment-wide login outage would report a fully green suite. Worth a
`question` card if it recurs.
