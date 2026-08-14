---
name: Closure record broken body-file substitution
description: A gh comment posted with a literal unexpanded file-reference string (e.g. "@/tmp/closure_body_final.txt") is a distinct closure-record failure mode from "bare done" — exit 0 on the gh call does not mean the intended content landed
type: feedback
---

## What happened

Issue #37 (ELITEA-1795 rework), 2026-07-15: the session's own daily-log
entry for that delivery narrates a fully-formed closure record ("posted
with a promotability table... self-caught a bare-link violation, fixed via
PATCH twice"). The actual comment that landed on the issue at that
timestamp is the literal 29-character string:

```
@/tmp/closure_body_final.txt
```

Some `gh issue comment` invocation used a form where the `@file` /
`--body-file` reference was passed as a literal `--body` string argument
(or similarly mismatched), instead of the flag that actually substitutes
file content. The command still exited 0 and a comment was posted — so
nothing in the session's own control flow signaled failure. The session's
memory log for that turn describes the *intended* final artifact, not the
artifact that actually reached GitHub.

## Why this matters for control-audit

This is worse than the already-known "bare ✅ done" anti-pattern
(`.agents/workflow.md` § Closure record) — that at least contains real,
if minimal, prose. A broken substitution posts something that looks like
noise/an accident, not a claim to evaluate — but a control audit reading
comments programmatically (or a human skimming fast) can miss that the
"real" closure record simply never happened, especially when a LATER
factory-dispatch banner comment immediately follows it and the broken
line scrolls out of casual view.

## The check

When auditing a closure record (or reading back any of your own posted
comments that used `--body-file`/`@file` interpolation), always read the
comment BACK via `gh issue view <n> --comments` or the REST API and
confirm its length/content is what you intended — never trust the CLI's
exit code alone. A comment body under ~50 characters that starts with `@`
and points at a path is a strong signal of exactly this failure.

## The fix going forward

- Prefer `gh issue comment <n> --body-file <path>` (the dedicated flag)
  over any manual `@`-prefix convention passed through `--body`.
- After posting a long/generated comment body, do one `gh issue view
  --comments` read-back before considering the closure record done —
  cheap insurance against a silent no-op.
