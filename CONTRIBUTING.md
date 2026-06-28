# Contributing to Photobook as Code

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/photobook-as-code.git
cd photobook-as-code
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e .
pip install -e ".[dev]"  # Install development dependencies
```

4. Verify installation:
```bash
photobook --version
```

## Development Workflow

### Making Changes

1. Create a new branch for your feature or fix:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and test them

3. Run tests (if available):
```bash
pytest
```

4. Commit your changes with clear messages:
```bash
git commit -m "Add feature: description of what you did"
```

5. Push to your fork and create a pull request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names

Example:
```python
def calculate_grid_dimensions(photos_per_page: int) -> GridLayout:
    """
    Calculate optimal grid dimensions for given photos per page.
    
    Args:
        photos_per_page: Target number of photos per page
        
    Returns:
        GridLayout with rows and columns
    """
    # Implementation here
```

### Project Structure

```
photobook-as-code/
├── src/photobook_as_code/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration parsing
│   ├── photos.py       # Photo collection and metadata
│   ├── themes.py       # Theme management
│   ├── layout.py       # Layout calculation
│   ├── renderer.py     # Page rendering
│   ├── output.py       # Output generation
│   └── themes/         # Built-in theme files
├── tests/              # Test files
├── pyproject.toml      # Project metadata and dependencies
└── README.md           # Documentation
```

## Types of Contributions

### Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your configuration file (sanitized if needed)
- Python version and operating system
- Error messages or logs

### Feature Requests

For new features, please describe:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered
- Examples of how it would be used

### Code Contributions

We welcome:
- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements
- New themes
- Examples and tutorials

### Documentation

Documentation contributions are highly valued:
- Fix typos or unclear explanations
- Add examples
- Improve installation instructions
- Translate documentation
- Create tutorials or blog posts

## Adding New Features

### Adding a New Theme

1. Create a YAML file in `src/photobook_as_code/themes/`:
```yaml
name: Your Theme Name
description: Brief description

background:
  color: "#HEXCODE"

borders:
  enabled: true/false
  width: pixels
  color: "#HEXCODE"
  shadow: true/false

spacing:
  grid_gap: pixels
  page_margin: pixels
```

2. Test your theme with various photo counts and layouts

3. Update README.md with theme description

### Adding New Layout Algorithms

1. Implement in `layout.py`
2. Add corresponding configuration options in `config.py`
3. Update configuration schema in README
4. Add tests

### Adding New Output Formats

1. Implement generator in `output.py`
2. Add format validation in `config.py`
3. Update documentation
4. Add examples

## Testing

### Manual Testing

Create test configurations and photo sets:

```bash
# Create test directory
mkdir test-photos
# Add some test images

# Test basic generation
photobook --config test-config.yaml --verbose

# Test different formats
photobook --config pdf-test.yaml
photobook --config png-test.yaml
photobook --config jpg-test.yaml
```

### Test Coverage

When adding new features:
- Add tests for normal cases
- Add tests for edge cases
- Add tests for error conditions
- Test with various photo counts (1, 2, 4, 7, 100, etc.)

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md (if exists)
5. Ensure code follows style guidelines
6. Create pull request with clear description

### Pull Request Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
```

## Code Review Process

- Maintainers will review pull requests
- Feedback will be provided for improvements
- Once approved, changes will be merged
- Be patient and respectful during review

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the code of conduct (if present)

## Questions?

- Open an issue for questions
- Check existing issues and documentation first
- Provide context and examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
