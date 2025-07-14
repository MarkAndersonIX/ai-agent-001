"""
Pytest configuration and shared fixtures for AI Agent Base tests.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock

import pytest

from core.base_config_provider import ConfigProvider
from core.base_document_store import DocumentStore, StoredDocument
from core.base_embedding_provider import EmbeddingProvider, EmbeddingResult
from core.base_llm_provider import LLMMessage, LLMProvider, LLMResponse
from core.base_memory_backend import ChatMessage, ConversationSession, MemoryBackend
from core.base_tool import BaseTool, ToolResult
from core.base_vector_store import Document, VectorStore


class MockConfigProvider(ConfigProvider):
    """Mock configuration provider for testing."""

    def __init__(self, config_data: Dict[str, Any] = None):
        self.config_data = config_data or {}

    def get_config(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        current = self.config_data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def set_config(self, key: str, value: Any) -> bool:
        keys = key.split(".")
        current = self.config_data

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        return True

    def has_config(self, key: str) -> bool:
        return self.get_config(key, object()) is not object()

    def get_section(self, section: str) -> Dict[str, Any]:
        return self.get_config(section, {})

    def list_keys(self, prefix=None):
        keys = []
        self._collect_keys(self.config_data, "", keys)
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return keys

    def _collect_keys(self, data, current_path, keys):
        for key, value in data.items():
            full_key = f"{current_path}.{key}" if current_path else key
            keys.append(full_key)
            if isinstance(value, dict):
                self._collect_keys(value, full_key, keys)


class MockVectorStore(VectorStore):
    """Mock vector store for testing."""

    def __init__(self):
        self.documents = {}
        self.next_id = 1

    def add_documents(self, documents):
        doc_ids = []
        for doc in documents:
            doc_id = doc.doc_id or f"doc_{self.next_id}"
            self.documents[doc_id] = doc
            doc_ids.append(doc_id)
            self.next_id += 1
        return doc_ids

    def similarity_search(self, query, k=5, filters=None):
        from core.base_vector_store import SearchResult

        results = []

        for doc_id, doc in list(self.documents.items())[:k]:
            if filters:
                match = True
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue

            # Simple similarity based on query presence in content
            score = 0.8 if query.lower() in doc.content.lower() else 0.3
            results.append(SearchResult(document=doc, score=score))

        return sorted(results, key=lambda x: x.score, reverse=True)

    def delete_documents(self, doc_ids):
        for doc_id in doc_ids:
            self.documents.pop(doc_id, None)
        return True

    def get_document(self, doc_id):
        return self.documents.get(doc_id)

    def list_documents(self, filters=None, limit=None, offset=None):
        docs = list(self.documents.values())
        if filters:
            filtered_docs = []
            for doc in docs:
                match = True
                for key, value in filters.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
            docs = filtered_docs

        if offset:
            docs = docs[offset:]
        if limit:
            docs = docs[:limit]

        return docs

    def count_documents(self, filters=None):
        return len(self.list_documents(filters))


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, responses=None):
        self.responses = responses or ["This is a mock response."]
        self.call_count = 0

    def generate(self, messages, **kwargs):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        return LLMResponse(
            content=response,
            model="mock-model",
            usage={"tokens": len(response.split())},
            metadata={"mock": True},
        )

    def generate_stream(self, messages, **kwargs):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        for word in response.split():
            yield word + " "

    def count_tokens(self, text):
        return len(text.split())

    def get_model_info(self):
        return {"name": "mock-model", "context_length": 4096}

    def validate_config(self, config):
        return True

    def supports_streaming(self):
        return True

    def supports_function_calling(self):
        return False


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""

    def embed_text(self, text, **kwargs):
        # Simple mock embedding based on text hash
        import hashlib

        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        return [float(hash_val % 100) / 100 for _ in range(10)]

    def embed_documents(self, texts, **kwargs):
        embeddings = [self.embed_text(text) for text in texts]

        return EmbeddingResult(
            embeddings=embeddings,
            model="mock-embedding-model",
            usage={"tokens": sum(len(text.split()) for text in texts)},
        )

    def get_embedding_dimension(self):
        return 10

    def get_model_info(self):
        return {"name": "mock-embedding-model", "dimension": 10}

    def validate_config(self, config):
        return True

    def get_max_input_length(self):
        return 1000


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(
        self, name="mock_tool", description="Mock tool for testing", responses=None
    ):
        self._name = name
        self._description = description
        self.responses = responses or ["Mock tool executed successfully"]
        self.call_count = 0
        self.last_input = None
        self.last_kwargs = None

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    def execute(self, input_text, **kwargs):
        self.last_input = input_text
        self.last_kwargs = kwargs

        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1

        return ToolResult(
            success=True,
            content=response,
            metadata={"mock": True, "call_count": self.call_count},
        )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config():
    """Create a mock configuration for tests."""
    config_data = {
        "vector_store": {"type": "mock", "path": "./test_data/vectors"},
        "document_store": {"type": "mock", "path": "./test_data/documents"},
        "memory": {"type": "mock", "max_sessions": 100},
        "llm": {"type": "mock", "model": "mock-model", "temperature": 0.7},
        "embedding": {"type": "mock", "model": "mock-embedding"},
        "agents": {
            "test_agent": {
                "system_prompt": "You are a test agent.",
                "tools": ["mock_tool"],
                "rag_settings": {"top_k": 5, "similarity_threshold": 0.7},
                "llm_settings": {"temperature": 0.5},
            }
        },
        "tools": {"mock_tool": {"type": "mock_tool"}},
    }

    return MockConfigProvider(config_data)


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    return MockVectorStore()


@pytest.fixture
def mock_llm_provider():
    """Create a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider."""
    return MockEmbeddingProvider()


@pytest.fixture
def mock_tool():
    """Create a mock tool."""
    return MockTool()


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            content="This is a test document about Python programming.",
            metadata={"type": "programming", "language": "python"},
            doc_id="doc1",
        ),
        Document(
            content="This document discusses machine learning concepts.",
            metadata={"type": "ml", "topic": "concepts"},
            doc_id="doc2",
        ),
        Document(
            content="Web development with Flask and FastAPI.",
            metadata={"type": "web", "framework": "flask"},
            doc_id="doc3",
        ),
    ]


@pytest.fixture
def sample_chat_messages():
    """Create sample chat messages for testing."""
    now = datetime.now()

    return [
        ChatMessage(role="user", content="Hello", timestamp=now),
        ChatMessage(role="assistant", content="Hi there!", timestamp=now),
        ChatMessage(role="user", content="How are you?", timestamp=now),
        ChatMessage(role="assistant", content="I'm doing well, thanks!", timestamp=now),
    ]


@pytest.fixture
def api_client():
    """Create a test client for the Flask API."""
    from api.server import create_app

    # Create app with test configuration
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


# Pytest markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "tools: mark test as tool test")
