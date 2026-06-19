# Elitea QA Handbook

Welcome to the **Elitea Quality Assurance Handbook** — the central resource for QA processes, testing standards, bug reporting, and team practices for the Elitea AI platform.

## Purpose

This handbook provides:

- **Clear processes** for bug reporting, test execution, and quality verification
- **Standardized workflows** for QA team members and contributors
- **Best practices** for creating AI-native bug reports and test data
- **Quick reference guides** for tools, environments, and project workflows
- **Onboarding resources** for new QA team members

## Who This Is For

- **QA Engineers**: Daily reference for testing processes and bug reporting
- **Developers**: Understanding QA workflows and bug expectations
- **Product Managers**: Triage standards and quality metrics
- **Support Team**: Guidance for reporting client issues
- **AI Agents**: Structured, reproducible information for automation

## Quick Navigation

### Essential Guides

- **[Bug Management](bug-management/index.md)** — How to report, triage, and track bugs
- **[QA Processes](qa-processes/index.md)** — Core QA workflows and standards
- **[Test Execution](test-execution/index.md)** — Running and documenting tests
- **[Environments](environments/index.md)** — DEV, STAGE, and environment access

### Reference Materials

- **[Templates](reference-templates/index.md)** — Bug reports, test cases, and other templates
- **[Useful Links](useful-links/index.md)** — Tools, dashboards, and external resources
- **[Onboarding](onboarding/index.md)** — Getting started as a new QA team member

## How to Use This Handbook

1. **Navigate by topic** using the left sidebar or links above
2. **Search** using the search box (top of page)
3. **Contribute** by submitting issues or pull requests to improve content
4. **Keep it current** — guidelines are living documents

## Contributing to This Handbook

We welcome improvements! To contribute:

1. **Report issues**: If you find outdated or unclear information, [open an issue](https://github.com/EliteaAI/elitea-testing/issues)
2. **Suggest changes**: Submit a pull request with improvements
3. **Ask questions**: Reach out to the QA team lead

### Documentation Ownership

- **QA Lead**: Owns QA processes and workflow sections
- **Engineering Leads**: Own severity/priority definitions and technical processes
- **Release Manager**: Owns milestone and release policy
- **All Contributors**: Can suggest improvements and updates

## Building Documentation Locally

This site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

**Quick start:**

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Serve locally (auto-reload)
mkdocs serve

# View at http://localhost:8000
```

**Build static site:**

```bash
mkdocs build
# Output in site/ directory
```

## Documentation Standards

- Use clear, concise language
- Include examples and screenshots where helpful
- Keep sensitive information out (no credentials, PII, or secrets)
- Use relative links for internal navigation
- Follow the [Assets README](assets/README.md) for images

## Support and Feedback

- **Questions**: Contact the QA team via Slack or email
- **Issues**: Use the [GitHub issue tracker](https://github.com/EliteaAI/elitea-testing/issues)
- **Updates**: Review this handbook regularly for process changes

---

**Last Updated**: January 2026  
**Maintained By**: Elitea QA Team
