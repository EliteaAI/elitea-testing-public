---
name: file-app-bug
description: File a CONFIRMED Elitea application bug into EliteaAI/elitea_issues — dedup, apply the label decision tree, create the issue, and back-link it to board #9 and the originating test-repo issue. ATTENDED + EXPLICITLY-REQUESTED ONLY — never runs autonomously and never files without a human asking. Use only after a human has reproduced the bug on DEV and explicitly asked to file it upstream. Does not reproduce or classify (those are human steps).
allowed-tools:
  - Bash
  - Skill
  - AskUserQuestion
---

# File an application bug (elitea_issues)

<GUARD — read first>
**This skill runs ONLY when the user explicitly asks to file an application bug.**
It is never autonomous, never a silent follow-on from reproduction, and is never
invoked by a factory loop. If you reached here from a reproduction that came back
`repro:confirmed`, STOP and surface the option — do not file until the user says
"file it" (or equivalent). `EliteaAI/elitea_issues` is an externally-visible tracker
the dev team reads; nothing lands there un-asked. This is the operator's standing
guardrail (`.agents/profile.md` § Bug filing).
</GUARD>

## Preconditions (all human-owned; verify, do not perform)

1. The bug was **reproduced on DEV** (`dev.elitea.ai`), verdict `repro:confirmed`
   (via `reproduce-elitea-bug`). Localhost-only ⇒ do not file.
2. A human **classified** it as an application bug (not test-drift / automation-drift).
3. A human **explicitly asked** to file it.

Reproduction and classification are NOT this skill's job. It takes over at the
mechanical steps below.

## Step 1 — Deduplicate against elitea_issues

Extract search terms (feature/component, symptom keyword, UI area). Run **≤3**
real-time list/search queries — identity-prefixed:

```bash
env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea_issues \
  --search '<keyword-phrase> type:Bug' --state open --limit 10 \
  --json number,title,url,createdAt,labels
```

Deduplicate by issue number, score by keyword overlap, keep top 5. Present them as
a numbered list (title · labels · URL) and ask with `AskUserQuestion`:
**Duplicate** / **Different** / **Not sure**.
- "Not sure" → show the top candidate's first ~50 body lines, ask once more.
- Second "Not sure" → treat as `no_duplicate`, proceed.
- `gh` API error → log it, skip dedup, proceed as `no_duplicate`.

**Outcome:** `duplicate:<N>` → skip to Step 4 (duplicate back-link). Else → Step 2.

## Step 2 — Label decision tree

Ask in order (`AskUserQuestion` unless noted). Only labels a human confirms, or the
agent can honestly derive, are applied — never guess a human-only fact.

| # | Question | Label |
|---|---|---|
| 1.1 | Client-reported? (Yes → skip to 1.4) | `client-reported-bug` |
| 1.2 | Current-release scope? | `bug-area:current-release-scope` \| `bug-area:not-current-release-scope` |
| 1.2a | Parent issue number? *(plain-text prompt; only if 1.2 = Yes)* | stored as `parent_issue` |
| 1.3 | Release-scope regression? *(only if 1.2 = Yes)* | `current-release-regression` |
| 1.4 | Highest env reproducible? | `bug-env:DEV` \| `bug-env:STAGE` \| `bug-env:NEXT` |
| 1.5 | Additional labels? *(plain-text, optional)* | free-form appended |

- Env → label map: `dev.elitea.ai` = DEV, `stage.elitea.ai` = STAGE,
  `next.elitea.ai` = NEXT. `bug-env:DEV` is the floor for anything filed
  (it reproduced on DEV per the precondition).
- **Feature area:** add the matching `feat:*` label the agent derives from the bug
  (`feat:agents`, `feat:chat`, `feat:artifacts`, …) — confirm with the human.
- **Provenance:** add `ai_created` (this issue was AI-authored via the factory).
- Parent-issue input validated: bare integer / full URL / `none`; re-prompt up to
  3×, then `null`.
- Show the full label set + parent summary before proceeding.

## Step 3 — File the issue

Render the body in the `issue-tracking` skill's Bug Report shape, with the Elitea
Environment line (`localhost-only | DEV | both` + DEV-verified: yes). Embed evidence
via `embed-evidence` (never a bare local path). **Show the rendered issue to the
human and get approval**, then create it — identity-prefixed, in elitea_issues, as
issue type **Bug**:

```bash
env -u GITHUB_TOKEN gh issue create --repo EliteaAI/elitea_issues \
  --title '[BUG] <concise title>' --body-file <rendered.md> \
  --label ai_created --label bug-env:DEV --label 'feat:<area>' <...other confirmed labels>
# then set issue type = Bug (org issue type) — via gh --type if supported, else the
# GraphQL updateIssue mutation. The issue-tracking skill owns the create mechanics.
```

Capture the new issue number + URL for Step 4.

## Step 4 — Back-link

**New filing (`no_duplicate`):**
1. Add to board #9: `env -u GITHUB_TOKEN gh project item-add 9 --owner EliteaAI --url <new-issue-url>`
2. Comment on the originating `elitea-testing-public` issue (identity-prefixed):
   > **APPLICATION BUG CONFIRMED** — filed as EliteaAI/elitea_issues#N _<title>_
3. Move the originating card → **`ReportedBug`** (the renamed Reproduce column).

**Duplicate (`duplicate:<N>`):**
- Comment on the originating issue (identity-prefixed):
  > **APPLICATION BUG CONFIRMED** — already tracked: EliteaAI/elitea_issues#N _<title>_
- Move the originating card → `ReportedBug`.

> Cross-repo references render as links only in the full `owner/repo#N` /
> `owner/repo@sha` form written as PLAIN TEXT (never in backticks). Same-repo refs
> stay bare `#N`. See `.agents/workflow.md` § Closure record.

## Notes

- **Composes** `embed-evidence` (screenshots) + `issue-tracking` (create mechanics
  + Bug Report template shape). The dedup + label logic is **inlined here** because
  the org-level `deduplicate-defect` / `label-bug` / `collect-bug-details` skills do
  not exist in reach; if they ever ship, extract Steps 1–2 to reference them.
- Every tracker/board write is `env -u GITHUB_TOKEN gh …` — the keyring account,
  never the shared token (`.agents/profile.md` § Issue tracker, identity rule).
