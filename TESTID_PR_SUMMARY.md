# Schedule Modal & Pipeline Timeline Testids - Summary

## PR Created

**EliteaUI PR #846**: https://github.com/EliteaAI/EliteaUI/pull/846
- **Branch**: `testids/schedule-modal-and-pipeline-timeline`
- **Base**: `main`
- **Status**: Draft

## What's Included

This PR consolidates testids from two sources:

### 1. Schedule Modal Testids (NEW - EL-2007)

Cherry-picked from `automation/testids` branch (commit aea8503f).

**Files:**
- `src/[fsd]/shared/ui/schedule/ScheduleModal.jsx`
- `src/[fsd]/shared/ui/schedule/CronBuilder.jsx`
- `src/[fsd]/shared/ui/schedule/CronSelect.jsx`

**12 Testids Added:**

| Testid | Component | Element |
|--------|-----------|---------|
| `pipeline-schedule-settings-modal` | ScheduleModal | Dialog root |
| `pipeline-schedule-mode-tabs` | ScheduleModal | Tab group (Builder/Cron Expression) |
| `pipeline-schedule-cron-input` | ScheduleModal | Raw cron input field |
| `pipeline-schedule-summary-text` | ScheduleModal | Summary display |
| `pipeline-schedule-modal-cancel-button` | ScheduleModal | Cancel button |
| `pipeline-schedule-modal-save-button` | ScheduleModal | Save button |
| `schedule-cron-period-select` | CronBuilder | Period dropdown (day/week/month) |
| `schedule-cron-monthdays-select` | CronBuilder | Month days selector |
| `schedule-cron-weekdays-select-month` | CronBuilder | Weekdays (month mode) |
| `schedule-cron-weekdays-select-week` | CronBuilder | Weekdays (week mode) |
| `schedule-cron-hour-select` | CronBuilder | Hour selector |
| `schedule-cron-minute-select` | CronBuilder | Minute selector |

### 2. Pipeline Timeline Testid (RESTORED - from PR #832)

Cherry-picked from closed PR #832 (commit 890082b5).

**File:**
- `src/[fsd]/features/pipelines/flow-editor/ui/state/RunStateDialog.jsx`

**1 Testid Restored:**
- `pipeline-run-details-timeline-section` - Timeline header container

**Background:** This testid was removed in commit a638b586 (Aug 11) but 17 pipeline tests depend on it.

## Test Automation Status

### Tests Fixed (elitea-testing-public)

**Commit f67ddf08** on `main` branch updated page objects to use fallback locators.

#### ✅ Fully Passing
- `test_pipeline_entry_point_trigger_types_persist.py::test_entry_point_trigger_types_persist`

#### ⚠️ Partially Working
- `test_pipeline_schedule_trigger_settings_modal.py::test_schedule_trigger_settings_modal`
  - Modal opens ✅
  - Tabs visible ✅
  - Period selection works ✅
  - **Still failing:** Hour/minute selection needs additional work

### Page Object Updates (elitea-testing-public)

**File**: `automation/pages/pipeline_detail_page.py`

**Changes:**
1. All schedule modal locators use **fallback only** (testid params commented out until deployed)
2. `SCHEDULE_CRON_SELECT` changed from `.react-js-cron-select` → `.MuiAutocomplete-root`
3. `CRON_DROPDOWN*` constants updated for MUI Autocomplete structure
4. `get_schedule_cron_select_count()` updated to count MUI components

**Why fallback only?**
The `LocatorDescriptor` class tries testid FIRST and doesn't fall back if the element doesn't exist. Since testids aren't on main yet, we need fallback-only mode until PR #846 merges and deploys.

## Next Steps

### 1. Merge EliteaUI PR #846
Once reviewed and approved, merge to `main` and deploy to target environments.

### 2. Uncomment Testids in Test Repo
After testids deploy, update `elitea-testing-public/automation/pages/pipeline_detail_page.py`:
- Uncomment all `testid=` parameters in schedule modal `LocatorDescriptor`s
- Remove TODO comments
- Keep fallbacks for compatibility with older environments

### 3. Fix Hour/Minute Selection
The `set_schedule_hour_minute()` method needs updating for MUI Autocomplete:
- Current: Tries to click `get_by_text("00")` to open dropdown
- Needed: Proper MUI Autocomplete interaction pattern

## Files to Track

### EliteaUI
```
src/[fsd]/shared/ui/schedule/ScheduleModal.jsx          (6 testids)
src/[fsd]/shared/ui/schedule/CronBuilder.jsx            (6 testids)
src/[fsd]/shared/ui/schedule/CronSelect.jsx             (prop support)
src/[fsd]/features/pipelines/flow-editor/ui/state/RunStateDialog.jsx  (1 testid)
```

### elitea-testing-public
```
automation/pages/pipeline_detail_page.py                (locator updates)
automation/tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py
automation/tests/ui/pipelines_2/test_pipeline_schedule_trigger_settings_modal.py
```

## Zero-Functional-Impact Compliance

✅ All changes follow PR #753 pattern:
- No new DOM nodes
- No behavior changes
- Testids on existing elements only
- CronSelect accepts `data-testid` prop (standard pattern)

## Related Links

- **EliteaUI PR #846**: https://github.com/EliteaAI/EliteaUI/pull/846
- **EliteaUI PR #832** (closed, content cherry-picked): https://github.com/EliteaAI/EliteaUI/pull/832
- **elitea-testing-public commit**: f67ddf084 (page object updates)
- **EliteaUI commit (schedule)**: aea8503f (on automation/testids)
- **EliteaUI commit (timeline)**: 890082b5 (from PR #832)

---

*Created: 2026-08-26*
*Test Automation Engineer: Axel*
