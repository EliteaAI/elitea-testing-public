---
name: Agent Hub family — "Agent HUB" vs live "Catalog" naming drift
description: Every ELITEA-2350..2370+ case says "Agent HUB"; live product says "Catalog" everywhere — cite #1208, don't re-file
type: feedback
---

The TMS "Agent Hub" case family (ELITEA-2350 through at least ELITEA-2370,
~20 sibling cases filed as GitHub tracking issues #858-#878, module
`agent-hub`) all use case text calling the surface "Agent HUB" ("Navigate to
Agent HUB", "Welcome to Agent HUB" header, etc.).

The LIVE product calls it **"Catalog"** everywhere, consistently: sidebar nav
item text, browser `<title>` (`"ELITEA Catalog - {project}"`), and the page
heading (`data-testid="catalog-page-heading"` = "Welcome to ELITEA
Catalog!"). `AgentHub`/`/agents-hub` is only a legacy redirect source in
`EliteaUI/src/routes.js`, never a rendered label anywhere. This is stale
case text (reverse-masking guard applies — the product is internally
consistent, not wrong).

**Filed once, for ELITEA-2350:**
[EliteaAI/elitea-testing-public#1208](https://github.com/EliteaAI/elitea-testing-public/issues/1208).
The identical drift was independently noticed (but never filed as its own
ticket) in the earlier ELITEA-2075 AFS
(`test-specs/chat-interface/l2_agent-hub-participant-readonly-canvas-llm-override_ELITEA-2075.md`,
step 1).

**Every remaining sibling in this family will hit the same drift** — when
analysing ELITEA-2351 or any other member, cite #1208 in the AFS's Coverage
Map / Known Defects section instead of re-discovering or re-filing a
duplicate clarification. Assert the live "Catalog" wording, not the case's
"Agent HUB" string.

Also confirmed while filing: the case family's OTHER content (the 11-item
category list: Trending, My Liked, Business Analyst, DevOps, Development,
Elitea, Epam, Knowledge & Documentation, Project Management, Quality
Assurance, Other) matches the live product exactly — the drift is scoped to
the "Agent HUB" naming only, not the whole case family.

Full handle map for this surface (page object, testid gaps, slug function):
`test-specs/agent-hub/_surface.md`.
