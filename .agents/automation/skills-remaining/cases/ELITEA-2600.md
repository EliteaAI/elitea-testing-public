---
id: ELITEA-2600
title: "Agent with Skills Publishing Flow"
priority: high
type: functional
module: skills
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, feat:agents, feat:publishing]
requirements: []
---

# ELITEA-2600: Agent with Skills Publishing Flow

**Module:** skills · **Priority:** high · **Type:** functional

**Objective:** Verify that when an agent with attached skills is published, the skills are embedded in the snapshot (NOT exposed as independent Catalog entities), the published agent uses its skills correctly, and skills are visible in the thought process during execution.

---

## Preconditions

- User is logged in to the Elitea platform with Admin or Editor role.
- A project exists and is accessible.
- The Skills and Agents sections are available in the project.
- User has publishing permissions for agents.

---

## Test Data

| Field | Value |
|-------|-------|
| Agent Name | `multi-skill-agent` |
| Agent Instructions | You are a helpful assistant that can format and analyze text. |
| Skill 1 Name | `format-uppercase` |
| Skill 1 Instructions | Convert all text to UPPERCASE format |
| Skill 2 Name | `word-counter` |
| Skill 2 Instructions | Count the words in the provided text and return the count |
| Skill 3 Name | `summarizer` |
| Skill 3 Instructions | Provide a brief summary of the given text |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Create Skill 1 (`format-uppercase`) with valid content | Skill 1 is created and saved |
| 2 | Create Skill 2 (`word-counter`) with valid content | Skill 2 is created and saved |
| 3 | Create Skill 3 (`summarizer`) with valid content | Skill 3 is created and saved |
| 4 | Create an Agent and attach all three skills to it | Agent is created with 3 skills listed as attached |
| 5 | Open the Agent publish wizard | Publish wizard opens |
| 6 | Complete the publishing process for the agent | Agent is published successfully |
| 7 | Navigate to the Agent Hub/Catalog | Published agent appears in the catalog |
| 8 | Search for the individual skills in the Skills Catalog | Skills are NOT listed as independent entities (they are embedded in agent snapshot) |
| 9 | Open the published agent from the Catalog | Agent details page loads |
| 10 | Start a conversation with the published agent | Chat interface opens |
| 11 | Send a message that triggers one of the attached skills | Agent responds using the skill |
| 12 | Expand the thought process/reasoning panel | Thought process is visible |
| 13 | Verify that the invoked skill is shown in the thought process | Skill invocation is logged/visible in thought process |
| 14 | Test another skill invocation | Second skill also works and appears in thought process |

---

## Expected Final State

1. The agent is published with all skills embedded in the snapshot.
2. Skills are NOT exposed as independent searchable entities in the Skills Catalog.
3. The published agent correctly uses its attached skills.
4. Skill invocations are visible in the thought process for observability.

---

## Pass/Fail Criteria

**Pass:**
- Agent publishes successfully with attached skills.
- Skills are embedded (not independently published to Skills Catalog).
- Published agent correctly invokes and uses attached skills.
- Skill usage is visible in thought process.

**Fail:**
- Agent fails to publish with skills attached.
- Skills appear as independent entities in Skills Catalog.
- Published agent cannot use its attached skills.
- Skill invocations are not visible in thought process.
