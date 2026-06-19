# Contributing to the QA Handbook

Thank you for contributing to the Elitea QA documentation!

## How to Contribute

### Reporting Issues

If you find outdated or unclear information:

1. [Open an issue](https://github.com/EliteaAI/elitea-testing/issues/new) with:
   - Clear title describing the problem
   - Page/section where the issue exists
   - What needs to be updated or clarified
   - Suggested improvement (if applicable)

### Suggesting Changes

To suggest improvements:

1. Fork the repository
2. Make your changes in a new branch
3. Submit a pull request with:
   - Clear description of changes
   - Rationale for the update
   - References (if updating process documentation)

## Documentation Standards

### Writing Style

- Use clear, concise language
- Write in active voice
- Use second person ("you") when addressing readers
- Use present tense
- Be specific and avoid ambiguity

### Structure

- Use headings hierarchically (h1 → h2 → h3)
- Include a brief overview at the top of each page
- Break content into digestible sections
- Use lists for steps and options
- Add examples where helpful

### Formatting

- Use **bold** for emphasis
- Use `code` for commands, file names, and technical terms
- Use > blockquotes for important notes
- Use tables for comparisons and reference data
- Use admonitions (via markdown extensions) for warnings/tips

### Links

- Use relative links for internal documentation
- Format: `[Link Text](../section/page.md)` for cross-section links
- Format: `[Link Text](page.md)` for same-section links
- Verify links work after changes

### Images

- Store in `docs/assets/img/`
- Use descriptive filenames (lowercase, hyphens)
- Follow guidelines in `docs/assets/README.md`
- Add alt text: `![Description](../assets/img/image.png)`
- Optimize images before committing

## Building Locally

### Prerequisites

```bash
pip install -r requirements.txt
```

### Serve Locally

```bash
mkdocs serve
```

Then open http://localhost:8000

### Build Static Site

```bash
mkdocs build
```

Output in `site/` directory (git-ignored).

## Testing Changes

Before submitting:

1. Build locally: `mkdocs build`
2. Check for warnings/errors
3. Verify links work
4. Review generated HTML in browser
5. Check navigation is correct

## Section Ownership

- **QA Lead**: QA processes, workflow sections
- **Engineering Leads**: Severity/priority definitions, technical processes
- **Release Manager**: Milestone and release policy
- **All Contributors**: Can suggest improvements

## Review Process

1. Submit pull request
2. Tag relevant section owner for review
3. Address feedback
4. Merge after approval

## Style Guide Quick Reference

### Headings

```markdown
# Page Title (H1)

## Main Section (H2)

### Subsection (H3)

#### Detail Section (H4)
```

### Lists

```markdown
- Unordered item
- Another item

1. Ordered item
2. Next item

- [ ] Checklist item unchecked
- [x] Checklist item checked
```

### Code

```markdown
Inline: `command` or `variable`

Block:
```bash
mkdocs serve
```
```

### Links

```markdown
[Internal Link](../section/page.md)
[External Link](https://example.com)
[Link with Anchor](page.md#section-heading)
```

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data     | Data     | Data     |
```

### Admonitions

```markdown
!!! note
    This is a note.

!!! warning
    This is a warning.

!!! tip
    This is a tip.
```

## Questions?

- Ask in the QA team channel
- Contact the QA lead
- Open a discussion issue

Thank you for helping maintain high-quality documentation!
