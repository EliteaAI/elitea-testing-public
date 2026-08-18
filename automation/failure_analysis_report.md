# Test Failure Analysis Report

**Base Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/31705800993  
**Previous Run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/31701959014  
**Date:** 2026-08-13

## Executive Summary

| Category | Count | Priority |
|----------|-------|----------|
| **Real Issues (Reproduced in both runs)** | 22 | **HIGH** |
| **Flaky Tests (Passed → Failed)** | 21 | **MEDIUM** |
| **Low Priority (Failed → Passed)** | 5 | **LOW** |

---

## 🔴 REAL ISSUES - Reproduced in Both Runs (22 tests)

These failures occurred in both runs and represent genuine product defects or test environment issues that need immediate attention.

### Root Cause 1: Timeout - Locator/Element Not Found (13 tests)

**Common Pattern:** Elements not appearing within timeout periods, suggesting either:
- Backend response delays
- Element rendering issues
- Race conditions in page load

#### Admin Module Failures (6 tests)

1. **test_blocked_tool_live_reload_case_insensitive**
   - Error: `Locator.wait_for: Timeout 15000ms exceeded` waiting for `text="Guardrails"`
   - Likely cause: Guardrails configuration not loading/saving properly

2. **test_invite_user_invalid_email_validation**
   - Error: `Locator.wait_for: Timeout 15000ms exceeded` waiting for `[data-testid="select-option-400"]`
   - Likely cause: Dropdown options not rendering for role selection

3. **test_create_personal_token_and_verify_in_table**
   - Error: Token row not appearing in table (count 0 instead of 1)
   - Likely cause: Token creation succeeds but doesn't persist/display

4. **test_expired_token_shows_expired_icon_and_label**
   - Error: Token row not found (count 0 instead of 1)
   - Same root cause as #3 above

5. **test_batch_edit_roles_for_multiple_selected_users**
   - Error: `Locator.wait_for: Timeout 15000ms exceeded` waiting for `[data-testid="select-option-400"]`
   - Same dropdown rendering issue as #2

6. **test_users_page_layout_and_components**
   - Error: `Locator.wait_for: Timeout 15000ms exceeded` waiting for `[data-testid="select-option-400"]`
   - Same dropdown rendering issue as #2

**Root Cause Analysis:** The `select-option-400` testid appears in 3 different tests, suggesting a **system-wide issue with dropdown/select components not rendering properly** on DEV environment. This could be:
- Backend API response delays for fetching options
- Frontend state management issue
- Role/permission data not loading correctly

#### Artifacts Module Failures (1 test)

7. **test_upload_via_three_options_and_verify_selection**
   - Error: Known defect #649 - Upload files dialog doesn't default to bucket root
   - Status: **Sanctioned RED** (documented product defect)

8. **test_create_bucket_max_length_name_and_delete**
   - Error: `Timeout 15000ms exceeded while waiting for event "response"`
   - Likely cause: Backend timeout on bucket creation

#### Toolkits Module Failures (5 tests)

9. **test_create_private_credential_from_toolkit_dropdown**
   - Error: `Locator.wait_for: Timeout 10000ms exceeded` waiting for `[data-testid="select-option-471"]`
   - Likely cause: Credential type dropdown not loading

10. **test_credential_duplicate_and_empty_required_field_validation**
    - Error: Save button should be disabled but is enabled
    - Likely cause: Form validation not working correctly

11. **test_delete_remote_mcp**
    - Error: `Locator.wait_for: Timeout 15000ms exceeded` waiting for `agent-card-view-button`
    - Likely cause: MCP list not loading after deletion

12. **test_mcp_search_by_name**
    - Error: `Locator.wait_for: Timeout 15000ms exceeded` waiting for `agent-card-view-button`
    - Likely cause: MCP search results not rendering

13. **test_cancel_artifact_toolkit_creation_creates_no_toolkit_no_bucket**
    - Error: Known defect #655 - Cancel should navigate to toolkits list
    - Status: **Sanctioned RED** (documented product defect)

14. **test_create_artifact_toolkit_creates_bucket_verify_list_files**
    - Error: Model selector not visible after toolkit creation
    - Likely cause: Page state corruption after creation

---

### Root Cause 2: Assertion Failures - Test Preconditions Not Met (6 tests)

**Common Pattern:** Tests expect specific data or state that doesn't exist on DEV environment.

1. **test_agent_row_click_opens_detail_view** (Analytics)
   - Error: Expected a row starting with 'autotest_test_empty_pipeline'
   - Root cause: **Test data missing** - precondition agent/pipeline not created

2. **test_agents_pipelines_tab_charts_and_activity_table** (Analytics)
   - Error: Pagination button should be enabled (expecting >1 page of data)
   - Root cause: **Insufficient test data** on DEV environment

