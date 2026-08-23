---
name: git show "$BRANCH:path" silently mangles the path under zsh
description: Quoting a ref+path as "$VAR:automation/..." makes zsh eat ":a" as a modifier — use the literal ref inline
type: feedback
aliases: [git show ref path, zsh modifier, ambiguous argument unknown revision, "$BR:automation"]
tags: [area/tooling, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

Reviewing a branch without checking it out means reading files with
`git show <ref>:<path>`. Putting the ref in a shell variable breaks under
**zsh** (this repo's shell):

```zsh
BR=tests/ELITEA-1968-1969-...
git show "$BR:automation/pages/secrets_page.py"
# fatal: ambiguous argument '<abs-path>utomation/pages/secrets_page.py':
#        unknown revision or path not in the working tree
```

zsh applies its **history/parameter modifier** `:a` (absolute path) to
`$BR`, so `:automation` is consumed as `:a` + `utomation`. Quoting does not
help — modifiers are applied inside double quotes. `${BR}:automation` is
also unsafe to rely on.

## What to do

**Write the ref literally inline** in the `git show` argument:

```bash
git show tests/ELITEA-1968-1969-credential-secret-password-toggle:automation/pages/secrets_page.py
```

Batch several of these into one Bash call rather than looping over a
variable. Loops over *testid strings* are fine — only the `<ref>:<path>`
colon is affected.

The symptom is distinctive: the error path is an **absolute** path with its
first character eaten (`...public/<branch>utomation/...`), which is exactly
what `:a` + a swallowed `a` produces.

Related: [[reviewer_mechanical_greps_must_run_from_repo_root]]
