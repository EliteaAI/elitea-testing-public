# Bug Priority and Severity — ELITEA / GitHub Projects Guide

> **Audience:** QA, Support, Developers, AI Agents assisting with triage/fixing  
> **Applies to:** GitHub Issues in `EliteaAI/elitea.github.io` + GitHub Projects v2 (`ELITEA Board`)  
> **Purpose:** Ensure bugs are consistently triaged and scheduled using clear definitions for **Severity** (impact) and **Priority** (urgency).

---

## Table of Contents

1. [Core Concepts: Severity vs Priority](#core-concepts-severity-vs-priority)  
2. [Severity Levels (Definitions, Characteristics, Examples)](#severity-levels-definitions-characteristics-examples)  
   - [Blocker](#blocker)  
   - [Critical](#critical)  
   - [High](#high)  
   - [Medium](#medium)  
3. [Priority Levels (P0 / P1 / P2)](#priority-levels-p0--p1--p2)  
4. [How to Choose Severity (Triage Questions)](#how-to-choose-severity-triage-questions)  
5. [How to Choose Priority (Scheduling Rules)](#how-to-choose-priority-scheduling-rules)  
6. [Recommended Severity ↔ Priority Matrix](#recommended-severity--priority-matrix)  
7. [Examples Based on Common Bug Patterns](#examples-based-on-common-bug-patterns)  
8. [ELITEA Board Field Mapping](#elitea-board-field-mapping)  
9. [Do’s / Don’ts](#dos--donts)  
10. [Maintenance: How to Update This Guide](#maintenance-how-to-update-this-guide)  

---

## Core Concepts: Severity vs Priority

### Severity = Impact (What happens if we do nothing?)
Severity measures how badly the bug affects:
- core workflows (agent creation, execution, pipelines),
- correctness/safety of outputs,
- stability/crashes,
- user trust,
- production readiness.

### Priority = Urgency (When must it be fixed?)
Priority indicates:
- how soon we need the fix,
- whether it must be done in current sprint/release,
- how it competes with other work.

**Key rule:**  
A bug can be **High Severity but lower Priority** (important but not release-blocking), or **Medium Severity but P0** (e.g., security/compliance requirement or executive escalation).

---

## Severity Levels (Definitions, Characteristics, Examples)

> Severity describes **impact** and should be set consistently across teams.

### Blocker

**Description:**  
A blocker issue completely prevents users from creating, saving, running, or deploying AI agents. **No workaround exists.**

**Characteristics:**
- Full system or workflow shutdown
- Data corruption or system errors that stop core functionality
- Crashes during critical flows
- Affects most/all users or environments in scope (DEV/STAGE)

**Examples:**
- Platform login or authentication failure
- “Create Agent” function does not work
- System crashes during agent execution
- No agent can be executed

**Evidence expected (recommended):**
- screenshot/video of the blocking step
- exact error message(s) / stack traces (when available)
- environment + user role + time window

---

### Critical

**Description:**  
Critical bugs impact key system functionality and produce broken or unsafe agent behavior. A workaround may exist but is unreliable or time-consuming.

**Characteristics:**
- Major functional failures
- Compromised accuracy, safety, or correctness
- Severely impacted workflows
- Data integrity risk without total outage

**Examples (aligned to ELITEA patterns):**
- Pipelines executing incorrect steps
- Credentials are not updated (breaks integrations)
- Toolkits/MCP integrations failing intermittently
- Artifacts are not properly indexed causing incorrect answers/hallucinations
- UI settings panels fail to load in a way that blocks configuration

**Evidence expected (recommended):**
- reproducible test data links (pipeline/toolkit/MCP/chat)
- logs and request IDs (if relevant)
- “before vs after” expected vs actual

---

### High

**Description:**  
High severity issues disrupt important system features but allow the platform to remain usable. Workflows are affected, but not fully blocked.

**Characteristics:**
- Significant inconvenience to users
- Partial feature failure
- Degraded performance, repeated retries needed
- Reduced reliability/trust

**Examples:**
- Agent analytics showing inaccurate metrics
- Misleading progress bar
- Slowness or performance degradation when executing agents
- Issues when switching between models requiring retries
- Custom instruction templates not being applied correctly

**Evidence expected (recommended):**
- frequency and conditions (e.g., “reproduces 4/5 times on STAGE”)
- performance timings (if performance-related)
- screenshots showing incorrect metrics or UI state

---

### Medium

**Description:**  
Medium-level issues are non-critical bugs that affect usability, display, or secondary features without interrupting main workflows.

**Characteristics:**
- Minor user experience degradation
- Visual inconsistencies
- Non-blocking functional defects
- Easy and safe workarounds exist

**Examples:**
- UI misalignment or styling issues
- Logs not updating in real time (but functionality works)
- Typos or inaccurate labels
- Non-blocking API warnings

**Evidence expected (recommended):**
- annotated screenshot
- browser/device info if UI-related

---

## Priority Levels (P0 / P1 / P2)

> Priority indicates **urgency and scheduling**.

### P0 — Fix ASAP (Now / Hotfix / Release blocker)
Use when:
- blocks release or critical path work
- major outage for many users
- security/compliance risk
- high risk of data loss/corruption
- urgent escalation with clear justification

**Typical timeline:** same day / 24–48 hours / current sprint.

### P1 — Fix in current release (or next planned sprint)
Use when:
- impacts important workflows
- workaround exists but is painful or unreliable
- must be addressed before “Ready for Public Release”

**Typical timeline:** current sprint or next sprint in the same release.

### P2 — Fix when scheduled (next release or backlog)
Use when:
- low risk / low impact
- cosmetic or minor feature issue
- safe workaround exists
- does not impact release goals

**Typical timeline:** planned when capacity allows.

---

## How to Choose Severity (Triage Questions)

Answer these in order:

1) **Can users complete core workflows (create/save/run/deploy agents)?**  
- No → **Blocker**

2) **Is correctness/safety compromised (wrong pipeline steps, wrong tool results, missing indexing leading to incorrect answers)?**  
- Yes → **Critical**

3) **Is the platform usable but unreliable or severely inconvenient (retries, timeouts, major features partially broken)?**  
- Yes → **High**

4) **Is it mainly visual/UX, minor defects, small inconsistencies?**  
- Yes → **Medium**

> If unsure between two levels, choose the higher severity and add a note: “Severity tentative — needs triage.”

---

## How to Choose Priority (Scheduling Rules)

1) **Does it block the current release milestone or sprint commitments?**  
- Yes → **P0** (or P1 if workaround exists and risk is contained)

2) **Is it required before “Ready for Public Release”?**  
- Usually **P1**

3) **Is it acceptable to ship and fix later?**  
- Usually **P2**

4) **Is it a post-release urgent fix?**  
- If it must ship as hotfix → **P0** + set **Hotfix=Yes** in Project fields.

---

## Recommended Severity ↔ Priority Matrix

Default guidance (override only with justification):

| Severity \ Priority | P0 (ASAP) | P1 (Current release) | P2 (Planned later) |
|---|---:|---:|---:|
| **Blocker** | ✅ Default | ⚠️ Rare | ❌ |
| **Critical** | ✅ Often | ✅ Default | ⚠️ Rare |
| **High** | ⚠️ Sometimes | ✅ Default | ✅ Sometimes |
| **Medium** | ⚠️ Rare | ⚠️ Sometimes | ✅ Default |

**Acceptable overrides:**
- **Medium + P0**: security/compliance/legal, or major customer impact with explicit escalation
- **Critical + P2**: occurs only in low-scope flow, safe workaround exists, not in current roadmap

---

## Examples Based on Common Bug Patterns

These examples are aligned with patterns commonly seen in `elitea.github.io` bugs (e.g., UI/flow issues, pipeline/tooling behavior, chat/agent experiences).

### Example A — Blocker + P0
**Symptom:** “Create Agent” fails for most users; cannot save agent.  
- Severity: **Blocker**  
- Priority: **P0**  
- Reason: core workflow unavailable, no workaround.

### Example B — Critical + P1 (or P0 if release-blocking)
**Symptom:** Pipeline executes incorrect steps or uses wrong toolkit selection leading to incorrect outputs.  
- Severity: **Critical**  
- Priority: **P1** (P0 if it blocks current release acceptance)  
- Reason: correctness compromised; unsafe/unreliable output.

### Example C — High + P1
**Symptom:** Summarization intermittently doesn’t produce output; retries needed; users can continue but lose productivity.  
- Severity: **High** (Critical if it breaks safety/correctness or blocks acceptance criteria)  
- Priority: **P1**  
- Reason: major inconvenience; platform still usable.

### Example D — Medium + P2
**Symptom:** UI alignment issue or minor label typo in settings panel.  
- Severity: **Medium**  
- Priority: **P2**  
- Reason: cosmetic; does not block workflow.

---

## ELITEA Board Field Mapping

When reporting/triaging a bug in **ELITEA Board**:

- **Priority** field: `P0 | P1 | P2`
- **Severity** field: `Blocker | Critical | High | Medium`

> If your project uses additional values (e.g., “Low”), update this guide and the templates accordingly.

---

## Do’s / Don’ts

### Do
- Set **Severity** based on impact.
- Set **Priority** based on milestone/sprint/release urgency.
- Add a short justification for **Blocker** and/or **P0**.
- Re-evaluate severity/priority after triage if new information appears.

### Don’t
- Don’t use Priority to “signal impact” (use Severity for that).
- Don’t inflate severity to get faster fixes.
- Don’t leave both unset—triage requires both.

---

## Maintenance: How to Update This Guide

- Update definitions only with QA Lead + Eng Lead alignment.
- Keep the matrix stable; update examples as patterns evolve.
- Review once per release (or quarterly).
- Add new examples based on recurring patterns from recent bugs.
