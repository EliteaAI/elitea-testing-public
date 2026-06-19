# ELITEA Issue Labeling & Project Fields Guide

This document explains **how to label issues in ELITEA**, how labels are categorized and colored, and how they work together with **GitHub Projects fields** (Type, Priority, Criticality, Environment, etc.).

> **Key rule:** Labels are for **classification**, not workflow state.  
> Workflow state (e.g., In progress / Done) must be tracked via **Projects fields**, not labels.

---

## 1) Why we use a strict labeling system

We aim for:
- **Fast triage** (find the right team and product area quickly)
- **Consistent reporting** (no duplicates between labels and Projects fields)
- **Actionable RCA** (prevent repeats of incidents/bugs)

To achieve this we keep labels:
- **namespaced** (e.g., `feat:chat`, `eng:backend`)
- **owned** (admins maintain them)
- **stable** (contributors do not create ad-hoc labels)

---

## 2) Label governance (who can do what)

### Who can create/update labels
- **Only repository admins** can create, rename, or delete labels.

### What contributors must NOT do
- Do **not** create new labels “on the fly”.
- Do **not** invent new labels when using **ELITEA Agents / AI / Pipelines** while reporting issues.

If you can’t find a label that fits:
1. Pick the closest existing label(s) (usually one `feat:*` + optionally one `eng:*` + optional `nfr:*`/`int:*`).
2. Add a comment: **“Label missing: suggest `feat:xyz`”**.
3. Admin will review and add/merge labels if needed.

---

## 3) Label categories (namespaces) and color schema

We use prefixes to keep labels easy to search and to avoid duplicates.

| Category | Prefix | Color | Meaning |
|---|---|---:|---|
| Product features / modules | `feat:` | `#1D4ED8` | **Where** in the product the issue belongs |
| Engineering ownership | `eng:` | `#7C3AED` | **Who** should work on it (discipline/workstream) |
| Non-functional quality | `nfr:` | `#F59E0B` | **Quality attribute** impacted (a11y, perf, observability…) |
| Integrations | `int:` | `#0F766E` | External system/provider involved |
| Root Cause Analysis | `rca:` | `#DC2626` | **Why** it happened / escaped (post-triage) |
| Triage / hygiene | `meta:` | `#6B7280` | Housekeeping (duplicate, invalid, needs info, etc.) |

---

## 4) How to label an issue (recommended pattern)

### Minimum recommended labeling
For most issues add:
1. **One** `feat:*` label (primary impacted product area)
2. Optionally **one** `eng:*` label (routing/ownership)
3. Optionally add `nfr:*` / `int:*` labels if applicable

### Examples
- “Chat UI freezes while streaming long response”
  - `feat:chat`
  - `eng:frontend`
  - `nfr:performance`

- “Indexer fails for SharePoint documents”
  - `feat:indexer`
  - `int:sharepoint`
  - `eng:backend`

- “Monitoring dashboard missing metrics”
  - `feat:monitoring`
  - `nfr:observability`
  - `eng:backend` (or `eng:frontend` depending on root)

---

## 5) Label category usage rules (DOs and NOT TO DOs)

### `feat:` — Product feature/module labels
**Use when:** the issue affects a specific ELITEA module/feature.  
**DO**
- Pick the most specific product module (`feat:chat`, `feat:mcp`, `feat:toolkits`).
- Use **one primary** `feat:*` label (add a second only if truly cross-feature).

**DON’T**
- Don’t create new feature labels yourself.
- Don’t use feature labels as “issue type” (bug/enhancement). Use **Type field** (see section 8).

---

### `eng:` — Engineering ownership labels
**Use when:** you know which engineering discipline owns the fix.

**DO**
- Use for routing: `eng:frontend`, `eng:backend`, `eng:api`, `eng:devops`, `eng:qa`, `eng:copilot`, `eng:migration`.
- Prefer `eng:api` when the primary work is API contract/endpoints/OpenAPI behavior.

**DON’T**
- Don’t use `eng:*` to represent a feature.
- Don’t assign multiple `eng:*` labels unless it truly requires multiple teams.

---

### `nfr:` — Non-functional quality labels
**Use when:** the main concern is a quality attribute (not just feature correctness).

**DO**
- Use `nfr:accessibility` for WCAG/a11y issues (keyboard, screen reader, contrast).
- Use `nfr:observability` for logging/metrics/tracing gaps or diagnostics problems.
- Use `nfr:usability` for UX friction and clarity problems.
- Use `nfr:performance` when the key issue is speed/latency.

**DON’T**
- Don’t use NFR labels instead of the actual product area label (`feat:*`).

---

### `int:` — Integration labels
**Use when:** the issue involves an external system/provider.

**DO**
- Use `int:*` alongside a `feat:*` label whenever possible.
- If unsure which product module owns the integration, still add the `int:*` label.

**DON’T**
- Don’t create new integration labels; request them via comment.

---

### `meta:` — Hygiene/triage labels
**Use when:** you need to keep the tracker clean.

