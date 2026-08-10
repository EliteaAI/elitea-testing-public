---
name: No inline page.locator() in test spec files
description: Locators must use page-object methods, never inline in test code
type: feedback
---

ELITEA-2355 fix round 2: all inline `page.locator(f'[data-testid="..."]')` calls replaced with page-object method calls.

**The violation:** Test file had four inline calls:
```python
# BAD - inline locators
like_button = page.locator(f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]')
```

**The fix:** Use the existing page-object method:
```python
# GOOD - page-object method
like_button = agent_hub.get_like_button(liked_agent_id)
```

**Why this matters:**
- Violates `.agents/role-overrides.md` locator policy: "Locators are class-level LocatorDescriptor fields ONLY — never inside methods or spec files"
- Page objects exist precisely to centralize selectors (DRY)
- AgentHubPage already has `LIKE_BUTTON` constant + `get_like_button()` method — reuse them
- Dynamic (runtime-parameterized) testids still use class-level template constants + methods, NOT inline f-strings

**Detection:** Reviewer's mechanical grep finds added lines with inline locators in diff (pattern: `get_by_role|get_by_label|...page\.locator|\.locator\(`)

**Lesson:** Before writing a locator in a test, check if the page object already has a method for it. AgentHubPage covers all catalog interactions — use `get_like_button()`, `click_like_button()`, `is_agent_liked()`, etc.
