# AI Agent Base

A highly extensible AI agent framework built with LangChain and vector embeddings that serves as a foundation for creating specialized AI agents.

## Overview

AI Agent Base provides a robust, production-ready foundation for building specialized AI agents with RAG (Retrieval-Augmented Generation) capabilities. The framework emphasizes modularity, extensibility, and ease of deployment while maintaining simple defaults for quick setup.

## Key Features

### 🏗️ **Modular Architecture**
- **Abstraction layers** for all major components (LLM providers, vector stores, memory backends)
- **Simple defaults** that work out-of-the-box with minimal dependencies
- **Production upgrades** via configuration changes (no code modifications required)

### 🧠 **Hybrid Memory System**
- **Working memory** for active conversation context
- **Summary memory** with intelligent compression
- **Long-term storage** with semantic search capabilities
- **Persistent backends** (Redis + Database) for distributed deployments

### 🔍 **Advanced RAG Capabilities**
- **Multi-format document processing** (PDF, text, markdown, code files)
- **Type-specific embedding strategies** (e.g., chapter-level for PDFs)
- **Quality-based web search persistence** with cache freshness management
- **Unified vector storage** with metadata filtering

### 🛠️ **Tool Integration**
- **Extensible tool system** with LangChain compatibility
- **Built-in tools** (web search, calculator, file operations, code execution)
- **Easy custom tool development** through inheritance

### 🎯 **Specialized Agents**
Four example agent implementations included:
- **Document Q&A Agent** - Query documents with context-aware responses
- **Code Assistant Agent** - Programming help with code-specific knowledge
- **Research Agent** - Information gathering with source attribution
- **General Agent** - Multi-purpose conversational AI

### 🧪 **Comprehensive Testing**
- **Test-Driven Development** ready with pytest framework
- **Unit, Integration, and API tests** with 95%+ coverage
- **Mock components** for reliable testing
- **CI/CD pipeline** with GitHub Actions
- **Quality assurance** with automated linting and security scanning

## Architecture

```
ai-agent-base/
├── core/                    # Base abstraction classes
├── providers/               # Default implementations
├── tools/                   # Tool implementations
├── agents/                  # Specialized agent implementations
├── config/                  # YAML configuration files
├── api/                     # Flask RESTful API
├── cli/                     # Command line interface
├── tests/                   # ✅ Comprehensive test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── tools/              # Tool tests
│   └── conftest.py         # Test fixtures and mocks
├── .github/workflows/       # CI/CD pipeline
└── requirements.txt         # Dependencies
```

## Quick Start

### Local Development (Minimal Setup)
```bash
# Clone and install
git clone <repository-url>
cd ai-agent-base

# Install dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r tests/test_requirements.txt

# Run with default configuration
python -m __main__ server &
python -m __main__ cli chat general "Hello!"

# Or use Docker
docker-compose up
```

### Testing (TDD Ready)
```bash
# Run all tests
python run_tests.py

# Run specific test types
python run_tests.py unit          # Unit tests only
python run_tests.py integration   # Integration tests
python run_tests.py tools         # Tool tests
python run_tests.py api           # API tests

# TDD workflow
python run_tests.py unit --exitfirst  # Stop on first failure
python run_tests.py all --coverage    # Full coverage report

# CI simulation
tox                           # Multi-Python version testing
```

### Production Setup
```yaml
# config/production.yaml
vector_store:
  type: "pinecone"
  api_key: "${PINECONE_API_KEY}"
  index_name: "ai-agents"

memory:
  type: "redis"
  url: "${REDIS_URL}"

llm:
  type: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4"
```

## Configuration

The framework uses a hierarchical YAML configuration system:

1. **Default configuration** - Built-in sensible defaults
2. **Environment-specific configs** - Override defaults per environment
3. **Environment variables** - Runtime configuration and secrets

