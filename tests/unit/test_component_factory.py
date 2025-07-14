"""
Unit tests for ComponentFactory.
"""

import pytest
from core.component_factory import ComponentFactory
from core.base_vector_store import VectorStore
from core.base_memory_backend import MemoryBackend
from core.base_config_provider import ConfigProvider


class TestComponentFactory:
    """Test ComponentFactory functionality."""

    def test_register_vector_store(self):
        """Test registering a vector store implementation."""

        class TestVectorStore(VectorStore):
            def __init__(self, config):
                pass

            def add_documents(self, documents):
                return []

            def similarity_search(self, query, k=5, filters=None):
                return []

            def delete_documents(self, doc_ids):
                return True

            def get_document(self, doc_id):
                return None

            def list_documents(self, filters=None, limit=None, offset=None):
                return []

            def count_documents(self, filters=None):
                return 0

        # Register the implementation
        ComponentFactory.register_vector_store("test_vector", TestVectorStore)

        # Check it's in the registry
        assert "test_vector" in ComponentFactory._vector_store_registry
        assert ComponentFactory._vector_store_registry["test_vector"] == TestVectorStore

    def test_register_memory_backend(self):
        """Test registering a memory backend implementation."""

        class TestMemoryBackend(MemoryBackend):
            def __init__(self, config):
                pass

            def save_session(
                self, session_id, messages, agent_type, user_id=None, metadata=None
            ):
                return True

            def load_session(self, session_id):
                return []

            def get_session_info(self, session_id):
                return None

            def delete_session(self, session_id):
                return True

            def list_sessions(
                self, user_id=None, agent_type=None, limit=None, offset=None
            ):
                return []

            def append_message(self, session_id, message, agent_type):
                return True

            def get_recent_messages(self, session_id, limit=10):
                return []

            def count_sessions(self, user_id=None, agent_type=None):
                return 0

            def cleanup_expired_sessions(self, max_age_hours=24):
                return 0

        ComponentFactory.register_memory_backend("test_memory", TestMemoryBackend)

        assert "test_memory" in ComponentFactory._memory_backend_registry
        assert (
            ComponentFactory._memory_backend_registry["test_memory"]
            == TestMemoryBackend
        )

    def test_create_vector_store_unknown_type(self):
        """Test creating vector store with unknown type raises error."""
        config = {"type": "unknown_vector_store_type"}

        with pytest.raises(ValueError, match="Unknown vector store type"):
            ComponentFactory.create_vector_store(config)

    def test_create_memory_backend_with_default(self):
        """Test creating memory backend with default type."""

        # Register a test implementation for the default
        class TestMemoryBackend(MemoryBackend):
            def __init__(self, config):
                self.config = config

            def save_session(
                self, session_id, messages, agent_type, user_id=None, metadata=None
            ):
                return True

            def load_session(self, session_id):
                return []

            def get_session_info(self, session_id):
                return None

            def delete_session(self, session_id):
                return True

            def list_sessions(
                self, user_id=None, agent_type=None, limit=None, offset=None
            ):
                return []

            def append_message(self, session_id, message, agent_type):
                return True

            def get_recent_messages(self, session_id, limit=10):
                return []

            def count_sessions(self, user_id=None, agent_type=None):
                return 0

            def cleanup_expired_sessions(self, max_age_hours=24):
                return 0

        ComponentFactory.register_memory_backend("in_memory", TestMemoryBackend)

        # Create with default type (should be 'in_memory')
        config = {}
        backend = ComponentFactory.create_memory_backend(config)

        assert isinstance(backend, TestMemoryBackend)
        assert backend.config == config

    def test_create_config_provider_default(self):
        """Test creating default config provider."""
        config_provider = ComponentFactory.create_config_provider()

        assert isinstance(config_provider, ConfigProvider)
        # Should be a CompositeConfigProvider
        assert hasattr(config_provider, "providers")

    def test_list_available_implementations(self):
        """Test listing available implementations."""
        implementations = ComponentFactory.list_available_implementations()

        assert isinstance(implementations, dict)
        assert "vector_stores" in implementations
        assert "memory_backends" in implementations
        assert "config_providers" in implementations
        assert "llm_providers" in implementations
        assert "embedding_providers" in implementations
        assert "tools" in implementations

        # Check that our registered test implementations are listed
        assert "test_vector" in implementations["vector_stores"]
        assert "test_memory" in implementations["memory_backends"]

    def test_create_tool_registry(self):
        """Test creating tool registry with configurations."""
        from core.base_tool import ToolRegistry, BaseTool, ToolResult

        class TestTool(BaseTool):
            def __init__(self, config):
                self.config = config

            @property
            def name(self):
                return "test_tool"

            @property
            def description(self):
                return "Test tool"

            def execute(self, input_text, **kwargs):
                return ToolResult(success=True, content="Test result")

        ComponentFactory.register_tool("test_tool", TestTool)

        tool_configs = [
            {"type": "test_tool", "param1": "value1"},
            {"type": "unknown_tool", "param2": "value2"},  # Should be ignored
        ]

        registry = ComponentFactory.create_tool_registry(tool_configs)

        assert isinstance(registry, ToolRegistry)
        assert "test_tool" in registry.list_tools()
        assert len(registry.list_tools()) == 1  # Unknown tool should be ignored

    def test_component_factory_state_isolation(self):
        """Test that ComponentFactory registrations don't interfere between tests."""
        # This test ensures our test setup doesn't pollute other tests
        initial_implementations = ComponentFactory.list_available_implementations()

        # Register a temporary implementation
        class TempVectorStore(VectorStore):
            def __init__(self, config):
                pass

            def add_documents(self, documents):
                return []

            def similarity_search(self, query, k=5, filters=None):
                return []

            def delete_documents(self, doc_ids):
                return True

            def get_document(self, doc_id):
                return None

            def list_documents(self, filters=None, limit=None, offset=None):
                return []

            def count_documents(self, filters=None):
                return 0

        ComponentFactory.register_vector_store("temp_vector", TempVectorStore)

        # Verify it was registered
        assert "temp_vector" in ComponentFactory._vector_store_registry

        # Note: In a real test suite, you might want to add cleanup
        # or use fixtures to ensure test isolation


