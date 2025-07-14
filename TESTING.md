# Testing Guide for AI Agent Base

This document provides comprehensive information about testing in the AI Agent Base project.

## Overview

The AI Agent Base project uses a comprehensive testing strategy that includes:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test component interactions and workflows
- **API Tests** - Test REST API endpoints and responses
- **Tool Tests** - Test individual tool implementations
- **Mock Objects** - Simulate external dependencies for reliable testing

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini              # Pytest configuration
├── test_requirements.txt   # Test-specific dependencies
├── unit/                   # Unit tests
│   ├── test_base_vector_store.py
│   ├── test_component_factory.py
│   └── ...
├── integration/            # Integration tests
│   ├── test_agent_integration.py
│   ├── test_api_integration.py
│   └── ...
├── tools/                  # Tool-specific tests
│   ├── test_calculator_tool.py
│   └── ...
├── providers/              # Provider tests
│   ├── test_in_memory_backend.py
│   └── ...
└── fixtures/               # Test data and fixtures
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r tests/test_requirements.txt

# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py unit
python run_tests.py integration
python run_tests.py tools
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_calculator_tool.py

# Run tests matching a pattern
pytest -k "test_calculator"

# Run tests with specific markers
pytest -m "unit"
pytest -m "not slow"
```

### Test Runner Options

The `run_tests.py` script provides convenient options:

```bash
# Verbose output
python run_tests.py unit --verbose

# Stop on first failure
python run_tests.py unit --exitfirst

# Run tests in parallel
python run_tests.py unit --parallel

# Generate HTML coverage report
python run_tests.py all --html-coverage

# Show available test markers
python run_tests.py --markers
```

## Test Categories

### Unit Tests (`tests/unit/`)

Test individual components in isolation using mocks for dependencies.

**Example:**
```python
def test_calculator_addition(calculator):
    result = calculator.execute("2 + 3")
    assert result.success is True
    assert result.metadata['result'] == 5
```

**Run:**
```bash
python run_tests.py unit
pytest tests/unit/
pytest -m "unit"
```

### Integration Tests (`tests/integration/`)

Test component interactions and end-to-end workflows.

**Example:**
```python
def test_agent_with_memory_persistence(mock_components, test_config):
    agent = GeneralAgent(test_config)
    response1 = agent.process_query("My name is Alice")
    response2 = agent.process_query("What is my name?")
    # Test that agent remembers context
```

**Run:**
```bash
python run_tests.py integration
pytest tests/integration/
pytest -m "integration"
```

### Tool Tests (`tests/tools/`)

Test individual tool implementations with various inputs.

**Example:**
```python
def test_calculator_complex_expression(calculator):
    result = calculator.execute("(2 + 3) * 4 - 1")
    assert result.success is True
    assert result.metadata['result'] == 19
```

**Run:**
```bash
python run_tests.py tools
pytest tests/tools/
```

### API Tests

Test REST API endpoints, error handling, and response formats.

**Example:**
```python
def test_chat_endpoint_success(api_client):
    response = api_client.post('/agents/general/chat',
        json={'message': 'Hello'})
    assert response.status_code == 200
```

**Run:**
```bash
python run_tests.py api
pytest tests/integration/test_api_integration.py
```

## Test Fixtures

### Available Fixtures

The `conftest.py` file provides shared fixtures:

- `temp_dir` - Temporary directory for file operations
- `mock_config` - Mock configuration provider
- `mock_vector_store` - Mock vector store implementation
- `mock_llm_provider` - Mock LLM provider
- `mock_embedding_provider` - Mock embedding provider
- `mock_tool` - Mock tool implementation
- `sample_documents` - Sample documents for testing
- `sample_chat_messages` - Sample chat messages
- `api_client` - Flask test client

### Using Fixtures

```python
def test_with_mock_config(mock_config):
    # Use the mock configuration
    assert mock_config.get_config("llm.type") == "mock"

def test_with_temp_dir(temp_dir):
    # Use temporary directory
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("test content")
```

## Mock Objects

### Mock Components

The testing framework provides mock implementations for all major components:

- **MockConfigProvider** - Configurable mock configuration
- **MockVectorStore** - In-memory vector store simulation
- **MockLLMProvider** - Controllable LLM responses
- **MockEmbeddingProvider** - Deterministic embeddings
- **MockTool** - Configurable tool responses

### Creating Custom Mocks

```python
@pytest.fixture
def custom_llm_provider():
    responses = ["Custom response 1", "Custom response 2"]
    return MockLLMProvider(responses=responses)

def test_with_custom_llm(custom_llm_provider):
    response = custom_llm_provider.generate([])
    assert response.content == "Custom response 1"
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.api` - API-specific tests
- `@pytest.mark.tools` - Tool-specific tests

### Using Markers

```python
@pytest.mark.unit
def test_calculator_basic():
    pass

@pytest.mark.slow
@pytest.mark.integration
def test_large_document_processing():
    pass
```

**Run tests by marker:**
```bash
pytest -m "unit"
pytest -m "integration and not slow"
pytest -m "tools or api"
```

## Coverage

### Generating Coverage Reports

```bash
# Terminal coverage report
pytest --cov=. --cov-report=term-missing

# HTML coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser

