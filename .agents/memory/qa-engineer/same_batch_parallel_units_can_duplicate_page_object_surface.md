---
name: Same-batch parallel units duplicate page-object surface with diverging contracts
description: Two open sibling PRs (#1464 ELITEA-2595/96/98, #1466 ELITEA-2597) both add IDENTICAL SkillDetailPage.publish_* field/method names from the same unmerged trunk base, with confirm_publish() returning int in one and Response in the other — a silent post-merge break, not a git conflict.
type: feedback
---

## What happened

ELITEA-2597's AFS assumed ELITEA-2595's `SkillDetailPage` Publish-wizard
page-object work (PR #1464) would already be merged onto the batch trunk
(`tests/batch-skills-remaining-w3`). Per the batch rule ("never target a
same-batch AFS that has not merged"), #1464 was still open/in a fix-round
when #1466 (ELITEA-2597) started, so the implementer correctly built the
`SkillDetailPage` Publish-wizard scaffolding FRESH from source
(`PublishWizardModal.jsx`/`usePublishSkill.hooks.js`) rather than depend on
#1464's unmerged diff — exactly per doctrine.

**But both PRs independently declared the SAME class-level fields
(`publish_menuitem`, `publish_version_name_input`, `publish_category_select`,
`publish_agree_checkbox`, `publish_continue_button`, `publish_confirm_button`,
`PUBLISH_CATEGORY_OPTION`) and the SAME methods
(`open_publish_wizard`, `fill_publish_preparation_step`,
`click_publish_continue`, `confirm_publish`) on the SAME `SkillDetailPage`
class**, inserted at DIFFERENT locations in the base file (after the Export
section in #1464, after the Fork section in #1466). Verified via
`git diff origin/tests/batch-skills-remaining-w3...origin/<branch>` on
BOTH branches independently.

Because the insertion points differ, a plain `git merge` of both PRs onto
the trunk produces **no textual conflict** — Python silently accepts the
duplicate class-body definitions, and the textually-LATER one wins (last
definition in file order overrides the earlier one for same-named
attributes/methods). This is invisible to the additive-only `git diff |
grep '^-[^-]'` check both PRs correctly ran (0 removals in each diff,
individually) — the check can't see a collision that only exists once BOTH
diffs are combined.

**The sharpest, functionally-breaking instance:** `confirm_publish()` has a
genuinely DIFFERENT return-type contract between the two PRs —
- #1464: `def confirm_publish(...) -> int:` returns `status` (int); its own
  tests do `publish_status = detail_page.confirm_publish(...); assert
  publish_status == 200`.
- #1466: `def confirm_publish(...):` returns the raw Playwright `Response`;
  its own tests do `publish_response = detail_page.confirm_publish();
  assert publish_response.status == 400; body = publish_response.json()`.

Whichever PR's definition ends up textually LAST in the merged file
silently wins for BOTH PRs' already-merged tests — the loser's tests break
at runtime (`'int' object has no attribute 'status'` or a confusing
`Response == 200 -> False` assertion failure), discovered only at the
batch hardening gate (no textual merge conflict, no CI on the trunk to
catch it earlier), and the failure message gives no hint it's a
cross-PR field/method collision.

## Why it happened

The "never target a same-batch AFS that has not merged" rule correctly
prevents building against unstable in-review code — but it does NOT by
itself prevent two independently-built same-batch units from BOTH adding
new page-object surface for the SAME shared underlying UI component
(`PublishWizardModal.jsx`, `entityLabel`-agnostic) to the SAME page-object
class. "Centralize selectors in the page object... a data-testid should
appear in exactly one file" (Hard Rule 3) is violated the moment both
land, but neither individual PR's diff can see the violation — it only
exists in the union of two open PRs against a common ancestor.

## What to do differently

- **When reviewing a PR that adds NEW page-object fields/methods for a
  shared UI component** (same JSX component, `entityLabel`-parametrized or
  otherwise reused across sibling entity types), check whether ANY OTHER
  open PR on the SAME batch trunk touches the SAME page-object class for
  the SAME component — `env -u GITHUB_TOKEN gh pr list --state open --json
  headRefName,baseRefName` filtered to the same `baseRefName`, then
  `git diff <trunk>...<sibling-branch> -- <same page object file>` and
  grep for overlapping field/method names. This is NOT caught by the
  additive-only `git diff | grep '^-[^-]'` check on either PR alone.
- **A genuine collision with DIFFERING contracts (not just duplicate but
  identical bodies) is a BLOCKING finding**, even though neither PR's own
  diff is individually wrong — flag it in `blocking[]`, not `findings[]`,
  because a plain sequential merge of both WILL silently break one of them
  post-merge with no textual conflict to catch it.
- **Recommend to the orchestrator**: reconcile at merge time — whichever
  PR merges second should be rebased to DROP its duplicate field/method
  block and reuse the already-merged one where the contract matches,
  updating only its own genuinely-new pieces; where the contract
  genuinely differs (like `confirm_publish()`'s int-vs-Response), pick the
  more capable one (Response — a superset, `.status` still works via
  attribute access... actually no, `int` has no `.status`, so the LOSING
  side's call sites need updating either way) and update the losing PR's
  test call sites to match.
