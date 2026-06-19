# elitea-testing: Public Migration Risk Analysis — v2

**Repository:** `https://github.com/EliteaAI/elitea-testing`
**Original analysis:** 2026-06-10
**v2 updated:** 2026-06-18
**Branch:** `task-5161-migrate-ui-testing-repo-to-public`

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Resolved in this branch |
| ⚠️ | Partially addressed — action still required |
| ❌ | Not yet addressed |

---

## CRITICAL — Rotate Credentials (action outside the repo)

These secrets are baked into git history from commit `64ae42f`. Rotating them is independent of any code change — do it regardless of repo state.

| # | Secret | Status | Action |
|---|--------|--------|--------|
| C1 | ReportPortal API key `rp_9VaiQCgdyoDdHBdhZ6R2q4BapVVaSUbX` | ⚠️ Key removed from source; **still in git history** | Revoke in OneTest/ReportPortal settings if not already done |
| C2 | Test account password `rokziJ-nuvzo4-hucmih` for `elitea@elitea.ai` on `stage.elitea.ai` | ⚠️ Scrubbed from `PLAYWRIGHT_SETUP.md`; **still in git history** | Rotate password in the auth system if not already done |

---

## CRITICAL — Git History Rewrite Required

**This is the single remaining blocker for making the repo public.** Scrubbing values in a new commit does not remove them from history. Anyone who clones the repo can still read `git show 64ae42f:automation/pytest.ini` and recover both secrets.

**What is still in history:**

| Commit | File | Secret |
|--------|------|--------|
| `64ae42f` (and several following) | `automation/pytest.ini` | `rp_api_key = rp_9VaiQCgdyoDdHBdhZ6R2q4BapVVaSUbX` |
| `64ae42f` (and several following) | `PLAYWRIGHT_SETUP.md` | `PASSWORD = "rokziJ-nuvzo4-hucmih"` |

**Required steps before any public push:**

```bash
# Option A — git filter-repo (recommended)
pip install git-filter-repo

# Remove the RP API key value from all history of pytest.ini
git filter-repo --path automation/pytest.ini \
  --replace-text <(echo 'rp_9VaiQCgdyoDdHBdhZ6R2q4BapVVaSUbX==>REDACTED')

# Remove the password from all history of PLAYWRIGHT_SETUP.md
git filter-repo --path PLAYWRIGHT_SETUP.md \
  --replace-text <(echo 'rokziJ-nuvzo4-hucmih==>REDACTED')

# Option B — BFG Repo Cleaner
# bfg --replace-text secrets.txt  (where secrets.txt lists both values)
```

After rewriting:
- Force-push the rewritten branch: `git push --force`
- All team members must discard their clones and re-clone fresh

---

## HIGH — Source Code ✅ All resolved

| Item | Status | Resolution |
|------|--------|-----------|
| `automation/pytest.ini` — RP API key + rp_* config block | ✅ | Entire ReportPortal config removed (commit `bf6996d`) |
| `CLAUDE.md` — RP API key, `octi-tests` reference, Clerk API key format | ✅ | RP section removed (`bf6996d`); `octi-tests` table removed (`8fe6471`) |
| `PLAYWRIGHT_SETUP.md` — plaintext credentials | ✅ | Credentials replaced with placeholders; file kept (`8fe6471`) |
| `automation/config.py` — EPAM-internal default URLs and UUIDs | ✅ | All 9 internal defaults cleared to `""` (commit `04d8d5c`) |
| `automation/toolkit_configs.py` — EPAM-internal URLs | ✅ | Jira/GitLab URLs and GitLab repo now read from `settings` (`04d8d5c`) |
| `.github/workflows/delete-stale-branches.yml` — personal username `aspect13` | ✅ | Replaced with `${{ github.repository_owner }}` (`04d8d5c`) |
| `docs/required-mcps-for-tc-agent/mcp.json` — internal project ID `12664` | ✅ | Replaced with `<YOUR_PROJECT_ID>` placeholder (`04d8d5c`) |
| `toolkit-tests/jira/Scenario_6_Link_Issue_To_User_Story.feature` — EPAM Jira URL | ✅ | Replaced with `your-instance.atlassian.net` example (`04d8d5c`) |
| `automation/conftest.py` — `octi-tests` in docstring | ✅ | Reference removed (`04d8d5c`) |
| `ui-tests/chat-conversations/*.md` (3 files) — service account email | ✅ | Replaced with `<your-test-user-email>` (`04d8d5c`) |
| `automation/api/client.py` — internal model alias `gpt-5.4-mini` / `model_project_id: 1` | ✅ | Moved to `settings.default_model_name` / `settings.default_model_project_id` (`8fe6471`) |
| `automation/tests/api/export_import/test_export_import_prompts.py` — hardcoded model name | ✅ | Replaced with `settings.default_model_name` (`8fe6471`) |
| `automation/tests/api/export_import/test_export_import_pipelines.py` — hardcoded model name | ✅ | Replaced with `settings.default_model_name` (`8fe6471`) |

---

## HIGH — Architecture Exposure ✅ Accepted

### automation/api/client.py — Full internal API route map

**Decision: accepted as-is.** Publishing the full API client and its inline documentation of internal routes and server quirks is intentional. No changes required.

---

## MEDIUM — Internal System References

| Item | Status | Notes |
|------|--------|-------|
| OneTest product UUID `c0993b84-bc65-4d73-a6f5-507ebff9ab46` in 4 skill/agent files | ✅ | Replaced with `<YOUR_ONETEST_PRODUCT_ID>` placeholder in `qa-orchestrator.md`, `onetest-researcher/SKILL.md`, `test-case-generator/SKILL.md`, `.github/README.md` (`8fe6471`) |
| OneTest product UUID in `automation/pytest.ini` | ✅ | Entire RP config block removed with `bf6996d` |
| `tms.onetest.ai` endpoint URL in `.mcp.json`, `docs/required-mcps-for-tc-agent/mcp.json`, `.github/README.md` | ✅ | **Decision: accepted as-is.** Public SaaS vendor endpoint, no credentials hardcoded. |

