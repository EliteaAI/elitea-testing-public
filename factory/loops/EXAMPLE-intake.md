# Intake — bring un-automated cases onto the board (cardless)

Your mission is to FILE cards right now, single purpose session.
You bring new tickets from backlog of test cases needed to be automated. 
First time you run - bring all test cases as tasks. After that just pull newlly added ones. 
execution_type: automated doesn't mean it's automated - in that folder all cases planned for automation and some of them may be automated but it means it need to have a task on our board, it may be data issue. The only judgement is actually do we have such task in our backlog or not.

**Source**: test cases as `.md` files in
`EliteaAI/onetest-ai-tm-Elitea`, path `tests/automated-full-regression-ui/`
(read via `gh api repos/EliteaAI/onetest-ai-tm-Elitea/contents/...` — it is a
private repo, your gh auth has access). Each file starts with YAML metadata:
`id`, `title`, `module`, `status`, `execution_type`, `automation_test_id`, …

Mind that cases from "automated-full-regression-ui" are our backlog of test cases needed to be automated.

**A case counts as ALREADY AUTOMATED** only when all three hold:
`execution_type: automated` AND `status: ready` AND `automation_test_id` is
non-empty. Exclude those. A case with contradictory metadata (e.g.
`automation_test_id` set but `status: draft`) is NOT guessed either way —
list it in your final report instead of filing or skipping silently.

**Dedup before filing.** NEVER use `--search` — the search index lags and
already produced duplicate #17/#18. Pull the full list once and grep it:
`env -u GITHUB_TOKEN gh issue list --state all --limit 200 --json title`
— any title containing `[ELITEA-<id>]` (open or closed) means skip. The canonical title format is the dedup key:

    [Automate][ELITEA-1735][module] Interact with Skills from Agent

**File** (every tracker write prefixed `env -u GITHUB_TOKEN` — identity
rule, `.agents/profile.md` § Issue tracker) one issue per new case, that exact title
format, body naming the source file path and the case metadata. Do NOT set
any board status and do NOT touch existing cards — auto-add places new
issues in the board's entry column; a human approves by dragging. 

**Questions**: no card exists to park. If something needs a human (access
denied, ambiguous conventions), file it as an issue labelled `question`,
skip the affected cases this run, continue with the rest, and note it in
your report.

**Scratch files: always `mktemp`** — never fixed `/tmp` names. Other agent
sessions share that namespace; a fixed name gets overwritten under you
mid-write (live finding: two intake sessions swapped each other's issue-body
files and one read the other's narrative as a prompt injection).

End every run with a short report: filed N (list), skipped M as automated,
K as duplicates, plus any contradictory-metadata cases.
File ONE github issue summarizing the sync and moove it to Done(just for tracking purposes).
