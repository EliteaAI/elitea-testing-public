---
name: On a fix round, diff the additive-only grep against the batch trunk, not the working tree
description: git diff <file> | grep '^-[^-]' after a fix round will show your OWN prior commit's lines as removed if you replaced them — that's fine (unmerged, your own code), but it looks identical to a real regression. Diff against the batch trunk (git diff <trunk>...HEAD -- <file>) to get the check that actually matters — is the MERGED/shared code still untouched.
type: feedback
---

## The trap

The additive-only check (`.agents/role-overrides.md` / skill Hard Rule 3) exists
to catch modification of a shared method's body that MERGED callers depend on.
The mechanical form is `git diff <file> | grep -E '^-[^-]' | head` → expect empty.

On a **fix round** (implementer revises its own PR after reviewer feedback),
running that grep against the **working tree vs. the last commit** will show a
`-` line for anything you're replacing from your OWN prior commit on this same
branch — e.g. swapping `create_response = modal.click_approve_and_wait_for_agent_created()`
for a new `with modal.expect_create_response() as create_info: ...` block. That
`-` line is completely fine: it's YOUR unmerged code from THIS PR, not a shared
method's merged body. But the grep output looks identical to a real violation,
and pausing to figure out "wait, is this a regression?" burns a turn every time.

## The fix

Scope the check to what it's actually protecting: diff against the **batch
trunk** (or `automation/base` outside a batch), not the working tree:

```bash
git --no-pager diff <batch-trunk-or-base>...HEAD -- <file> | grep -E '^-[^-]'
```

Empty output here means "nothing that existed BEFORE my branch cut got
removed" — the real additive-only guarantee. A `-` line against the working
tree during a fix round is expected noise; a `-` line against the trunk is the
signal that actually matters.

## When this applies

Any fix round that edits a helper/page-object method you yourself added
earlier in the SAME PR (not a pre-existing shared one). If you're editing a
genuinely pre-existing shared method (≥3 merged callers), the working-tree
diff and the trunk diff say the same thing — no ambiguity, this trap doesn't
apply.
