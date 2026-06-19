---
name: test-deduplication
description: Analyzes pytest test files to identify duplicate or redundant tests that check the same functionality but are named differently. Use when the user asks to deduplicate tests, find redundant tests, or analyze test coverage in a test class. Especially useful for UI test suites where similar test logic may be repeated with minor variations.
argument-hint: <test-file-path>
allowed-tools:
  - Read
  - Edit
---

# Test Deduplication Skill

Identifies duplicate and redundant tests in pytest test files by analyzing test logic, assertions, and functionality.

## When to Use

Use this skill when:
- User asks to "deduplicate tests" or "find duplicate tests"
- User wants to know which tests are redundant
- User mentions tests that "do the same thing"
- User asks to analyze test coverage for a specific test class
- User provides a test file path and wants analysis

## How It Works

This skill performs semantic analysis of test methods to identify:

1. **Exact duplicates** - Tests with identical logic under different names
2. **Functional duplicates** - Tests checking the same functionality with minor variations
3. **Setup duplicates** - Tests with identical setup but different assertions (may indicate poor test organization)
4. **Subset tests** - Tests where one is a superset of another's checks

## Analysis Process

### Step 1: Read the Test File

```python
from pathlib import Path

# Get the test file path from user
test_file_path = # user provided path
content = Path(test_file_path).read_text()
```

### Step 2: Parse Test Structure

Identify test classes and methods. For each test method, extract:

**Identification:**
- Method name
- Test class name
- Docstring (TC-ID, description)
- Markers (p0, p1, smoke, etc.)

**Test Logic:**
- Page objects used
- Methods called on page objects
- Assertions made
- Expected behaviors verified

**Example extraction:**
```python
# For test_send_text_message:
{
    "name": "test_send_text_message",
    "class": "TestSendingMessages",
    "tc_id": "TC-CHAT-004",
    "description": "Send a text message",
    "markers": ["p0"],
    "page_objects": ["ChatPage"],
    "actions": [
        "navigate_to_chat",
        "send_message",
        "wait_for_ai_response"
    ],
    "assertions": [
        "is_input_empty() -> True",
        "get_message_count() > initial_count"
    ],
    "verifies": [
        "Message is sent",
        "Message appears in chat history",
        "Input field is cleared"
    ]
}
```

### Step 3: Compare Tests

For each pair of tests in the same class, calculate similarity:

**Action Similarity:**
- Percentage of shared page object method calls
- Order of operations (sequential vs different flow)

**Assertion Similarity:**
- Number of shared assertions
- Assertion target overlap (same elements checked)

**Functional Similarity:**
- Do they test the same feature?
- Is one a strict subset of the other?

**Similarity Scoring:**
```
- 90-100% similar → Exact duplicate (different names only)
- 70-89% similar → Functional duplicate (minor variations)
- 50-69% similar → Overlapping coverage (consider consolidation)
- <50% similar → Distinct tests
```

### Step 4: Generate Report

Output should be structured as:

```markdown
# Test Deduplication Report
## File: `path/to/test_file.py`
## Class: `TestClassName`

### Exact Duplicates (90-100% similar)

#### Test Pair 1: test_a vs test_b
**Similarity:** 95%

**test_a (TC-001):**
- Verifies: X, Y, Z
- Actions: navigate, click, assert
- Markers: p0, smoke

**test_b (TC-002):**
- Verifies: X, Y, Z
- Actions: navigate, click, assert  
- Markers: p1

**Analysis:**
Both tests verify the same functionality with identical logic. Only difference is test names and markers.

**Recommendation:**
Keep `test_a` (higher priority marker p0). Remove `test_b` or merge into `test_a` if TC-002 coverage is needed.

---

### Functional Duplicates (70-89% similar)

#### Test Pair 2: test_c vs test_d
**Similarity:** 78%

**test_c (TC-003):**
- Verifies: Input field visible, editable
- Actions: navigate, check visibility, check editable

**test_d (TC-004):**
- Verifies: Input field visible, editable, send button visible
- Actions: navigate, check visibility, check editable, check button

**Analysis:**
`test_d` is a superset of `test_c`. Both navigate to the same page and check input field properties. `test_d` adds one additional check for send button.

**Recommendation:**
Merge `test_c` into `test_d`. Update docstring to cover both TC-003 and TC-004. Or, if tests serve different purposes (load test vs functional test), keep both but document why.

---

### Overlapping Coverage (50-69% similar)

#### Test Pair 3: test_e vs test_f
**Similarity:** 62%

**test_e (TC-005):**
- Verifies: Can send message with Enter key
- Actions: navigate, type message, press Enter, verify sent

**test_f (TC-006):**
- Verifies: Can send message with button click
- Actions: navigate, type message, click send, verify sent

**Analysis:**
Similar setup and verification, but different user actions (Enter vs button). Both are valid test cases for different interaction methods.

**Recommendation:**
Keep both tests. They verify different user paths to achieve the same outcome. Consider parameterization if more send methods are added in future.

---

## Summary

**Total tests analyzed:** 24
**Exact duplicates:** 2 pairs (4 tests)
**Functional duplicates:** 3 pairs (6 tests)  
**Overlapping coverage:** 5 pairs (10 tests)
**Distinct tests:** 14

**Recommendation:**
- Remove/merge 4 exact duplicate tests
- Review 6 functional duplicates for consolidation
- Keep overlapping tests (different interaction paths)

**Potential test reduction:** 4-10 tests (17-42% reduction)
```

