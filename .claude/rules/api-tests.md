---
description: API test guidelines for REST endpoints using pytest
paths:
  - automation/tests/api/**/*.py
  - automation/api/**/*.py
---

# API Test Guidelines

## Response Verification Requirements

**Every API test MUST verify both status and response body:**

```python
# ❌ WRONG - Only checks status code
def test_create_agent_api(agent_api):
    response = agent_api.create_agent("Test Agent", "Test Description")
    assert response.status_code == 200

# ✅ CORRECT - Verifies status AND response body
def test_create_agent_api(agent_api):
    name = "Test Agent"
    description = "Test Description"
    
    response = agent_api.create_agent(name, description)
    
    # Status verification
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Response body verification
    data = response.json()
    assert data["id"] is not None, "Agent should have an ID"
    assert data["name"] == name, f"Expected name '{name}', got '{data['name']}'"
    assert data["description"] == description
    assert data["type"] == "interface", "Default type should be 'interface'"
```

**Why:** API could return 200 with empty body, wrong data, or malformed JSON. Test would still pass but miss critical bugs.

## Required Test Coverage

**Every API endpoint needs these test types:**

### 1. Happy Path Test
```python
@pytest.mark.p0
@pytest.mark.api
def test_create_agent_success(agent_api):
    """Create agent with valid data returns 200 and correct response."""
    response = agent_api.create_agent("Valid Name", "Valid Description")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Valid Name"
```

### 2. Invalid Input Test
```python
@pytest.mark.p1
@pytest.mark.api
def test_create_agent_empty_name(agent_api):
    """Create agent with empty name returns 400."""
    response = agent_api.create_agent("", "Valid Description")
    
    assert response.status_code == 400, "Empty name should fail validation"
    error = response.json()
    assert "name" in error.get("message", "").lower()
```

### 3. Boundary Test
```python
@pytest.mark.p2
@pytest.mark.api
def test_create_agent_max_length_name(agent_api):
    """Create agent with 256-char name succeeds."""
    long_name = "A" * 256
    response = agent_api.create_agent(long_name, "Description")
    
    assert response.status_code == 200
    assert response.json()["name"] == long_name

@pytest.mark.p2
@pytest.mark.api
def test_create_agent_too_long_name(agent_api):
    """Create agent with 257-char name returns 400."""
    too_long = "A" * 257
    response = agent_api.create_agent(too_long, "Description")
    
    assert response.status_code == 400
```

### 4. Not Found Test (for GET/DELETE/UPDATE)
```python
@pytest.mark.p1
@pytest.mark.api
def test_get_nonexistent_agent(agent_api):
    """Get agent with invalid ID returns 404."""
    response = agent_api.get_agent(agent_id=999999)
    
    assert response.status_code == 404
    error = response.json()
    assert "not found" in error.get("message", "").lower()
```

## Error Response Verification

**Always verify error response structure:**

```python
def test_invalid_request(agent_api):
    response = agent_api.create_agent("", "")  # Invalid
    
    # Status check
    assert response.status_code == 400
    
    # Error structure check
    error = response.json()
    assert "message" in error, "Error response should have 'message' field"
    assert error["message"], "Error message should not be empty"
    
    # Optional: Check error details if API provides them
    if "errors" in error:
        assert len(error["errors"]) > 0, "Should list validation errors"
```

## Test Data Lifecycle

**Always clean up test data, even on failure:**

```python
# ✅ CORRECT - Fixture with cleanup (preferred)
@pytest.fixture
def agent_id(agent_api):
    """Create agent for testing, delete after test."""
    agent = agent_api.create_agent("Test Agent", "Test Description")
    agent_id = agent["id"]
    
    yield agent_id
    
    # Cleanup - runs even if test fails
    try:
        agent_api.delete_agent(agent_id)
    except Exception as e:
        print(f"Warning: Failed to cleanup agent {agent_id}: {e}")

# ✅ CORRECT - Manual cleanup with try/finally
def test_something(agent_api):
    agent_id = None
    try:
        agent = agent_api.create_agent("Test", "Description")
        agent_id = agent["id"]
        
        # Test logic here
        response = agent_api.update_agent(agent_id, name="Updated")
        assert response.status_code == 200
        
    finally:
        if agent_id:
            try:
                agent_api.delete_agent(agent_id)
            except Exception:
                pass  # Already deleted or other error
```

## Assertion Quality Standards

### ❌ Forbidden Patterns

**1. Status-only checks (incomplete verification):**
```python
# ❌ WRONG
assert response.status_code == 200

# ✅ CORRECT
assert response.status_code == 200
data = response.json()
assert data["id"] is not None
```

**2. Overly broad assertions:**
```python
# ❌ WRONG - Any status is acceptable?
assert response.status_code in [200, 201, 400, 404, 500]

# ✅ CORRECT - Specific expected status
assert response.status_code == 200
```

**3. Trivial assertions:**
```python
# ❌ WRONG - Always passes
assert True
assert 1 == 1

# ✅ CORRECT - Meaningful check
assert response.json()["status"] == "active"
```

**4. Assertions with side effects:**
```python
# ❌ WRONG - Assertion performs action
assert agent_api.delete_agent(agent_id)

# ✅ CORRECT - Separate action from assertion
deleted = agent_api.delete_agent(agent_id)
assert deleted is True
```

**5. Wrong variable assertions:**
```python
# ❌ WRONG - Checking wrong variable
response = agent_api.create_agent("Test", "Desc")
assert status == 200  # 'status' is undefined or from previous test!

# ✅ CORRECT
assert response.status_code == 200
```

