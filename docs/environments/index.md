# Environments

This section describes the testing environments available for Elitea QA and how to access them.

## Available Environments

### DEV
**Purpose**: Active development and initial testing  
**URL**: [Contact QA team for access]  
**Stability**: Frequent changes, may be unstable  
**Use for**: Feature testing, bug reproduction, test data creation

### STAGE
**Purpose**: Pre-production verification  
**URL**: [Contact QA team for access]  
**Stability**: More stable, mirrors production  
**Use for**: Release verification, final testing, stakeholder demos

### NEXT
**Purpose**: Beta testing and early access  
**URL**: [Contact QA team for access]  
**Stability**: Production-like  
**Use for**: Beta testing, pre-release validation

### Production
**Purpose**: Live system  
**Stability**: Stable  
**Use for**: Limited testing, issue verification only

## Environment Access

See the following guides for access details:
- [Environment Access](environment-access.md) — How to get access
- [Test Accounts](test-accounts.md) — QA test accounts and credentials

## Environment Guidelines

### DEV Environment
- Primary environment for bug reproduction
- Create test data in "Bugs & Features" project
- Expect frequent deployments
- May have experimental features

### STAGE Environment
- Use for final verification before release
- More stable than DEV
- Production-like configuration
- Verify bugs here before closing

### Testing Rules

**DO:**
- Create bugs in DEV or STAGE
- Use dedicated test accounts
- Create test data in appropriate projects
- Document which environment was used

**DON'T:**
- Create test data in production
- Use real user accounts
- Test unverified changes in production

## Related Guides

- [Test Data Management](../test-execution/test-data-management.md)
- [Bug Reporting Guide](../bug-management/bug-reporting-guide.md)
