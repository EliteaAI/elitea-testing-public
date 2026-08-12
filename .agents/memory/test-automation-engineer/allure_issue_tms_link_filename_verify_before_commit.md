---
name: allure.issue TMS link filename — verify before commit, don't hand-type
description: An @allure.issue TMS case URL typo (dropped a word from the filename) 404'd and survived one implementer round unaddressed; verify + add a guard test.
type: feedback
---

## What happened (ELITEA-2609, PR #1475)

The `@allure.issue(...)` decorator on `test_skill_explicit_and_autonomous_
invocation_coexistence` (`automation/tests/ui/skills/test_skill_agent_interaction.py`)
pointed at `skills/ELITEA-2609_skill-explicit-autonomous-invocation-coexistence.md`
— hand-typed from the case title, missing the "and-" the real filename has:
`skills/ELITEA-2609_skill-explicit-and-autonomous-coexistence.md`. The link
404'd. Flagged by reviewer round 1, **not fixed in the first "fix round"
response** (no diff touched it) — cost a whole extra round.

## Fix + durable guard

1. **Never hand-type a TMS case filename into an `@allure.issue` URL.**
   Verify it exists first:
   ```bash
   env -u GITHUB_TOKEN gh api repos/EliteaAI/onetest-ai-tm-Elitea/contents/tests/automated-full-regression-ui/<feature>/<exact-filename>.md --jq '.name'
   ```
   or `ls ../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/<feature>/ | grep -i <id>`
   — the sibling clone is on disk (`.agents/architecture.md`), no network needed.
2. **When a reviewer flags this class of finding, grep the PR diff for the
   exact string before claiming it's fixed** — an "addressed" round with no
   line touching the decorator is indistinguishable from a skip, and the
   reviewer (correctly) treats it as one.
3. Added a standing regression guard:
   `automation/tests/unit/test_skill_agent_interaction_allure_issue_links.py`
   — parses every `@allure.issue` TMS URL in that spec via `ast` (handles
   adjacent-string-literal URL wrapping) and asserts the path resolves in
   the sibling `onetest-ai-tm-Elitea` clone. Pattern is copy-pasteable to
   any other spec file that accumulates multiple `@allure.issue` links.
