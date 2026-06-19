# Test Data Management

## Overview

Effective test data management ensures tests are reproducible, stable, and maintain quality standards.

## Test Data Principles

### Stability
- Use dedicated test accounts and projects
- Version test data
- Keep test data isolated from production

### Reproducibility
- Document how to create test data
- Provide links to test objects
- Include credentials (stored securely)

### Organization
- Name test objects clearly
- Use consistent naming: `BUG-<issueNumber> <description> (DEV|STAGE)`
- Tag and categorize appropriately

## Creating Test Data

### Test Accounts
- Use dedicated QA accounts
- Document roles and permissions
- Never use production user data

### Test Objects
- Create in "Bugs & Features" project or equivalent
- Name descriptively
- Link in bug reports and test cases

### Test Environments
- Create data in DEV and STAGE
- Do not create test data in production

## Test Data for Bugs

When reporting bugs:
- Provide direct links to test objects (agents, pipelines, toolkits, MCPs, chats)
- Include account credentials (securely)
- Document configuration settings
- Ensure data remains available for verification

## Security

**Never include:**
- Real production passwords
- API keys or tokens
- PII or customer data
- Internal infrastructure details

**Use:**
- Test accounts only
- Placeholder credentials
- Synthetic data
- Secure credential storage

## Best Practices

- Create test data before testing
- Keep test data current
- Clean up obsolete data periodically
- Document test data dependencies
- Share test data locations with team

## Related Guides

- [Bug Reporting Guide](../bug-management/bug-reporting-guide.md)
- [Environments](../environments/index.md)
