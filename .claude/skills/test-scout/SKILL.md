---
name: test-scout
description: Analyzes existing test suite to determine if a test case can be added to an existing test or requires a new test. Use when the user wants to create new tests - scouts the codebase first to avoid duplication and find the right location. Triggers on "create test for X", "add test for Y", "write test that does Z", or when planning new test implementation.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Test Scout

Analyzes existing tests before creating new ones and returns **one of three verdicts**:

1. **ALREADY COVERED** — existing tests fully cover this flow. Nothing to do.
2. **UPDATE EXISTING** — a test exists but needs a new variation method added.
3. **CREATE NEW** — no test covers this flow. Specify file and class.

**Goal:** Give a single, decisive answer. No ambiguity. No suggestions for additional tests.

> **Evidence rule:** Verdicts must be based only on tests you personally found using `Read`, `Grep`, or `Glob` in this codebase. Examples shown throughout this skill are hypothetical patterns — they are never evidence of actual coverage.

## Analysis Process

### Step 1: Understand the Test Case

Extract from user's description:
- **Feature/functionality** being tested
- **User flow** or API endpoint
- **Domain** (chat, agents, pipelines, etc.)
- **Test type** (UI or API)
- **Key actions** (what user does)
- **Expected outcome** (what should happen)

### Step 2: Find Candidate Tests

Search existing tests for similar coverage:

```bash
# Find tests in relevant domain
Glob(pattern="tests/ui/{domain}/test_*.py")  # or tests/api/

# Search for related test names
Grep(pattern="def test_.*{feature_keyword}", path="tests/", output_mode="content")

# Search for tests using same page object
Grep(pattern="from pages.{page}_page import", path="tests/ui/{domain}/", output_mode="content")
```

### Step 3: Analyze Candidates

For each candidate test, check:

**Similarity signals (update existing):**
- Same test class
- Same page object / API client
- Same fixtures
- Similar user flow (e.g., both test chat message features)
- Test is a variation (different input, same flow)

**Difference signals (create new):**
- Different user flow
- Different preconditions/setup
- Different domain (chat vs agents)
- Different test type (UI vs API)
- Test would make existing test too complex

### Step 4: Make Recommendation

#### ALREADY COVERED — when:
- Existing test(s) cover the exact same user flow end-to-end
- The new request is the same sequence of actions with no meaningfully different outcome
- The flow is tested with both a realistic and a minimal/edge-case input

Return **ALREADY COVERED**. Stop. Do not suggest alternatives or variations.

**Example:**
```
Existing: test_<feature>_with_<input_a>() + test_<feature>_with_<input_b>()
New case: same sequence of actions, different wording of the prompt
→ ALREADY COVERED — both flows are identical in action and assertion.
```

#### UPDATE EXISTING — when:
- The flow differs in **one meaningful dimension** not yet tested (different model, different state, error path)
- The new method fits cleanly in the existing class without bloating it

**Example:**
```
Existing: test_<feature>_with_<standard_input>()
New case: same feature, but after toggling a setting off and back on
→ UPDATE EXISTING: add test_<feature>_after_<state_change>() to Test<Feature>
```

#### CREATE NEW — when:
- Different user flow or preconditions
- Different domain or page object
- Existing test class is already large (>3 test methods)

**Example:**
```
Existing: test_<action>_<basic_variant>()
New case: same action area, but requires different page object methods and setup
→ CREATE NEW: test_<action>_with_<new_input_type>() — different flow, different page object methods
```

### Step 5: Provide Location Guidance

Specify:
- **File path** - `tests/ui/chat/test_chat_messaging.py`
- **Class name** - `TestChatMessaging` or create new `TestFileAttachments`
- **Reasoning** - Why this location makes sense

## Output Format

```markdown
## Test Scout Analysis

**Test case:** [Brief description of what user wants to test]

### Existing Test Coverage

Found [N] related tests:
1. `test_existing_name` in `tests/ui/domain/test_file.py:45`
   - **Similarity:** [What overlaps]
   - **Difference:** [What's different, if any]

### Verdict: [ALREADY COVERED / UPDATE EXISTING / CREATE NEW]

[If ALREADY COVERED:]
> The described flow is fully covered. No action needed.

[If UPDATE EXISTING:]
- **File:** `tests/ui/domain/test_file.py`
- **Class:** `TestClassName`
- **New method:** `test_method_name`
- **Reasoning:** [What's different about this variation]

[If CREATE NEW:]
- **File:** `tests/ui/domain/test_file.py`
- **Class:** `TestClassName`
- **Reasoning:** [Why no existing test fits]
```

**Do not add a "Next Steps" or "Additional angles" section.** The verdict is the output. The caller decides what to do next.

## Decision Matrix

| Scenario | Verdict |
|----------|---------|
| Same flow, same outcome, already tested | **ALREADY COVERED** |
| Same flow with one untested dimension (error path, different state) | **UPDATE EXISTING** |
| Same flow, different input only, already have a minimal + detailed variant | **ALREADY COVERED** |
| Different user flow or preconditions | **CREATE NEW** |
| Different feature area or domain | **CREATE NEW** |
| Existing class already has 3+ test methods | **CREATE NEW** |

## Anti-Patterns to Avoid

**Don't return ALREADY COVERED when:**
- The new test exercises a meaningfully different state (toggle off/on, error scenario)
- The new test targets a different model or configuration not yet tested

**Don't return UPDATE/CREATE when:**
- The same complete end-to-end flow already exists in the test suite
- The only difference is wording of the prompt, not the user's actions or assertions

## Implementation Notes

**For UI tests:**
- Check page object usage (`ChatPage`, `AgentPage`, etc.)
- Look for fixture usage (`conversation_id`, `agent_id`)
- Consider test priority markers (P1, P2)

**For API tests:**
- Check API client usage (`ConversationAPI`, `AgentAPI`)
- Look for entity lifecycle (create/read/update/delete)
- Consider setup/cleanup patterns

## References

- UI test patterns: `.claude/rules/ui-tests.md`
- Test organization: `automation/tests/ui/` and `automation/tests/api/`
