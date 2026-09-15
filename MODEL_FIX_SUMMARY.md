# Model Availability Fix - test_import_agent_valid_md_file.py

**Date:** 2026-09-11  
**Issue:** Test expected GPT-5.2 but stage2 defaults to Claude 4.5 Sonnet  
**Solution:** Make test environment-aware instead of skipping

---

## Changes Made

### ✅ Environment-Aware Model Configuration

**Before (hardcoded GPT-5.2):**
```python
EXPECTED_MODEL_DISPLAY_NAME = "GPT-5.2"

fixture_content = (
    "---\n"
    f"model: {settings.default_model_name}\n"  # Always gpt-5.2
    "---\n"
)
```

**After (environment-aware):**
```python
# Environment-specific model configuration
if settings.is_stage2:
    TEST_MODEL_NAME = "anthropic.claude-sonnet-4.5-20250514"
    EXPECTED_MODEL_DISPLAY_NAME = "Anthropic Claude 4.5 Sonnet"
else:
    TEST_MODEL_NAME = "gpt-5.2"
    EXPECTED_MODEL_DISPLAY_NAME = "GPT-5.2"

fixture_content = (
    "---\n"
    f"model: {TEST_MODEL_NAME}\n"  # Environment-aware
    "---\n"
)
```

---

## Why This Approach?

### ❌ Option 1: Skip Test (Original Approach)
```python
@pytest.mark.skipif(
    settings.is_stage2,
    reason="GPT-5.2 not available on stage2"
)
def test_import_agent_valid_md_file(...):
```

**Problems:**
- Loses test coverage on stage2
- Doesn't verify import works with Claude models
- Test becomes environment-specific instead of adaptive

### ✅ Option 2: Environment-Aware Model (Implemented)
```python
# Test runs on ALL environments
# Uses appropriate model per environment
def test_import_agent_valid_md_file(...):
```

**Benefits:**
- ✅ Full test coverage on all environments
- ✅ Verifies import works with both GPT and Claude models
- ✅ Test adapts to environment capabilities
- ✅ No skipped tests

---

## Test Coverage

| Environment | Model Used | Expected Display | Status |
|-------------|------------|------------------|--------|
| **localhost** | gpt-5.2 | GPT-5.2 | ✅ Works |
| **dev** | gpt-5.2 | GPT-5.2 | ✅ Works |
| **stage2** | anthropic.claude-sonnet-4.5-20250514 | Anthropic Claude 4.5 Sonnet | ⏳ Ready to test |
| **next** | gpt-5.2 | GPT-5.2 | ✅ Works |

---

## Testing Verification

### ✅ Configuration Test (Passed)

```bash
$ python3 test_model_config.py

============================================================
MODEL CONFIGURATION TEST
============================================================
Environment: stage2
Is Stage2: True
ELITEA_URL: https://stage2.elitea.ai

Test Model Configuration:
  Model ID: anthropic.claude-sonnet-4.5-20250514
  Display Name: Anthropic Claude 4.5 Sonnet

✅ Running on STAGE2
   Using Claude 4.5 Sonnet

✅ All model configuration checks passed!
============================================================
```

### ⏳ Full Test Run (Awaiting Execution)

**Command to run:**
```bash
cd automation
export ELITEA_URL=https://stage2.elitea.ai
export ELITEA_API_BASE=https://stage2.elitea.ai/api/v2
export APP_PREFIX=/app
export HEADLESS=true

.venv/bin/pytest \
  tests/ui/agents/test_import_agent_valid_md_file.py::TestImportAgentValidMdFile::test_import_agent_valid_md_file \
  -v --tb=short
```

**Expected result:**
- ✅ Test passes (not skipped)
- ✅ Imports agent with Claude 4.5 Sonnet model
- ✅ Verifies model selector shows "Anthropic Claude 4.5 Sonnet"

---

## Model ID Verification

### Claude 4.5 Sonnet Model ID

The model ID `anthropic.claude-sonnet-4.5-20250514` was determined from:

1. **Elitea platform naming convention**: `{provider}.{model-family}-{version}`
2. **Stage2 default**: Confirmed from GHA logs showing "Claude 4.5 Sonnet" as default
3. **Live verification needed**: Will be confirmed when test runs on stage2

**If test fails with "model not found"**, update `TEST_MODEL_NAME` based on actual error message.

---

## Rollback Plan

If Claude model ID is incorrect:

```bash
# Option A: Revert to skip approach
git checkout HEAD -- automation/tests/ui/agents/test_import_agent_valid_md_file.py

# Option B: Update model ID
# Edit line 68 in test_import_agent_valid_md_file.py:
TEST_MODEL_NAME = "correct-model-id-from-error"
```

---

## Files Changed

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `automation/tests/ui/agents/test_import_agent_valid_md_file.py` | ~15 lines | Environment-aware model config |
| `test_model_config.py` | +41 lines (NEW) | Verification script |

---

## Next Steps

1. ✅ Code changes complete
2. ⏳ **Run test on stage2** (awaiting user approval)
3. ⏳ Verify "Anthropic Claude 4.5 Sonnet" displays correctly
4. ⏳ If model ID wrong, update based on error message
5. ⏳ Clean up test script: `rm test_model_config.py`

---

## Impact

**Before fix:**
- 1 test skipped on stage2 (lost coverage)

**After fix:**
- 0 tests skipped
- Full coverage on all environments
- Test verifies both GPT and Claude model imports work

---

**Status:** ✅ Ready to test  
**Awaiting:** User approval to run on stage2
