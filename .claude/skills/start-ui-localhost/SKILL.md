---
name: start-ui-localhost
description: Starts EliteaUI dev server on localhost:5173 if not already running. Use before Stage 2.5 (add-data-testid) to ensure UI changes are visible for testing.
argument-hint: [optional: port to check, default 5173]
allowed-tools:
  - Bash
  - Read
---

# Start UI Localhost Skill

Ensures EliteaUI dev server is running on localhost:5173 for local testing of UI changes.

## When to Use

Call this skill **before Stage 2.5** (add-data-testid) when:
- You need to test UI changes locally
- Adding data-testid attributes and want to verify them in browser
- Running tests against localhost instead of dev.elitea.ai

## Process

### Step 1: Check if Already Running

```bash
# Check if port 5173 is in use
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 2>/dev/null || echo "not running"
```

If returns 200 or 30x → server is running, skip to Step 4.

### Step 2: Verify EliteaUI Setup

```bash
# Check .env exists
if [ -f "../EliteaUI/.env" ]; then
    echo ".env exists"
else
    echo "ERROR: .env not found. Copy from .env.example and configure."
    exit 1
fi

# Always run npm install to ensure dependencies are up-to-date
# (npm install is fast if nothing changed, handles new deps if package.json updated)
cd ../EliteaUI && npm install
```

### Step 3: Start Dev Server

```bash
# Start in background
cd ../EliteaUI && npm run dev &

# Wait for server to be ready (max 30 seconds)
for i in {1..30}; do
    if curl -s -o /dev/null http://localhost:5173 2>/dev/null; then
        echo "Server ready on http://localhost:5173"
        break
    fi
    sleep 1
done
```

### Step 4: Report Status

**If running:**
> UI localhost is running at http://localhost:5173
> Ready for Stage 2.5 (add-data-testid)

**If failed to start:**
> ERROR: Could not start UI localhost
> Check: .env configuration, node_modules, port availability

---

## Prerequisites

1. **EliteaUI repo** at `../EliteaUI/` (relative to elitea-testing)
2. **.env file** configured with:
   ```
   VITE_SERVER_URL=/api/v2/
   VITE_DEV_SERVER=https://dev.elitea.ai
   VITE_DEV_TOKEN=<your-token>
   VITE_SOCKET_SERVER=https://dev.elitea.ai
   ```
3. **Node.js** installed

## Notes

- Server runs with Hot Module Replacement (HMR) — UI changes apply automatically
- After adding data-testid in EliteaUI, just refresh browser or call `page.reload()` in tests
- To stop: `pkill -f "vite"` or close the terminal

## Integration with ui-test-orchestrator

This skill should be called at the **beginning of Stage 2.5** if testing locally:

```
# In Stage 2.5, before add-data-testid
Skill(skill="start-ui-localhost")
Skill(skill="add-data-testid", args="[elements list]")
```
