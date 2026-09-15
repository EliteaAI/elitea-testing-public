# EliteaUI Testid Additions - Schedule Modal

## Summary

Schedule modal tests (`test_pipeline_schedule_trigger_settings_modal`, `test_pipeline_entry_point_trigger_types_persist`) were failing because the modal root and all child elements lack data-testid attributes.

**Current Status:** Tests now use fallback locators (role/text-based) as temporary workarounds. These work but violate project policy (testid-only locators).

**Goal:** Add proper testids to EliteaUI ScheduleModal component and related components so tests can switch back to testid-only locators.

---

## Component Location

**File:** `/Users/Aliaksei_Breilian/PycharmProjects/elitea_local/EliteaUI/src/[fsd]/shared/ui/schedule/ScheduleModal.jsx`

**Related Components:**
- `/Users/Aliaksei_Breilian/PycharmProjects/elitea_local/EliteaUI/src/[fsd]/shared/ui/schedule/CronBuilder.jsx`
- `/Users/Aliaksei_Breilian/PycharmProjects/elitea_local/EliteaUI/src/[fsd]/shared/ui/schedule/CronSelect.jsx`

---

## Required Testids

### 1. Modal Root
**Component:** Modal.BaseModal  
**Suggested testid:** `pipeline-schedule-settings-modal`  
**Location:** ScheduleModal.jsx root element  
**Current Fallback:**
```javascript
fallback: page.locator('[role="dialog"]').filter(has_text="Schedule Settings").first
```

### 2. Mode Selection Tabs
**Component:** Tab.TabGroupButton  
**Values:** "builder" (Default/visual mode), "cron" (Advanced/text mode)  
**Suggested testids:**
- `pipeline-schedule-mode-tab-builder` (for "Builder" tab button)
- `pipeline-schedule-mode-tab-cron` (for "Cron Expression" tab button)

**Current Fallback:**
```javascript
// Default mode tab
fallback: page.locator('[role="dialog"]').filter(has_text="Schedule Settings").locator('button:has-text("Builder")').first

// Advanced mode tab
fallback: page.locator('[role="dialog"]').filter(has_text="Schedule Settings").locator('button:has-text("Cron Expression")').first
```

**Note:** Tests currently refer to these as "Default" and "Advanced" mode radios, but UI implements them as tabs with "Builder" and "Cron Expression" labels.

### 3. Cron Builder Selects (Builder/Default Mode)
**Component:** CronSelect (MUI Autocomplete)  
**Suggested testids:**
- `schedule-cron-period-select` - Every dropdown (day/week/month/year)
- `schedule-cron-weekdays-select` - Day-of-week selector (visible for week period)
- `schedule-cron-monthdays-select` - Day-of-month selector (visible for month period)
- `schedule-cron-hour-select` - Hour selector (HH)
- `schedule-cron-minute-select` - Minute selector (MM)

**Current Issues:**
- Test expects `.react-js-cron-select` class but actual component uses MUI Autocomplete
- Needs testids on each CronSelect component instance in CronBuilder

### 4. Cron Text Input (Cron Expression/Advanced Mode)
**Component:** FormInput  
**Suggested testid:** `pipeline-schedule-cron-input`  
**Current Fallback:** TBD - not yet reached in test execution

### 5. Summary Text Display
**Component:** Typography element showing "At 00:00, only on Saturday" style text  
**Suggested testid:** `pipeline-schedule-summary-text`  
**Current Fallback:**
```javascript
fallback: page.locator('[role="dialog"]').filter(has_text="Schedule Settings").locator('text=/At \\d+:\\d+|Every |Daily|Weekly|Monthly/').first
```

### 6. Modal Buttons
**Component:** Buttons in modal footer  
**Suggested testids:**
- `pipeline-schedule-modal-cancel-button` - "Cancel" button
- `pipeline-schedule-modal-save-button` - "Save" button (test calls it "Apply")

**Current Fallback:**
```javascript
// Cancel
fallback: page.locator('[role="dialog"]').filter(has_text="Schedule Settings").locator('button:has-text("Cancel")').first

// Save
fallback: page.locator('[role="dialog"]').filter(has_text="Schedule Settings").locator('button:has-text("Save")').first
```

**Note:** Button text is "Save" not "Apply" as test originally expected.

---

## Implementation Notes

### Modal Structure