## Test Structure

**Use descriptive names and docstrings:**

```python
@pytest.mark.p0
@pytest.mark.api
@pytest.mark.agents
def test_create_agent_returns_correct_fields(agent_api):
    """Create agent returns all expected fields with correct types.
    
    Verifies:
    - Status code is 200
    - Response has id (int), name (str), description (str), type (str)
    - Name and description match input
    - Default type is 'interface'
    """
    # Given
    name = "Test Agent"
    description = "Test Description"
    
    # When
    response = agent_api.create_agent(name, description)
    
    # Then
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data["id"], int)
    assert data["name"] == name
    assert data["description"] == description
    assert data["type"] == "interface"
```

## Parametrized Tests for Boundary Cases

**Use pytest.mark.parametrize for multiple similar tests:**

```python
@pytest.mark.p2
@pytest.mark.api
@pytest.mark.parametrize("name,expected_status", [
    ("", 400),                    # Empty name
    ("A", 200),                   # Min valid length
    ("A" * 256, 200),             # Max valid length
    ("A" * 257, 400),             # Over max length
    ("Valid Name", 200),          # Normal case
    ("Name\nWith\nNewlines", 400),  # Invalid characters
])
def test_create_agent_name_validation(agent_api, name, expected_status):
    """Test agent name validation with various inputs."""
    response = agent_api.create_agent(name, "Description")
    assert response.status_code == expected_status, (
        f"Name='{name}' should return {expected_status}, got {response.status_code}"
    )
```

## Error Handling

**Don't catch exceptions unless testing error handling:**

```python
# ❌ WRONG - Hides real errors
def test_something(agent_api):
    try:
        response = agent_api.create_agent("Test", "Desc")
        assert response.status_code == 200
    except Exception:
        pass  # Silently fails!

# ❌ WRONG - Catches too much
def test_something(agent_api):
    try:
        response = agent_api.create_agent("Test", "Desc")
    except Exception as e:
        assert "error" in str(e)  # What kind of error?

# ✅ CORRECT - Let pytest handle failures
def test_something(agent_api):
    response = agent_api.create_agent("Test", "Desc")
    assert response.status_code == 200

# ✅ CORRECT - Test specific error
def test_connection_error(agent_api, monkeypatch):
    """Test API handles connection errors gracefully."""
    def mock_request(*args, **kwargs):
        raise requests.ConnectionError("Network unreachable")
    
    monkeypatch.setattr(requests, "post", mock_request)
    
    with pytest.raises(requests.ConnectionError):
        agent_api.create_agent("Test", "Desc")
```

## Authentication Tests

**Test auth separately from business logic:**

```python
@pytest.mark.p0
@pytest.mark.api
@pytest.mark.auth
def test_api_requires_authentication(agent_api):
    """Requests without auth token return 401."""
    # Create client without auth
    unauth_api = AgentAPI(base_url=agent_api.base_url, token=None)
    
    response = unauth_api.create_agent("Test", "Desc")
    assert response.status_code == 401

@pytest.mark.p0
@pytest.mark.api
@pytest.mark.auth
def test_api_rejects_invalid_token(agent_api):
    """Requests with invalid token return 401."""
    invalid_api = AgentAPI(base_url=agent_api.base_url, token="invalid_token")
    
    response = invalid_api.create_agent("Test", "Desc")
    assert response.status_code == 401
```

## Performance Considerations

**Set reasonable timeouts:**

```python
# At top of test file
API_TIMEOUT = 30  # seconds
LONG_OPERATION_TIMEOUT = 60  # For batch operations

def test_create_agent(agent_api):
    response = agent_api.create_agent("Test", "Desc", timeout=API_TIMEOUT)
    assert response.status_code == 200
```

## Markers

**Use appropriate pytest markers:**

```python
@pytest.mark.api           # API test (vs UI test)
@pytest.mark.agents        # Feature area
@pytest.mark.p0            # Critical priority
@pytest.mark.smoke         # Fast smoke test

def test_something(agent_api):
    pass
```

## Common Anti-Patterns

❌ **Don't test implementation details:**
```python
# ❌ WRONG
assert response.headers["X-Internal-Version"] == "2.0"

# ✅ CORRECT - Test public API contract
assert response.json()["version"] == "2.0"
```

❌ **Don't rely on test execution order:**
```python
# ❌ WRONG
def test_1_create():
    global agent_id
    agent_id = create_agent()

def test_2_update():
    update_agent(agent_id)  # Depends on test_1_create

# ✅ CORRECT - Use fixtures
@pytest.fixture
def agent_id(agent_api):
    agent = agent_api.create_agent("Test", "Desc")
    yield agent["id"]
    agent_api.delete_agent(agent["id"])
```

❌ **Don't hard-code test data that conflicts:**
```python
# ❌ WRONG - Tests will conflict if run in parallel
def test_create():
    agent_api.create_agent("my_unique_agent", "Desc")

# ✅ CORRECT - Use unique identifiers
def test_create():
    name = f"test_agent_{uuid.uuid4().hex[:8]}"
    agent_api.create_agent(name, "Desc")
```

## Automated Quality Checks

These standards are enforced by the `test-quality-checker` skill.
Run it before submitting PRs:

```bash
# Check test quality
claude test-quality-checker automation/tests/api/test_api_health.py
```

See `.claude/skills/test-quality-checker/SKILL.md` for detection details.

## References

- API client: `automation/api/`
- Test examples: `automation/tests/api/test_api_health.py`
- Fixtures: `automation/conftest.py`
