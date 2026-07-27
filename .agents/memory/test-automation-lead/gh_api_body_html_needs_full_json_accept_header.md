---
name: gh api body_html needs the full+json Accept header
description: "gh api repos/.../issues/comments/<id> --jq .body_html returns an empty/1-byte result by default — GitHub only includes body_html when the request sends Accept: application/vnd.github.v3.full+json; without it, the commit-link-anchor verification technique silently 'confirms' zero links even when real links exist"
type: feedback
---

## What happened (#268/ELITEA-1846, 2026-07-20)

Verifying the closure record's `EliteaAI/EliteaUI@<sha>` commit citations
rendered as real clickable cross-repo links (the established technique from
`closure_record_sha_present_but_not_a_link_still_fails.md` and several
control-audit entries) initially came back with **zero** `commit-link`
anchors found — which would have read as a hard FAIL on the closure record's
own citations. The body_html field itself was empty (`wc -c` → 1 byte,
i.e. just a `null` from the default `gh api` mediatype).

## The fix

`gh api repos/<owner>/<repo>/issues/comments/<id>` alone returns the default
JSON shape, which does NOT include `body_html`/`body_text` — only `body`
(raw markdown). To get the rendered HTML GitHub actually served, add the
explicit Accept header:

```bash
gh api repos/<owner>/<repo>/issues/comments/<id> \
  -H "Accept: application/vnd.github.v3.full+json" \
  --jq '.body_html'
```

Without it, `--jq '.body_html'` on the plain response silently returns
`null` (prints as nothing / a lone newline) — indistinguishable at a glance
from "genuinely zero links rendered," which is the dangerous part: a
default-mediatype check that finds 0 anchors looks exactly like a real
FAIL. Always check `wc -c` on the fetched HTML (or eyeball that it's a
real multi-KB HTML blob) before concluding "no commit-link anchors" — a
suspiciously empty/tiny result means the request itself was wrong, not
that the citations are broken.

## Generalizes to

Any `gh api` read that expects `body_html`/`body_text` (issue bodies, PR
bodies, comments, releases) needs this same explicit `full+json` Accept
header — the tool's default output omits both fields.