class TestComponentFactoryConfigCreation:
    """Test configuration-driven component creation."""

    def test_create_with_valid_config(self, mock_config):
        """Test creating components with valid configuration."""
        # This would work if we had registered mock implementations
        # For now, we test the config retrieval logic

        vector_config = mock_config.get_section("vector_store")
        assert vector_config["type"] == "mock"
        assert vector_config["path"] == "./test_data/vectors"

        memory_config = mock_config.get_section("memory")
        assert memory_config["type"] == "mock"
        assert memory_config["max_sessions"] == 100

    def test_config_error_handling(self):
        """Test error handling in component creation."""
        # Test with missing configuration
        with pytest.raises(ValueError):
            ComponentFactory.create_vector_store({"type": "nonexistent"})

        with pytest.raises(ValueError):
            ComponentFactory.create_memory_backend({"type": "nonexistent"})


# Example of equivalent unittest.TestCase approach (commented out)
"""
import unittest
from core.component_factory import ComponentFactory

class TestComponentFactoryUnittest(unittest.TestCase):
    '''Example unittest.TestCase version of the same tests'''
    
    def setUp(self):
        '''Set up test fixtures.'''
        self.initial_registrations = ComponentFactory.list_available_implementations()
    
    def tearDown(self):
        '''Clean up after tests.'''
        # In a real implementation, you might restore initial state
        pass
    
    def test_register_vector_store(self):
        '''Test registering vector store implementation.'''
        class TestVectorStore:
            def __init__(self, config): pass
        
        ComponentFactory.register_vector_store('test_vector', TestVectorStore)
        
        self.assertIn('test_vector', ComponentFactory._vector_store_registry)
        self.assertEqual(
            ComponentFactory._vector_store_registry['test_vector'], 
            TestVectorStore
        )
    
    def test_create_vector_store_unknown_type(self):
        '''Test creating unknown vector store type raises ValueError.'''
        config = {'type': 'unknown_type'}
        
        with self.assertRaises(ValueError) as context:
            ComponentFactory.create_vector_store(config)
        
        self.assertIn("Unknown vector store type", str(context.exception))

if __name__ == '__main__':
    unittest.main()
"""
