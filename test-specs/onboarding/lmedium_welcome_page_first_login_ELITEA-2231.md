# ELITEA-2231: Onboarding — Welcome Page First Login

**TMS ID:** ELITEA-2231  
**Priority:** medium  
**Status:** `blocked`  
**Type:** UI  
**Feature:** onboarding

---

## Summary

Verify that the "Welcome to Elitea!" onboarding page displays correctly on a user's **first login**, showing the welcome card with "Sure, let's go!" button and confirming that project provisioning has NOT started yet (i.e., the personal/private project creation does not begin until the button is clicked).

---

## Preconditions

- User account exists in Keycloak
- **CRITICAL**: User has **never logged in before** — `user.personal_project_id` must be `null`
- User authenticates successfully
- Application is accessible at base URL

---

## Blocked Steps

**This test is BLOCKED and cannot be executed with the current test infrastructure.**

### Blocking Issue

The Welcome screen is conditionally rendered based on the user NOT having a `personal_project_id`:

```javascript
// From src/pages/Onboarding/Onboarding.jsx:158-163
{!showTour && !user.personal_project_id && user.id && (
  <Welcome name={user.name || user.email} onShowTour={handleShowTour} />
)}
```

**The existing test user (`TEST_USER_EMAIL`) likely already has a `personal_project_id`** from previous test runs, which means:
- The Welcome screen will NOT be displayed for this user
- The user will be redirected directly to the application OR shown the onboarding tour
- The test cannot verify the "project provisioning has not started yet" condition

### What's Needed to Unblock

One of the following approaches is required:

1. **New User Provisioning** (recommended)
   - Automated Keycloak API integration to create fresh test users
   - User cleanup after test completion
   - Fixture: `new_user` that provides credentials for a never-logged-in account

2. **Backend Test Reset Capability**
   - API endpoint to delete/nullify a user's `personal_project_id`
   - Allows reusing the same test user account
   - Requires backend support

3. **Frontend Mocking**
   - Override user state in the Redux store to simulate `personal_project_id: null`
   - Requires test-mode flag or special build
   - Less authentic but fastest to implement

4. **Database Snapshot/Restore**
   - Restore database to pristine state before each run
   - Requires CI/test infrastructure changes
   - Most authentic but highest overhead

---

## Coverage Map

### Axis 1 — TMS Case Elements

| # | Case Element | Expected Result | Covered by | Asserted where | Disposition |
|---|--------------|-----------------|------------|----------------|-------------|
| Pre | User is logged in | User authenticated | Auth fixture | Browser storage state | **blocked** — needs new user |
| 1 | Log in for first time | User authenticated, lands on expected page | Navigate to `/onboarding` after auth | URL verification | **blocked** — needs new user |
| 2 | Full-screen welcome page with ELITEA logo at top center | Logo visible at top | Verify `onboarding-page-logo` visible | `expect(locator).to_be_visible()` | **ready** — testid exists |
| 3 | Page title "Welcome to Elitea!" | Title text matches | Verify `onboarding-welcome-title` has text "Welcome to Elitea!" | `expect(locator).to_have_text()` | **ready** — testid exists |
| 4 | Card with greeting "Hello, [Username]!" | Greeting personalizes with username | Verify `onboarding-welcome-greeting` contains user's name | `expect(locator).to_contain_text()` with `user.name` | **blocked** — needs new user to verify runtime substitution |
| 5 | Card body text about workspace setup | Body text matches expected copy | Verify `onboarding-welcome-body-text` text | `expect(locator).to_have_text()` with exact copy | **ready** — testid exists |
| 6 | Secondary text "Ready to explore..." | Secondary text matches | Verify `onboarding-welcome-secondary-text` text | `expect(locator).to_have_text()` | **ready** — testid exists |
| 7 | "Sure, let's go!" button visible | Button present and clickable | Verify `onboarding-welcome-get-started-button` visible and enabled | `expect(locator).to_be_visible()` + `to_be_enabled()` | **ready** — testid exists |
| 8 | No sidebar navigation visible | No left panel, no project dropdown | Verify sidebar element NOT present | `expect(sidebar_locator).to_have_count(0)` | **ready** — check layout |
| 9 | Personal project NOT loading yet | No progress bar, no "Configuring Personal project..." footer | Verify `onboarding-progress-footer` NOT present | `expect(locator).to_have_count(0)` | **blocked** — needs verification of negative state |
| Final | Project provisioning not started | `user.personal_project_id` still null | Backend API check OR verify no polling started | API assertion or session storage check | **blocked** — needs new user |

### Axis 2 — Additional Coverage Beyond Case

| Observable | Reason | Assertion |
|------------|--------|-----------|
| Page container has correct testid | Base element for page identification | Verify `onboarding-page-container` exists |
| Welcome card container structure | Validate component rendered correctly | Verify `onboarding-welcome-card` exists |
| Illustration image present | Visual element completion | Verify `onboarding-welcome-illustration` exists |
| Button does NOT trigger action until clicked | Test explicitly verifies button visibility only, not click | Verify button is present but NOT clicked during test |

---

## Handles Reference

### UI Elements — Welcome Screen

All testids are **already present** in `src/[fsd]/features/onboarding/ui/Welcome.jsx` and `src/pages/Onboarding/Onboarding.jsx`:

