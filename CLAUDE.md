# elitea-testing — Elitea AI Platform Automation

Test automation suite for [Elitea](https://stage.elitea.ai), an AI collaboration platform.

## Quick Start

```bash
source ~/Development/venv/bin/activate
cd ~/Development/elitea-testing/automation

# Smoke tests (<5 min, critical paths)
HEADLESS=true pytest -m smoke -v
```

## Project Structure

```
automation/
├── conftest.py              # Fixtures, Keycloak auth, screenshots
├── pytest.ini               # Markers, pytest config
├── .env.test                # URLs, credentials, project ID
├── api/                     # REST API client
├── pages/                   # Page Object Model (ChatPage, etc.)
├── components/              # UI helpers
└── test_*.py                # Test files
```

## Target System

- **URL**: https://stage.elitea.ai
- **Auth**: Keycloak (username/password, NOT Clerk)
- **Login field**: `input[name="username"]` (NOT `input[name="email"]`)

## Application Structure

Sidebar navigation:
- Chat — AI conversations with model selection
- Agents — Configurable AI assistants
- Pipelines — Multi-step AI workflows
- Credentials — Auth management
- Toolkits — Integrations (Jira, GitHub, etc.)
- Apps — Published applications
- MCPs — Model Context Protocol servers
- Artifacts — File storage & RAG
- Agents Studio — Agent builder
- Settings — Configuration

## ChatPage Object

```python
from pages.chat_page import ChatPage

chat = ChatPage(page)
chat.navigate_to_chat()
chat.wait_for_page_load()
chat.send_message("Hello", use_enter=True)
chat.wait_for_response()  # ~2s WebSocket delay
count = chat.get_message_count()
```

## Running Tests

```bash
# All tests
HEADLESS=true pytest -v

# Chat tests only
pytest test_chat_interface.py -v

# Headed (debug)
HEADLESS=false pytest test_chat_interface.py -v

# API health
pytest test_api_health.py -v
```

## Gotchas

1. Keycloak login: `input[name="username"]`, NOT email
2. WebSocket delay: AI responses take ~2 seconds
3. Message locators: `main span:has-text("EliteA Yoko")` for message blocks
4. Model selector: Button text changes with selected model

## Python Environment

- **Shared venv**: `~/Development/venv` (Python 3.12)
- **Key packages**: pytest==9.0.2, playwright==1.58.0
