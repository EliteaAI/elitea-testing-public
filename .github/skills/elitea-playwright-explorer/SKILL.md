---
name: elitea-playwright-explorer
description: Navigates and explores the ELITEA platform at https://next.elitea.ai/app/ using Playwright browser automation. Handles login via "Login with EAPM", navigates to the relevant feature page, and returns a structured UI exploration report covering page layout, controls, workflows, and observed behaviors. Use this skill when you need a factual UI report of an ELITEA feature before generating checklists or test cases.
---

# Elitea Playwright Explorer

## OBJECTIVE

Navigate and explore the ELITEA platform at `https://next.elitea.ai/app/` using browser automation. Return a detailed structured report of the UI layout, available controls, tabs, buttons, workflows, and any observed behaviors relevant to a provided feature or topic.

---

## INPUT

- **Feature or topic** to explore (e.g., "Artifacts", "Agent Toolkit configuration", "Chat file attachments")
- **Optional:** specific page URL or navigation path to go to directly

---

## EXECUTION FLOW

1. **Navigate** to `https://next.elitea.ai/app/`

2. **Check accessibility:**
   - If a login page is detected:
     1. Click the **"Login with EAPM"** button.
     2. Wait for the authentication flow to complete and the app to fully load.
     3. If still inaccessible after the first attempt, retry up to **3 more times** (4 total), waiting between each retry.
     4. If login succeeds, proceed to step 3.
     5. If still inaccessible after all 4 attempts, STOP and return: `"Unable to access https://next.elitea.ai/app/ after 4 login attempts."`

3. **Select the Private project context:**
   - After login, locate the project/workspace switcher in the UI.
   - Select the **"Private"** project. Do NOT open, click into, or interact with any other project (shared, public, or team projects).
   - All subsequent navigation must remain within the Private project context.

4. **Navigate to the relevant page:**
   - If a specific URL or path was provided, navigate there directly (ensure it is within the Private project scope).
   - Otherwise, examine the top-level navigation (sidebar tabs, buttons such as Agents, Chat, Artifacts, Pipelines, etc.) and navigate to the section most relevant to the provided feature/topic.

5. **Explore the page thoroughly:**
   - Take a snapshot of the page structure.
   - Identify and list all visible UI elements: tabs, buttons, forms, dropdowns, modals, toggles, file upload controls, tables, etc.
   - Navigate into sub-sections, dialogs, or nested views where relevant.
   - Note any interactive workflows (e.g., create/edit/delete flows, upload flows, configuration panels).
   - Capture any error states, loading indicators, or empty states visible.

6. **Return a structured report** containing:
   - **Page URL(s) visited**
   - **Top-level navigation elements observed**
   - **Feature-specific UI elements** (grouped by section/tab)
   - **Available actions/workflows** (step-by-step description of what can be done)
   - **Observed behaviors** (e.g., validation messages, success/error feedback, loading states)
   - **Edge cases or notable UI patterns** spotted

---

## CONSTRAINTS

- **Private project only:** Only navigate and explore within the **Private** project. Do NOT open, switch to, or interact with any shared, public, or team project.
- **No destructive actions:** Do NOT perform any action that modifies, deletes, overwrites, or submits real data. This includes but is not limited to: clicking Delete, Remove, or Confirm-delete buttons; saving or submitting forms with real data; triggering publish or deploy actions.
- Do NOT expose credentials, tokens, or session data in the report.
- Do NOT navigate outside of `https://next.elitea.ai/`.
- If Playwright tools fail or the page is unreachable, STOP and report the error clearly.
- Return only factual observations — do not speculate about backend behavior.