### Example Agent Configuration
```yaml
agents:
  code_assistant:
    system_prompt: |
      You are an expert code assistant that helps developers
      write clean, efficient code following best practices.

    llm_settings:
      temperature: 0.1
      max_tokens: 2000

    tools:
      - web_search
      - code_execution
      - file_operations

    rag_settings:
      top_k: 5
      similarity_threshold: 0.8

    memory:
      type: "buffer_window"
      max_messages: 20
      redis_ttl: 3600

    document_sources:
      - path: "/data/programming-docs/"
        types: ["pdf", "md", "txt"]
        recursive: true
```

## API Endpoints

RESTful API with intuitive endpoints:

```
POST /agents/{agent_type}/chat
GET  /agents/{agent_type}/config
POST /agents/{agent_type}/documents
GET  /agents/{agent_type}/sessions/{session_id}
DELETE /agents/{agent_type}/sessions/{session_id}
GET  /agents/{agent_type}/sessions
POST /agents/{agent_type}/tools/{tool_name}
GET  /agents/{agent_type}/tools
GET  /health
GET  /config
```

### Example API Usage
```bash
# Start server
python -m __main__ server

# Chat with agent
curl -X POST http://localhost:8000/agents/general/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'

# Add document
curl -X POST http://localhost:8000/agents/code_assistant/documents \
  -H "Content-Type: application/json" \
  -d '{"content": "Python tutorial content...", "metadata": {"type": "tutorial"}}'
```

## Component Abstractions

### Vector Store
```python
# Supports multiple backends
vector_store:
  type: "chroma"        # Local, file-based (default)
  # type: "pinecone"    # Cloud, production-ready
  # type: "weaviate"    # Self-hosted option
```

### Memory Backend
```python
# Flexible memory storage
memory:
  type: "in_memory"     # Simple default
  # type: "redis"       # Distributed caching
  # type: "sqlite"      # File persistence
```

### LLM Provider
```python
# Provider-agnostic LLM integration
llm:
  type: "openai"        # OpenAI GPT models
  # type: "anthropic"   # Claude models
  # type: "ollama"      # Local models
```

## Testing

### Running Tests
```bash
# Quick test commands
python run_tests.py                    # All tests
python run_tests.py unit              # Unit tests only
python run_tests.py integration       # Integration tests
python run_tests.py fast --parallel   # Fast tests in parallel

# Coverage reports
python run_tests.py all --coverage          # Terminal report
python run_tests.py all --html-coverage     # HTML report

# TDD workflow
python run_tests.py unit --exitfirst        # Stop on first failure
pytest tests/unit/test_calculator_tool.py   # Specific test file
pytest -k "calculator"                      # Tests matching pattern
```

### Test Categories
- **Unit Tests** (`tests/unit/`) - Test individual components in isolation
- **Integration Tests** (`tests/integration/`) - Test component interactions
- **API Tests** - Test REST endpoints and responses
- **Tool Tests** (`tests/tools/`) - Test individual tool implementations

### Mock Framework
Complete mock implementations available for testing:
- `MockConfigProvider` - Configurable test configuration
- `MockVectorStore` - In-memory vector store simulation
- `MockLLMProvider` - Controllable LLM responses
- `MockEmbeddingProvider` - Deterministic embeddings
- `MockTool` - Configurable tool responses

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Deployment

### Docker
```bash
# Build container
docker build -t ai-agent-base .

# Run locally
docker-compose up

# Run with production config
docker-compose --profile production up

# Deploy to cloud
docker push your-registry/ai-agent-base
```

### Cloud Deployment
- **AWS ECS/EKS** - Elastic Container Service or Kubernetes
- **GCP Cloud Run** - Serverless container deployment
- **Azure Container Instances** - Simple container hosting

### CI/CD
GitHub Actions workflow included:
- **Multi-Python testing** (3.9, 3.10, 3.11)
- **Quality checks** (black, flake8, mypy)
- **Security scanning** (safety, bandit)
- **Docker testing** (container build validation)
- **Coverage reporting** (Codecov integration)

