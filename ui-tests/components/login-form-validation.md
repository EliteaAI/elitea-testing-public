### Test Case ID: UI-001
**Description**: Verify login form validation with invalid credentials
**Preconditions**: User is on the login page and not authenticated
**Test Steps**:
1. Navigate to the login page
2. Enter invalid email address "invalid-email"
3. Enter password "wrongpassword"
4. Click the "Login" button
**Expected Results**: 
- Error message should display "Invalid email format"
- User should remain on login page
- No authentication should occur
**Actual Results**: [To be filled during test execution]
**Status**: [To be filled during test execution]
**Notes**: Test validates client-side form validation