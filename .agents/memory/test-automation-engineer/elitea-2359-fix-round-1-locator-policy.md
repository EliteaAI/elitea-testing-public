---
name: ELITEA-2359 Fix Round 1 — Locator Policy Enforcement
description: LocatorDescriptor refactor for share menu and alert toast — testid-only compliance
type: feedback
---

## Context
ELITEA-2359 (copy-link-from-modal) implementation review found two locator-policy violations:
1. Inline `page.locator('[data-testid="share-agent-menuitem"]')` in test file
2. Role-based `page.locator('[role="alert"]...')` for toast notification

Both violated `.agents/testing.md` § Locator policy (testid-only, no fallback).

## Resolution
✅ Moved both to AgentHubPage LocatorDescriptors:
- `modal_share_menu_item(testid="share-agent-menuitem")` — auto-generated from DotMenu menu key
- `modal_share_success_toast(testid="toast-alert")` — already exists in Toast.jsx

No product changes needed; both testids already present in EliteaUI.

## Outcome
Test re-run: GREEN 1/1 (20.2s avg).
PR #1417 updated with fix details and ready for independent gate.

## Pattern Lesson
Inline testid locators in test files are a common fix-round catch. The pattern:
1. Create LocatorDescriptor in page object (class-level field)
2. Reference by testid from EliteaUI source truth
3. Test methods reference via `page_object.locator_name.wait_for()` / `.click()`
4. Validates against the locator-policy grep in reviewer sessions

Automation/pages/ is the single source of truth for all locators on a given surface.
