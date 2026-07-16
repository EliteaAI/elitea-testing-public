---
name: EliteaUI testid commit-message format
description: EliteaUI's husky/commitlint pre-commit hook requires the literal [EL-NNNN] ticket-prefix format on every commit subject — NOT [ELITEA-NNNN]; use EL-0000 for TMS-only work with the real TMS id in parens
type: feedback
---

When committing a `data-testid` addition to `EliteaUI/src` on `automation/testids`
(e.g. via the `add-data-testid` skill), the repo's husky `commit-msg` hook runs
commitlint and **rejects** a subject that doesn't start with `[EL-NNNN]`.

- `test: [ELITEA-1881] add data-testid for ...` → **REJECTED**
  (`subject must contain ticket number - [EL-XXXX]`)
- `test: [EL-0000] add data-testid for ... (ELITEA-1881)` → **ACCEPTED**

`EL-NNNN` is the Jira/EliteaUI-internal ticket key convention (e.g. `EL-1737`,
`EL-1893`). This project's automation work is tracked by TMS case IDs
(`ELITEA-NNNN`), which have no EliteaUI-side Jira ticket — the established
precedent (confirmed via `git log --oneline | grep 'test:'` on
`automation/testids`) is to use the placeholder `EL-0000` and put the real TMS
id in parens at the end of the subject, e.g.:

```
test: [EL-0000] add data-testid for LLM model selector menu options (ELITEA-1881)
```

Prior art: `558160a6 test: [EL-0000] add data-testid to agent/card icon <img> elements (ELITEA-1899)`,
`6bb6a23c test: [EL-0000] add data-testid for agent icon picker flow (ELITEA-1899)`.

Check `git log --oneline -20` on `automation/testids` before the first commit
attempt to confirm this convention still holds — don't rediscover it via a
failed commit every time.