3. **test_sensitive_tool_live_reload_case_insensitive** (Guardrails)
   - Error: Tool should execute without auth before marking sensitive
   - Root cause: Tool already marked sensitive or auth already required

4. **test_notification_text_content_renders_correctly** (Notifications)
   - Error: Expected notification '<user> mentioned you in <chat>' not found
   - Root cause: **Test data missing** - notification not generated

5. **test_search_credentials_by_name** (Credentials)
   - Error: ExceptionGroup with 2 soft assertion failures
   - Root cause: Search functionality not working correctly

6. **test_credential_usage_and_deletion_mismatch** (Credentials)
   - Error: Expected real branch objects, got generic message
   - Root cause: API response format incorrect or test settings invalid

---

### Root Cause 3: Assertion Failures - Content Mismatch (2 tests)

**Common Pattern:** API/tool responses not containing expected data.

1. **test_github_toolkit_test_settings**
   - Error: Expected 'main' branch name in tool result JSON
   - Root cause: **GitHub toolkit API integration issue** - not returning expected data

2. **test_toolkit_test_settings[github]**
   - Error: Expected '"main"' in tool output for GitHub
   - Same root cause as above - parameterized version of same test

**Root Cause Analysis:** Both failures point to the **GitHub toolkit's test settings function not working properly**. The tool executes but doesn't return the expected branch data.

---

## 🟡 FLAKY TESTS - Passed in Previous, Failed in Base (21 tests)

These tests are unstable and need investigation for race conditions, timing issues, or environmental dependencies.

### Root Cause 4: Timeout - Timing/Race Conditions (12 tests)

#### Agents Module (5 tests)

1. **test_agent_hub_unlike_agent_from_list_view**
   - Error: Like count element not found
   - Flakiness: Element rendering race condition

2. **test_agent_self_attachment_blocked**
   - Error: Agent information section not visible
   - Flakiness: Page load timing issue

3. **test_fork_agent_to_different_project**
   - Error: select-option-400 not visible
   - Flakiness: Dropdown rendering timing

4. **test_llm_selector_change_model_settings_dialog_persist**
   - Error: Model selector shows 'None' instead of saved model
   - Flakiness: State persistence race condition after reload

5. **test_agent_embedded_chat_conversation_starter_chips**
   - Error: Message count didn't increase
   - Flakiness: Chat message not sent/rendered in time

#### Skills Module (7 tests)

6-12. **Multiple skill icon and form tests:**
   - `test_skill_back_navigation`
   - `test_skill_card_shows_icon_name_description_and_tags`
   - `test_skill_custom_icon_upload_and_validation`
   - `test_skill_custom_icon_visible_across_ui`
   - `test_fork_skill_end_to_end`
   - `test_fork_non_base_skill_version`
   - `test_skill_custom_icon_persists_on_save_as_version`

**Common Pattern:** All fail with either:
- `skill-form-icon-button` scroll_into_view timeout
- Page navigation timeouts
- Element visibility timeouts

**Root Cause Analysis:** The skill form/icon tests are hitting **consistent timing issues** with the skill editor page loading. Likely causes:
- Slow page load on DEV
- Heavy UI components (icon picker, form validation)
- Network latency for loading skills

---

### Root Cause 5: Assertion Failures - Incorrect Expected Values (6 tests)

1. **test_suggested_skills_section_capped_at_5_skills**
   - Error: Soft assertion failures
   - Known defect documented in test

2. **test_download_all_files_via_select_all_as_zip**
   - Error: Progress sequence missing '1 of 6 files' frame
   - Flakiness: Progress bar updates too fast

3. **test_interact_with_skills_from_agent**
   - Error: Skill should return UPPER CASE text
   - Flakiness: Skill execution not working or wrong version used

4. **test_interact_with_skills_from_conversation**
   - Error: Skill should return UPPER CASE text
   - Same issue as #3

5. **test_multiple_tags_persist_on_creation_and_edit**
   - Error: Tag order different ['tag2', 'tag1'] vs ['tag1', 'tag2']
   - Flakiness: **Tag ordering not deterministic** - should sort or accept any order

6. **test_llm_model_settings_configurable**
   - Error: GPT-5 mini should show Creativity slider, not Reasoning
   - Flakiness: Model type detection or UI rendering issue

---

### Root Cause 6: Known Product Defect (1 test)

1. **test_selected_suggested_resources_attached_and_non_selected_absent**
   - Error: Suggested Agents section missing
   - Root cause: Missing precondition (github_relevant_agents)

---

## 🟢 LOW PRIORITY - Failed in Previous, Passed in Base (5 tests)

