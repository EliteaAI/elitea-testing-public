# Triage Process

## Overview

Bug triage is the process of evaluating, prioritizing, and routing bugs to ensure critical issues are addressed promptly.

## Triage Workflow

### 1. Initial Review
- Verify bug is reproducible
- Check for duplicates
- Validate completeness of bug report

### 2. Classification
- Set Type (Bug)
- Set Severity (Blocker, Critical, High, Medium)
- Set Priority (P0, P1, P2)
- Add appropriate labels

### 3. Routing
- Assign to appropriate team/developer
- Set milestone (current release, next, future)
- Link to parent issue if applicable

### 4. Action
- Move to appropriate status (Bugs → Development)
- Communicate urgency if needed
- Add to sprint if immediate action required

## Triage Criteria

### Priority Assessment
- **P0**: Blocks release or critical functionality
- **P1**: Must fix in current release
- **P2**: Plan for future release

### Severity Assessment
- **Blocker**: System unusable, no workaround
- **Critical**: Major functionality broken, unsafe behavior
- **High**: Significant inconvenience, partial failure
- **Medium**: Minor UX issues, cosmetic defects

## Triage Meeting

Weekly triage meeting to review:
- New bugs
- Unassigned bugs
- Stale bugs
- Priority changes

## Best Practices

- Triage promptly (within 24-48 hours)
- Be objective in assessment
- Consider user impact
- Communicate clearly
- Document rationale for decisions

## Related Guides

- [Bug Priority and Severity](../bug-management/bug-priority-severity.md)
- [Labels and Taxonomy](../bug-management/labels-taxonomy.md)
- [Bug Lifecycle](../bug-management/bug-lifecycle.md)
