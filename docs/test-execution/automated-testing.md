# Automated Testing

## Overview

Automated testing uses scripts and tools to execute tests repeatedly and consistently.

## Automated Test Types

### UI Automation
- Playwright-based tests in `ui-tests/`
- Page object pattern
- Cross-browser testing

### API Automation
- API tests in `api-tests/`
- Integration tests
- Contract testing

### Toolkit Automation
- Toolkit tests in `toolkit-tests/`
- MCP integration tests
- End-to-end workflows

## Running Automated Tests

See the main repository README and test directories for specific commands.

## Test Maintenance

- Update tests when features change
- Keep test data current
- Review flaky tests
- Refactor for maintainability

## Best Practices

- Make tests independent
- Use stable selectors
- Handle waits properly
- Clean up test data
- Run locally before committing

## Related Guides

- [Manual Testing](manual-testing.md)
- [Test Data Management](test-data-management.md)
