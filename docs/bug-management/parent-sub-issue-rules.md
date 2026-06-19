# Parent Issue & Sub‑Issue Rules — ELITEA Board (GitHub Issues + Projects)

> **Audience:** QA, Developers, PMs, Support, AI agents assisting with triage  
> **Applies to:** `EliteaAI/elitea.github.io` issues tracked in **ELITEA Board**  
> **Purpose:** Define when and how to use **Parent issues** and **Sub‑issues** so work is traceable, measurable, and easy to plan/release.

---

## Table of Contents

1. [Why Parent/Sub‑Issue structure matters](#why-parentsub-issue-structure-matters)  
2. [Definitions](#definitions)  
3. [When to create a Parent issue vs a stand‑alone issue](#when-to-create-a-parent-issue-vs-a-stand-alone-issue)  
4. [When to create a Sub‑issue](#when-to-create-a-sub-issue)  
5. [How to create a Sub‑issue in GitHub](#how-to-create-a-sub-issue-in-github)  
6. [Rules by Issue Type (Epic / Story / Task / Bug / Enhancement)](#rules-by-issue-type-epic--story--task--bug--enhancement)  
7. [Acceptance Criteria & “Done” definition](#acceptance-criteria--done-definition)  
8. [Best practices (AI‑native)](#best-practices-ai-native)  
9. [Anti‑patterns (what not to do)](#anti-patterns-what-not-to-do)  
10. [Examples (from ELITEA issues)](#examples-from-elitea-issues)  
11. [Maintenance](#maintenance)  

---

## Why Parent/Sub‑Issue structure matters

Using Parent/Sub‑issue relationships correctly enables:

- **Traceability:** Every bug or task is linked to the feature/epic it supports.
- **Progress visibility:** Parent issues can show “sub‑issues progress” in ELITEA Board.
- **Release planning:** PM/Leads can see what blocks a release milestone.
- **AI-native workflows:** AI agents can understand scope boundaries, dependencies, and missing work.

---

## Definitions

### Parent issue
A higher-level issue that represents a larger unit of work (usually **Epic** or **Story**, sometimes **Enhancement**). The Parent:
- defines goals and acceptance criteria
- owns scope
- groups implementation items (sub-issues)

### Sub‑issue (child issue)
A smaller, actionable piece of work that contributes to completing the parent. Common child types:
- Bug
- Task
- Story (under Epic)
- Enhancement (under Epic)

### Relationship fields in GitHub
GitHub supports “Parent issue” and “Sub‑issues” in the issue sidebar (Relationships section). When used correctly:
- Parent shows child list
- Child shows parent link
- Projects can display sub-issue progress

---

## When to create a Parent issue vs a stand‑alone issue

Create a **Parent** when:

- the work spans multiple components (FE + BE + SDK)
- there are multiple deliverables or acceptance criteria
- there will be more than ~2–3 implementation items (bugs/tasks/stories)
- you need progress tracking across sub-tasks

Create a **stand-alone** issue when:

- it is a single fix with one clear owner and scope
- it does not require breaking down into smaller pieces
- it can be completed end-to-end without additional tracked subtasks

---

## When to create a Sub‑issue

Create a **Sub‑issue** when all of these are true:

1) The child work is **required** to complete the parent’s acceptance criteria **or**
2) The child work is a clear dependency/blocker for the parent **or**
3) The child work is tightly scoped and can be assigned/implemented independently

Typical cases:
- A Story needs 1–5 bugs fixed before it can be accepted
- An Epic contains multiple Enhancements and Bug fixes across modules
- A feature needs discrete tasks (UI, API, docs, tests)

---

## How to create a Sub‑issue in GitHub

### Option A — Create from the Parent (recommended)
1. Open the **Parent issue**.
2. Find **Relationships** section.
3. Click **Create sub-issue**.
4. Select issue type (Bug/Task/Story/etc.).
5. Fill template and fields.
6. Save. GitHub automatically links the child to the parent.

### Option B — Link an existing issue as a Sub‑issue
1. Open the **Parent issue**.
2. In **Relationships**, choose “Add sub-issue”.
3. Paste the issue link or number.

### QA tip
If you discover a bug while validating a Story or Epic:
- create the bug as a **sub-issue** of that Story/Epic **if it blocks acceptance**.

---

## Rules by Issue Type (Epic / Story / Task / Bug / Enhancement)

### Epic → what belongs under it?
Use an **Epic** to group a large initiative.
**Children of Epic typically include:**
- Stories (recommended)
- Enhancements
- Bugs that are clearly part of the epic scope
- Cross-cutting Tasks (e.g., “update docs”, “add telemetry”)

**Epic should contain:**
- Objective and scope
- Business goals
- Links to designs/specs
- High-level acceptance criteria
- Sub-issues list (or relationships)

### Story → what belongs under it?
A **Story** represents a user-visible capability with acceptance criteria.

**Children of Story typically include:**
- Tasks (implementation)
- Bugs (found during story work, blocking acceptance)
- Docs task (if required by acceptance)

**Story should contain:**
- User story format (As a / I want / So that)
- Clear acceptance criteria
- Testing scenarios (optional but recommended)

### Enhancement → parent or child?
An **Enhancement** can be either:
- a child under an Epic, or
- a parent itself if it has multiple implementation pieces.

Rule of thumb:
- If it needs multiple steps or teams → treat it as a **parent** and create sub-issues.

### Task → usually a child
Tasks are usually sub-issues of:
- a Story
- an Enhancement
- an Epic (less common)

A Task should be:
- narrowly scoped
- clearly implementable
- assigned to a single team/owner where possible

### Bug → usually a child (when related)
A Bug can be:
- stand-alone (if it’s general platform bug)
- a sub-issue of a Story/Epic/Enhancement if it blocks the related scope

**If bug is related to feature work, prefer sub-issue.**

---

## Acceptance Criteria & “Done” definition

### Parent is “Done” only when:
- all required sub-issues are completed, and
- acceptance criteria are met, and
- verification has occurred where relevant (DEV → STAGE per process), and
- release requirements are met (milestone/sprint alignment)

### Sub‑issues “Done” only when:
- acceptance criteria for that sub-issue are met
- testing/verification evidence exists (for bugs)
- links to test data remain available and stable

> Avoid closing sub-issues prematurely; it breaks progress metrics.

---

## Best practices (AI‑native)

To make parent/sub-issues useful for humans and AI:

### Parent issue best practices
- Use **clear scope boundaries**: what is in/out.
- Write **acceptance criteria** in checklist form.
- Link to specs/designs, and add “source of truth” links.
- Prefer **child issues for each implementable piece** (UI, API, tests, docs).

### Sub‑issue best practices
- Keep each child issue:
  - independently reproducible (for bugs)
  - independently testable
  - assigned to one owner
- Add references back to the parent context (why it matters).

### Labels and fields
- Parent and children should share:
  - release milestone (when applicable)
  - relevant feature labels (e.g., `feat:toolkits`)
- Child bugs must follow the bug template and have fields set in ELITEA Board.

---

## Anti‑patterns (what not to do)

- **One giant parent with 50 unrelated sub-issues**  
  If sub-issues do not contribute to the same objective, they don’t belong together.

- **Using “related” links instead of parent/sub-issue**  
  If work is required for completion, use parent/sub-issue, not a loose link.

- **Sub-issues without clear acceptance criteria**  
  Makes “progress” meaningless and increases rework.

- **Multiple owners per sub-issue by default**  
  Prefer single owner; add reviewers/collaborators if needed.

- **Closing parent while leaving children open**  
  Breaks progress, confuses release readiness.

---

## Examples (from ELITEA issues)

> These examples illustrate correct patterns for parent/sub-issue usage.

### Example 1 — Epic with structured sub-issues
**Epic:** #2446 — Enhancements and Redesign of OpenAPI toolkit  
https://github.com/EliteaAI/elitea.github.io/issues/2446

Why it’s a good parent:
- Clear objective and business goals
- Lists sub-issues (enhancements) and acceptance criteria
- Contains technical considerations by component (Frontend / Backend/SDK)

**Recommended practice for this epic:**
- Ensure each listed sub-issue (#2445, #2441, #2481, etc.) is linked in **Relationships** as sub-issues (not only mentioned in text).
- Add milestone/sprint rules if it targets a specific release.

---

### Example 2 — Epic mixing enhancements + bug fixes (valid pattern)
**Epic:** #2426 — Enhancements for QTest toolkit  
https://github.com/EliteaAI/elitea.github.io/issues/2426

Why it’s a good parent:
- Contains enhancements and also includes bug fixes that are within QTest toolkit scope
- Has acceptance criteria describing the end state

**Notes:**
- Bugs under this epic should still follow the bug template and be tracked as child issues.

---

### Example 3 — Story as a parent with acceptance criteria (create sub-issues as needed)
**Story:** #2391 — Add Syngen Support for Synthetic Test Data Generation as a Toolkit  
https://github.com/EliteaAI/elitea.github.io/issues/2391

This Story is detailed and could benefit from sub-issues if implementation is multi-step:
- FE Task: UI for toolkit configuration (if needed)
- SDK Task: implement train/infer tools
- Docs Task: usage guide
- QA Task: test plan & validation dataset

Use sub-issues when the story is too large for one PR/owner.

---

### Example 4 — Story with acceptance criteria and test scenarios (ideal parent)
**Story:** #2587 — Summary Messages Modal with Token Analytics  
https://github.com/EliteaAI/elitea.github.io/issues/2587

Why it’s a good parent:
- Clear acceptance criteria with checkboxes
- Includes UI layout notes and test scenarios
- Supports splitting into sub-issues if needed:
  - UI implementation
  - token analytics correctness
  - responsiveness / accessibility
  - automated tests

---

## Maintenance

To keep parent/sub-issue practices consistent:
- Review parent issues during planning (weekly/bi-weekly).
- Ensure:
  - parent acceptance criteria are present
  - child issues are actually linked via Relationships
  - statuses and milestones are aligned
- Update this guide whenever GitHub Projects settings or status workflow changes.

---

## Screenshot placeholders (add later)

- [ ] Creating a sub-issue from a parent issue (Relationships → Create sub-issue)
- [ ] Linking existing issue as sub-issue
- [ ] Viewing Sub-issues progress field in ELITEA Board
- [ ] Example: Epic with multiple sub-issues and progress indicator
