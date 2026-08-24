---
name: provenance_reverse_error_bulk_promotion_makes_not_on_main_false
description: A PROVENANCE row can be wrong in the OTHER direction — "not yet on main" goes stale when a bulk testid promotion lands; verify both directions
type: feedback
aliases: [provenance not on main stale, bulk testid promotion, promotability row wrong direction]
tags: [area/testids, type/review-trap]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

Every prior provenance lesson here guards the **false-positive** direction —
an AFS claiming `on-main ✓` for a testid that only exists on
`automation/testids` (see [[confirmed_live_is_not_on_main_provenance_check]]).
The **reverse** error is just as damaging and nobody checks for it:

> An AFS row that says **"on-`automation/testids` only — NOT yet on `main`"**
> goes stale the moment a human runs a bulk promotion.

Caught reviewing ELITEA-1936 (PR #1724, 2026-08-24). The AFS marked
`toolkit-connection-status` and `toolkit-connection-login-button` as
testids-only, "human cherry-pick of EliteaAI/EliteaUI@a467c0ac pending", and
warned the spec would be red on any deployed env because of them. Both had
been on `origin/main` since **2026-08-12**, promoted twelve days earlier by
`bf4a13ad` — *"test: promote 400 accumulated data-testids to main (batch
2026-08-11) (#753)"*. A single bulk promotion can invalidate every
"not-on-main" row written before it, across many AFS files at once.

## Consequence

The lead copies the promotability row into the closure record and the card
sits in `Ready` "awaiting a human cherry-pick" that already happened — the
#19 false-row failure, mirrored. It also misdirects: the real deployed-env
blocker on ELITEA-1936 was a *different*, newly added testid
(`toolkit-connection-status-icon`, @55dc4f66), which the wrong rows buried.

## What to do as reviewer

Run the two-stage grep on **both** refs for **every** handle the case uses —
never spot-check only the rows the AFS flags as risky, and never trust a
"NOT on main" claim any more than an "on-main ✓" one:

```bash
cd ../EliteaUI && git fetch origin
for t in <every testid the diff uses>; do
  printf "%-34s main:%-4s testids:%s\n" "$t" \
    "$(git grep -- "$t" origin/main -- src/ | grep -qiE '(data-testid|testid[[:space:]]*[:=])' && echo YES || echo no)" \
    "$(git grep -- "$t" origin/automation/testids -- src/ | grep -qiE '(data-testid|testid[[:space:]]*[:=])' && echo YES || echo no)"
done
git log -1 --format='%h %ad %s' --date=short -S'<testid>' origin/main -- src/   # when it landed
```

A `no/no` result is usually a **runtime-composed** testid, not a missing one —
confirm with the composed pattern before reporting it
([[testid_provenance_runtime_composed]]): `toolkit-type-card-mcp` and
`toolkit-field-url-input` both read `no/no` on this PR and both are on `main`
as `` `toolkit-type-card-${itemKey}` `` / `` `toolkit-field-${k}-input` ``.

Related: [[confirmed_live_is_not_on_main_provenance_check]] ·
[[testid_provenance_runtime_composed]] ·
[[agent_hub_catalog_testid_provenance_was_wrong_in_prior_afs]]
