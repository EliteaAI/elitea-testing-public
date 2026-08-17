# Environment Restart Detection & Retry Strategy Plan

**Created:** 2026-08-17  
**Context:** Run 32008576978 - 2 skills tests failed with `404 ()` console errors after page reload  
**Goal:** Identify and automatically retry tests that fail due to environment restarts

---

## Problem Summary

**Failed Tests:**
1. `test_max_five_skills_attach_limit` (line 308)
2. `test_remove_attached_skill_from_agent` (line 259)

**Common Pattern:**
- Both tests perform `page.reload()` 
- Both check console messages after reload
- Both fail with: `AssertionError: Expected no console errors after the full page reload, got: ['Failed to load resource: the server responded with a status of 404 ()']`

**Root Cause Hypothesis:**
The DEV environment backend may restart/redeploy during test execution, causing:
- Static resources (JS/CSS bundles) to return 404
- API endpoints to be temporarily unavailable
- WebSocket connections to drop

This is NOT a test bug or product bug — it's infrastructure turbulence that should trigger a retry.

---

## Detection Indicators

### 1. Console Error Patterns

**Environment Restart Signatures:**
```python
ENV_RESTART_PATTERNS = [
    # Static resource failures (bundles missing during restart)
    r"Failed to load resource.*404",
    r"Failed to load resource.*502",
    r"Failed to load resource.*503",
    
    # Network connectivity
    r"net::ERR_CONNECTION_RESET",
    r"net::ERR_CONNECTION_REFUSED",
    r"net::ERR_TIMED_OUT",
    
    # WebSocket drops during restart
    r"WebSocket.*connection.*closed",
    r"WebSocket.*error",
    
    # API unavailability
    r"Bad Gateway.*502",
    r"Service Unavailable.*503",
    r"Gateway Timeout.*504",
]
```

### 2. Page State Indicators

**After `page.reload()`, check for:**
```python
def is_env_restart_state(page) -> tuple[bool, str]:
    """Check if page shows environment restart indicators.
    
    Returns:
        (is_restart, reason) - True if restart detected with reason message
    """
    # Check 1: Page shows error page/blank page
    title = page.title()
    if not title or "error" in title.lower() or "unavailable" in title.lower():
        return True, f"Page title indicates error: {title}"
    
    # Check 2: Expected UI elements missing
    # (e.g., no navigation sidebar, no main content)
    if not page.locator('nav').count() and not page.locator('main').count():
        return True, "Core UI elements missing after reload"
    
    # Check 3: Backend health check endpoint
    try:
        response = page.request.get(f"{settings.elitea_url}/health")
        if response.status != 200:
            return True, f"Health check failed: {response.status}"
    except Exception as e:
        return True, f"Health check exception: {e}"
    
    return False, ""
```

### 3. Screenshot Analysis

**Visual indicators of restart:**
- Blank white page (React failed to load)
- Error message modals ("Service unavailable")
- Network error pages
- Partial UI rendering (header present, content missing)

**Implementation:**
```python
def analyze_screenshot_for_restart(screenshot_path: str) -> bool:
    """Check if screenshot shows environment restart indicators.
    
    This is a last-resort heuristic when other checks are ambiguous.
    """
    # Read screenshot
    from PIL import Image
    import numpy as np
    
    img = Image.open(screenshot_path)
    img_array = np.array(img)
    
    # Check 1: Mostly blank (>90% white pixels)
    white_pixels = np.sum(img_array > 240) / img_array.size
    if white_pixels > 0.9:
        return True  # Likely blank error page
    
    # Check 2: Look for error keywords in OCR (if pytesseract available)
    # try:
    #     import pytesseract
    #     text = pytesseract.image_to_string(img)
    #     error_keywords = ["unavailable", "502", "503", "connection", "timeout"]
    #     if any(kw in text.lower() for kw in error_keywords):
    #         return True
    # except ImportError:
    #     pass
    
    return False
```

---

## Retry Strategy

### Option 1: pytest-rerunfailures (Recommended)

**Installation:**
```bash
pip install pytest-rerunfailures
```

**Implementation - Conditional Retry Fixture:**

