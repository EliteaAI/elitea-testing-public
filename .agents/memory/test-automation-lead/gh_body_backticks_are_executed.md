---
name: Backticks in a gh --body string are executed, not quoted
description: zsh command-substitutes every backtick span in `gh issue comment --body "..."` — closure records and dispatch comments come out with code spans silently ERASED
type: feedback
aliases: [gh comment backticks, closure record mangled, command substitution in issue body, code spans disappeared, gh api PATCH body file]
tags: [area/tracker, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

Every tracker comment this role writes is dense with `code spans` — testids,
node ids, refs, commands. Written as:

```bash
env -u GITHUB_TOKEN gh issue comment 2066 --body "… (`cd ../EliteaUI && git fetch origin` first, `origin/main` @ `9ef77d26`) …"
```

the shell **runs** what is inside the backticks and substitutes the output.
`cd ../EliteaUI && git fetch origin` executed; `origin/main` failed with
`no such file or directory`. The posted line read:

> **Testid promotability — verified, not copied** ( first,  @ `9ef77d26`):

The commands are gone, replaced by nothing. **It is silent** — `gh` returns the
comment URL, exit code 0, and the only clue is one stray stderr line scrolled
above the URL. A closure record whose verification block was erased still reads
plausibly, which is exactly the failure mode the closure-record rules exist to
prevent.

Escaping (`\``) works and is what saves most of the body — but one missed span
is enough, and long bodies make a miss certain.

## The move

**Write the body to a file, pass the file.**

```bash
cat > /tmp/body.md <<'EOF'          # quoted heredoc — NO substitution at all
… `anything` `you` `like` …
EOF
env -u GITHUB_TOKEN gh issue comment 2066 --body-file /tmp/body.md
```

The quoted `'EOF'` is the load-bearing part: unquoted, the heredoc substitutes
too.

**To repair one already posted** (edit, don't re-post — a duplicate closure
record is worse than a damaged one):

```bash
env -u GITHUB_TOKEN gh api repos/<owner>/<repo>/issues/comments/<id> --jq .body > /tmp/cr.md
# fix /tmp/cr.md with python3/sed
env -u GITHUB_TOKEN gh api -X PATCH repos/<owner>/<repo>/issues/comments/<id> -F body=@/tmp/cr.md --jq .html_url
```

`-F body=@file` reads the file as the field value. Read the comment back
afterwards — the repair is only as good as the readback.

## Always read back a long tracker write

Not just after a suspected problem. The damage class is *deletion*, and deleted
text does not announce itself. One `gh api …/comments/<id> --jq .body | grep`
on the lines you care about costs one call.

Related: [[closure_record_discipline]] · [[closure_record_promotability_must_be_pasted_even_if_true]]
