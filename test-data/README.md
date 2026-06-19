# Test Data Directory

This directory contains sample test data files used across different test scenarios.

## Guidelines

- Place sample/template data files here that can be reused across tests
- Use descriptive filenames (e.g., `sample-users.json`, `test-dataset.csv`)
- Avoid committing sensitive or large data files
- Document the purpose and format of each data file

## File Organization

- **sample-*.*** : Template/example data files (committed to repo)
- **test-*.*** : Generated test data (excluded by .gitignore)
- **fixtures/**: Static test fixtures and mock data

## Example Files

Create your test data files following these patterns:
- `sample-users.json` - Sample user data for API tests
- `sample-products.csv` - Sample product data for import tests
- `test-scenarios.json` - Test scenario configurations