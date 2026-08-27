---
name: Build with AI suggested-resources has no display cap
description: ResourceSuggestions.jsx renders all items unconditionally, no .slice(0,5) anywhere — filed #1317
type: feedback
---

## What

`../EliteaUI/src/[fsd]/features/agent/ui/generate-agent-modal/ResourceSuggestions.jsx`
(shared by all five "Suggested {Category}:" sections in the "Build with AI" agent
draft review form — Toolkits/MCP/Pipelines/Agents/Skills) renders every item in
`items.map(...)` unconditionally. No `.slice(0, 5)` or count guard exists anywhere
in that component, `GenerateAgentReviewForm.jsx`, or `GenerateAgentModal.jsx`
(confirmed by grepping all three for `slice|MAX_|limit|cap` — only unrelated
`MAX_*` constants for name/description/welcome-message/conversation-starters).

## How it was live-verified (ELITEA-1910 analysis, 2026-08-08)

Wrote a throwaway scratch pytest test using the SAME sanctioned
`GenerateEntityModalPageBase.mock_generate_success()` / `page.route()` technique
ELITEA-1907/1915 already use in `test_agent_build_with_ai.py`, mocked a 7-item
`suggested_skills` payload, ran it headless against the real app: **all 7 cards
rendered**, not 5. Deleted the scratch file after use (not committed) — the real
coverage lives in the AFS's directed implementation (a sibling test method with a
`.slice`-style soft-assert + `# Known defect: #1317`).

## Why this matters for future cases in this family

- If a TMS case asserts a cap/limit on any "Suggested {Category}" section count
  (any of the 5 categories, not just Skills — one shared component, one root
  cause), the same gap applies. Don't re-derive from scratch — cite `#1317`.
- **Real live suggestion counts cannot be reliably driven past ~2** per category
  (LLM relevance-matching against project inventory, confirmed across ELITEA-1907's
  and ELITEA-1911's own precondition audits). Testing any count/cap boundary on
  this surface needs the mocking technique, not live fixture creation — don't burn
  effort trying to coax >5 real Skills/Toolkits/etc. into suggestion relevance.
- The backend's response schema for `generate_application_draft` is undocumented
  in the OpenAPI spec (`https://dev.elitea.ai/shared/openapi/?all=true` — note: NO
  `/api/v2` prefix on that path, unlike most other endpoints; `/api/v2/shared/openapi/`
  404s) — whether the backend itself ever sends >5 suggestions is unverifiable from
  this repo. The bug is filed strictly as a frontend gap (no display-side defense),
  not a claim about backend behavior.

## AFS

`test-specs/agents/lextend_build-with-ai-suggested-skills-section-shown-with-up-to-5-skills_ELITEA-1910.md`
