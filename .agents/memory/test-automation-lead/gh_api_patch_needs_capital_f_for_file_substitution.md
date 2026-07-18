---
name: gh api PATCH needs capital -F for @file substitution
description: "gh api -X PATCH -f body=@file.md does NOT read the file — only -F/--field (capital) does @file substitution; lowercase -f/--raw-field always treats @... as a literal string, silently posting the filename itself as the body"
type: feedback
---

## What happened (control-audit, issue #166, ELITEA-1947, 2026-07-18)

Tried to append a standing-watch section to an already-posted verdict comment:

```bash
gh api repos/.../issues/comments/<id> -X PATCH -f body=@/tmp/watch_166.md
```

This returned HTTP 200 and looked like it worked. The comment's body was actually set
to the literal 20-character string `@/tmp/watch_166.md` — not the file's contents.
Caught immediately by the mandatory read-back (`gh api .../comments/<id> --jq '.body'`),
which is exactly the discipline `closure_record_broken_body_file_substitution.md`
already prescribes for posted comments — but that entry is about a *different* root
cause (an unexpanded `@file` reference inside a rendered comment BODY, from
`gh issue comment --body-file` context). This one is about the flag itself.

## Root cause

`gh api` has two distinct field flags, and only one does file substitution:

- `-F` / `--field` (capital) — **typed** parameter; if the value starts with `@`, the
  rest is read as a filename and the file's contents become the value.
- `-f` / `--raw-field` (lowercase) — **string** parameter; `@...` is never special-
  cased, it is always sent as a literal string.

`gh issue comment --body-file <path>` (a different, higher-level command) reads the
file directly and has no `@`-prefix requirement at all — don't confuse its calling
convention with `gh api`'s.

## Rule going forward

For any `gh api` call that needs to post file contents as a field value (editing a
comment body via `PATCH`, `POST`ing a new comment via the raw API instead of
`gh issue comment`, etc.), use `-F field=@path`, never `-f field=@path`. And regardless
of which flag was used, always read the write back before trusting it landed — the
call returning 200 proves the request succeeded, not that the intended content is what
got stored.