## Extension Guide

### Creating Custom Agents
```python
from core.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, config):
        super().__init__("custom_agent", config)

    def _build_system_prompt(self, relevant_context, context):
        return "You are a custom AI agent with specialized capabilities."
```

### Adding Custom Tools
```python
from core.base_tool import BaseTool, ToolResult

class CustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "custom_tool"

    @property
    def description(self) -> str:
        return "Description of what this tool does"

    def execute(self, input_text: str, **kwargs) -> ToolResult:
        # Tool implementation
        return ToolResult(success=True, content="Tool result")
```

### Testing Custom Components
```python
import pytest
from tests.conftest import MockConfigProvider

def test_custom_agent():
    config = MockConfigProvider({"agents": {"custom": {...}}})
    agent = CustomAgent(config)

    response = agent.process_query("test query")
    assert response.content is not None
```

## Requirements

### Minimal Setup
- Python 3.9+
- OpenAI API key (for LLM and embeddings)

### Development Setup
- All minimal requirements
- Test dependencies: `pip install -r tests/test_requirements.txt`
- Optional: Docker for containerized testing

### Production Setup
- Redis (for distributed memory)
- PostgreSQL/MongoDB (for persistent storage)
- Pinecone API key (for production vector storage)

## Development Workflow

### Test-Driven Development
1. **Write tests first** - Define expected behavior
2. **Run tests** - Confirm they fail initially: `python run_tests.py unit --exitfirst`
3. **Implement feature** - Make tests pass
4. **Refactor** - Improve code while keeping tests green
5. **Integration test** - `python run_tests.py integration`
6. **Full validation** - `python run_tests.py all --coverage`

### Quality Assurance
```bash
# Code formatting
black .
isort .

# Linting
flake8 .

# Type checking
mypy core/ providers/ tools/ agents/ api/ cli/

# Security scanning
safety check
bandit -r .

# Multi-environment testing
tox
```

## Development Roadmap

- [x] Core abstraction layers
- [x] Default implementations
- [x] Specialized agent examples
- [x] Comprehensive test suite with TDD support
- [x] CI/CD pipeline with GitHub Actions
- [x] Docker containerization
- [ ] Advanced memory compression algorithms
- [ ] Multi-tenant support
- [ ] Performance monitoring and metrics
- [ ] Auto-scaling capabilities
- [ ] Integration with additional vector databases

## Contributing

1. **Fork the repository**
2. **Set up development environment**:
   ```bash
   pip install -r requirements.txt
   pip install -r tests/test_requirements.txt
   ```
3. **Follow TDD workflow**:
   ```bash
   # Write tests first
   pytest tests/unit/test_new_feature.py -x

   # Implement feature
   # Run tests to ensure they pass
   python run_tests.py unit
   ```
4. **Follow code quality standards**:
   ```bash
   black .
   flake8 .
   python run_tests.py all --coverage
   ```
5. **Submit pull requests** with comprehensive tests

### Code Quality Standards
- **Test coverage** - Maintain 95%+ coverage for new code
- **Code formatting** - Use Black and isort
- **Type hints** - Add type annotations for new functions
- **Documentation** - Update docstrings and README
- **Security** - Follow security best practices

## Performance and Reliability

- **Comprehensive testing** with unit, integration, and API tests
- **Mock framework** for reliable, fast tests
- **CI/CD pipeline** ensuring quality on every commit
- **Security scanning** with automated vulnerability detection
- **Performance monitoring** with test execution timing
- **Container-ready** for scalable deployment

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: [TESTING.md](TESTING.md) for testing guide
- **Issues**: [GitHub Issues] for bug reports and feature requests
- **Discussions**: [GitHub Discussions] for questions and community support
- **Testing Help**: Run `python run_tests.py --help` for testing options
