---
description: API client patterns and common pitfalls for Elitea API
paths:
  - automation/tests/**/*.py
  - automation/conftest.py
---

# API Patterns

## CRITICAL: Content-Type Header Rule

**NEVER send `Content-Type: application/json` on GET or DELETE requests.**

The Elitea API returns 400 if Content-Type is set on bodiless requests.

```python
# ❌ WRONG - Causes 400 error
headers = {"Authorization": "Bearer token", "Content-Type": "application/json"}
response = requests.get(url, headers=headers)  # 400 Bad Request

# ✅ CORRECT - Only send Content-Type on requests with body
def _headers_for_method(self, method: str) -> dict:
    headers = dict(self._auth_header)
    if method.upper() in ("POST", "PUT", "PATCH"):
        headers["Content-Type"] = "application/json"
    return headers
```

**Rule:** Only POST, PUT, and PATCH should include Content-Type header.

---

## Singular vs Plural Path Pattern

The Elitea API uses **plural** paths for list/create and **singular** for get/update.

```python
# ✅ CORRECT pattern
# List/Create → PLURAL
GET  /elitea_core/conversations/prompt_lib/{project_id}
POST /elitea_core/conversations/prompt_lib/{project_id}

# Get/Update → SINGULAR
GET /elitea_core/conversation/prompt_lib/{project_id}/{id}
PUT /elitea_core/conversation/prompt_lib/{project_id}/{id}

# Delete → Usually SINGULAR (check docs for exceptions)
DELETE /elitea_core/agent/prompt_lib/{project_id}/{id}  # Singular for agents

# Exception: Conversations use PLURAL for delete
DELETE /elitea_core/conversations/prompt_lib/{project_id}/{id}  # Plural!
```

**Rule:** When adding new API endpoints:
1. List/Create → use plural entity name
2. Get/Update/Delete → use singular entity name (check for exceptions)
3. Test both paths if unsure

**Common mistake:** Using `/conversations/{id}` for GET → returns 404. Must use `/conversation/{id}`.

---

## Authentication Strategy

Choose the right authentication method based on endpoint requirements.

```python
# ✅ Cookie-based auth (for UI-related APIs)
conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
agent_api = AgentAPI(browser_cookies=_browser_cookies)
credential_api = CredentialAPI(browser_cookies=_browser_cookies)
toolkit_api = ToolkitAPI(browser_cookies=_browser_cookies)

# ✅ Bearer token auth (for pure API endpoints)
api_client = APIClient()  # Uses ELITEA_API_TOKEN from .env
```

**Why two methods?**
- Some endpoints require Keycloak session cookies
- Some endpoints accept Bearer tokens
- Use cookie-based clients for APIs that power the UI

**Getting cookies:**
```python
# In conftest.py - extract once per session
@pytest.fixture(scope="session")
def _browser_cookies(browser, auth_state):
    ctx = browser.new_context(storage_state=auth_state)
    pg = ctx.new_page()
    pg.goto("/")
    cookies = ctx.cookies()
    return cookies
```

---

## API Fixture Scoping

Use the right scope to avoid connection pool exhaustion.

```python
# ✅ Session scope - for read-heavy or light create/delete
@pytest.fixture(scope="session")
def conversation_api(_browser_cookies):
    api = ConversationAPI(browser_cookies=_browser_cookies)
    yield api
    api.close()

# ✅ Function scope - for tests creating many entities
@pytest.fixture(scope="function")  # Fresh session per test
def credential_api(_browser_cookies):
    api = CredentialAPI(browser_cookies=_browser_cookies)
    yield api
    api.close()
```

**When to use function scope:**
- Test creates/deletes many entities (>5 per test)
- Previous tests caused "Connection pool exhausted" errors
- Entities are short-lived (credentials, toolkits)

**When to use session scope:**
- Mostly read operations
- Few creates/deletes per test
- Long-lived entities (agents, conversations)

---

## Error Handling Pattern

Always check response status before accessing data.

```python
# ❌ WRONG - No error checking
response = api.create_agent(payload)
agent_id = response["id"]  # KeyError if request failed

# ✅ CORRECT - Check status first
response = api.create_agent(payload)
if response.status_code != 200:
    raise Exception(f"Create failed: {response.status_code} {response.text}")
data = response.json()
agent_id = data["id"]

# ✅ BETTER - Let API client handle errors
class AgentAPI:
    def create_agent(self, payload):
        response = self._post(f"/applications/prompt_lib/{self.project_id}", payload)
        response.raise_for_status()  # Raises on 4xx/5xx
        return response.json()
```

**Rule:** API client methods should call `response.raise_for_status()` before returning data.

---

## Payload Validation

Validate required fields before sending requests.

