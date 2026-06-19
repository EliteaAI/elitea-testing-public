# Bug Lifecycle

The bug lifecycle in ELITEA Board defines the states a bug goes through from discovery to resolution.

## Bug States

### 1. Bugs (New)
**When:** Newly reported bugs  
**Who:** QA, Support, Developers, AI agents  
**Actions:**
- Triage and validate the bug
- Set Priority and Severity
- Assign to appropriate owner
- Ensure all required fields are filled

**Exit criteria:**
- Bug is validated and triaged
- Owner accepts the bug

---

### 2. Development
**When:** Bug is actively being fixed  
**Who:** Developer/Engineer  
**Actions:**
- Implement fix
- Write or update tests
- Submit pull request
- Link PR to bug issue

**Exit criteria:**
- Fix is merged
- Deployed to DEV environment

---

### 3. In Testing
**When:** Bug fix is deployed to DEV and ready for QA verification  
**Who:** QA Engineer  
**Actions:**
- Reproduce original bug using same test data
- Verify fix resolves the issue
- Test for regressions
- Document verification results

**Exit criteria:**
- Bug is verified fixed in DEV
- No regressions detected
- Verification evidence attached

---

### 4. Verified on DEV Env
**When:** Bug fix is confirmed working in DEV  
**Who:** QA Engineer  
**Actions:**
- Wait for deployment to STAGE
- Prepare verification plan for STAGE

**Exit criteria:**
- Fix is deployed to STAGE environment

---

### 5. Ready for Public Release
**When:** Bug fix is verified on STAGE and accepted for release  
**Who:** QA Lead, Release Manager  
**Actions:**
- Final acceptance review
- Include in release notes if applicable
- Mark for deployment to production

**Exit criteria:**
- Release is approved
- Deployed to production

---

### 6. Done
**When:** Bug fix is released and completed  
**Who:** Release Manager  
**Actions:**
- Close the bug issue
- Archive for metrics

**Exit criteria:**
- Fix is live in production (or released as planned)

---

## State Transitions

```
Bugs → Development → In Testing → Verified on DEV Env → Ready for Public Release → Done
```

**Possible backward transitions:**
- **In Testing → Development**: If verification fails or regressions are found
- **Verified on DEV Env → Development**: If issues are found in STAGE

---

## Field Requirements by State

### Bugs
- Type: Bug
- Priority: Set
- Severity: Set
- Assignee: Set
- Milestone: Set (or Next/Future)

### Development
- All fields from "Bugs" state
- PR linked (when available)

### In Testing
- Deployment confirmation
- QA assignee verification

### Verified on DEV Env
- Verification evidence
- Test data validation

### Ready for Public Release
- STAGE verification complete
- Release notes updated (if applicable)

### Done
- Release version noted
- Closure date recorded

---

## Best Practices

1. **Do not skip states** — Follow the lifecycle sequentially
2. **Provide evidence** — Attach screenshots or logs when transitioning states
3. **Update fields** — Keep Priority/Severity current if context changes
4. **Link PRs** — Always link pull requests to bug issues
5. **Verify with same test data** — Use the original test data for verification

---

## Related Guides

- [Bug Reporting Guide](bug-reporting-guide.md)
- [Project Fields Guide](project-fields-guide.md)
- [Bug Priority and Severity](bug-priority-severity.md)
