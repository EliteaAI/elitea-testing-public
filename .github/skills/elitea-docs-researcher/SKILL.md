---
name: elitea-docs-researcher
description: Researches ELITEA/EliteA documentation using indexed search tools. Given a feature name, topic, or question, it queries all three documentation indexes (search_index, stepback_search_index, stepback_summary_index) and returns a comprehensive, structured documentation report. Use this skill when you need to understand how a feature works in ELITEA/EliteA before writing checklists, test cases, or answering product questions.
---

# EliteA Docs Researcher

## OBJECTIVE

Research ELITEA/EliteA documentation thoroughly for a given feature, topic, or question. Use all three documentation search tools to gather relevant information and return a structured, comprehensive summary ready to be used for checklist generation, test case design, or answering questions.

---

## INPUT

- **Topic or feature name** to research (e.g., "Artifacts", "Artifact Toolkit", "Chat file attachments", "Agent configuration")
- **Optional:** specific aspect or question to focus on (e.g., "retention policies", "folder support", "nested folders")

---

## EXECUTION FLOW

For each provided topic, run the following three tools — use varied query formulations to maximize coverage:

1. **`elitea_by_mcp/EliteA_docs_search_index`** — searches across indexed documentation content to find specific feature descriptions, configuration details, UI behavior, and any content directly related to the topic.
   - Run at least 2 queries: one with the exact topic name, one with related terms or workflows.

2. **`elitea_by_mcp/EliteA_docs_stepback_search_index`** — performs advanced contextual searches with broader scope to surface related concepts, edge cases, and expanded context not found by direct search.
   - Run at least 2 queries: one broader than the topic (e.g., parent feature area), one targeting integration with other product areas.

3. **`elitea_by_mcp/EliteA_docs_stepback_summary_index`** — creates comprehensive summaries of indexed documentation content to generate intelligent overviews of the feature area or module.
   - Run at least 1 query for a high-level summary of the feature area.

After running all queries, consolidate the results and return a **structured documentation report** containing:

### Documentation Report Structure

- **Feature Overview:** What the feature is, its purpose, and primary use cases (from docs).
- **Key Concepts & Terminology:** Important terms and definitions relevant to the topic.
- **Configuration & Setup:** How to configure or set up the feature (steps, required fields, options).
- **Available Functionality:** Full list of capabilities, tools, actions, or options described in the docs.
- **UI & Navigation:** Where to find the feature in the product, menu paths, relevant pages.
- **Integration Points:** Other features or product areas that interact with or depend on this feature.
- **Constraints & Limitations:** Known limitations, retention policies, size limits, permission requirements, etc.
- **Recent Changes:** Any release notes or change descriptions found for this feature.
- **Gaps / Not Found:** Note any aspects of the topic that were queried but not found in the documentation.

---

## CONSTRAINTS

- Only report information found in the documentation — do NOT fabricate or infer details not present in the index results.
- If a query returns no relevant results, note it explicitly under "Gaps / Not Found".
- Do NOT skip any of the three tools — all must be queried.
- Return the full structured report, not just raw search results.
