# Test Failure Investigation Notes

## Session: 2026-08-13
## Investigator: TAL (test-automation-lead)

---

## ROOT CAUSE #1: Dropdown/Select Rendering Failures (6+ tests)

### Affected Tests
1. `test_invite_user_invalid_email_validation` (Admin)
2. `test_batch_edit_roles_for_multiple_selected_users` (Admin)
3. `test_users_page_layout_and_components` (Admin)
4. `test_create_private_credential_from_toolkit_dropdown` (Toolkits)
5. `test_fork_agent_to_different_project` (Agents - flaky)
6. `test_fork_non_base_skill_version` (Skills - flaky)

### Error Pattern
```
playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"select-option-400\"]") to be visible
```

or

```
playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"select-option-471\"]") to be visible
```

### Analysis

#### Code Review - AdminUsersPage

**Location:** `automation/pages/admin_users_page.py`

**Locator Pattern:**
```python
SELECT_OPTION = '[data-testid="select-option-{}"]'

def _select_multi_select_role_and_close(self, combobox, role: str, timeout: int = UI_ELEMENT_TIMEOUT):
    combobox.click(timeout=timeout)
    option = self.page.locator(self.SELECT_OPTION.format(role))  # ← role="editor"
    option.wait_for(state="visible", timeout=timeout)
    option.click(timeout=timeout)
    self.page.keyboard.press("Escape")
```

**Test Usage:**
```python
SELECTED_ROLE = "editor"
users_page.select_role_in_invite_dialog(SELECTED_ROLE)  # Passes "editor"
```

**Expected behavior:**
- Formats testid as `[data-testid="select-option-editor"]`
- Should wait for and click that option

**Actual failure:**
- Waits for `[data-testid="select-option-400"]` instead
- 400 looks like a PROJECT ID or ROLE ID, not "editor"

### Hypothesis

**Primary Hypothesis:** Testid pattern mismatch

The EliteaUI dropdown options may be using a **role ID** or **project ID** in their testids, not the role **name**:
- Expected by test: `data-testid="select-option-editor"`
- Actually rendered: `data-testid="select-option-{roleId}"` where roleId = some numeric value

**Why "400" specifically?**
- Could be a role ID for "editor" role
- Could be project ID 400 (mentioned in code as "UI Testing" team project)
- Error says it's looking for `select-option-400`, not `select-option-editor`

### Verification Needed

#### Option A: Check EliteaUI source
Look at `SingleSelectMenuItem.jsx` or related component to see:
- How testids are constructed for select options
- Whether they use role.id or role.name
- Whether pattern changed recently

#### Option B: Live inspection on DEV
1. Navigate to Settings → Users
2. Open invite dialog
3. Click role dropdown
4. Inspect actual testid values on rendered options
5. Compare with what test expects

#### Option C: Check other working tests
Find similar dropdown selections that ARE working and compare their approach.

### Potential Root Causes

1. **Testid pattern changed in UI** (EliteaUI PR changed from name to ID)
2. **Test assumption incorrect** (was always ID, test never properly verified)
3. **Environment-specific** (DEV environment data issue with roles)
4. **Race condition** (options not loaded/rendered yet)

### Next Steps

1. ✅ **COMPLETED:** Document findings in investigation_notes.md
2. **TODO:** Check EliteaUI source for `SingleSelectMenuItem.jsx` testid construction
3. **TODO:** Check if testid naming changed recently (git history)
4. **TODO:** Review other tests that successfully select from dropdowns
5. **TODO:** Verify actual testids in browser DevTools on DEV
6. **TODO:** If pattern mismatch confirmed, determine:
   - Should test use role ID instead of name?
   - Should UI use role name instead of ID?
   - Or add a mapping layer?

### Skip Criteria

If after 5 investigation attempts no clear fix emerges:
- Mark as **UNCLEAR - needs product team input**
- Document: What we found, what we tried, what's unclear
- Move to next root cause

### Findings - Attempt 1

**Code Investigation Complete:**

1. **SingleSelectMenuItem testid pattern** (Line 117):
   ```jsx
   data-testid={option.testId ?? `select-option-${option.value}`}
   ```

2. **Users.jsx rolesOptions** (Line 74):
   ```jsx
   const rolesOptions = useMemo(() => roles.map(({ name }) => ({ label: name, value: name })), [roles]);
   ```

3. **Test passes correct value:**
   ```python
   SELECTED_ROLE = "editor"
   users_page.select_role_in_invite_dialog(SELECTED_ROLE)
   ```

**Conclusion:** The code is CORRECT. Options DO use role names as values. The testid SHOULD be `select-option-editor`.

**New Hypothesis:** The error showing `select-option-400` suggests the dropdown is rendering the WRONG options entirely:
- "400" is the UI Testing team project ID
- Maybe the dropdown is showing PROJECT options instead of ROLE options
- Or roles aren't loading, and some fallback/default options appear instead

### Next Investigation

Need to determine why roles aren't loading in the dropdown. Possibilities:
1. API `/admin/roles/default/{project}` failing or slow
2. Race condition - dialog opens before roles load
3. State management issue - roles not passed to dialog correctly
4. DEV environment data issue - roles don't exist for project 400

### Status: IN PROGRESS (Attempt 2/5 - investigating API/timing)

---

## Notes on Other Root Causes

### Personal Token Persistence (Root Cause #2)
- Status: PENDING
- Tests affected: 2
- Pattern: Token created but not visible in table

### GitHub Toolkit Integration (Root Cause #3)
- Status: PENDING
- Tests affected: 2
- Pattern: Expected 'main' branch not in output

### Test Data Dependencies (Root Cause #4)
- Status: PENDING
- Tests affected: 4
- Pattern: Missing precondition data

### Remaining Failures (Root Cause #5)
- Status: PENDING
- Tests affected: 8
- Pattern: Various timeouts and assertions

