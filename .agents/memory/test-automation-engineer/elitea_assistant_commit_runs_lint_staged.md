---
name: elitea_assistant commit runs lint-staged (prettier + eslint) and stashes your tree
description: Committing testids in ../elitea_assistant triggers husky/lint-staged; the "Backing up original state in git stash" line is normal, not a lost-work incident
type: project
aliases: [elitea_assistant lint-staged, connected repo commit stash, assistant testid commit]
tags: [area/support-assistant, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## What happens

`git commit` in the connected repo `../elitea_assistant` (branch `automation/testids`)
runs husky + lint-staged. Output looks like this and is **expected**:

```
[COMPLETED] Backed up original state in git stash (<sha>)
[STARTED] prettier --write / eslint --fix
[COMPLETED] Applying modifications from tasks...
```

Two consequences worth knowing before you panic or "fix" anything:

1. **The stash is lint-staged's own mechanism.** It parks *unstaged* changes, runs the
   formatters on the staged files, then restores. Verified 2026-08-22 (ELITEA-2419): the
   repo's four modified `dist/*` build artifacts — which were NOT mine — were still
   modified after the commit. Do not `git stash pop` or clean anything in response.
2. **Your staged JSX may be reformatted in the commit.** Write it prettier-shaped
   (2-space indent, single quotes, JSX props one-per-line once the line is long) and the
   commit content will match what you wrote. Always `git show HEAD -- <file>` afterwards
   rather than trusting your pre-commit diff.

EliteaUI (`../EliteaUI`) has no such hook — this is specific to the connected assistant repo.

Related: [[support_assistant_widget_handles]]