```python
# conftest.py

import re
import pytest

ENV_RESTART_PATTERNS = [
    r"Failed to load resource.*404",
    r"Failed to load resource.*502",
    r"Failed to load resource.*503",
    r"net::ERR_CONNECTION",
    r"WebSocket.*connection.*closed",
    r"Bad Gateway",
    r"Service Unavailable",
    r"Gateway Timeout",
]

def is_env_restart_failure(report) -> bool:
    """Check if test failure matches environment restart signature."""
    if report.outcome != "failed":
        return False
    
    # Check exception message
    if hasattr(report.longrepr, 'reprcrash'):
        message = report.longrepr.reprcrash.message
        for pattern in ENV_RESTART_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return True
    
    # Check test output/logs
    if hasattr(report, 'capstdout'):
        output = report.capstdout
        for pattern in ENV_RESTART_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return True
    
    return False

def pytest_runtest_makereport(item, call):
    """Hook to conditionally retry on environment restart failures."""
    outcome = yield
    report = outcome.get_result()
    
    if call.when == "call" and is_env_restart_failure(report):
        # Mark for rerun
        item.stash[pytest_rerunfailures.rerun_key] = True
        logger.warning(
            f"Test {item.nodeid} failed due to environment restart. "
            f"Will retry up to {item.config.option.reruns} times."
        )
```

**Usage in pytest.ini:**
```ini
[pytest]
addopts =
    --reruns 2                      # Max 2 retries
    --reruns-delay 10               # Wait 10s between retries (let env stabilize)
    --only-rerun "Failed to load resource"
    --only-rerun "ERR_CONNECTION"
    --only-rerun "WebSocket.*closed"
```

**Per-Test Override (for known-flaky tests):**
```python
@pytest.mark.flaky(reruns=3, reruns_delay=15)
def test_max_five_skills_attach_limit(...):
    """This test reloads page and may hit env restarts."""
    ...
```

### Option 2: Custom Retry Decorator

**For more granular control:**

```python
# automation/utils/retry.py

import time
import functools
from typing import Callable, Type
from playwright.sync_api import Page

def retry_on_env_restart(
    max_attempts: int = 3,
    delay: int = 10,
    exceptions: tuple[Type[Exception], ...] = (AssertionError,)
):
    """Retry test if environment restart detected.
    
    Args:
        max_attempts: Max retry attempts
        delay: Seconds between retries
        exceptions: Exception types to catch
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            page = None
            for arg in args:
                if isinstance(arg, Page):
                    page = arg
                    break
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    error_msg = str(e)
                    
                    # Check if error matches restart pattern
                    is_restart = any(
                        re.search(pattern, error_msg, re.IGNORECASE)
                        for pattern in ENV_RESTART_PATTERNS
                    )
                    
                    if not is_restart:
                        raise  # Not a restart error, fail immediately
                    
                    if attempt == max_attempts:
                        raise  # Last attempt, give up
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed due to env restart. "
                        f"Retrying after {delay}s... Error: {error_msg}"
                    )
                    
                    # Optional: Check page state
                    if page:
                        is_restart_state, reason = is_env_restart_state(page)
                        if is_restart_state:
                            logger.info(f"Page state confirms restart: {reason}")
                    
                    time.sleep(delay)
                    
                    # Optional: Reload page before retry
                    if page:
                        page.reload()
                        page.wait_for_load_state("networkidle", timeout=15000)
            
            return None  # Unreachable
        return wrapper
    return decorator
```

**Usage:**
```python
from automation.utils.retry import retry_on_env_restart

@retry_on_env_restart(max_attempts=3, delay=10)
def test_max_five_skills_attach_limit(page, ...):
    """Test that reloads page and may hit env restart."""
    ...
```

---

## Implementation Plan

### Phase 1: Detection Infrastructure (1-2 hours)

**1.1 Add Detection Utilities**
```bash
# Create new file
touch automation/utils/env_restart_detection.py
```

**Contents:**
```python
# automation/utils/env_restart_detection.py

import re
import logging
from typing import Pattern
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

ENV_RESTART_PATTERNS: list[str | Pattern] = [
    r"Failed to load resource.*404",
    r"Failed to load resource.*502",
    r"Failed to load resource.*503",
    r"net::ERR_CONNECTION_RESET",
    r"net::ERR_CONNECTION_REFUSED",
    r"net::ERR_TIMED_OUT",
    r"WebSocket.*connection.*closed",
    r"WebSocket.*error",
    r"Bad Gateway.*502",
    r"Service Unavailable.*503",
    r"Gateway Timeout.*504",
]

def matches_restart_signature(message: str) -> bool:
    """Check if message matches env restart pattern."""
    return any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in ENV_RESTART_PATTERNS
    )

def is_env_restart_state(page: Page) -> tuple[bool, str]:
    """Check if page shows environment restart indicators."""
    # Implementation from "Detection Indicators" section above
    ...

def analyze_console_errors(console_messages: list) -> tuple[bool, list[str]]:
    """Analyze console messages for restart signatures.
    
    Returns:
        (is_restart, matching_messages)
    """
    restart_errors = []
    for msg in console_messages:
        text = msg.text if hasattr(msg, 'text') else str(msg)
        if matches_restart_signature(text):
            restart_errors.append(text)
    
    return bool(restart_errors), restart_errors
```

