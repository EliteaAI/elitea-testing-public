# Bug Management

Welcome to the Bug Management section of the Elitea QA Handbook. This section covers everything related to identifying, reporting, tracking, and resolving bugs in the Elitea platform.

## Overview

Effective bug management is critical for maintaining product quality and enabling rapid development cycles. Our bug management process is designed to be:

- **AI-native**: Structured for both human and AI agent comprehension
- **Reproducible**: Clear steps and stable test data
- **Traceable**: Linked to features, releases, and acceptance criteria
- **Consistent**: Standardized reporting and triage

## Core Guides

### Bug Reporting

- **[Bug Reporting Guide](bug-reporting-guide.md)** — Complete guide to reporting bugs using GitHub Issues and ELITEA Board
- **[Bug Template Examples](bug-template-examples.md)** — Concrete examples of well-written bug reports

### Bug Classification

- **[Bug Priority and Severity](bug-priority-severity.md)** — How to assess impact (severity) and urgency (priority)
- **[Labels and Taxonomy](labels-taxonomy.md)** — Label categories, usage rules, and governance

### Process and Workflow

- **[Bug Lifecycle](bug-lifecycle.md)** — Bug states and transitions in ELITEA Board
- **[Project Fields Guide](project-fields-guide.md)** — All GitHub Projects fields explained
- **[Parent Issue and Sub-Issue Rules](parent-sub-issue-rules.md)** — When and how to use parent/child relationships

## Quick Links

- [ELITEA Board Project](https://github.com/orgs/EliteaAI/projects/3/views/1)
- [Bug Report Template](../reference-templates/bug-report-template.md)
- [Test Data Guidelines](../test-execution/test-data-management.md)

## Key Principles

1. **Report in DEV/STAGE** — All bugs must be reproducible in DEV or STAGE environments
2. **Include test data** — Provide stable links to agents, pipelines, toolkits, MCPs, and chats
3. **Be deterministic** — Avoid vague language; use explicit steps and conditions
4. **Fill required fields** — Type, Status, Priority, Severity, Milestone, Assignee
5. **Attach evidence** — Screenshots, logs, and error messages

## Common Tasks

- [How to report a new bug](bug-reporting-guide.md#quick-start-minimum-good-bug)
- [How to choose priority and severity](bug-priority-severity.md#how-to-choose-severity-triage-questions)
- [How to select labels](labels-taxonomy.md#how-to-label-an-issue-recommended-pattern)
- [How to create a sub-issue](parent-sub-issue-rules.md#how-to-create-a-sub-issue-in-github)

## Support

If you have questions about bug management:

- Review the guides in this section
- Ask in the QA team channel
- Contact the QA lead
- Open a documentation issue for unclear content
