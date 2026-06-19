# Regression Testing

## Overview

Regression testing ensures that existing functionality continues to work correctly after changes (bug fixes, new features, refactoring).

## When to Perform Regression Testing

- After bug fixes
- After new feature implementations
- Before releases
- After major refactoring
- When dependencies are updated

## Regression Test Strategy

### Full Regression
Test all core functionality across the platform.

**When to use:**
- Major releases
- Significant architectural changes
- After multiple features merged

### Targeted Regression
Test areas likely to be affected by recent changes.

**When to use:**
- Individual bug fixes
- Minor feature additions
- Hotfixes

### Smoke Testing
Quick validation of critical paths.

**When to use:**
- After deployments
- Daily sanity checks
- Build verification

## Regression Test Suite

### Core Test Areas
- User authentication and authorization
- Agent creation and execution
- Pipeline workflows
- Toolkit integrations
- Chat functionality
- MCP operations
- Settings and configuration

### Automation
- Automated regression suite runs on each deployment
- Manual regression for complex scenarios
- AI agent-assisted regression testing

## Test Execution

1. Select appropriate regression scope
2. Execute test cases systematically
3. Document any failures immediately
4. Report new bugs following [Bug Reporting Guide](../bug-management/bug-reporting-guide.md)
5. Track regression coverage metrics

## Regression Testing Checklist

- [ ] Identify scope based on changes
- [ ] Review test cases for relevance
- [ ] Prepare test environment and data
- [ ] Execute tests systematically
- [ ] Document results
- [ ] Report defects
- [ ] Update test cases if needed

## Best Practices

- Maintain a regression test suite
- Automate repetitive tests
- Prioritize based on risk and usage
- Update tests when features change
- Track regression metrics
- Use stable test data

## Related Guides

- [Test Execution](../test-execution/index.md)
- [Automated Testing](../test-execution/automated-testing.md)
- [Bug Reporting Guide](../bug-management/bug-reporting-guide.md)