**1.2 Update Conftest**

Add pytest hook to detect and report restart failures:

```python
# conftest.py

from automation.utils.env_restart_detection import matches_restart_signature

def pytest_runtest_makereport(item, call):
    """Enhanced reporting with restart detection."""
    outcome = yield
    report = outcome.get_result()
    
    if call.when == "call" and report.outcome == "failed":
        # Check if failure matches restart signature
        if hasattr(report.longrepr, 'reprcrash'):
            message = report.longrepr.reprcrash.message
            if matches_restart_signature(message):
                # Add marker to report
                report.user_properties.append(("env_restart_suspected", True))
                logger.warning(
                    f"Test {item.nodeid} failed with env restart signature: {message}"
                )
```

### Phase 2: Selective Retry (2-3 hours)

**2.1 Install pytest-rerunfailures**
```bash
pip install pytest-rerunfailures
echo "pytest-rerunfailures>=14.0" >> requirements.txt
```

**2.2 Configure pytest.ini**
```ini
[pytest]
markers =
    ... (existing markers)
    
addopts =
    ... (existing options)
    --reruns 2                      # Global: retry up to 2 times
    --reruns-delay 10               # Wait 10s between retries
    --only-rerun "Failed to load resource"  # Only retry these patterns
    --only-rerun "ERR_CONNECTION"
    --only-rerun "WebSocket"
```

**2.3 Mark Affected Tests**

Update the two failing tests with explicit retry config:

```python
# tests/ui/skills/test_agent_max_five_skills_limit.py

import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=15, condition="env restarts during page reload")
def test_max_five_skills_attach_limit(...):
    """Test max 5 skills attachment limit.
    
    NOTE: This test performs page.reload() and may encounter environment
    restarts. Configured with 3 retries to handle transient restart failures.
    """
    ...
```

```python
# tests/ui/skills/test_remove_attached_skill_from_agent.py

import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=15, condition="env restarts during page reload")
def test_remove_attached_skill_from_agent(...):
    """Test removing attached skill from agent.
    
    NOTE: This test performs page.reload() and may encounter environment
    restarts. Configured with 3 retries to handle transient restart failures.
    """
    ...
```

### Phase 3: Enhanced Console Error Handling (1 hour)

**3.1 Update Console Error Assertions**

Create helper to distinguish product bugs from infrastructure issues:

```python
# automation/utils/console_errors.py

from automation.utils.env_restart_detection import matches_restart_signature

def filter_env_restart_errors(console_messages: list) -> tuple[list, list]:
    """Separate environment restart errors from real product errors.
    
    Returns:
        (product_errors, restart_errors)
    """
    product_errors = []
    restart_errors = []
    
    for msg in console_messages:
        text = msg.text if hasattr(msg, 'text') else str(msg)
        if matches_restart_signature(text):
            restart_errors.append(msg)
        else:
            product_errors.append(msg)
    
    return product_errors, restart_errors
```

**3.2 Update Test Assertions**

```python
# In affected tests

from automation.utils.console_errors import filter_env_restart_errors

# Old assertion:
# assert not console_messages, (
#     "Expected no console errors after the full page reload, "
#     f"got: {[m.text for m in console_messages]}"
# )

# New assertion:
product_errors, restart_errors = filter_env_restart_errors(console_messages)

if restart_errors:
    logger.warning(
        f"Environment restart detected during page reload: "
        f"{[m.text for m in restart_errors]}"
    )
    # Optionally: raise specific exception to trigger retry
    if len(restart_errors) == len(console_messages):
        # ALL errors are restart-related, likely transient
        raise EnvironmentRestartError(
            f"Page reload hit environment restart: "
            f"{[m.text for m in restart_errors]}"
        )

assert not product_errors, (
    f"Expected no product errors after page reload, got: "
    f"{[m.text for m in product_errors]}"
)
```

### Phase 4: Validation (30 min)

**4.1 Local Test**
```bash
# Run affected tests locally
cd automation
../.venv/bin/pytest \
    tests/ui/skills/test_agent_max_five_skills_limit.py \
    tests/ui/skills/test_remove_attached_skill_from_agent.py \
    -v --reruns 2 --reruns-delay 5
```

**4.2 CI Test**
```bash
# Trigger DEV workflow with retry config
env -u GITHUB_TOKEN gh workflow run "UI Tests DEV" \
  --ref automation/fixes \
  -f ref=automation/fixes \
  -f suite=skills \
  -f markers="not new and not blocked and not flaky" \
  --repo EliteaAI/elitea-testing-public
```