| Element | testid | Provenance | Type | Fallback |
|---------|--------|------------|------|----------|
| Page container | `onboarding-page-container` | **on-main ✓** | Box | N/A |
| Top logo | `onboarding-page-logo` | **on-main ✓** | Box (Logo SVG) | N/A |
| Welcome card container | `onboarding-welcome-card` | **on-main ✓** | Box | N/A |
| Illustration image | `onboarding-welcome-illustration` | **on-main ✓** | Box (img) | N/A |
| Page title | `onboarding-welcome-title` | **on-main ✓** | Typography | N/A |
| User greeting | `onboarding-welcome-greeting` | **on-main ✓** | Typography | N/A |
| Body text | `onboarding-welcome-body-text` | **on-main ✓** | Typography | N/A |
| Secondary text | `onboarding-welcome-secondary-text` | **on-main ✓** | Typography | N/A |
| Get started button | `onboarding-welcome-get-started-button` | **on-main ✓** | Button.BaseBtn | N/A |
| Progress footer (should NOT exist) | `onboarding-progress-footer` | **on-main ✓** | Box | N/A |
| Sidebar navigation (should NOT exist) | — | N/A | Layout | Use layout container checks |

**Note:** All testids verified in source code. No testid additions needed.

### Routing

| Route | Pattern | Auth Required |
|-------|---------|---------------|
| Onboarding | `/onboarding` | Yes (Keycloak) |

### Authentication

- **Auth field:** `input[name="username"]` (Keycloak) — NOT `input[name="email"]`
- **Localhost:** `auth_state` fixture skips login via `VITE_DEV_TOKEN`
- **Deployed envs:** Full Keycloak authentication flow

### Backend State

The Welcome screen visibility is determined by:

```javascript
!showTour && !user.personal_project_id && user.id
```

Where:
- `showTour`: Boolean state, default `false` for first-time users
- `user.personal_project_id`: Null for first-time users, set after project creation
- `user.id`: User authenticated successfully

**Clicking "Sure, let's go!" triggers:**
1. `sessionStorage.setItem('onboarding_state', 'true')`
2. `setShowTour(true)` — hides Welcome, shows OnboardingTour
3. Starts project provisioning polling (if `!user.personal_project_id`)
4. Polls `/api/v2/social/author/details` every 5 seconds
5. When backend sets `personal_project_id`, polling stops

---

## Test Execution Notes

### Cannot Execute Yet

This analysis is based on **code review only**, not live execution, because:
1. Test user already has `personal_project_id` (likely from previous runs)
2. No fixture exists to provision new users
3. No backend API to reset user state

### When Unblocked, Expected Observations

**Step-by-step flow:**
1. Navigate to `http://localhost:5173/onboarding` after auth
2. Verify page loads with logo at top center
3. Verify "Welcome to Elitea!" title visible
4. Verify greeting "Hello, [User's Name]!" personalizes correctly
5. Verify body text: "We're setting up your personal workspace — it'll be ready in about 5 minutes. While we work our magic, take a quick tour through our onboarding slides!"
6. Verify secondary text: "Ready to explore Elitea's smart tools and tips?"
7. Verify "Sure, let's go!" button is visible and enabled
8. Verify sidebar navigation is NOT present (no left panel)
9. **CRITICAL**: Verify progress footer (`onboarding-progress-footer`) is NOT present — this confirms project provisioning has not started
10. **Backend check**: Verify `user.personal_project_id` is still `null` via API call OR verify `sessionStorage.getItem('onboarding_state')` is NOT set

**DO NOT click the "Sure, let's go!" button** — that would start project provisioning, which is outside the scope of this test.

### Evidence Paths

```
test-results/screenshots/ELITEA-2231-step-02-logo-visible.png
test-results/screenshots/ELITEA-2231-step-03-title-visible.png
test-results/screenshots/ELITEA-2231-step-04-greeting-visible.png
test-results/screenshots/ELITEA-2231-step-07-button-visible.png
test-results/screenshots/ELITEA-2231-step-08-no-sidebar.png
test-results/screenshots/ELITEA-2231-step-09-no-progress-footer.png
test-results/json/ELITEA-2231-user-state-before-click.json
```

---

## Known Issues

None — but test is **blocked** due to infrastructure limitation.

---

## Out of Scope (Explicitly NOT Covered)

- Clicking "Sure, let's go!" button (separate test case)
- Project provisioning progress tracking (separate test case)
- Onboarding tour slides (separate test case)
- "Workspace is ready" final screen (separate test case)

---

## Classification Rationale

**Status: `blocked`**

This test requires a **first-time user** (no `personal_project_id`) which cannot be satisfied with the current test infrastructure. The existing test user has already been through onboarding and has a personal project, so the Welcome screen will not render.

**Recommendations:**
1. **Immediate**: Create enhancement ticket for new-user provisioning capability
2. **Short-term**: Explore backend API for user state reset
3. **Long-term**: Consider dedicated onboarding test environment with clean user database

---

## Related Test Cases

- **ELITEA-XXXX**: Onboarding — Click "Sure, let's go!" starts project provisioning (next step)
- **ELITEA-XXXX**: Onboarding — Project provisioning progress tracking
- **ELITEA-XXXX**: Onboarding — Tour slides navigation
- **ELITEA-XXXX**: Onboarding — "Workspace is ready" final screen

---

## Defects Filed

None — no product defects found during analysis. The blocker is test infrastructure only.

---

## Notes for Implementation

When this test is unblocked:

1. **Page Object**: Create `OnboardingPage` class in `automation/pages/onboarding_page.py`
2. **Fixture**: Create `new_user` fixture that provisions a fresh Keycloak account OR resets existing user state
3. **Test structure**:
   ```python
   def test_welcome_page_first_login(page, new_user, auth_state):
       # Authenticate with new user (no personal_project_id)
       # Navigate to /onboarding
       # Assert all visible elements per Coverage Map
       # Assert progress footer NOT present
       # Take screenshots for evidence
       # DO NOT click "Sure, let's go!"
   ```

4. **Cleanup**: Ensure user is deleted OR project is reset after test

---

**Analyst:** Sage (qa-engineer)  
**Date:** 2026-08-18  
**Analysis method:** Code review (live execution blocked)
