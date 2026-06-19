# Exploratory Testing

## Overview

Exploratory testing is simultaneous learning, test design, and test execution — an investigative approach to uncovering defects that scripted tests might miss.

## When to Use Exploratory Testing

- New feature areas without documented test cases
- Complex workflows with many variations
- After major UI/UX changes
- To discover edge cases and unexpected behaviors
- When investigating customer-reported issues

## Exploratory Testing Approach

### 1. Charter
Define the exploration goal:
- What area to explore
- What risks to investigate
- Time box (typically 60-90 minutes)

### 2. Explore
- Follow user workflows naturally
- Try unexpected inputs
- Combine features in unusual ways
- Note observations and questions

### 3. Document
- Record bugs immediately
- Note interesting behaviors
- Capture test ideas for future

### 4. Debrief
- Review findings
- Update test cases
- Share insights with team

## Exploratory Testing Techniques

### Tours
Structured exploration patterns:
- **Feature Tour**: Explore each feature systematically
- **User Tour**: Follow typical user journeys
- **Data Tour**: Test with various data types
- **Boundary Tour**: Push limits and boundaries
- **Error Tour**: Deliberately cause errors

### Heuristics
- What if…?
- What about…?
- How does it handle…?

## Documentation

While exploratory, document:
- Charter and goals
- Key observations
- Bugs found (file immediately)
- Test ideas generated
- Time spent

## Best Practices

- Set clear time boxes
- Take notes as you go
- File bugs immediately when found
- Pair with developers when possible
- Share findings with the team
- Balance with scripted testing

## Tools and Techniques

- Session-based test management
- Mind mapping
- Screen recording for complex scenarios
- Note-taking tools

## Related Guides

- [Test Design](test-design.md)
- [Bug Reporting Guide](../bug-management/bug-reporting-guide.md)
- [Test Execution](../test-execution/index.md)