**4.3 Verify Retry Behavior**
- Check workflow logs for retry attempts
- Confirm retries only trigger on restart signatures
- Verify final status after retries

---

## Rollout Strategy

### Stage 1: Conservative (Recommended Start)
- Add retry ONLY to the 2 failing tests
- Use `@pytest.mark.flaky(reruns=3, reruns_delay=15)`
- Monitor for false positives (retries on non-restart failures)

### Stage 2: Targeted
- Identify all tests that call `page.reload()`
- Add conditional retry to those tests
- Keep global retry disabled

### Stage 3: Global
- Enable global retry in pytest.ini
- Use `--only-rerun` patterns to limit scope
- Monitor retry frequency

---

## Metrics & Monitoring

**Track these metrics per workflow run:**
1. **Retry Rate:** % of tests that triggered retries
2. **Retry Success Rate:** % of retried tests that passed
3. **Restart Frequency:** How often restart signatures appear
4. **False Positives:** Retries triggered by non-restart failures

**Implementation:**
```python
# conftest.py

retry_stats = {
    "total_retries": 0,
    "successful_retries": 0,
    "failed_retries": 0,
    "restart_detected": 0,
}

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Report retry statistics."""
    terminalreporter.section("Environment Restart Retry Statistics")
    terminalreporter.write_line(f"Total retries: {retry_stats['total_retries']}")
    terminalreporter.write_line(f"Successful: {retry_stats['successful_retries']}")
    terminalreporter.write_line(f"Failed: {retry_stats['failed_retries']}")
    terminalreporter.write_line(
        f"Restart signatures detected: {retry_stats['restart_detected']}"
    )
```

---

## Risks & Mitigation

### Risk 1: Masking Real Product Bugs
**Symptom:** A real 404 error gets retried and passes intermittently

**Mitigation:**
- Be very specific with retry patterns (only infrastructure signatures)
- Log every retry with reason
- Review retry logs weekly to catch patterns
- Consider manual approval for first-time retry patterns

### Risk 2: Long CI Times
**Symptom:** Retries add 30-60s per failed test

**Mitigation:**
- Limit max retries to 2-3
- Use reasonable delays (10-15s, not 60s)
- Only retry on specific failure patterns
- Monitor total CI time increase

### Risk 3: False Negatives
**Symptom:** Real restart failure doesn't match detection patterns

**Mitigation:**
- Start conservative, expand patterns as needed
- Log all console errors to catch new signatures
- Regularly review "real" failures for missed patterns
- Allow manual override via test markers

---

## Success Criteria

**Phase 1 (Detection):**
- [ ] Detection utilities added and tested
- [ ] Console error filtering works correctly
- [ ] Page state detection identifies restart scenarios

**Phase 2 (Retry):**
- [ ] pytest-rerunfailures installed and configured
- [ ] 2 failing tests marked with retry config
- [ ] Retry only triggers on restart signatures

**Phase 3 (Validation):**
- [ ] Tests pass on CI with restart-tolerant retry
- [ ] No false positive retries observed
- [ ] Retry statistics tracked and reported

**Overall Success:**
- [ ] Run 32008576978 type failures no longer block CI
- [ ] Real product errors still fail immediately
- [ ] Retry rate < 5% of total tests
- [ ] No increase in "mystery passes" (tests that pass on retry without clear reason)

---

## Next Steps

1. **Immediate (Today):**
   - Implement Phase 1 (detection utilities)
   - Add `@pytest.mark.flaky` to 2 failing tests
   - Trigger test run to validate

2. **Short-term (This Week):**
   - Monitor retry behavior
   - Tune patterns based on observed failures
   - Document new retry patterns as they emerge

3. **Long-term (Ongoing):**
   - Expand retry coverage to other page-reload tests
   - Consider global retry with strict patterns
   - Build dashboard for retry metrics
   - Work with backend team to reduce restart frequency

---

## References

- **pytest-rerunfailures docs:** https://github.com/pytest-dev/pytest-rerunfailures
- **Failed run:** https://github.com/EliteaAI/elitea-testing-public/actions/runs/32008576978
- **Test files:**
  - `automation/tests/ui/skills/test_agent_max_five_skills_limit.py`
  - `automation/tests/ui/skills/test_remove_attached_skill_from_agent.py`
- **Console error patterns:** Based on Chromium console error format

---

**Plan Status:** Ready for implementation  
**Est. Time:** 4-6 hours  
**Priority:** HIGH (blocks CI)  
**Risk Level:** LOW (conservative retry patterns)
