# Assets Management Guide

This directory contains static assets for the Elitea QA Documentation site.

## Directory Structure

- `img/` - Images, screenshots, and diagrams

## Image Guidelines

### Storage and Organization

- Store all images in the `img/` subdirectory
- Use descriptive, lowercase filenames with hyphens (e.g., `bug-report-example.png`)
- Group related images by prefixing with the section name (e.g., `bug-mgmt-workflow.png`)

### Naming Conventions

**Good examples:**
- `test-execution-flow.png`
- `bug-report-template-example.png`
- `environment-architecture-diagram.svg`

**Avoid:**
- `Screenshot 2024-01-15.png` (not descriptive)
- `IMG_1234.jpg` (not descriptive)
- `image (1).png` (spaces and generic)

### File Formats

- **Screenshots**: Use PNG format for clarity
- **Diagrams**: Prefer SVG for scalability, PNG as fallback
- **Photos**: Use JPEG for photographs if needed

### Security and Privacy

**DO NOT include:**
- Real passwords or API keys
- Personal identifiable information (PII)
- Production credentials or secrets
- Internal IP addresses or infrastructure details
- Customer data

**Safe practices:**
- Redact sensitive information before uploading
- Use placeholder text for credentials (e.g., `***`)
- Blur or mask sensitive UI elements
- Use test/demo environments in screenshots

### Image Size

- Keep images reasonably sized (< 2MB per file preferred)
- Optimize screenshots before committing
- Consider compressing large images

## Referencing Images in Documentation

Use relative paths from the markdown file:

```markdown
![Description](../assets/img/image-name.png)
```

For images in the same directory structure:

```markdown
![Test Flow Diagram](../assets/img/test-execution-flow.png)
```

## Contributing

When adding new images:

1. Ensure the image follows naming conventions
2. Verify no sensitive data is included
3. Optimize image size if large
4. Add descriptive alt text in markdown
5. Commit with a clear message describing the image purpose
