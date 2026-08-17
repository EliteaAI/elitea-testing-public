# Blocked Tests in Toolkits Suite

**Date:** 2026-08-17  
**Branch:** automation/fixes  
**Total Tests in Suite:** 49  
**Blocked Tests:** 7  
**Blocked Percentage:** 14.3%

---

## Blocked Tests List

| # | Test Name | File | Notes |
|---|-----------|------|-------|
| 1 | `test_create_private_credential_from_toolkit_dropdown` | `test_credential_create_private_from_toolkit_dropdown.py` | Private credential creation flow |
| 2 | `test_credential_usage_and_deletion_mismatch` | `test_credential_usage_in_toolkit_flows.py` | Credential usage validation |
| 3 | `test_mcp_search_by_name` | `test_mcp_search_by_name.py` | MCP search functionality |
| 4 | `test_credential_duplicate_and_empty_required_field_validation` | `test_credential_duplicate_mismatch_validation.py` | Validation edge cases |
| 5 | `test_toolkit_test_settings` | `test_toolkit_parameterized.py` | Parameterized toolkit test |
| 6 | `test_delete_remote_mcp` | `test_mcp_delete_remote.py` | Remote MCP deletion |
| 7 | `test_create_artifact_toolkit_creates_bucket_verify_list_files` | `test_toolkit_creation_create_bucket_verify_list_files.py` | Artifact toolkit + bucket creation |

---

## Test Collection Summary

When running with markers `"not new and not blocked and not flaky"`:

```
Total collected: 49 tests
Blocked: 7 tests
Flaky: Some (exact count TBD - includes test_github_toolkit_test_settings)
Selected: ~3 tests (remaining stable tests)
```

**Recent runs:**
- Run 32031634934: 3 tests selected from toolkits suite
- Run 32033709516: Failed due to GitHub toolkit not available on DEV environment

---

## Categories of Blocked Tests

### Credential-Related (4 tests)
- `test_create_private_credential_from_toolkit_dropdown`
- `test_credential_usage_and_deletion_mismatch`
- `test_credential_duplicate_and_empty_required_field_validation`

### MCP-Related (2 tests)
- `test_mcp_search_by_name`
- `test_delete_remote_mcp`

### Toolkit Creation (2 tests)
- `test_toolkit_test_settings` (parameterized)
- `test_create_artifact_toolkit_creates_bucket_verify_list_files`

---

## Investigation Needed

None of the blocked tests have inline comments explaining why they're blocked. To understand the reasons:

1. Check git history: `git log --all --grep="blocked" -- tests/ui/toolkits/`
2. Check related issues in GitHub
3. Run tests locally to identify blocking issues
4. Review `BLOCKED_TESTS_INVESTIGATION.md` for patterns

---

## Related Files

- **Investigation docs:**
  - `BLOCKED_TESTS_INVESTIGATION.md` (2026-08-17)
  - `GITHUB_TOKEN_CI_ANALYSIS.md`
  - `TOKEN_UPDATE_SUMMARY.md`

- **Test files:**
  ```
  tests/ui/toolkits/test_credential_create_private_from_toolkit_dropdown.py
  tests/ui/toolkits/test_credential_usage_in_toolkit_flows.py
  tests/ui/toolkits/test_mcp_search_by_name.py
  tests/ui/toolkits/test_credential_duplicate_mismatch_validation.py
  tests/ui/toolkits/test_toolkit_parameterized.py
  tests/ui/toolkits/test_mcp_delete_remote.py
  tests/ui/toolkits/test_toolkit_creation_create_bucket_verify_list_files.py
  ```

---

## Environment Issue Discovery

**Critical Finding (2026-08-17):**

GitHub toolkit tests that were previously passing are now hitting:
```
ERROR: 403 Client Error: Forbidden
{"ok": false, "error": "Toolkit type 'github' is not available in this deployment"}
```

**Timeline:**
- Run 32031634934 (~12:50 UTC): GitHub tests **PASSED** ✅
- Run 32033709516 (~13:11 UTC): GitHub tests **ERROR** ❌ (41 min later)

**Root Cause:** GitHub toolkit type was disabled/removed from DEV environment configuration between runs.

**Impact:**
- Any test using `github_toolkit` fixture will fail
- Tests: `test_agent_with_toolkit_executes_in_chat`, `test_github_toolkit_test_settings`, and others

**Action Required:**
- Check DEV environment toolkit configuration
- Re-enable GitHub toolkit type if intended
- Or mark all GitHub toolkit tests as blocked if it's permanently unavailable on DEV
