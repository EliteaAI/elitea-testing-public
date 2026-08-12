---
name: Closure record format violations can co-occur wholesale
description: a single closure record can abandon the artifact-table format entirely (free-form prose), backtick its one cross-repo commit reference into an inert non-link, AND narrate the promotability conclusion instead of pasting the per-testid table — all three at once, not as isolated slips
type: feedback
---

Prior audits (#105/#143/#160/#166/#175/#181/#197) each caught ONE item-4 gap
per record — usually a missing/backticked commit SHA on an otherwise-correct
table, or a narrated promotability line in an otherwise-correct table. The
#209/PR#635 audit (2026-07-19) found a record that failed all three
independently-logged shapes AT ONCE:

1. **No markdown artifact table at all** — the canon's `| Artifact | Where |
   State |` table was replaced wholesale by bold-header prose paragraphs
   (`**Merged:**`, `**Testids:**`, `**TMS back-written:**`, etc.). Every
   prior recurrence still HAD a table, just an incomplete/wrong cell in it.
   This is a step further: the format itself wasn't attempted.
2. **The one cross-repo commit reference present was backticked AND
   mis-composed** — `` `EliteaAI/EliteaUI@automation/testids` `` @
   `` `bf008838` `` (two disconnected backticked fragments — a branch ref
   plus a bare SHA — not the canon's single plain-text `owner/repo@<sha>`
   token). Confirmed via `body_html`: renders as two inert `<code>` spans,
   zero `<a href>`.
3. **Promotability section is pure narration** — no `for t in ...; do git
   grep ...; done` output pasted, just a prose conclusion (which happened
   to be true on independent re-verification, but narration is the risk
   factor the rule targets regardless).

Takeaway for judging future records: don't stop checking item 4 once you've
found ONE violation and confirmed the underlying facts are true — check the
table's existence, the link's clickability, AND the promotability paste
independently of each other. A record built by paraphrasing the template's
gist from memory (rather than copying the actual template text and filling
it in as a checklist) tends to drop several format requirements at once, not
just one. This is a strong argument for the closure-record-authoring step
to literally copy `.agents/workflow.md`'s fenced template block and fill in
the blanks, rather than free-composing "the same information" from
recollection.
