---
name: Escalating a sanctioned-RED product defect to elitea_issues in factory mode — the human comment lives on the BUG card, not the FIX card
description: A human "place the product bug in elitea_issues" steer on the linked `bug` issue is the explicit file-app-bug opt-in; the mechanics (issue type via GraphQL w/ feature header, milestone by name, ELITEA Board Status "Bugs" option 22b71710, auto-add lag) fit inside one null-delta FIX-card session
type: procedure
aliases: [file-app-bug factory, elitea_issues escalation, ELITEA Board Bugs status, issue type Bug graphql, #6627]
tags: [area/tracker, area/escalation, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---

## What happened (#2294, 20th [FIX] off ELITEA-1899 / #2055)

The steer that mattered was NOT on the dispatched card. breilian commented on **#2055** (the
`bug` issue the FIX card references): *"Place product bug in elitea_issues. Milestone R-2.0.7.
Status: Bugs. Check for existing duplicates." + "Approved to proceed."* That is exactly the
explicit ask `.agents/profile.md` § Escalation path and `file-app-bug`'s GUARD require — so the
"read comments on referenced question/bug issues newer than your last work-log" rule is what
turned a routine null-delta disposition into a two-deliverable session. Result:
EliteaAI/elitea_issues#6627.

## Mechanics that worked first try (elitea_issues)

```bash
env -u GITHUB_TOKEN gh issue create --repo EliteaAI/elitea_issues --title '[BUG] …' \
  --body-file /tmp/body.md --label ai_created --label bug-env:DEV --label feat:agents \
  --milestone R-2.0.7                                   # milestone by NAME works
# issue type = Bug (org type id IT_kwDOECVEvc4B6uMm) — needs the feature header:
gh api graphql --header 'GraphQL-Features: issue_types' -F id=$ISSUE_NODE_ID \
  -f query='mutation($id:ID!){ updateIssue(input:{id:$id, issueTypeId:"IT_kwDOECVEvc4B6uMm"}){ issue{ issueType{name} } } }'
```

- **ELITEA Board = project #1** (`PVT_kwDOECVEvc4BTt77`), Status field `PVTSSF_lADOECVEvc4BTt77zhA6-xM`;
  option **Bugs = `22b71710`** (To Do `5d242908`, Reproduction `b8e572f6`, In Progress `9279332c`).
  Read options via `node(id:"<field id>")` GraphQL — 1 point, never `gh project field-list`.
- New elitea_issues issues **auto-add to project #1 as "To Do"** within ~10 s; poll the issue's
  `projectItems` (1 point) and then `item-edit` — do NOT `item-add` unless the poll finds nothing.
- Labels agent may derive: `ai_created`, `bug-env:DEV`, `feat:<area>`. `bug-area:*` /
  `current-release-regression` / `client-reported-bug` are human-only — leave unset and SAY so in
  the back-link so the human can add them.
- Dedup: `gh issue list --repo EliteaAI/elitea_issues --state all --search "<kw>"` ×≤5 keywords;
  name the closest siblings in the body's Dedup section even when they are not dupes.

## Back-link shape

Comment `APPLICATION BUG CONFIRMED — filed as EliteaAI/elitea_issues#N _<title>_` on the
originating `bug` issue (#2055), move ITS board-#9 card → `ReportedBugs` (`7ab41d6b`). Never add
the elitea_issues issue to board #9. The FIX card itself still gets the normal null-delta closure
record + `duplicate` + `Ready`.

## Evidence reuse

The `evidence` release screenshots already embedded on the internal bug are public URLs — reuse
them verbatim in the elitea_issues body; the gate's own failure screenshot is the list page at
test end, useless for a header defect.

Related: [[post_promotion_fix_card_means_intake_gap_not_promotion_gap]] ·
[[the_devenv_plugin_is_the_factory_safe_dev_gate]] · [[a_null_delta_card_still_owes_a_full_gate]]
