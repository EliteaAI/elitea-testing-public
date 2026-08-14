---
name: Closure record — shape and backing are checked independently of truth
description: A closure record fails on format and on missing artifacts even when every fact in it is true; copy the workflow.md template literally, cite an originating commit SHA for every testid (new, reused, or already on main), paste gate + promotability output, and read the posted comment back.
type: feedback
---

## Rule

**Copy `.agents/workflow.md` § Closure record's fenced template and fill blanks.**
Free-composing "the same information" from memory drops several requirements at
once. Content correctness earns no credit against format compliance — they are
separate checks, and a narrated-but-true claim FAILs.

Independently required, each its own check:

- The literal `| Artifact | Where | State |` table exists (not prose, not bullets).
- An explicit **AFS path** row — self-sufficient, even though the work-log mentioned it.
- A **Testids** row even when the answer is "none new".
- **Pasted** per-testid promotability output (the `printf` loop), not a conclusion.
- **Pasted** 3× merge-gate command+output, or at minimum 3 distinct timings.
- Cross-repo refs as plain text `EliteaAI/EliteaUI@<sha>` / `owner/repo#N` — never
  backticked, never bare `#N`, never inside a code fence. None of those render as
  links or create the backlink a human uses to find the cherry-pick.

**Every testid owes an originating commit SHA** — new, reused, or already fully on
`main`. "Reuses 6 testids from ELITEA-1922" is a FAIL. Resolve it:
`git log --oneline origin/main..origin/automation/testids -S"<testid>" -- src/`
(or `-S ... origin/main` when already promoted) — under a minute each. Never
reconstruct the source-case list from memory or copy it from the AFS: attribution
drifts (phantom deps ELITEA-1809, ELITEA-1824 both traced wrong).

## Mechanics that bite

- Grep the **whole posted comment**, not the table: bare `[^/]#[0-9]+`, unfilled
  `#…` placeholders, and "N things" prose vs the actual enumeration.
- **Read the comment back** (`gh issue view <n> --comments`). `gh` exits 0 on a
  literal `@/tmp/closure_body_final.txt` body. Use `--body-file`, never `@` in `--body`.
- Verifying rendering: fetch `body_html` with
  `-H "Accept: application/vnd.github.full+json"` (absent by default → silent
  null) and count `class="commit-link"`; a `EliteaUI@[0-9a-f]{7,}` grep on
  body_html false-negatives because GitHub splits the hash into a `<tt>`.
- Zero-testid case (third-party widget, no first-party JSX): confirm N/A with
  `git diff <merge-base>..<merged-sha> -- <touched files> | grep -c data-testid` == 0.
  Don't take the AFS's "permanent scope exception" narrative on faith.

## Seen 10×

- #31/PR#278 — bare `#526,#540,#545` in prose below the table (dead links); recurred INSIDE the table on #36.
- #37 — posted comment was the literal 29-char string `@/tmp/closure_body_final.txt`.
- #28/PR#206 — checklist asserted a reviewer grep; `pulls/206/reviews` = `[]`, no artifact anywhere.
- …plus 7 earlier occurrence(s) — full per-case detail in the source entries below.

See also: closure_record_bare_link_check_is_whole_comment.md ·
closure_record_broken_body_file_substitution.md ·
closure_record_claims_need_artifact_backing.md ·
closure_record_format_violations_can_co_occur.md ·
closure_record_must_paste_merge_gate_output.md ·
closure_record_narrative_can_fail_on_template_shape_alone.md ·
closure_record_promotability_must_be_pasted_even_if_true.md ·
closure_record_reused_testids_still_need_commit_shas.md ·
closure_record_sha_present_but_not_a_link_still_fails.md ·
no_testid_dependency_case_simplifies_closure.md
