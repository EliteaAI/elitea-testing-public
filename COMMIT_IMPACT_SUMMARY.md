# Orphan TMS References - Visual Impact Summary

## The Problem in Numbers

```
TMS Dashboard Claims:
┌─────────────────────────────────────────┐
│  Tests in automation:        432        │
│  Tests linked to TMS:        286  ✅    │
│  TMS Coverage:               66.2% ✅   │
└─────────────────────────────────────────┘

Reality After Analysis:
┌─────────────────────────────────────────┐
│  Tests in automation:        432        │
│  Valid TMS links:            159  ✅    │
│  Orphan refs:                127  ❌    │
│  True TMS Coverage:          36.8%      │
└─────────────────────────────────────────┘

Ghost Coverage:
  127 orphan refs = 44% of "automated" cases don't exist!
```

## Orphan Refs by Category

```
Chat Features                   94  ████████████████████
├── Folder Management           18  ████
├── Conversation Renaming       18  ████
├── Pinning                     11  ███
├── Attachments                  6  ██
├── Starters                     5  █
├── Hash Search                  7  ██
└── Other (Context, Canvas...)  29  ██████

Skills                          23  █████
├── Build/Edit with AI          17  ████
├── Publishing                   6  ██
└── Agent Interaction            6  ██

Help Center                     10  ███

Other                            3  █
├── Artifacts                    1
├── Settings                     1
└── Onboarding                   1
```

## What This Means

### For Coverage Metrics ❌

```diff
- Claimed TMS Coverage:  66.2%  (inflated by 127 ghost refs)
+ Actual TMS Coverage:   36.8%  (only counting real tests)
```

### For CI Correlation ❌

```bash
# correlate_results can't match 127 of these:
✅ PASS: tests.ui.chat.test_conversation_management...  ← Real test
❌ ORPHAN: tests.ui.chat.test_folder_creation...       ← Ghost ref
❌ ORPHAN: tests.ui.help_center.test_help_center...    ← Ghost ref
```

### For Developers 🤷

```
Developer: "Where's the automated test for ELITEA-2093?"
TMS:       "Right here! tests.ui.chat.test_agent_hub..."
Codebase:  "That file doesn't exist" ← 404 Not Found
```

## The Fix

### Before Cleanup
```yaml
# ELITEA-2093.md
execution_type: automated ❌
status: ready ❌
automation_test_id:
  - tests.ui.chat.test_agent_hub_create_conversation_via_starter... ❌
```

### After Cleanup
```yaml
# ELITEA-2093.md  
execution_type: manual ✅
status: draft ✅
# automation_test_id removed ✅
```

## Impact Timeline

```
State 1: Current (Orphan Refs Present)
├── TMS shows 66% coverage
├── CI can't correlate 127 refs
├── Developers confused by missing tests
└── Coverage metric is misleading

State 2: After Cleanup
├── TMS shows 37% coverage (accurate)
├── CI correlation works for all valid refs
├── No ghost refs confusing developers
└── Clear signal of what IS and ISN'T automated
```

## Action Plan

```
┌─────────────────────────────────────────────────────┐
│  Step 1: Review with Team                          │
│  ├── Folder Management (18) - Build or cancel?     │
│  ├── Conversation Renaming (18) - Build or cancel? │
│  ├── Skills Build/Edit AI (17) - Build or cancel?  │
│  └── Help Center (10) - Build or cancel?           │
├─────────────────────────────────────────────────────┤
│  Step 2: Clean TMS Case Files                      │
│  └── Update 127 case files (remove orphan refs)    │
├─────────────────────────────────────────────────────┤
│  Step 3: Rebuild TMS Index                         │
│  └── npx @onetest/tms build-index                  │
├─────────────────────────────────────────────────────┤
│  Step 4: Regenerate Dashboard                      │
│  └── Shows corrected 37% coverage                  │
└─────────────────────────────────────────────────────┘
```

## Files to Review

All generated reports are in project root:

1. **ORPHAN_REFS_SUMMARY.md** ← Start here
2. **LATEST_ORPHAN_ANALYSIS.md** ← Full list with all 127
3. **ALL_ORPHAN_REFS_COMPLETE.md** ← Actionable mapping
4. **TMS_ORPHAN_UPDATES.md** ← Update instructions
5. **COMMIT_IMPACT_SUMMARY.md** ← This visual summary

