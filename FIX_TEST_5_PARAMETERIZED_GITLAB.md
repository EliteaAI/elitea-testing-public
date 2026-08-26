# Test #5: test_toolkit_parameterized.py - GitLab Variant Analysis

**Date:** 2026-08-17  
**Test:** `test_create_toolkit[gitlab]`  
**File:** `tests/ui/toolkits/test_toolkit_parameterized.py`  
**Status:** ❌ **CONFIGURATION ISSUE - Missing Environment Variable**

---

## Issue

### Test Result:
**FAILED** - Page stayed on `/toolkits/create/gitlab` (save did not succeed)

```
AssertionError: assert '/toolkits/create' not in 'https://dev.elitea.ai/app/toolkits/create/gitlab'
```

### Screenshot Evidence:
Shows GitLab toolkit creation form with:
- ✅ Toolkit Name filled: "AutoTest GitLab Toolkit 17869790"
- ✅ Description filled: "Test GitLab toolkit for automation"
- ✅ GitLab Configuration selected
- ❌ **Repository field EMPTY with RED error: "Field is required"**
- Branch: "main" (filled)

---

## Root Cause

**Missing environment variable:** `GITLAB_REPOSITORY` is **not set** in `.env.test`

### Test Configuration Chain:

**toolkit_configs.py (line ~140):**
```python
"gitlab": ToolkitConfig(
    ...
    ui_form_fields={
        "Repository": settings.gitlab_repository,  # ← This is EMPTY
    },
    ...
)
```

**config.py (line ~127):**
```python
gitlab_repository: str = ""  # ← Default empty, NOT set in .env.test
```

**Actual .env.test values:**
```bash
gitlab_repository: []  # EMPTY ❌
gitlab_url: [https://githyd.epam.com]  # ✅
gitlab_private_token: [20 chars]  # ✅
```

### Test Flow:

1. Test calls `_fill_toolkit_form_fields(page, cfg)` (line 324)
2. Function iterates `cfg.ui_form_fields` → `{"Repository": ""}`
3. Line 696: `if not existing:` check sees the field is empty
4. Line 697-698: Tries to fill with `value=""` → **fills nothing**
5. Save button clicked
6. **Backend validation fails:** "Repository" is required
7. Page stays on `/toolkits/create/gitlab`
8. Test fails

---

## Fix Options

### Option 1: Add GITLAB_REPOSITORY to .env.test (Recommended)

Add to `.env.test`:
```bash
GITLAB_REPOSITORY=your-gitlab-org/your-test-repo
```

**Pros:**
- Simple, direct fix
- Mirrors the pattern for other toolkits (GitHub has `GIT_REPO`, etc.)
- Test will work for anyone who has a GitLab instance

**Cons:**
- Requires a real GitLab repository
- Different team members may use different repositories

---

### Option 2: Skip GitLab Tests if Repository Not Set

Modify `toolkit_configs.py`:
```python
"gitlab": ToolkitConfig(
    ...
    skip_reason="GITLAB_REPOSITORY not set" if not settings.gitlab_repository else None,
    ...
)
```

**Pros:**
- Test skips gracefully with clear message
- No false failures

**Cons:**
- GitLab tests never run on this environment
- Reduces test coverage

---

### Option 3: Use a Default Test Repository

Modify `toolkit_configs.py`:
```python
"gitlab": ToolkitConfig(
    ...
    ui_form_fields={
        "Repository": settings.gitlab_repository or "elitea/elitea-testing-default",
    },
    ...
)
```

**Pros:**
- Test runs even without explicit env var
- Can use a public test repository

**Cons:**
- Hardcoded default may not exist
- Mixing configuration with code

---

## Recommended Action

**Add `GITLAB_REPOSITORY` to `.env.test`** with a valid repository path that exists on the configured GitLab instance (`https://githyd.epam.com`).

Example:
```bash
# .env.test
GITLAB_URL=https://githyd.epam.com
GITLAB_PRIVATE_TOKEN=your_token_here
GITLAB_REPOSITORY=your-org/test-repo  # ← ADD THIS
GITLAB_BASE_BRANCH=main
```

---

## Impact on Other Parameterized Tests

This same pattern affects **ALL toolkit types** in `test_toolkit_parameterized.py`:

| Toolkit | Required Env Var | Status in .env.test |
|---------|-----------------|-------------------|
| GitHub | `GIT_REPO` | ✅ Set to `EliteaAI/elitea-testing-public` |
| Jira | (none - username/url in credential) | ✅ No form fields |
| GitLab | `GITLAB_REPOSITORY` | ❌ **MISSING** |
| Bitbucket | `BITBUCKET_PROJECT`, `BITBUCKET_REPOSITORY` | ❓ Need to check |
| Confluence | (none - space field may have issues) | ❓ Need to check |

**Next:** Check if Bitbucket tests also failed due to missing `BITBUCKET_REPOSITORY`.

---

## Summary

**Status:** ❌ **CONFIGURATION ISSUE**

Test `test_create_toolkit[gitlab]` fails because `GITLAB_REPOSITORY` is not set in `.env.test`. The test cannot fill the required "Repository" field, so the save fails and the test correctly reports failure.

**Action:** Add `GITLAB_REPOSITORY=<valid-repo-path>` to `.env.test`, then re-run the test.

**Alternative:** If GitLab testing is not currently needed, skip GitLab tests by marking them appropriately or leaving them blocked until the environment is configured.