# XML coverage report (for CI)
pytest --cov=. --cov-report=xml
```

### Coverage Configuration

Coverage settings are in `tox.ini`:

```ini
[coverage:run]
source = .
omit =
    tests/*
    setup.py
    .tox/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

## Continuous Integration

### GitHub Actions

The project includes GitHub Actions workflows (`.github/workflows/test.yml`):

- **test** - Run tests across Python versions
- **integration-tests** - Run integration tests
- **docker-test** - Test Docker build and deployment
- **security-scan** - Security vulnerability scanning

### Local CI Simulation

```bash
# Run tests like CI
tox

# Test specific environment
tox -e py311

# Run linting
tox -e lint

# Run type checking
tox -e type-check
```

## Writing Tests

### Best Practices

1. **Use descriptive test names**
   ```python
   def test_calculator_handles_division_by_zero_gracefully():
       pass
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert)
   ```python
   def test_agent_processes_query():
       # Arrange
       agent = GeneralAgent(config)
       query = "Hello"

       # Act
       response = agent.process_query(query)

       # Assert
       assert response.content is not None
   ```

3. **Test both success and failure cases**
   ```python
   def test_calculator_valid_expression():
       # Test success case
       pass

   def test_calculator_invalid_expression():
       # Test failure case
       pass
   ```

4. **Use fixtures for setup**
   ```python
   @pytest.fixture
   def configured_agent():
       return GeneralAgent(test_config)

   def test_agent_behavior(configured_agent):
       # Use the fixture
       pass
   ```

5. **Mock external dependencies**
   ```python
   @patch('requests.get')
   def test_web_search_tool(mock_get):
       mock_get.return_value.text = "mock response"
       # Test tool behavior
   ```

### Test Template

```python
"""
Tests for [Component Name].
"""

import pytest
from unittest.mock import Mock, patch
from [module] import [ComponentClass]


class Test[ComponentName]:
    """Test [ComponentName] functionality."""

    @pytest.fixture
    def component(self):
        """Create component instance for testing."""
        config = {"test": "config"}
        return ComponentClass(config)

    def test_component_initialization(self, component):
        """Test component initializes correctly."""
        assert component is not None
        # Add specific assertions

    def test_component_basic_functionality(self, component):
        """Test basic component functionality."""
        result = component.some_method("input")
        assert result is not None
        # Add specific assertions

    def test_component_error_handling(self, component):
        """Test component handles errors gracefully."""
        with pytest.raises(ValueError):
            component.some_method(invalid_input)

    @pytest.mark.slow
    def test_component_performance(self, component):
        """Test component performance with large inputs."""
        # Performance-related tests
        pass
```

## Debugging Tests

### Running Individual Tests

```bash
# Run single test
pytest tests/unit/test_calculator_tool.py::TestCalculatorTool::test_addition

# Run with debugging
pytest -s tests/unit/test_calculator_tool.py::test_addition

# Run with PDB on failure
pytest --pdb tests/unit/test_calculator_tool.py
```

### Using Print Debugging

```python
def test_debug_example():
    result = some_function()
    print(f"Debug: result = {result}")  # Will show with -s flag
    assert result == expected
```

### Using Logging in Tests

```python
import logging

def test_with_logging(caplog):
    with caplog.at_level(logging.INFO):
        some_function_that_logs()

    assert "expected log message" in caplog.text
```

## Performance Testing

### Timing Tests

```python
import time

@pytest.mark.slow
def test_performance():
    start_time = time.time()
    result = expensive_operation()
    duration = time.time() - start_time

    assert duration < 1.0  # Should complete within 1 second
    assert result is not None
```

### Memory Testing

```python
import psutil
import os

def test_memory_usage():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Perform operation
    large_operation()

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Assert memory increase is reasonable
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB
```

## Test Data Management

### Using Factory Boy

```python
import factory
from core.base_vector_store import Document

class DocumentFactory(factory.Factory):
    class Meta:
        model = Document

    content = factory.Faker('text')
    metadata = factory.Dict({'type': 'test'})
    doc_id = factory.Sequence(lambda n: f"doc_{n}")

# Usage in tests
def test_with_factory_data():
    doc = DocumentFactory()
    assert doc.content is not None
    assert 'type' in doc.metadata
```

### Test Data Files

```python
from pathlib import Path

def load_test_data(filename):
    """Load test data from file."""
    test_data_dir = Path(__file__).parent / "fixtures"
    return (test_data_dir / filename).read_text()

def test_with_file_data():
    sample_text = load_test_data("sample_document.txt")
    result = process_document(sample_text)
    assert result is not None
```

## Troubleshooting

### Common Issues

1. **Import errors**
   - Ensure `PYTHONPATH` includes project root
   - Check for circular imports
   - Verify test dependencies are installed

2. **Fixture not found**
   - Check `conftest.py` is in the right location
   - Verify fixture name spelling
   - Ensure fixture scope is appropriate

3. **Mock not working**
   - Check mock path is correct
   - Verify mock is applied before function call
   - Use `patch.object` for instance methods

4. **Tests pass individually but fail in suite**
   - Check for test isolation issues
   - Look for shared state problems
   - Verify fixture cleanup

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review existing test examples in the codebase
- Ask team members for guidance on test patterns
- Use `pytest --collect-only` to see discovered tests