## Implementation Guidelines

### Read the Test File

```python
import ast
from pathlib import Path

test_file = Path(user_provided_path)
content = test_file.read_text()
tree = ast.parse(content)
```

### Extract Test Classes

```python
test_classes = []
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
        test_classes.append(node)
```

### For Each Test Method

Parse:
- Function name
- Docstring (contains TC-ID and description)
- Decorator markers (`@pytest.mark.p0`, etc.)
- Function body (calls, assertions)

### Compare Test Logic

Build a representation of each test:
- List of method calls on page objects
- List of assertions
- Variables checked in assertions

Compare these representations to find similarity.

### Scoring Algorithm

```python
def calculate_similarity(test1, test2):
    # Action similarity (Jaccard index)
    actions1 = set(test1["actions"])
    actions2 = set(test2["actions"])
    action_sim = len(actions1 & actions2) / len(actions1 | actions2)
    
    # Assertion similarity
    asserts1 = set(test1["assertions"])
    asserts2 = set(test2["assertions"])
    assert_sim = len(asserts1 & asserts2) / len(asserts1 | asserts2)
    
    # Weighted average
    similarity = 0.6 * action_sim + 0.4 * assert_sim
    return similarity * 100  # Return as percentage
```

### Edge Cases

**Setup vs Behavior Tests:**
Some tests may have identical setup but check different things. Example:
- `test_page_loads` - checks page elements exist
- `test_send_message` - checks message sending works

These should NOT be flagged as duplicates even if they share navigation logic.

**Marker Differences:**
Tests with different priority markers (p0 vs p2) might be intentional duplicates for different test runs. Flag these but note the marker difference in the recommendation.

**Parameterized Tests:**
If tests could be parameterized instead of duplicated, mention this in recommendations:
```python
# Instead of test_send_with_enter and test_send_with_button
@pytest.mark.parametrize("method", ["enter", "button"])
def test_send_message(page, conversation_id, method):
    # ...
```

## Output Format

Always output as Markdown with:
1. **Header** - File and class name
2. **Duplicate sections** - Grouped by similarity level
3. **Per-pair analysis** - Side-by-side comparison
4. **Recommendations** - Specific, actionable advice
5. **Summary** - Statistics and overall recommendations

## Example User Interactions

**User:** "Check what tests I have for test_chat_interface.py and remove duplicates"

**You:**
1. Read the test file
2. Analyze all test classes and methods
3. Generate the deduplication report (as shown above)
4. Present the report to the user
5. Ask: "Would you like me to implement the recommended consolidations?"

**User:** "Yes, merge the exact duplicates"

**You:**
1. For each exact duplicate pair in the report
2. Keep the higher-priority test (p0 > p1 > p2 > p3)
3. Update docstring to include both TC-IDs if applicable
4. Delete the redundant test method
5. Show the user what was changed

## Important Notes

**Don't Auto-Delete:**
Never automatically remove tests without user confirmation. Always generate the report first and get approval.

**Consider Test Intent:**
Two tests may look similar in code but serve different purposes:
- Smoke test vs full test
- Happy path vs edge case
- Different priority levels for different test runs

Always read docstrings and markers to understand intent before flagging as duplicate.

**Preserve Coverage:**
If merging tests, ensure all TC-IDs and verifications are preserved in the consolidated test's docstring.

**Update Docstrings:**
When merging, update the docstring to reflect combined coverage:
```python
def test_message_input_functional(self, page, conversation_id):
    """TC-CHAT-001, TC-CHAT-002: Page loads and message input is functional.
    
    Verifies:
    - Page loads without errors (TC-CHAT-001)
    - Message input is visible and editable (TC-CHAT-001, TC-CHAT-002)
    - Send button is visible (TC-CHAT-002)
    - Attach files button is visible (TC-CHAT-002)
    """
```

## Anti-Patterns to Avoid

❌ **Don't flag tests with shared setup as duplicates:**
```python
# These are NOT duplicates (different assertions)
def test_page_loads(page):
    chat = ChatPage(page)
    chat.navigate()  # Shared setup
    assert chat.is_loaded()  # Different check

def test_send_button_exists(page):
    chat = ChatPage(page)
    chat.navigate()  # Shared setup
    assert chat.send_button.is_visible()  # Different check
```

❌ **Don't merge tests with different user paths:**
```python
# Keep both (different interaction methods)
def test_send_with_enter(page):
    # Tests keyboard interaction
    
def test_send_with_button(page):
    # Tests mouse interaction
```

✅ **Do flag tests that verify the exact same thing:**
```python
# These ARE duplicates (rename one of them)
def test_can_send_message(page):
    chat.send_message("Hello")
    assert chat.get_message_count() == 1
    
def test_message_appears_after_send(page):
    chat.send_message("Hello")
    assert chat.get_message_count() == 1
```

## Success Criteria

A good deduplication report should:
- Identify all true duplicates (no false negatives)
- Not flag distinct tests as duplicates (no false positives)
- Provide clear rationale for each flagged pair
- Give actionable recommendations
- Help reduce test suite size without losing coverage
