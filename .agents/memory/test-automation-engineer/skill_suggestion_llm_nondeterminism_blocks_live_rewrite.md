---
name: Skill-suggestion LLM nondeterminism blocks live rewrite
description: Build-with-AI's suggested_skills array is empty on ~1/6 live calls for the same prompt/project — don't build a deterministic test on its presence
type: feedback
---

## What happened

ELITEA-1910 fidelity rework (`test_suggested_skills_section_capped_at_5_skills`,
`automation/tests/ui/agents/test_agent_build_with_ai.py`): attempted to replace
`mock_generate_success(SUGGESTED_SKILLS_CAP_PROBE_PAYLOAD)` with a live
`click_generate_and_wait_for_response()` call, per the fidelity rework brief.

`SUGGESTED_SKILLS_CAP_PROMPT_TEXT` = `"An agent that uses several specialized
skills to manage repository workflows"`, against project 399 (`Private`,
localhost dev backend). 6 consecutive live attempts, same prompt, same
project:

| Attempt | `suggested_skills` count |
|---|---|
| 1 | 3 |
| 2 | 3 |
| 3 | 3 |
| 4 | **0 (empty)** |
| 5 | 3 |
| 6 | 3 |

5/6 non-empty, 1/6 empty — genuine LLM-suggestion nondeterminism, not a setup
mistake or infra flake (confirmed via the actual assertion error: `response_body
.get("suggested_skills")` was falsy). This is exactly the risk ELITEA-1910's own
AFS Preconditions predicted when it originally chose mocking ("live-inventory
suggestion counts are LLM-relevance-driven and not reliably controllable").

## Why this matters

Any live-rewrite attempt on a Build-with-AI (or similar suggestion-engine)
test whose Pass criteria depend on a suggestion CATEGORY being non-empty is
NOT safe to treat as "3 successful manual tries = stable enough to ship."
The category can — and did — go empty on an unpredictable later call, which
means:
- It will NOT pass the deterministic N×-green merge gate reliably.
- It doesn't qualify as a "sanctioned RED" defect either (not deterministic,
  not single-cause — it's inherent LLM variance, not a code defect).
- The only two honest paths are: (a) route it back BLOCKED (what happened
  here — mock restored, human decides), or (b) seed enough real Skill
  fixtures live (à la ELITEA-1911's `github_relevant_skills` fixture) so the
  suggestion engine reliably has material to work with, which trades
  determinism for fixture-creation cost.

## What to do differently

Before attempting a live rewrite of ANY test whose assertions depend on a
`suggested_*` category being non-empty (toolkit/mcp/pipeline/agent/skill),
run the live generate call 5-6 times FIRST (not 2-3) to check the empty-rate
before writing the assertions — 2-3 successes can look deceptively stable.
If any run comes back empty, treat that as decisive per the rework brief's
own instruction: stop, don't average it away, don't retry-until-non-empty
inside the test (that's fabricating a workaround). Report the split
(non-empty/empty counts) so the human deciding has real data, not "it didn't
work once."
