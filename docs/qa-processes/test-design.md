# Test Design

## Overview

Test design focuses on creating effective, maintainable test cases that validate functionality and catch defects.

## Test Case Structure

A well-designed test case includes:

1. **Test ID** — Unique identifier
2. **Title** — Clear, descriptive name
3. **Preconditions** — Required setup or state
4. **Test Steps** — Numbered, deterministic actions
5. **Test Data** — Input data and test objects
6. **Expected Result** — What should happen
7. **Priority** — Importance level

## Test Design Techniques

### Equivalence Partitioning
Group inputs into valid and invalid partitions; test one value from each partition.

### Boundary Value Analysis
Test values at boundaries (min, max, just inside, just outside).

### Decision Tables
Map combinations of inputs to expected outputs.

### State Transition Testing
Test state changes and transitions in workflows.

### Use Case Testing
Design tests based on user scenarios and journeys.

## AI-Native Test Design

For AI agent testing:
- Use stable, reproducible test data
- Include explicit expected outputs
- Document model versions and configurations
- Test with consistent prompts and parameters

## Best Practices

- **Keep tests independent** — No dependencies between test cases
- **Make tests repeatable** — Same inputs yield same results
- **Use descriptive names** — Test purpose is clear from title
- **Cover positive and negative scenarios**
- **Include edge cases and boundary conditions**
- **Document assumptions and limitations**

## Test Case Template

See the [Test Case Template](../reference-templates/test-case-template.md) for a standard format.

## Related Guides

- [Test Planning](test-planning.md)
- [Test Execution](../test-execution/index.md)
- [Testing Standards](testing-standards.md)
