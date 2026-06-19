# QA Bug Reporting Guide — GitHub Issues + ELITEA Board (GitHub Projects)

> **Audience:** QA engineers, Support, and anyone reporting defects  
> **Tooling:** GitHub Issues (repo: `EliteaAI/elitea.github.io`) + GitHub Projects v2 (`ELITEA Board`)  
> **Goal:** Make every bug report **easy to reproduce**, **easy to triage**, and **AI‑native** (so AI agents and automation can reproduce, propose fixes, write tests, and verify).

---

## Table of Contents

1. [Purpose & Principles](#purpose--principles)  
2. [Quick Start (Minimum Good Bug)](#quick-start-minimum-good-bug)  
3. [What “AI‑Native Bug Reporting” Means](#what-ai-native-bug-reporting-means)  
4. [Where to Report Bugs (DEV/STAGE Only)](#where-to-report-bugs-devstage-only)  
5. [Bug Lifecycle in ELITEA Board](#bug-lifecycle-in-elitea-board)  
6. [Bug Report Structure (Template Fields)](#bug-report-structure-template-fields)  
7. [Project Fields to Fill in ELITEA Board](#project-fields-to-fill-in-elitea-board)  
8. [Test Data Requirements (Agents / Pipelines / MCP / Toolkits / Chats)](#test-data-requirements-agents--pipelines--mcp--toolkits--chats)  
9. [Attachments & Evidence Standards](#attachments--evidence-standards)  
10. [Labels & Taxonomy](#labels--taxonomy)  
11. [Priority & Criticality](#priority--criticality)  
12. [Parent Issue / Sub‑Issue Rules](#parent-issue--sub-issue-rules)  
13. [DOs and NOT TO DOs](#dos-and-not-to-dos)  
14. [Examples & Reference Guides](#examples--reference-guides)  
15. [Maintenance & How to Update This Guide](#maintenance--how-to-update-this-guide)  

---

## Purpose & Principles

This guide defines **how QA should report bugs** so that:

- Developers can reproduce the issue quickly
- QA can verify fixes reliably using the same test data
- AI agents (Copilot/automation) can reproduce and reason about the issue deterministically
- Product owners can triage and prioritize consistently using GitHub Projects fields

**A bug report is “done” only when:**
- reproduction is deterministic,
- expected behavior is explicit,
- test data is complete and stable,
- the issue is triaged with required fields in the Project.

---

## Quick Start (Minimum Good Bug)

If you’re in a hurry, your report must still include:

1) **Title** starting with `[BUG]`  
2) **Description** (1–3 sentences)  
3) **Steps to reproduce** (numbered, deterministic)  
4) **Test Data** (links + credentials + objects used)  
5) **Actual result** vs **Expected result**  
6) **At least one screenshot** (or console logs when relevant)  
7) **Project fields** filled in ELITEA Board (see [Project Fields](#project-fields-to-fill-in-elitea-board))

---

## What “AI‑Native Bug Reporting” Means

An AI‑native bug report is structured so that an AI agent can:

- set up the environment,
- locate the exact screen/page/API,
- replay the steps,
- reproduce consistently,
- infer why it is wrong,
- identify affected components (FE/BE/SDK),
- propose a fix and tests,
- verify the fix with your same test data.

To achieve that, **avoid vague language** (“sometimes”, “doesn’t work”, “buggy”) and replace it with:

- conditions (browser/device/build),
- deterministic steps,
- stable links to data (agent/pipeline/toolkit/chat),
- exact error messages (copy/paste),
- screenshots with annotated focus.

---

## Where to Report Bugs (DEV/STAGE Only)

### Environments allowed for bug creation/reproduction
Bugs must be created or reproduced (if reported by client) in:
- **DEV**
- **STAGE**

**Do not create new bug reproductions in NEXT/PROD** unless explicitly required and approved.

### Where test data must live
All test data used for reproduction must be created in the **Bugs & Features** project (internal environment where dev/QA/AI agents have access) on DEV and STAGE envs.

---

## Bug Lifecycle in ELITEA Board


1) **Bugs** — newly reported bugs (default for new bug reports)  
2) **Development** — picked up / actively being fixed  
3) **In Testing** — deployed to DEV, ready for QA verification  
4) **Verified on DEV Env** — confirmed in DEV  
5) **Ready for Public Release** — verified and accepted on STAGE env
6) **Done** — released / completed

---

## Bug Report Structure (Template Fields)

Your bug report must follow the bug template described in:
- **Bug Template — Examples (separate guide)**: see [Bug Template Examples](bug-template-examples.md)

### Required sections in the bug body

- **Description**
- **Preconditions (optional)**
- **Steps to reproduce**
- **Test Data**
- **Actual Result**
- **Expected Result**
- **Attachments**
- **Notes (optional)**

> Use **h3 headings (`###`)**, numbered steps for “Steps to reproduce” and “Preconditions”, and bullet points for “Test Data” and “Notes”.

---

## Project Fields to Fill in ELITEA Board

When reporting a bug in GitHub Project **ELITEA Board**, fill these fields:

### Required fields (must set)
- **Assignee**  
  Assign to the correct developer or team lead if unknown.  
  If allowed, you may assign to an AI bot for initial analysis/triage.

- **Type**: `Bug`

- **Status**: set to **`Bugs`** for newly reported bugs

- **Milestone**  
  Choose based on fix timing:
  - **Current release**: must be fixed in this release → select current release milestone  
  - **Upcoming 1–2 releases**: select the planned upcoming release milestone  
  - **Next**: plan to fix in next **3–6 months**  
  - **Future**: plan to fix in **6+ months**

- **Labels**  
  Add appropriate labels (see [Labels & Taxonomy](#labels--taxonomy)).

- **Priority**: `P0 | P1 | P2`

- **Criticality**: `Blocker | Critical | Relatively Critical | Not Critical`

### Conditional / context fields
- **Sprint**  
  Set only if bug must be fixed for the current release.  
  If for upcoming releases → leave empty.

- **Environment**  
  Select where bug was found/reproduced: `Dev | Stage | Next | All | Client`  
  May be skipped if not applicable.

- **Parent Issue**  
  If bug relates to a Story/Epic/Enhancement/Feature, set Parent Issue and treat this bug as a sub-issue.  
  See [Parent Issue rules](#parent-issue--sub-issue-rules).

- **RN Inclusion**  
  Usually skip. If feature is not publicly available and is in development for upcoming release, default is **No**.

- **Hotfix**  
  Only after release when issue must be fixed immediately and released as hotfix.  
  Use **Yes** only for critical/high impact post-release issues.

### Auto-managed (do not set manually)
- **Reporter** — set automatically (weekly script)  
- **Creation Date** — set automatically (weekly script)

---

## Test Data Requirements (Agents / Pipelines / MCP / Toolkits / Chats)

### Why test data matters
Fix verification must use the **same test data** that reproduced the bug.

### What must be included in “Test Data”
Include **direct links** and identifiers for anything used:

- Account(s): email/login, role, tenant/workspace, permissions
- Links to:
  - agent
  - pipeline
  - MCP
  - toolkit
  - chat conversation
- IDs / names of objects created
- Configuration: key settings (e.g., model selection, token limits, toggles)
- If secrets exist: store them securely; do not paste real passwords in public issues

### Naming convention for test data objects
When creating artifacts in **Bugs & Features** project:

- Use consistent naming:  
  `BUG-<issueNumber> <short-title> (DEV|STAGE)`
- Add descriptions matching the bug context:
  - what it’s for
  - how to use it
  - expected output/behavior
- Tags:
  - For **agents and pipelines**, apply tags that match GitHub labels.
  - For Chat/Toolkit/MCP, use description fields similarly.

---

## Attachments & Evidence Standards

### Screenshots (preferred)
- Provide 1–3 screenshots showing:
  - where you clicked
  - what you expected
  - what happened instead
- Annotate with:
  - arrows
  - highlights
  - short callouts

### Videos (use only when needed)
- Keep under ~30–60 seconds
- Include narration or captions (what to observe)
- Avoid long, unedited recordings with idle time

### Logs / Console output
Include:
- exact error messages
- stack traces (if safe)
- network request/response details (if relevant)

> **Placeholder:** Add a “How to capture network logs” section if needed.

---

## Labels & Taxonomy

Use labels consistently. Do not create new labels unless you’re the label owner / taxonomy maintainer.

- **Labels & Taxonomy Guide**: *(link placeholder)* `./Labels-and-Taxonomy-Guide.md`

### Suggested label categories (examples)
- Component: `eng:frontend`, `eng:backend`, `eng:sdk`
- Feature: `feat:mcp-remote`, `feat:pipelines`
- Meta: `meta:regression`

> Check real label list and meaning in the taxonomy guide.

---

## Priority & Criticality

Priority and criticality are different:

- **Priority (P0/P1/P2)** = urgency and scheduling
- **Criticality** = severity and impact

- **Bug Priority & Criticality Guide**: [Bug Priority and Severity](bug-priority-severity.md)

### Quick mapping (example — adjust to your org)
- **P0 + Blocker**: cannot release / major feature unusable / data loss
- **P1 + High**: significant impact, workaround exists
- **P2 + Not Critical**: minor UX defects, cosmetic issues

---

## Parent Issue / Sub‑Issue Rules

Use **Parent Issue** when:
- bug is discovered during a feature/story implementation
- bug blocks acceptance of a story/epic
- bug is part of known scope for a feature

Benefits:
- preserves traceability
- enables progress reporting per feature
- simplifies release notes planning

---

## DOs and NOT to DOs

### DO
- Use the template exactly (see examples guide)
- Provide deterministic steps
- Provide complete test data links
- Attach annotated screenshots
- Fill required Project fields (Type, Status, Milestone, Priority, Criticality, Assignee)
- Use existing labels and taxonomy
- Keep bugs focused: **one bug = one issue** (unless truly inseparable)
- Make it AI-native: plain language, explicit conditions, stable links, no ambiguity

### NOT to DO
- Don’t paste long, unedited videos (prefer screenshots + concise clips)
- Don’t omit expected result
- Don’t use vague statements (“broken”, “doesn’t work sometimes”)
- Don’t create new labels ad hoc
- Don’t assign the same bug to multiple engineers unless cross-team work is explicitly required
- Don’t reproduce/create test data in NEXT/PROD without approval

---

## Examples & Reference Guides

### Bug Template Examples
- See: **[Bug Template Examples](bug-template-examples.md)**

### Other helpful guides
- [Labels & Taxonomy Guide](labels-taxonomy.md)
- [Bug Priority and Severity](bug-priority-severity.md)
- [Project Fields Guide](project-fields-guide.md)
- [Parent Issue & Sub-Issue Rules](parent-sub-issue-rules.md)

---

## Maintenance & How to Update This Guide

To keep this guide easy to update:

### Structure rules
- Keep policy in this main guide.
- Put detailed examples in separate docs (templates, taxonomy, priority matrix).
- Prefer checklists and tables over long prose when possible.

### Suggested ownership
- QA Lead owns process sections.
- Eng leads own severity/priority definitions.
- Release manager owns milestone policy.

### Versioning
- Keep change notes at the bottom (optional).
- Review quarterly or per-release.

---

> **Screenshots placeholders**
> - Add screenshots for:
>   - Creating a new GitHub Issue using template
>   - Setting Project fields in ELITEA Board side panel
>   - Example of good screenshot annotations
>   - Example of linking test data in Bugs & Features project
