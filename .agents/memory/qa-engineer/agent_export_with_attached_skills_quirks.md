---
name: Agent export with attached Skills quirks
description: Agent export embeds full Skill content (name/description/version/instructions) verbatim in nested skills list, unlike a Skill's own standalone export which omits version:
type: feedback
---

## Context

Found during ELITEA-1794 (Export Agent with attached Skills) analyst pass,
localhost:5173, agent detail page's actions overflow menu.

## Findings

1. **`Export` lives in the agent-actions overflow menu's `VERSION` group** —
   `agent-actions-menu-button` (same button documented for ELITEA-1792) opens a
   menu with `VERSION` group (`Set as a default` [disabled], `Export`, `Share`,
   `Fork`, `Publish`, `Delete` [disabled]) and an `AGENT` group (`Share`, `Pin to
   top`, `Delete agent`). No dedicated `data-testid` observed on the `Export`
   menuitem itself in this run — located via `getByRole('menuitem', { name:
   'Export' })` scoped to the opened menu.

2. **Clicking Export triggers an immediate browser download, no dialog.**
   Filename pattern: `{agent-name}.agent.md` (double extension, still resolves
   as a valid `.md`). Network trace: `GET
   /api/v2//elitea_core/export_import/prompt_lib/{project}/{agent-id}?format=md&follow_version_ids={agent-id}`
   → `200 OK`. Note the literal doubled `//` after `/v2` in the URL — cosmetic,
   the endpoint responds fine; not a defect.

3. **Contrast with a Skill's own standalone export** (documented in
   `skill_form_and_export_import_quirks.md`, ELITEA-1737): a bare Skill export
   omits the `version:` key entirely from its frontmatter. An **Agent** export
   with attached Skills is different — each entry in the agent's `skills:` list
   is a **full nested object** with `name`, `description`, `version` (e.g.
   `base`), and `instructions` (the complete text, verbatim — confirmed live by
   planting a unique marker substring in the Skill's instructions and finding it
   intact in the downloaded file). This is the correct, expected behavior for
   ELITEA-1794's assertion ("Skill content embedded, not just referenced") — do
   not confuse the two export surfaces when documenting/asserting `version:`
   presence.

4. **Full captured Agent-export frontmatter shape** (fields present):
   `name`, `description`, `model`, `temperature`, `max_tokens`, `agent_type`,
   `step_limit`, `skills` (list of `{name, description, version, instructions}`).
   The Agent's own instructions text follows as the markdown body after the
   closing `---`.

## Where used

`test-specs/skills/l3_export-agent-with-attached-skills_ELITEA-1794.md` (Test
Steps 5–7, Handles Reference, Coverage Map Axis 1/2).
