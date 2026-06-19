---
name: ui-test-creator
description: Creates UI tests focused on user flows and meaningful variations, not preconditions. Use when adding new UI tests for a feature. Ensures tests exercise real user behavior, not implementation details.
argument-hint: <feature-description-or-page>
allowed-tools:
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - Bash
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_click
  - mcp__playwright__browser_type
---

# UI Test Creator

Creates UI tests that exercise real user flows, not preconditions.

**For syntax, patterns, timeouts, markers:** See `.claude/rules/ui-tests.md`

## Core Philosophy

**Test User Outcomes, Not Setup Steps**

A user doesn't care if a toggle can be switched on - they care if enabling it produces the expected result.

| Don't Test (Preconditions) | Test Instead (User Flows) |
|---------------------------|---------------------------|
| "Can I enable feature X?" | "When I enable X and do A, I get B" |
| "Can I select option Y?" | "With option Y, different inputs give appropriate outputs" |
| "Does button Z appear?" | "Clicking Z produces expected result" |

## The Anti-Pattern to Avoid

**BAD - Separate tests for each precondition:**
```python
def test_toggle_feature_enabled():
    page.enable_feature()
    assert feature_is_enabled()  # Precondition, not outcome

def test_select_model():
    page.select_model("GPT-5")
    assert selected_model() == "GPT-5"  # Precondition, not outcome

def test_feature_with_model():  # Only useful test
    page.enable_feature()
    page.select_model("GPT-5")
    page.do_action("input")
    assert result_is_valid()
```

**GOOD - Complete flow + variations:**
```python
@pytest.mark.p1
def test_feature_with_detailed_input(page, fixture):
    """Full user flow with realistic input."""
    page.enable_feature()
    page.select_model("GPT-5")
    page.do_action("A rich, realistic description...")
    page.wait_for_result()
    assert result_is_valid()

@pytest.mark.p2
def test_feature_with_minimal_input(page, fixture):
    """Variation: works with minimal input too."""
    page.enable_feature()
    page.select_model("GPT-5")
    page.do_action("Simple request")
    page.wait_for_result()
    assert result_is_valid()
```

## What NOT to Create as Separate Tests

- Toggle/switch states (if toggle fails, main test fails anyway)
- Dropdown selections (if selection fails, main test fails)
- Button visibility (unless visibility IS the feature)
- UI element presence (unless presence IS the requirement)

**Where preconditions belong:** Smoke tests, setup fixtures, page object assertions.

## Creating Tests - Process

### 1. Identify User Goal
"What is the user trying to accomplish?"

### 2. Map Complete Flow
List every action start to finish:
1. Navigate
2. Enable/configure
3. Primary action
4. Wait for result
5. Verify outcome

### 3. Identify Meaningful Variations
What different inputs/paths produce different (but valid) outcomes?
- Input variations: detailed vs minimal, edge cases
- Path variations: different models, options
- State variations: empty state, pre-existing data

### 4. Write Tests
- **P1 Primary:** Complete flow with realistic input
- **P2 Variations:** Different inputs/paths that explore edges

## Exploring Unfamiliar Features

1. **Use Playwright MCP** - Navigate, snapshot, identify interactions
2. **Check page objects** - `grep -l "feature" pages/*.py`
3. **Add missing methods** - Use page-object-generator skill

## Checklist

- [ ] Primary test covers complete user flow
- [ ] Setup steps inline, not separate tests
- [ ] At least one variation test
- [ ] Assertions verify user-visible outcomes
- [ ] Follows `.claude/rules/ui-tests.md` for syntax/patterns