These tests failed in the previous run but passed in the base run. Monitor for recurrence.

1. **test_agent_creates_files_at_root_and_in_subfolder** - Network/API error (resolved)
2. **test_create_github_toolkit** - Network/API error (resolved)
3. **test_create_github_credential** - Timeout (resolved)
4. **test_toolkit_credential_indicators_e2e** - Timeout (resolved)
5. **test_download_multiple_files_as_zip** - Content mismatch (resolved)

---

## Recommendations by Priority

### Immediate Action (Real Issues - 22 tests)

#### 1. **Fix Dropdown Rendering Issue (Highest Impact)**
   - **Affected:** 6+ tests across Admin, Agents, Skills, Toolkits
   - **Symptom:** `select-option-400`, `select-option-471` not appearing
   - **Action:** Investigate dropdown/select component rendering on DEV
   - **Likely Fix:** Backend API for options, frontend state management, or role permissions

#### 2. **Fix Personal Token Persistence**
   - **Affected:** 2 tests
   - **Action:** Debug token creation → database → UI table flow
   - **Likely Fix:** Backend token persistence or frontend table refresh

#### 3. **Fix GitHub Toolkit Test Settings**
   - **Affected:** 2 tests
   - **Action:** Debug GitHub toolkit API integration
   - **Likely Fix:** Tool configuration, API response parsing, or credentials

#### 4. **Address Test Data Dependencies**
   - **Affected:** 4 tests (Analytics, Notifications)
   - **Action:** Add test data setup or make tests more resilient
   - **Likely Fix:** Test setup automation or data seeding

#### 5. **Sanctioned RED Tests** (Monitor, Don't Block)
   - test_upload_via_three_options_and_verify_selection (#649)
   - test_cancel_artifact_toolkit_creation_creates_no_toolkit_no_bucket (#655)
   - Action: Track in issues, accept red until product fixes ship

---

### Medium Priority (Flaky Tests - 21 tests)

#### 1. **Stabilize Skill Form Tests (7 tests)**
   - **Pattern:** Icon button scroll/visibility timeouts
   - **Action:** Increase waits, add page load checks, or optimize skill editor load
   - **Investigation:** Profile DEV skill editor page performance

#### 2. **Fix Skill Execution Tests (2 tests)**
   - **Pattern:** Skills not returning uppercase text
   - **Action:** Debug skill version selection and execution
   - **Investigation:** Verify correct skill version attached and executed

#### 3. **Fix Non-Deterministic Behaviors**
   - Tag ordering (test_multiple_tags_persist)
   - Progress bar timing (test_download_all_files)
   - Action: Make tests order-agnostic or add deterministic sorting

#### 4. **Stabilize Agent Tests (5 tests)**
   - **Pattern:** Page load, dropdown, state persistence timing issues
   - **Action:** Add explicit waits, verify page state before actions
   - **Investigation:** Common pattern suggests DEV environment slowness

---

### Low Priority (Monitor - 5 tests)

- Continue monitoring these tests
- If they fail again in subsequent runs, promote to Medium priority

---

## Root Cause Summary

| Root Cause | Count | Severity | Action Owner |
|------------|-------|----------|--------------|
| **Dropdown/Select rendering failure** | 6 | CRITICAL | Backend + Frontend Teams |
| **Skill form/icon page load timing** | 7 | HIGH | Frontend Team |
| **Personal Token persistence** | 2 | HIGH | Backend Team |
| **GitHub Toolkit API integration** | 2 | HIGH | Integrations Team |
| **Test data dependencies** | 4 | MEDIUM | QA Team |
| **Skill execution** | 2 | MEDIUM | Backend Team |
| **Non-deterministic behaviors** | 3 | MEDIUM | QA Team |
| **Sanctioned RED (known defects)** | 2 | INFO | Product Team |

---

## Test Environment Concerns

Several patterns suggest **DEV environment performance issues**:

1. **Consistent timeout increases** needed across multiple test types
2. **Dropdown/select components** consistently failing to render
3. **Page load timing** affecting many skill and agent tests
4. **API response delays** evident in multiple toolkit tests

**Recommendation:** Profile DEV environment performance, check:
- Backend API response times
- Database query performance
- Frontend bundle size and load times
- Network latency between services

---

## Next Steps

1. **Immediate:** File bugs for the 6 dropdown rendering failures (clustered root cause)
2. **Today:** Investigate Personal Token persistence (2 tests)
3. **Today:** Debug GitHub Toolkit test settings (2 tests)
4. **This Week:** Stabilize skill form tests (7 tests) - likely environment issue
5. **This Week:** Profile DEV environment performance
6. **Monitor:** Track the 5 low-priority tests for recurrence
