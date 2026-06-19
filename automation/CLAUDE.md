# Elitea Test Automation

Test automation for [Elitea AI Platform](https://stage.elitea.ai) using Playwright + pytest.

# Additional Instructions
- Coding rules (auto-applied): @.claude/rules/page-objects.md, @.claude/rules/ui-tests.md, @.claude/rules/api-patterns.md, @.claude/rules/mui-patterns.md, @.claude/rules/api-tests.md

---

## Quick Start

```bash
cd automation

# Smoke tests (<5 min)
HEADLESS=true pytest -m smoke -v

# Headed debugging
HEADLESS=false pytest tests/ui/chat/test_chat_interface.py -v
```

---

## Critical Non-Obvious Patterns

### Authentication (Keycloak, NOT Clerk)
- Login field: `input[name="username"]` — NOT `input[name="email"]`
- API clients use **cookie-based auth** extracted from browser state
- The `APIClient` (generic) uses Bearer tokens; entity-specific clients (`ConversationAPI`, `AgentAPI`) use cookies

### Entity Naming (UI → API)
| UI Term | API Entity | Path |
|---------|-----------|------|
| Agent | `application` | `/applications/` |
| Toolkit | `tool` | `/tools/` |
| Credential | `configuration` | `/configurations/` |

### API Quirks
- **Content-Type rule**: GET/DELETE requests must NOT have `Content-Type: application/json` header (causes 400)
- **Singular vs plural**: List/create use plural (`/conversations/`), get/update/delete use singular (`/conversation/{id}`)
- Exception: Conversation delete uses plural path

### Fixture Scoping
| Fixture | Scope | Reason |
|---------|-------|--------|
| `credential_api`, `toolkit_api` | **function** | Avoids connection pool exhaustion |
| `conversation_api`, `agent_api` | session | Shared across tests |

**Fixture location rule:** All fixtures must live in `automation/fixtures/` and be
registered in `conftest.py`. Never define fixtures inside test files.
See `.claude/rules/api-patterns.md` → Anti-Patterns for the full rule.

---

## Test Organization

Tests are in `tests/ui/{domain}/`:
- `tests/ui/agents/` — Agent CRUD, toolkit integration
- `tests/ui/chat/` — Chat interface, conversations
- `tests/ui/pipelines/` — Pipeline management
- `tests/ui/toolkits/` — Toolkit parameterized tests
- `tests/ui/smoke/` — Critical path smoke tests

---

## Common Gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| `fill()` doesn't update React state | MUI needs keyboard events | Use `click()` + `type()` or `press_sequentially()` |
| Click intercepted by overlay | MUI invisible overlay div | Use `force=True` or `evaluate("el => el.click()")` |
| Banner covers elements | z-index 1200 overlay | Call `dismiss_banner_if_present()` first |
| Message count wrong | Using `div:has(> p)` | Use `ul.MuiList-root > li.MuiListItem-root` |
| AI response takes time | WebSocket streaming | Use `wait_for_ai_response()` with appropriate timeout |

---

## Environment Variables

Required in `.env.test`:
```
ELITEA_URL=https://stage.elitea.ai
ELITEA_API_BASE=https://stage.elitea.ai/api/v2
ELITEA_PROJECT_ID=23
TEST_USER_EMAIL=<keycloak username>
TEST_USER_PASSWORD=<keycloak password>
```

Toolkit tokens (tests auto-skip if missing):
```
GITHUB_TOKEN=ghp_...
JIRA_API_KEY=...  JIRA_BASE_URL=...  JIRA_USERNAME=...
```

---

## Test Reporting

### Automatic Reports (Generated on Every Run)

| Report Type | Location | When Generated | Contains |
|------------|----------|----------------|----------|
| **JUnit XML** | `reports/junit.xml` | Always (all environments) | CI/CD compatible test results |
| **HTML Report** | `reports/report.html` | Command line only (not VS Code) | Full logs, durations, environment info |
| **Historical Archive** | `reports/archive/` | Command line only | Timestamped copies of HTML + XML |

**Note:** HTML reports are auto-disabled when running tests from VS Code Test Explorer (which doesn't support the pytest-html plugin). JUnit XML is always generated.

### Screenshots

**Captured only on test failures** (mirrors JUnit's TestWatcher pattern):
- ✅ Test fails → Screenshot saved to `screenshots/{test_name}_FAIL_{timestamp}.png`
- ❌ Test passes → No screenshot (reduces noise and storage)

Screenshots are automatically:
- Saved locally for debugging
- Included in HTML report

### Viewing Reports

```bash
# Latest reports (always overwritten)
start reports/report.html
start reports/junit.xml

# Historical reports (timestamped)
ls reports/archive/
start reports/archive/report_20260408_153339.html
```

### Cleanup Old Reports

```bash
# Delete archive reports older than 30 days
cd reports/archive
find . -name "*.html" -mtime +30 -delete
find . -name "*.xml" -mtime +30 -delete
```

---

## Markers

```bash
pytest -m smoke -v        # Critical paths (<5 min)
pytest -m p0 -v           # Must pass for deploy
pytest -m "p0 or p1" -v   # High priority
pytest -m agents -v       # Agent tests only
```
