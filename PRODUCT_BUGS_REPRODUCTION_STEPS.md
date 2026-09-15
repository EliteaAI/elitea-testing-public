# Product Bugs Detected in Stage2 Investigation

**Date:** 2026-09-11  
**Environment:** stage2.elitea.ai  
**Source:** GHA Run #34597349245 analysis

---

## Bug #1: Agent Icon Selection Does Not Persist

**Severity:** Medium  
**Test:** `test_agent_icon_change_persists_on_list_card`  
**Test File:** `automation/tests/ui/agents/test_agent_icon_management.py`  
**TMS Case:** ELITEA-1899

### 🐛 Description

When a user changes an agent's icon in the icon picker, the icon:
- ✅ **Updates immediately** in the agent header (no reload needed)
- ✅ **Triggers PUT request** to `upload_icon` endpoint (returns 200)
- ❌ **Does NOT persist** on the agents list card when navigating back to dashboard

The icon change appears to save (200 response) but the card still shows the old/default icon.

### 📋 Steps to Reproduce

**Prerequisites:**
- Access to https://stage2.elitea.ai
- Logged in as test user
- At least one agent exists in your project

**Steps:**

1. **Navigate to Agents dashboard**
   - Go to https://stage2.elitea.ai/app/agents/all
   - Verify at least one agent card is visible

2. **Open an agent detail page**
   - Click on any agent card
   - Agent detail page loads

3. **Open the icon picker**
   - Hover over the agent icon in the header (top-left circle)
   - A pencil/edit overlay appears
   - Click the icon
   - Icon picker dialog opens

4. **Select a different icon**
   - Click on any icon in the picker (e.g., 4th option)
   - Observe: Header icon updates immediately
   - Network tab shows: `PUT .../upload_icon/.../` returns 200 OK

5. **Navigate back to Agents dashboard**
   - Click the browser back button OR navigate to `/app/agents/all`
   - Agents list loads

6. **Check the agent card icon**
   - ❌ **BUG:** Card still shows the OLD icon (not the one selected in step 4)
   - Expected: Card should show the NEW icon

### 🔍 Technical Details

**API Call:**
- **Endpoint:** `PUT /elitea_core/upload_icon/.../prompt_lib/{versionId}`
- **Status:** 200 OK (success)
- **Problem:** Response is successful but data doesn't persist

**UI Behavior:**
- Detail page header icon updates immediately (client-side only?)
- List card icon does NOT update
- Main Save button stays disabled (icon change is independent of form state)

**Note from test:**
> "The icon change persists immediately and independently via its own PUT 
> .../upload_icon/.../{versionId} call, decoupled from the agent form's 
> Save/Discard state"

This suggests the icon should persist without clicking main Save button.

### 📊 Impact

- **User Experience:** Confusing - users see the icon change in detail but not in list
- **Data Integrity:** Icon selection is lost
- **Workaround:** Unknown (main Save button is disabled for icon-only changes)

### 🧪 Test Evidence

**Test assertion that fails:**
```python
card_src = list_page.get_card_icon_src(agent_name)
assert card_src == new_src, (
    "Agent card icon src should exactly match the header icon "
    f"src set in Step 3/4 — expected {new_src!r}, got {card_src!r}"
)
```

**Expected:** Card icon URL matches header icon URL  
**Actual:** Card icon URL is different (old icon)

---

## Bug #2: Agent Detail Back Button Navigation Timeout

**Severity:** High (P0 - critical path)  
**Test:** `test_back_button_from_agent_detail_returns_to_intact_agents_list`  
**Test File:** `automation/tests/ui/agents/test_agent_back_navigation.py`  
**TMS Case:** ELITEA-1869

### 🐛 Description

Clicking the Back button on an agent detail page times out after 10-15 seconds instead of navigating back to the Agents dashboard. The navigation either:
- Doesn't trigger at all, OR
- Takes longer than 15 seconds to complete

### 📋 Steps to Reproduce

**Prerequisites:**
- Access to https://stage2.elitea.ai
- Logged in as test user
- At least one agent exists

**Steps:**

1. **Navigate to Agents dashboard**
   - Go to https://stage2.elitea.ai/app/agents/all?viewMode=owner
   - Note the list of agents displayed

