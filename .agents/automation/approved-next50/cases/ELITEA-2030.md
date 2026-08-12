---
id: ELITEA-2030
title: "Pipeline — Add Node Menu"
priority: high
type: functional
module: pipelines
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:pipelines]
requirements: []
---

# ELITEA-2030: Pipeline — Add Node Menu

**Module:** pipelines · **Priority:** high · **Type:** functional

**Objective:** Verify that the "Add node" menu displays all available node types and that selecting a type adds the node to the canvas with its configuration panel open.

---

## Preconditions

- User is logged in to the Elitea platform.
- A pipeline is open in Flow view.

---

## Test Data

| Field | Value |
|-------|-------|
| Expected node types | Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit |

---

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Open a pipeline in Flow view | Pipeline canvas is displayed |
| 2 | Click "Add node" button (with "+" icon) | A popup menu appears |
| 3 | Verify a popup menu appears with the following node type options: Agent, Code, Custom, Decision, Human-in-the-loop, LLM, MCP, Printer, Router, State modifier, Toolkit | All 11 node types are listed in the menu |
| 4 | Click "LLM" to add an LLM node | LLM node is added to the canvas |
| 5 | Verify a new LLM node appears on the canvas with default configuration panel open | LLM node is visible on canvas and its configuration panel is open |
| 6 | Press Escape or click outside to close menu without adding (verify menu dismisses) | Menu closes without adding a node |

---

## Expected Final State

The "Add node" menu lists all 11 node types. Selecting a type adds the node to the canvas and opens its configuration panel. The menu dismisses when Escape is pressed.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All 11 node types are listed, LLM node is added and its panel opens, menu dismisses on Escape.

**Fail:**
- Any step produces an error or unexpected result.
- Node types are missing from the menu, node is not added, or menu does not dismiss.