```python
# ✅ CORRECT - Validate in API client method
def create_agent(self, name: str, description: str, instructions: str = ""):
    if not name:
        raise ValueError("Agent name is required")
    if not description:
        raise ValueError("Agent description is required")
    
    payload = {
        "name": name,
        "description": description,
        "type": "interface",
        "versions": [{
            "name": "base",
            "instructions": instructions or "You are a helpful assistant.",
            # ... rest of version config
        }]
    }
    response = self._post(f"/applications/prompt_lib/{self.project_id}", payload)
    response.raise_for_status()
    return response.json()
```

**Benefits:**
- Clearer error messages at test level
- Prevents unnecessary API calls
- Documents required fields

---

## Entity Mapping (UI → API)

The UI and API use different names for some entities.

| UI Term | API Entity | Endpoint Path |
|---------|-----------|---------------|
| Agent | `application` | `/applications/` |
| Toolkit | `tool` | `/tools/` |
| Credential | `configuration` | `/configurations/` |
| Conversation | `conversation` | `/conversations/` |

```python
# ✅ CORRECT - Use API entity name in code
def create_agent(self, name: str):  # UI calls it "agent"
    # But API calls it "application"
    response = self._post("/applications/prompt_lib/...", payload)
    
# Variable names can use UI terms for clarity
agent = agent_api.create_agent("Test")
agent_id = agent["id"]  # "agent" is clear in test context
```

**Rule:** API paths and payload keys use API entity names. Variable names in tests can use UI terms.

---

## Anti-Patterns

❌ **Don't define fixtures inside test files:**

```python
# ❌ WRONG — fixture in test file, invisible to other modules
# tests/ui/chat/test_agent_chat.py
@pytest.fixture
def github_toolkit(toolkit_api):
    toolkit = toolkit_api.create_github_toolkit(...)
    yield {"id": toolkit["id"], "name": name}
    toolkit_api.delete_toolkit(toolkit["id"])
```

```python
# ✅ CORRECT — fixture in fixtures/data_fixtures.py
@pytest.fixture
def github_toolkit(github_credential, toolkit_api, request):
    name = f"autotest_gh_toolkit_{request.node.name}"[:50]
    toolkit = toolkit_api.create_github_toolkit(name=name, ...)
    yield {"id": toolkit["id"], "name": name, "branch": _GITHUB_BRANCH}
    toolkit_api.delete_toolkit(toolkit["id"])

# conftest.py — register so pytest discovers it everywhere
from fixtures.data_fixtures import github_toolkit
```

**Why:** Fixtures in test files cannot be shared across modules and give the
test file two responsibilities (test logic + infrastructure setup). All
fixtures belong in `automation/fixtures/` and must be registered in
`conftest.py`. See `fixtures/__init__.py` for the full module guide.

---

❌ **Don't retry API calls without backoff:**
```python
# BAD - hammers the API
for _ in range(10):
    response = api.create_agent(...)
    if response.status_code == 200:
        break
```

✅ **Use exponential backoff or fix the root cause:**
```python
# BETTER - but question if retries are needed
import time
for attempt in range(3):
    response = api.create_agent(...)
    if response.status_code == 200:
        break
    time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

❌ **Don't mix auth methods in same client:**
```python
# BAD - confusing
class AgentAPI:
    def __init__(self, bearer_token, cookies):
        self._token = bearer_token
        self._cookies = cookies  # Which one to use?
```

✅ **One auth method per client:**
```python
# GOOD - clear strategy
class AgentAPI:
    def __init__(self, browser_cookies):
        self._cookies = browser_cookies  # Only cookies
```

❌ **Don't hardcode project ID:**
```python
# BAD
response = requests.get("/agents/prompt_lib/23/1234")
```

✅ **Use from environment:**
```python
# GOOD
self.project_id = os.getenv("ELITEA_PROJECT_ID")
response = requests.get(f"/agents/prompt_lib/{self.project_id}/1234")
```

---

## Testing API Clients

When writing tests for API client methods:

```python
# ✅ Test happy path
def test_create_agent_success(agent_api):
    agent = agent_api.create_agent("Test", "Description")
    assert agent["id"] is not None
    assert agent["name"] == "Test"

# ✅ Test error handling
def test_create_agent_missing_name(agent_api):
    with pytest.raises(ValueError, match="name is required"):
        agent_api.create_agent("", "Description")

# ✅ Clean up test data
def test_create_and_delete(agent_api):
    agent = agent_api.create_agent("Test", "Description")
    agent_id = agent["id"]
    
    agent_api.delete_agent(agent_id)
    
    # Verify deletion
    agents = agent_api.list_agents()
    ids = [a["id"] for a in agents.get("rows", [])]
    assert agent_id not in ids
```

---

## References

- API Client Implementation: `automation/api/client.py`
- Fixture Examples: `automation/conftest.py`
- Critical Patterns: `automation/CLAUDE.md` - API Quirks section
