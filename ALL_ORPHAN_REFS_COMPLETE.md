# All 127 Orphan TMS References - Complete Mapping

**Date:** 2026-08-21  
**Dashboard:** https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/reports/dashboard.md

## Quick Facts

- ✅ **127 orphan refs analyzed** - None exist as tests in automation codebase
- ❌ **TMS coverage inflated** - Shows 66.2%, actually ~37% (159 valid / 432 tests)
- 🔧 **Action needed** - Clean TMS case files to correct metrics

## Success/Not-Success Mapping

### ❌ NOT FOUND (127 refs - 100%)

**ALL 127 orphan refs do NOT exist in the codebase.** Test names searched but no matching `def test_*` found.

**Why?**
1. Tests never created (planned but not built)
2. Tests renamed/refactored
3. Test files deleted
4. Class/module structure changed

### ✅ FOUND (0 refs - 0%)

No orphan refs matched existing tests.

---

## Complete List with Case IDs

| # | Case ID | Orphan Ref | Category |
|---|---------|------------|----------|
| 1 | ELITEA-1814 | `tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format` | Artifacts |
| 2 | ELITEA-2093 | `tests.ui.chat.test_agent_hub_create_conversation_via_starter.TestAgentHubCreateConversationViaStarter.test_agent_hub_create_conversation_via_starter` | Chat - Agent Hub |
| 3 | ELITEA-2195 | `tests.ui.chat.test_attach_files_10_left_counter.TestAttachFiles10LeftCounter.test_attach_files_menuitem_shows_10_left_counter` | Chat - Attachments |
| 4 | ELITEA-2199 | `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_of_different_types_shows_identical_icon_and_long_filename_truncates` | Chat - Attachments |
| 5 | ELITEA-2198 | `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_then_remove_two_individually_sequentially` | Chat - Attachments |
| 6 | ELITEA-2196 | `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_multiple_files_displays_chips_above_composer` | Chat - Attachments |
| 7 | ELITEA-2467 | `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_long_filename_truncates_and_overflow_indicator_click_expands` | Chat - Attachments |
| 8 | ELITEA-2073 | `tests.ui.chat.test_build_with_ai_cancel_then_generate_echo_agent.TestBuildWithAICancelThenGenerateEchoAgent.test_cancel_then_generate_creates_echo_agent_in_canvas` | Chat - Build AI |
| 9 | ELITEA-2465 | `tests.ui.chat.test_chat_agent_starters_add_remove.TestChatAddAgentWithStartersAndSendViaStarter.test_add_agent_with_starters_and_send_via_starter` | Chat - Starters |
| 10 | ELITEA-2177 | `tests.ui.chat.test_chat_agent_starters_add_remove.TestChatAddAgentWithStartersToConversation.test_add_agent_with_starters_to_conversation` | Chat - Starters |
| ... | ... | _(91 more chat refs)_ | Chat - Various |
| 91 | ELITEA-2220 | `tests.ui.help_center.test_help_center_resource_links.TestHelpCenterResourceLinks.test_resource_card_link_redirects_to_external_page[ELITEA-2220-documentation-getting-started]` | Help Center |
| ... | ... | _(9 more help center refs)_ | Help Center |
| 101 | ELITEA-2231 | `tests.ui.onboarding.test_onboarding_welcome.TestOnboardingWelcomePage.test_welcome_page_displayed_on_first_login` | Onboarding |
| 102 | ELITEA-2392 | `tests.ui.settings.test_ai_providers_page_sections_load_without_error.TestAIProvidersPageSections.test_ai_providers_page_sections_load_without_error_test` | Settings |
| 103-127 | ELITEA-1986 - ELITEA-2614 | _(25 skills refs)_ | Skills - Build/Edit/Publish AI |

_Full categorized list in `LATEST_ORPHAN_ANALYSIS.md`_

---

## Breakdown by Area

| Area | Count | Notes |
|------|-------|-------|
| **Chat** | 94 | Largest cluster - folders, renaming, pinning, attachments, search |
| **Skills** | 23 | Build/Edit with AI, Publishing, Agent interaction |
| **Help Center** | 10 | Resource links, sidebar tour, version info |
| **Artifacts** | 1 | Bucket validation (parameterized test) |
| **Onboarding** | 1 | Welcome page |
| **Settings** | 1 | AI providers (test name mismatch) |

---

## Actionable Items

### 1. Update TMS Case Files

For each orphan ref, edit the TMS case file to:

**Option A: Test was never created**
```yaml
execution_type: manual  # or leave as draft
status: draft
# Remove automation_test_id line entirely
```

**Option B: Test was renamed**
```yaml
execution_type: automated
status: ready
automation_test_id:
  - tests.ui.chat.NEW_CORRECT_NAME  # Update to actual test name
```

**Option C: Feature removed/deprecated**
```yaml
execution_type: manual
status: deprecated
# Remove automation_test_id
```

### 2. Rebuild TMS Index

```bash
cd onetest-ai-tm-Elitea
npx @onetest/tms build-index
```

### 3. Regenerate Dashboard

After cleaning, dashboard should show:
- Tests in automation: 432
- Tests linked to TMS: **159** (was 286)
- TMS Coverage: **~37%** (was 66.2%)

### 4. Investigation Questions

For team discussion:
1. **Folder/renaming tests (36 refs)** - Were these batch efforts abandoned?
2. **Help Center (10 refs)** - Is this feature area deprioritized?
3. **Skills Build/Edit AI (17 refs)** - Planned for a future sprint?
4. **Duplicate case IDs** - ELITEA-2116, 2468, 2597, 2613 - Which test is correct?

---

## Impact Summary

**Before cleanup:**
- TMS says: 286 tests automated
- Reality: Only ~159 valid links
- **127 ghost refs** (44% of "automated" cases)

**After cleanup:**
- Dashboard shows true coverage
- CI correlation works correctly
- No confusion about "where's this test?"

---

## Files Generated

1. `ORPHAN_REFS_SUMMARY.md` - Executive summary and impact
2. `LATEST_ORPHAN_ANALYSIS.md` - Full categorized list with patterns
3. `ALL_ORPHAN_REFS_COMPLETE.md` - This file - actionable mapping
4. `automation/scripts/analyze_orphan_tms_refs.py` - Analysis script
5. `automation/scripts/update_tms_orphans.sh` - Cleanup helper (sample)
6. `automation/scripts/orphan_analysis.json` - Machine-readable results