2. **Open an agent detail page**
   - Click on any agent card
   - Agent detail page loads (URL: `/app/agents/all/{agentId}`)

3. **Click the Back button**
   - Locate the Back button in the agent detail header (top-left)
   - Click it
   - ❌ **BUG:** Navigation times out after 10-15 seconds
   - Expected: Should navigate to `/app/agents/all?viewMode=owner` within 2-3 seconds

### 🔍 Technical Details

**Expected Navigation:**
- **From:** `/app/agents/all/{agentId}` (agent detail)
- **To:** `/app/agents/all?viewMode=owner` (agents list)
- **Expected Time:** < 3 seconds
- **Actual Time:** > 15 seconds (timeout)

**Expected API Call:**
```
GET /elitea_core/applications/prompt_lib/{projectId}?agents_type=classic
```

**Possible Root Causes:**

1. **Missing testid on back button**
   - Button not properly identified by automation
   - Unlikely (test worked on dev environment)

2. **Element not clickable**
   - MUI overlay intercepting click
   - Button disabled/loading state

3. **Navigation not triggered**
   - Click handler not firing
   - JavaScript error preventing navigation
   - Backend latency on stage2

4. **Stage2 backend latency**
   - API call takes > 15s to respond
   - Network issues between stage2 components

### 🧪 Test Evidence

**Test code:**
```python
with page.expect_response(
    lambda r: "applications/prompt_lib/" in r.url and "agents_type=classic" in r.url
):
    agent.click_back_button(timeout=NAVIGATION_TIMEOUT)  # 15000ms

# Times out here - navigation never completes
```

**Timeout:** 15000ms (15 seconds)  
**Marker:** `@pytest.mark.p0` (critical priority)

### 📊 Impact

- **User Experience:** Users stuck on detail page, can't navigate back
- **Critical Path:** P0 test - blocks deployment
- **Workaround:** Browser back button or manual URL navigation

### 🔬 Investigation Needed

1. **Check back button implementation**
   - Verify click handler is attached
   - Check for JavaScript errors in console
   - Verify button is not disabled

2. **Check API response time**
   - Monitor `/applications/prompt_lib/` endpoint
   - Check if it takes > 15s on stage2
   - Compare with dev environment (<3s)

3. **Check network conditions**
   - Stage2 backend connectivity
   - Database query performance

---

## Summary Table

| Bug | Severity | Component | Impact | Status |
|-----|----------|-----------|--------|--------|
| **Icon doesn't persist** | Medium | UI/Backend | Data loss | Needs investigation |
| **Back button timeout** | High (P0) | UI/Backend | Navigation blocked | Needs investigation |

---

## Environment Comparison

| Aspect | DEV | STAGE2 |
|--------|-----|--------|
| Icon persistence | ✅ Works | ❌ Broken |
| Back button | ✅ < 3s | ❌ Timeout (>15s) |
| Backend latency | Fast | Slow |

**Note:** Both bugs may be related to stage2 backend performance/configuration rather than code defects.

---

## Next Steps

### For Icon Bug (#1)
1. Check database to verify icon was NOT saved
2. Review `upload_icon` endpoint logs on stage2
3. Check if 200 response is false positive
4. Compare with working dev environment

### For Back Button Bug (#2)
1. Measure actual API response time on stage2
2. Check `/applications/prompt_lib/` endpoint performance
3. Add backend logging to identify bottleneck
4. Consider increasing timeout (if backend issue) or fix backend (if code issue)

### File Bug Tickets

If confirmed as product bugs (not environment issues):

```bash
# Icon bug
gh issue create --repo EliteaAI/elitea_issues \
  --title "[STAGE2] Agent icon selection does not persist on list card" \
  --body "$(cat bug_1_description.md)"

# Back button bug
gh issue create --repo EliteaAI/elitea_issues \
  --title "[STAGE2][P0] Agent detail back button navigation times out" \
  --body "$(cat bug_2_description.md)"
```

---

**Report Created:** 2026-09-11  
**Created By:** Test Automation Investigation  
**Source:** Stage2 GHA failure analysis
