# ELITEA Board — Project Fields Guide (GitHub Projects v2)

> **Audience:** QA, Developers, PMs, Support, AI agents assisting with triage  
> **Project:** ELITEA Board (GitHub Projects v2)  
> **Link:** https://github.com/orgs/EliteaAI/projects/3/views/1  
> **Purpose:** Explain **what each Project field means**, **when to set it**, **how to set it**, and **best practices** so issues are consistent, searchable, and AI‑native.

---

## Table of Contents

1. [What is ELITEA Board?](#what-is-elitea-board)  
2. [How Project Fields Work in GitHub Projects](#how-project-fields-work-in-github-projects)  
3. [Where to Edit Fields (UI Walkthrough)](#where-to-edit-fields-ui-walkthrough)  
4. [Field Reference (All Fields)](#field-reference-all-fields)  
   - [Status](#status)  
   - [Type](#type)  
   - [Milestone](#milestone)  
   - [Assignees](#assignees)  
   - [Priority](#priority)  
   - [Severity](#severity)  
   - [Sprint](#sprint)  
   - [Environment](#environment)  
   - [RN Inclusion](#rn-inclusion)  
   - [Hotfix](#hotfix)  
   - [Size](#size)  
   - [Reporter](#reporter)  
   - [Creation Date](#creation-date)  
   - [Parent issue / Sub-issues](#parent-issue--sub-issues)  
   - [Sub-issues progress](#sub-issues-progress)  
5. [Field Combinations (Common Scenarios)](#field-combinations-common-scenarios)  
6. [Views & Filters (How to Find Work)](#views--filters-how-to-find-work)  
7. [Examples (Based on Real Issues)](#examples-based-on-real-issues)  
8. [Troubleshooting](#troubleshooting)  
9. [Maintenance Notes](#maintenance-notes)  

---

## What is ELITEA Board?

ELITEA Board is the main Project used to track and manage ELITEA work end‑to‑end across repositories:
- Epics / Stories
- Bugs
- Enhancements
- Tasks
- Documentation

> The project’s **default repository** is `EliteaAI/elitea.github.io` (visible in Project settings).  
> This matters because many issues are created and triaged from that repository.

**Screenshot (Board overview):**  
![image4](image4)

---

## How Project Fields Work in GitHub Projects

GitHub Projects v2 fields are attached to **Project items**. A Project item may represent:
- a GitHub Issue (most common)
- a Pull Request
- a draft item (not recommended for bug tracking unless agreed)

Important details:
- An issue can exist in a repository without being added to the project.
- When you add an issue to ELITEA Board, you can set additional metadata via **Project fields** (Status, Sprint, Priority, etc.).
- Fields are searchable and can be used to build views, dashboards, and exports (pivot charts).

---

## Where to Edit Fields (UI Walkthrough)

### Option A — From the Board (recommended)
1. Open the project view (Kanban or Sprint view).  
2. Click a card to open the right-side details panel (or the issue preview).  
3. In the side panel, locate the **Projects** section and **custom fields**.  
4. Set required fields (see [Field Reference](#field-reference-all-fields)).  

**Screenshot (issue + field panel):**  
![image1](image1)

### Option B — From the Issue page
1. Open the GitHub issue in the repository.  
2. In the right sidebar, add it to **ELITEA Board** (if not already).  
3. Open ELITEA Board item fields and set them.  

**Screenshot (Issue Type & Milestone appear on issue page):**  
![image5](image5)

> **Tip:** Most field updates are fastest from the project board because you can move cards between columns and set fields without leaving the view.

---

## Field Reference (All Fields)

> “Required” means: expected for triage correctness, board visibility, and automation.

### Status

**What it means:** Current workflow state inside ELITEA Board (Kanban columns).  
**Why it matters:** Drives team flow (triage → dev → testing → done) and most board views.

**Typical values (as seen in board columns):**
- `To Do`
- `Bugs` (newly reported bugs)
- `Development`
- `In Testing`
- `Verified on DEV Env`
- `Ready for Public Release`
- `Done`

**When to set:**
- New bug → set to **Bugs**
- Bug accepted for work → **Development**
- Deployed and waiting QA → **In Testing**
- Verified in DEV → **Verified on DEV Env**
- Verified and ready to ship → **Ready for Public Release**
- Released → **Done**

**Common mistakes:**
- Leaving a new bug in `To Do` instead of `Bugs`
- Moving to `Done` before verification evidence exists

**Screenshots:**  
- Board columns and status usage: ![image4](image4)

---

### Type

**What it means:** The **Issue Type** (organization-level issue type) such as:
- Bug
- Design
- Documentation
- Enhancement
- Epic
- Feature
- Q&A (etc.)

**Where it is set:** On the **Issue itself** (“Select issue type”), not as a project custom field.  
In the UI, it appears as “Type” with a dropdown.

**Why it matters:**
- Powers project filters like `type:Bug` (used in views)
- Prevents mixing bugs with stories/enhancements in the same dashboards

**Required?**
- Yes for triage quality. Bugs must be `Type: Bug`.

**Screenshot (Issue Type selection / list):**  
![image6](image6)

**Common mistakes:**
- Using title prefix `[BUG]` but leaving Type as something else
- Treating “Type” as a project field named “Type” (it is not)

---

### Milestone

**What it means:** Repository milestone representing release planning (e.g., `R-2.0.0B2`).  
**Where it is set:** On the Issue itself (repo milestone).

**Why it matters:**
- Used to plan releases and release progress views
- Used heavily in searches and filtered exports (e.g., milestone-based bug lists)

**Required?**
- Required for bugs that are planned for a release.  
- If not scheduled, use “Next”/“Future” milestone buckets (as described in your process).

**Best practice:**
- Set milestone as soon as the bug is triaged.
- Use consistent naming: your milestone example indicates `R-2.0.0B2`.

**Common mistakes:**
- Typos in milestone name (export scripts and filters require exact titles)
- Using project “Sprint” field instead of milestone to represent release

---

### Assignees

**What it means:** Who is responsible for fixing (or triaging) the item.

**Required?**
- Yes: set to developer, team lead, or AI triage bot when appropriate.

**Best practice:**
- Assign **one primary owner** unless cross-team work is required.
- For unknown ownership, assign to team lead rather than multiple engineers.

**Common mistakes:**
- Assigning 3–4 engineers by default (reduces accountability)

---

### Priority

**What it means:** Scheduling urgency.  
**Values (from your process):** `P0 | P1 | P2` *(optional P3 later if adopted)*

**Required?**
- Yes for bugs (at least P1/P2). For stories/tasks, recommended.

**How to choose:**
- Use the Priority rules from: [Bug Priority and Severity guide](bug-priority-severity.md)

**Common mistakes:**
- Using Priority to represent impact (use Severity for impact)

---

### Severity

**What it means:** Impact level on system/workflows.  
**Values:** `Blocker | Critical | High | Medium` (and possibly others if your board uses them)

**Required?**
- Yes for bugs.

**How to choose:**
- Use the Severity definitions from: [Bug Priority and Severity guide](bug-priority-severity.md)

**Screenshot (Priority & Severity badges on cards):**  
![image3](image3)

---

### Sprint

**What it means:** The iteration/sprint bucket for delivery within the release.

**Required?**
- **Required only when the bug is in the current release scope** and you need sprint-level planning.
- If bug belongs to upcoming releases, keep Sprint empty.

**How it is used:**
- Sprint views and current sprint dashboards
- Filter examples: `sprint:@current` is used in some views

**Screenshot (Current Sprint view filter):**  
![image3](image3)

**Common mistakes:**
- Setting Sprint for “Future” items (creates noise in sprint dashboards)

---

### Environment

**What it means:** Where the issue is found or reproducible.  
**Options (from your process):** `DEV | STAGE | NEXT | ALL | Client_Env`

**Required?**
- Recommended for bugs; optional if not applicable.

**Best practice:**
- Prefer DEV/STAGE for reproduction and test data creation.
- If found on Client_Env, still reproduce in DEV/STAGE and link both contexts.

**Common mistakes:**
- Leaving Environment blank when reproduction depends on environment-specific config

---

### RN Inclusion

**What it means:** Whether to include in Release Notes.

**Required?**
- Typically **No** for QA reporters to set; leave for release owner/creator decision.

**Special rule you provided:**
- If feature is not publicly available and is for upcoming release, default is **No**.

---

### Hotfix

**What it means:** Flag for post-release urgent fixes that must ship as hotfix.

**Required?**
- Only for post-release bugs requiring urgent delivery.

**Best practice:**
- Set **Hotfix=Yes** only when confirmed by release owner / triage policy.
- Combine with: `Priority=P0` and high Severity when applicable.

---

### Size

**What it means:** Rough estimate of effort/complexity.

**Required?**
- Optional for QA reporters; may be filled by engineering.

**Best practice:**
- If used, ensure size values are clearly defined (S/M/L or numeric).
- Add a separate “Sizing Guide” if your team depends on it.

---

### Reporter

**What it means:** Name/login of person who reported the issue (project custom field).  
**Automation:** You noted this is set automatically weekly by script.

**Required?**
- Do not set manually.

---

### Creation Date

**What it means:** Project custom field representing when the bug was created/reported (for reporting/analytics).  
**Automation:** set automatically weekly by script.

**Required?**
- Do not set manually.

---

### Parent issue / Sub-issues

**What it means:** Links a bug to a parent Story/Epic/Feature/Enhancement.

**When to set:**
- When bug is part of a feature scope or blocks acceptance criteria.
- When bug is logically owned by a parent item.

**Best practice:**
- Create bug as **sub-issue** of the parent when appropriate (not just “related”).

**Example from your list:**
- #2548 is a `[Story]` and could have sub-issues (bugs) that block acceptance.

---

### Sub-issues progress

**What it means:** A computed progress indicator for parent issues with sub-issues.  
**Who uses it:** PMs/Leads to track completion.

**Best practice:**
- Ensure sub-issues use consistent Status transitions so progress is meaningful.

---

## Field Combinations (Common Scenarios)

### Scenario 1 — New bug found in DEV
- Type: **Bug**
- Status: **Bugs**
- Environment: **DEV**
- Priority: **P1** (or P0 if release-blocker)
- Severity: based on impact
- Milestone: current release milestone if required
- Sprint: current sprint only if it must be delivered now

### Scenario 2 — Client-reported issue
- Reproduce in DEV/STAGE
- Set Environment: `Client_Env` (optional) + `DEV/STAGE` once reproduced
- Create/attach stable test data links
- Status: Bugs → Development after triage

### Scenario 3 — Post-release urgent fix
- Hotfix: **Yes**
- Priority: **P0**
- Severity: often Critical/Blocker
- Milestone: current hotfix milestone if used
- Sprint: only if your hotfix process uses sprints

---

## Views & Filters (How to Find Work)

Your project has multiple views (tabs) for different workflows (Kanban, sprint, release, per reporter, etc.).

### Common filter patterns seen in your board
- Filter by sprint current: `sprint:@current`
- Filter by milestone: `milestone:"R-2.0.0B2"`
- Filter by issue type: `type:Bug`
- Filter by statuses: `status:"Bugs","Development",...`

**Screenshot (board with complex filter):**  
![image4](image4)

**Screenshot (Current Sprint filter view):**  
![image3](image3)

> **Note:** GitHub Projects filter syntax is powerful but strict. Document your commonly used filters here to standardize usage.

---

## Examples (Based on Real Issues)

> These references explain how fields should look by work type.  
> (Field values shown here are illustrative; verify actual values in ELITEA Board.)

### Example: Bug issue
- #3039 `[BUG] Incorrect icon displayed for child agent in thinking steps`  
  https://github.com/EliteaAI/elitea.github.io/issues/3039  
  Expected field pattern:
  - Type: Bug
  - Status: Bugs/Development depending on stage
  - Priority + Severity: set
  - Milestone: set if planned for a release
  - Environment: DEV/STAGE if reproducible

### Example: Enhancement
- #2781 `[Enhancement] Add Search Functionality...`  
  https://github.com/EliteaAI/elitea.github.io/issues/2781  
  Expected field pattern:
  - Type: Enhancement
  - Status: To Do / Development depending on plan
  - Milestone: optional depending on release scope

### Example: Story
- #2548 `[Story] Restore Conversation from Agent/Pipeline Run History`  
  https://github.com/EliteaAI/elitea.github.io/issues/2548  
  Expected field pattern:
  - Type: Story
  - Status: To Do / Development
  - Sub-issues: bugs/tasks linked under it

### Example: Task
- #3019 `[Task] Add "Diagram Validation & Fixing"...`  
  https://github.com/EliteaAI/elitea.github.io/issues/3019

### Example: Epic
- #2223 `[Epic] Redesign and enhance Error Messages`  
  https://github.com/EliteaAI/elitea.github.io/issues/2223

### Example: Documentation
- #2505 `[Documentation] Redesign and Update Getting Started section`  
  https://github.com/EliteaAI/elitea.github.io/issues/2505

---

## Troubleshooting

### “I don’t see the field in the side panel”
- Ensure the issue is added to **ELITEA Board**
- Check you have access to the project fields
- Some fields may appear only after expanding the Projects section

### “I can’t set Type/ Milestone from the project field list”
- That’s expected: **Type** and **Milestone** are Issue-level metadata, not project custom fields.
- Set them on the Issue page or in the issue side panel when available.

### “Reporter / Creation Date are empty”
- Those are auto-filled weekly by script; do not set manually.

---

## Maintenance Notes

To keep this guide maintainable:
- Keep the field definitions in one place (this guide).
- Keep example templates in: [Bug Template Examples](bug-template-examples.md)
- Keep priority/severity policy in: [Bug Priority and Severity](bug-priority-severity.md)
- Update screenshots when UI changes; keep placeholders if screenshots are missing.

---

## Screenshot placeholders (to add later)

- [ ] Screenshot: editing fields from Kanban card
- [ ] Screenshot: selecting Type on Issue page
- [ ] Screenshot: setting Milestone
- [ ] Screenshot: setting Sprint/Iteration
- [ ] Screenshot: example of properly filled bug fields
- [ ] Screenshot: example of release view (milestone)
