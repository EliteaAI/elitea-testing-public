# Release Verification

## Overview

Release verification ensures that all features, fixes, and changes are working correctly before a release goes to production.

## Release Verification Process

### Pre-Release Checklist
- [ ] All planned features are complete
- [ ] All P0 and P1 bugs are resolved
- [ ] Regression testing passed
- [ ] Performance testing passed (if applicable)
- [ ] Security scanning completed
- [ ] Documentation updated

### Verification Activities

#### Feature Verification
- Test all new features against acceptance criteria
- Verify features in STAGE environment
- Test integration points
- Validate user workflows

#### Bug Fix Verification
- Verify all closed bugs are actually fixed
- Test with original reproduction steps
- Use same test data
- Check for regressions

#### Regression Testing
- Execute regression test suite
- Focus on core user paths
- Test integrations
- Verify performance

### Release Sign-Off

QA provides release sign-off when:
- All verification activities complete
- All blocking issues resolved
- Acceptable defect levels
- Documentation current

## Best Practices

- Start verification early
- Test in production-like environment (STAGE)
- Document all findings
- Communicate status clearly
- Don't skip verification steps

## Related Guides

- [Release Checklist Template](../reference-templates/release-checklist-template.md)
- [Regression Testing](regression-testing.md)
- [Bug Lifecycle](../bug-management/bug-lifecycle.md)