```javascript
// ScheduleModal.jsx (simplified)
<Modal.BaseModal
  data-testid="pipeline-schedule-settings-modal"  // ← ADD THIS
  isOpen={isOpen}
  title="Schedule Settings"
>
  <Tab.TabGroupButton
    arrayBtn={[
      { value: 'builder', label: 'Builder' },  // ← testid: pipeline-schedule-mode-tab-builder
      { value: 'cron', label: 'Cron Expression' },  // ← testid: pipeline-schedule-mode-tab-cron
    ]}
    currentBtn={viewBtn}
    onSelectBtn={handleViewBtnChange}
  />
  
  {viewBtn === 'builder' && (
    <>
      <Typography data-testid="pipeline-schedule-summary-text">  // ← ADD THIS
        {summary}
      </Typography>
      <CronBuilder 
        value={cronStr} 
        onChange={handleCronChange}
        // CronBuilder needs to pass testids to its CronSelect instances
      />
    </>
  )}
  
  {viewBtn === 'cron' && (
    <FormInput
      data-testid="pipeline-schedule-cron-input"  // ← ADD THIS
      value={cronStr}
      onChange={handleCronChange}
    />
  )}
  
  <Button
    data-testid="pipeline-schedule-modal-cancel-button"  // ← ADD THIS
    onClick={onClose}
  >
    Cancel
  </Button>
  <Button
    data-testid="pipeline-schedule-modal-save-button"  // ← ADD THIS
    onClick={handleSave}
  >
    Save
  </Button>
</Modal.BaseModal>
```

### CronBuilder/CronSelect

CronBuilder uses multiple CronSelect instances. Each needs its own testid passed as a prop:

```javascript
// CronBuilder.jsx
<CronSelect
  data-testid="schedule-cron-period-select"
  value={periodOption}
  options={PERIOD_OPTIONS}
  onChange={opt => emit({ period: opt?.value ?? null })}
/>

<CronSelect
  data-testid="schedule-cron-weekdays-select"  // when visible
  value={weekDayOptions}
  options={WEEKDAY_OPTIONS}
  onChange={opts => emit({ weekDays: opts.map(o => o.value) })}
  multiple
/>

// Similar for hour, minute, monthdays selects...
```

### Tab.TabGroupButton

Tab component needs to support testid props for each button. If the component doesn't currently accept per-button testids, it may need:

```javascript
// Tab.TabGroupButton.jsx (hypothetical enhancement)
arrayBtn.map((btn) => (
  <button
    data-testid={btn.testId}  // Pass from parent
    // ...
  >
    {btn.label}
  </button>
))
```

---

## Test Changes After Testids Added

Once testids are in EliteaUI `automation/testids` branch (and eventually `main`), remove ALL fallback locators from `automation/pages/pipeline_detail_page.py`:

### Lines to Update (approximate)

**Line ~1325-1333:** `schedule_modal` - restore testid, remove fallback
```python
schedule_modal = LocatorDescriptor(
    testid="pipeline-schedule-settings-modal",
    description="Schedule settings modal (dialog root)"
)
```

**Line ~1334-1362:** All child elements - restore testids, remove fallbacks:
```python
schedule_summary_text = LocatorDescriptor(
    testid="pipeline-schedule-summary-text",
    description='Schedule modal cron summary text'
)

schedule_modal_cancel_button = LocatorDescriptor(
    testid="pipeline-schedule-modal-cancel-button",
    description="Schedule settings modal Cancel button"
)

schedule_modal_save_button = LocatorDescriptor(
    testid="pipeline-schedule-modal-save-button",
    description="Schedule settings modal Save button"
)

schedule_mode_tab_builder = LocatorDescriptor(
    testid="pipeline-schedule-mode-tab-builder",
    description="Schedule modal Mode — Builder (Default) tab"
)

schedule_mode_tab_cron = LocatorDescriptor(
    testid="pipeline-schedule-mode-tab-cron",
    description="Schedule modal Mode — Cron Expression (Advanced) tab"
)

schedule_cron_input = LocatorDescriptor(
    testid="pipeline-schedule-cron-input",
    description="Schedule modal cron expression text input (Advanced mode)"
)
```

**Also update:**
- `get_schedule_cron_select_count()` method - may need to locate CronSelect by testids instead of CSS class
- Test expectations: change "Default"/"Advanced" references to "Builder"/"Cron Expression" if UI labels stay as-is

---

## Related Files

**Test Files:**
- `automation/tests/ui/pipelines_2/test_pipeline_schedule_trigger_settings_modal.py`
- `automation/tests/ui/pipelines/test_pipeline_entry_point_trigger_types_persist.py`

**Page Object:**
- `automation/pages/pipeline_detail_page.py` (lines 1325-1400 approx)

**Investigation Documents:**
- `PIPELINES_INVESTIGATION_RUN_32864131553.md` - Initial failure analysis
- `SCHEDULE_MODAL_FIX_VERIFICATION_RUN_32910843812.md` - Fallback locator verification
- `SCHEDULE_MODAL_TESTID_TODO.md` - Tracking document (superseded by this file)

---

## Priority

**High** - These tests are in the pipelines regression suite and currently using non-compliant fallback locators as workarounds.

---

## Next Steps

1. **Add testids to EliteaUI** - All components listed above
2. **Commit to `automation/testids` branch** - HMR will make them available immediately on localhost
3. **Test with new testids** - Verify tests pass with testid-only locators
4. **Remove fallback locators** - Restore testid-only pattern in `pipeline_detail_page.py`
5. **Human cherry-picks to `main`** - Per project workflow

---

*Document created: 2026-08-26*  
*Last updated: 2026-08-26*
