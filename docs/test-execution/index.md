# Test Execution

This section covers the practical aspects of executing tests, managing test data, and documenting test results.

## Overview

Test execution is the process of running test cases, recording results, and reporting defects to validate that software meets requirements.

## Core Guides

### Execution Practices

- **[Manual Testing](manual-testing.md)** — Best practices for manual test execution
- **[Automated Testing](automated-testing.md)** — Running and maintaining automated tests
- **[Test Data Management](test-data-management.md)** — Creating and maintaining test data
- **[Test Results Documentation](test-results-documentation.md)** — Recording and reporting test outcomes

### Test Types

- **[UI Testing](ui-testing.md)** — Testing user interface and workflows
- **[API Testing](api-testing.md)** — Testing APIs and integrations
- **[Toolkit Testing](toolkit-testing.md)** — Testing toolkits and MCP integrations
- **[Agent Testing](agent-testing.md)** — Testing AI agents and pipelines

## Quick Reference

### Before Testing
- Review test cases and acceptance criteria
- Prepare test environment
- Create/verify test data
- Understand expected results

### During Testing
- Execute tests systematically
- Document results as you go
- Report bugs immediately
- Take screenshots for evidence

### After Testing
- Complete test results documentation
- Report summary and metrics
- Update test cases if needed
- Provide feedback to team

## Test Execution Checklist

- [ ] Test environment ready and accessible
- [ ] Test data created and stable
- [ ] Test cases reviewed and current
- [ ] Expected results clearly defined
- [ ] Bug reporting template ready
- [ ] Screen capture tools available

## Best Practices

1. **Follow test cases systematically** — Don't skip steps
2. **Document as you go** — Record results immediately
3. **Report defects promptly** — File bugs when found
4. **Use consistent test data** — Enable reproducibility
5. **Take evidence** — Screenshots, logs, recordings
6. **Communicate blockers** — Alert team to critical issues

## Testing Environments

Tests should be executed in appropriate environments:
- **DEV**: Active development, frequent changes
- **STAGE**: Pre-production, stable for verification
- **Production**: Live system, limited testing

See [Environments](../environments/index.md) for details.

## Related Guides

- [Test Planning](../qa-processes/test-planning.md)
- [Bug Reporting Guide](../bug-management/bug-reporting-guide.md)
- [Environments](../environments/index.md)