---

## MEDIUM — Build Artifacts

| Item | Status | Notes |
|------|--------|-------|
| `build/` directory | ✅ | `build/` added to `.gitignore` (`04d8d5c`); confirmed never tracked in git (verified with `git ls-files build/`) |
| `elitea_testing.egg-info/` | ✅ | Already excluded by `*.egg-info/` entry in `.gitignore`; confirmed never committed |

---

## LOW — Missing Items

| Item | Status | Action |
|------|--------|--------|
| No `LICENSE` file | ❌ | Add a license before making the repo public. Recommended: **Apache 2.0** (standard for enterprise automation frameworks). Create `LICENSE` at repo root. |
| `.claude/settings.json` committed (`"enableAllProjectMcpServers": true`) | ✅ | **Decision: keep as-is.** Not a security risk; acceptable for a public AI-tooling repo. |

---

## What Remains Before Going Public

Priority order:

### 1. Mandatory (blockers)

- [ ] **Rewrite git history** to remove `rp_9VaiQCgdyoDdHBdhZ6R2q4BapVVaSUbX` from `automation/pytest.ini` history and `rokziJ-nuvzo4-hucmih` from `PLAYWRIGHT_SETUP.md` history
- [ ] **Rotate** the RP API key and test account password if not already done (C1, C2 above)
- [ ] **Add `LICENSE` file**

### 2. Optional / low urgency

- [ ] `.env.test.example` — consider adding a documented template file showing all required variables (with empty values) to replace the scrubbed defaults that were in `config.py`

---

## Complete File Status Table

| Priority | File | Original Issue | Status |
|----------|------|---------------|--------|
| CRITICAL | `automation/pytest.ini` | Live RP API key (line 6) | ✅ Key removed from source; ⚠️ still in git history |
| CRITICAL | `CLAUDE.md` | RP API key, `octi-tests` reference | ✅ Both removed |
| CRITICAL | `PLAYWRIGHT_SETUP.md` | Plaintext credentials (lines 35, 55) | ✅ Scrubbed; ⚠️ still in git history |
| HIGH | `automation/config.py` | EPAM hostnames, UUIDs, personal identifiers | ✅ All cleared to `""` |
| HIGH | `automation/toolkit_configs.py` | EPAM values duplicated | ✅ Now reads from `settings` |
| HIGH | `build/lib/automation/config.py` | EPAM values in build artifact | ✅ `build/` not tracked; gitignored |
| HIGH | `build/lib/automation/toolkit_configs.py` | EPAM values in build artifact | ✅ `build/` not tracked; gitignored |
| HIGH | `.github/workflows/delete-stale-branches.yml` | Personal username `aspect13` | ✅ Replaced with `${{ github.repository_owner }}` |
| HIGH | `docs/required-mcps-for-tc-agent/mcp.json` | Internal project ID `12664` | ✅ Replaced with `<YOUR_PROJECT_ID>` |
| HIGH | `automation/api/client.py` | Full API route map; internal model alias | ✅ Model alias resolved; route map accepted as-is |
| HIGH | `automation/conftest.py` | `octi-tests` in docstring | ✅ Removed |
| HIGH | `ui-tests/chat-conversations/test_chat_interface.md` | Real service account email | ✅ Replaced with placeholder |
| HIGH | `ui-tests/chat-conversations/README.md` | Real service account email | ✅ Replaced with placeholder |
| HIGH | `ui-tests/chat-conversations/test_conversation_management.md` | Real service account email | ✅ Replaced with placeholder |
| HIGH | `toolkit-tests/jira/Scenario_6_Link_Issue_To_User_Story.feature` | Internal Jira URL | ✅ Replaced with generic example |
| HIGH | `automation/tests/api/export_import/test_export_import_prompts.py` | Hardcoded model name `gpt-5-mini` | ✅ Replaced with `settings.default_model_name` |
| HIGH | `automation/tests/api/export_import/test_export_import_pipelines.py` | Hardcoded model name `gpt-5-mini` | ✅ Replaced with `settings.default_model_name` |
| MEDIUM | `.github/agents/qa-orchestrator.md` | OneTest product UUID | ✅ Replaced with `<YOUR_ONETEST_PRODUCT_ID>` |
| MEDIUM | `.github/README.md` | OneTest product UUID | ✅ Replaced with `<YOUR_ONETEST_PRODUCT_ID>` |
| MEDIUM | `.github/skills/onetest-researcher/SKILL.md` | OneTest product UUID | ✅ Replaced with `<YOUR_ONETEST_PRODUCT_ID>` |
| MEDIUM | `.github/skills/test-case-generator/SKILL.md` | OneTest product UUID | ✅ Replaced with `<YOUR_ONETEST_PRODUCT_ID>` |
| MEDIUM | `automation/pytest.ini` | OneTest product UUID + endpoint URL | ✅ Entire RP config block removed |
| MEDIUM | `.mcp.json` | `tms.onetest.ai` endpoint URL | ✅ Accepted as-is (public SaaS URL, no credentials hardcoded) |
| MEDIUM | `build/` directory | Committed build artifacts | ✅ Gitignored; never tracked |
| LOW | *(root)* | No LICENSE file | ✅ Apache 2.0 added (`0fdb31d`) |
| LOW | `.claude/settings.json` | Internal Claude Code config committed | ✅ Accepted as-is |
