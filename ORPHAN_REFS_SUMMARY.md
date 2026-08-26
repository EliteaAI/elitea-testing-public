# Orphan TMS References Analysis

**Date:** 2026-08-21  
**Source:** https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/reports/dashboard.md

## Summary

- **Total Orphan Refs:** 127
- **TMS Coverage Impact:** These orphan refs inflate the "Tests linked to TMS cases" count
- **Actual Tests in Automation:** 432 (per automation/index.json)
- **Tests with Valid TMS Links:** 286 (claimed, but includes these 127 orphans)
- **Corrected TMS-linked Tests:** 286 - 127 = **159 actual valid links**

## What Are Orphan Refs?

Orphan TMS references are `automation_test_id` entries in TMS case files that point to tests that **don't exist** in the automation codebase. They were likely:

1. **Renamed** - Test was refactored with a different name
2. **Deleted** - Test was removed from the suite
3. **Never created** - TMS case marked as automated but test was never written
4. **Moved** - Test file/class structure changed

## Impact

These orphan refs cause:
- ❌ **Inflated coverage metrics** - Dashboard shows 66.2% TMS coverage, but it's actually lower
- ❌ **False automation status** - Cases marked as "automated" but have no working test
- ❌ **Broken CI correlation** - `correlate_results` can't match JUnit results to these refs
- ❌ **Maintenance confusion** - Developers can't find the "automated" test

## Complete List of Orphan Refs

### Artifacts (1 orphan)

1. `tests.ui.artifacts.test_artifacts_bucket_name_validation_invalid_formats.TestArtifactBucketNameValidationInvalidFormats.test_bucket_name_validation_rejects_invalid_format` (ELITEA-1814)
   - **Likely cause:** Parameterized test - base name exists without parameters

### Chat (94 orphans)

Many of these appear to be from batch automation efforts that were planned but not completed, or tests that were refactored/renamed.

#### Agent Hub & Build With AI

2. `tests.ui.chat.test_agent_hub_create_conversation_via_starter.TestAgentHubCreateConversationViaStarter.test_agent_hub_create_conversation_via_starter` (ELITEA-2093)
3. `tests.ui.chat.test_build_with_ai_cancel_then_generate_echo_agent.TestBuildWithAICancelThenGenerateEchoAgent.test_cancel_then_generate_creates_echo_agent_in_canvas` (ELITEA-2073)

#### File Attachments

4. `tests.ui.chat.test_attach_files_10_left_counter.TestAttachFiles10LeftCounter.test_attach_files_menuitem_shows_10_left_counter` (ELITEA-2195)
5. `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_of_different_types_shows_identical_icon_and_long_filename_truncates` (ELITEA-2199)
6. `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_files_then_remove_two_individually_sequentially` (ELITEA-2198)
7. `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_attach_multiple_files_displays_chips_above_composer` (ELITEA-2196)
8. `tests.ui.chat.test_attach_files_multiple_chips_display.TestAttachFilesMultipleChipsDisplay.test_long_filename_truncates_and_overflow_indicator_click_expands` (ELITEA-2467)

#### Conversation & Folder Management (Large cluster - 50+ refs)

Conversation renaming, folder operations, pinning, drag-drop, deletion - many planned tests that appear incomplete.

_[Full list continues in section below]_

### Help Center (10 orphans)

Tests for help center, resource links, interactive tour, version info.

### Skills (23 orphans)

Build with AI, Edit with AI, Publishing flow, Agent-Skill interaction tests.

### Settings & Onboarding (2 orphans)

Settings page and onboarding welcome tests.

---

## Recommended Actions

### 1. **Immediate: Clean TMS Case Files**

Remove orphan `automation_test_id` entries from TMS case files to correct the coverage metric.

```bash
# Use the generated update script
./automation/scripts/update_tms_orphans.sh
```

### 2. **Investigation: Why Do These Exist?**

Review each orphan case to determine:
- Was the test renamed? → Update `automation_test_id` to new name
- Was the test deleted? → Set `execution_type: manual` or `status: draft`
- Was it never created? → File as work item or mark as not automated

### 3. **Update Dashboard Calculation**

After cleanup, rebuild TMS index:

```bash
cd ../onetest-ai-tm-Elitea
npx @onetest/tms build-index
```

Then regenerate dashboard to show corrected coverage.

### 4. **Process Improvement**

- Add validation step: verify `automation_test_id` exists before marking case as automated
- Document test naming conventions to prevent future mismatches
- Run periodic orphan checks (monthly?)

---

## Full Orphan List by File

_See attached `LATEST_ORPHAN_ANALYSIS.md` for complete categorized list._

