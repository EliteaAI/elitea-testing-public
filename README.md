# Elitea Testing Repository

This repository is designed for organizing and managing test cases and scenarios for the Elitea AI platform. It provides a structured approach to maintain different types of tests in an organized manner.

## Repository Structure

```
elitea-testing/
├── ui-tests/                 # User Interface test cases
│   ├── components/          # Individual UI component tests
│   ├── workflows/           # End-to-end workflow tests
│   └── integration/         # UI integration tests
├── toolkit-tests/           # Toolkit and tools test cases
│   ├── tools/              # Individual tool tests
│   ├── integrations/       # Toolkit integration tests
│   └── performance/        # Performance and load tests
├── api-tests/              # API test cases
│   ├── endpoints/          # Individual endpoint tests
│   ├── authentication/    # Authentication tests
│   └── data-validation/   # Data validation tests
└── README.md               # This file
```

## Test Categories

### 🖥️ UI Tests
Test cases for the Elitea AI platform user interface, including component testing, user workflows, and integration scenarios.

### 🔧 Toolkit Tests  
Test cases for Elitea AI toolkits, tools, and utilities, including functionality, integration, and performance testing.

### 🔌 API Tests
Test cases for Elitea AI platform APIs, including endpoint testing, authentication, and data validation.

## Getting Started

1. **Navigate** to the appropriate test category directory
2. **Read** the README.md in each directory for specific guidelines
3. **Use** the provided templates to create new test cases
4. **Follow** the naming conventions and structure guidelines

## Contributing

- Use descriptive file names for test cases
- Follow the templates provided in each directory
- Include all necessary information for test reproduction
- Update documentation when adding new test scenarios
- Group related tests in appropriate subdirectories

## Test Case Naming Convention

- UI Tests: `ui-tests/category/feature-description.md`
- Toolkit Tests: `toolkit-tests/category/tool-feature-description.md`  
- API Tests: `api-tests/category/endpoint-method-description.md`

## Documentation (MkDocs)

This repository includes MkDocs-based documentation for browsing test cases in a structured format.

### Building Documentation Locally

To build and preview the documentation:

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Serve documentation locally
mkdocs serve
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

### Documentation Files

- **[docs/index.md](docs/index.md)**: Documentation home page with build instructions
- **mkdocs.yml**: MkDocs configuration file
- **docs/requirements.txt**: Python dependencies for MkDocs

### Note

GitHub Pages publishing is not enabled for this repository. Documentation can be consumed by:
- Browsing markdown files directly in GitHub
- Building locally using the instructions above
- Viewing build validation in CI workflows

---

Each test directory contains:
- **README.md**: Guidelines and templates specific to that test type
- **Example test cases**: Demonstrating the expected format and structure
- **Subdirectories**: For organizing tests by feature or component
