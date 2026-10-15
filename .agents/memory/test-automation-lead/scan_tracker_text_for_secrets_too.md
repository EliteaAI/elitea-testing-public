---
name: Secret-scan tracker text, not just git commits
description: scripts/scan-secrets.py is wired for pre-commit, but a subagent's dispatch report can quote a live credential in plain prose (e.g. "typed X / Y, got invalid") when documenting a failed DEV login attempt — and that text reaches GitHub issue comments on a PUBLIC repo before it ever reaches a commit. Run the same scan (or an ad-hoc grep for the known env values) against any comment body before posting it, not only before git commit.
type: feedback
---

## The trap

`sync-base-branches` Step 0b wires `python3 scripts/scan-secrets.py` as a pre-**commit**
gate. That's necessary but not sufficient: `elitea-testing-public` is public, and the
Issue tracker (`gh issue comment`) is a second, independent write surface the scanner
is never consulted for. A dispatched subagent diagnosing a DEV-auth failure will
naturally quote exactly what it typed and what came back — "typed `<username>` /
`<password>`, got `Invalid username or password`" — because that's the honest, useful
evidence a triage report should carry. If you relay that report verbatim into a
work-log comment (as this role routinely does), the literal credential value posts to
a public page before any `git commit` ever happens.

## The fix

Before posting ANY comment that quotes a subagent's auth-attempt output (login script
failures, CDP/browser credential tries, Bearer-token checks) — not just before
committing a file:

```bash
# cheap, no need to invoke the full scanner machinery if quoting ad-hoc text:
printf '%s' "$COMMENT_BODY" | grep -F -- "$(grep '^TEST_USER_EMAIL=\|^TEST_USER_PASSWORD=\|^ELITEA_API_TOKEN=' automation/.env.test | cut -d= -f2-)"
# any hit -> redact to a placeholder like <redacted-test-username> before posting
```

Or just read the subagent's own report text yourself for anything that looks like a
credential before relaying it — don't trust a Blocked/triage report to have scrubbed
itself; it's optimizing for diagnostic completeness, not secret hygiene.

**If a leak already posted:** `gh api repos/<owner>/<repo>/issues/comments/<id> -X PATCH
-f body="<redacted text>"` edits it in place (no need to delete + recreate, preserves
the thread). Sweep every comment on the current issue AND any sibling issue the same
dispatch commented on — one leak is rarely isolated to one comment. File a `question`
for a human to actually rotate the credential; editing the comment stops new exposure,
it doesn't un-expose what was already visible, and only a real rotation closes that.

**If it already reached a commit on a shared branch:** do NOT rewrite history
(rebase/force-push is banned on `automation/factory` — `.agents/workflow.md`). Report
it, let the credential rotation make it moot, and just make sure your OWN pending
write doesn't repeat it.

## Seen 1×

- #2408/#2405/#2435/#2437 (2026-10-15) — a qa-engineer subagent's `adjust-automated-test`
  blocked-report quoted the literal DEV test-user username+password while documenting
  a failed Keycloak login + a `+'0'`-suffix guess; relayed into 4 issue comments across
  3 issues before I ran the scanner against unrelated memory text and it flagged the
  same username, which is what caught it. Redacted all 4 comments via PATCH; filed #2437
  for the human rotation; found the username (not the password) also already baked into
  two older, already-pushed `automation/factory` commits from a prior session — left
  that alone per the no-rewrite-shared-history rule and noted it on #2437 instead.