**DO**
- `meta:needs-info` when the report is missing steps/logs/expected vs actual.
- `meta:duplicate` when it’s already tracked elsewhere.
- `meta:needs_refinement` when scope/AC/context must be clarified before work starts.
- `meta:reported-by-support` when issue was reported by end users/support.

**DON’T**
- Don’t use `meta:*` as a substitute for Status in Projects.

---

## 6) RCA labels (`rca:`) — how and why to use them

### What RCA labels are
`rca:*` labels capture the **root cause category** of *why the issue happened or escaped*, not what feature it belongs to.

They help us:
- reduce repeat incidents
- identify systemic process gaps (testing, requirements, integration boundaries)
- prioritize preventive work (automation, observability, clearer AC)

### When to apply RCA labels
Apply RCA labels:
- after triage is complete, **or**
- after a fix is identified/merged, **or**
- after post-incident review

RCA labels are not required at issue creation time if the root cause is unknown.

### How many RCA labels to use
- Usually **one** RCA label is enough.
- Use two only when a second factor is clearly confirmed (e.g., unclear requirements + missing automation).

### Common RCA examples
- Issue escaped because no test existed:
  - `rca:no-test-case`
- Issue escaped because automation didn’t cover it:
  - `rca:missing-automation`
- Integration mismatch / boundary bug:
  - `rca:integration-issue`
- Requirement/AC unclear:
  - `rca:unclear-requirement`
- Implementation gap:
  - `rca:missing-functionality`
- Regression from previous behavior:
  - `rca:regression`
- Environment/config mismatch:
  - `rca:env-config`
- Bad or unexpected data:
  - `rca:data-quality`

### RCA DOs / NOT TO DOs
**DO**
- Add the RCA label **only when confirmed** (or very strongly evidenced).
- Add a short comment explaining the choice (one sentence is enough).

**DON’T**
- Don’t use RCA as blame; it’s a learning tool.
- Don’t apply RCA labels if you don’t know the cause yet.

---

## 7) “Do not create new labels” reminder (especially with AI/Agents/Pipelines)

When using ELITEA (Agents / AI / Pipelines) to draft or file issues:
- **Do not** let AI create new labels.
- Always select labels from the existing taxonomy.
- If AI suggests new labels, convert them into:
  - a comment suggestion, or
  - an existing closest label (preferred)

---

## 8) Project Fields: Type (mandatory)

**Type is not a label.** It is a **Projects field** and must be used to describe what the item is.

Use **Type** to classify:
- Bug
- Enhancement
- Task
- Feature
- Epic
- Design
- Story
- QA
- Q&A
- Documentation
- Support

> If you are unsure, choose the closest option and add a short note in the issue body.

---

## 9) Project Fields: Priority, Criticality, Environment (how to use)

### Priority (P0/P1/P2)
Use **Priority** to answer: *How urgently does the team need to act?*

General guidance:
- **P0**: must address immediately, active impact, blocks release/production usage
- **P1**: high urgency, significant impact, should be scheduled ASAP
- **P2**: normal priority, can be planned in regular flow

### Criticality (Blocker/Critical/Relatively Critical/Not Critical)
Use **Criticality** to answer: *How severe is the impact if it occurs?* (independent of urgency)

- **Blocker**: stops core user journeys or system is unusable
- **Critical**: major functionality broken, severe degradation, or high-risk issue
- **Relatively Critical**: meaningful impact with workaround available
- **Not Critical**: minor impact, cosmetic, low-risk

> Example: something can be **Critical** but not **P0** if a workaround exists and it doesn’t block current release.

### Environment (Nexus/Next/Stage/Dev/All/Client_env)
Use **Environment** to answer: *Where does the issue reproduce?*

- **Dev/Stage/Next/Nexus**: internal environments
- **All**: environment-independent
- **Client_env**: customer environment (provide details in issue)

**DO**
- Always specify the environment when reporting bugs.
- If you picked `Client_env`, include customer-safe details: URL domain (if allowed), time window, logs if possible.

**DON’T**
- Don’t create labels for environments. Environment is a field.

---

## 10) DOs and NOT TO DOs (quick checklist)

### DO
- Use **one `feat:*`** label (primary product area)
- Add **one `eng:*`** label when routing is clear
- Add **`nfr:*`** for quality attributes (a11y, perf, observability…)
- Add **`int:*`** when an external system is involved
- Use Projects fields for **Type / Priority / Criticality / Environment**
- Add **RCA labels** after confirmation

### NOT TO DO
- Don’t create new labels (only admins)
- Don’t use labels for Type, Priority, Status, or Environment
- Don’t add many `feat:*` or many `eng:*` labels “just in case”
- Don’t guess RCA: apply it only after confirmation

---

## 11) Maintainers section (admins only)

### Updating labels
Admins should:
- keep the taxonomy stable
- merge duplicates instead of creating near-identical labels
- maintain prefix + color consistency
- keep GitHub label descriptions **≤ 100 characters**
- document changes in this file when making significant updates

---

## Appendix A: Current canonical label namespaces
- `feat:*` product features/modules
- `eng:*` engineering ownership
- `nfr:*` non-functional quality
- `int:*` integrations/ecosystem
- `rca:*` root cause categories
- `meta:*` triage/hygiene
