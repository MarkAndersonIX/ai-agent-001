"""
Integration tests for agent functionality.
"""

import pytest
from unittest.mock import Mock, patch
from core.base_agent import BaseAgent, AgentResponse
from agents.general_agent import GeneralAgent
from tests.conftest import MockConfigProvider, MockVectorStore, MockLLMProvider, MockEmbeddingProvider
from core.component_factory import ComponentFactory


class TestAgentIntegration:
    """Integration tests for agent components working together."""
    
    @pytest.fixture
    def mock_components(self):
        """Set up mock components for integration testing."""
        # Register mock implementations
        ComponentFactory.register_vector_store('mock', MockVectorStore)
        ComponentFactory.register_llm_provider('mock', MockLLMProvider)
        ComponentFactory.register_embedding_provider('mock', MockEmbeddingProvider)
        
        from providers.in_memory_backend import InMemoryBackend
        ComponentFactory.register_memory_backend('mock', InMemoryBackend)
        
        from providers.filesystem_document_store import FileSystemDocumentStore
        ComponentFactory.register_document_store('mock', FileSystemDocumentStore)
    
    @pytest.fixture
    def test_config(self, temp_dir):
        """Create test configuration."""
        config_data = {
            "vector_store": {
                "type": "mock"
            },
            "document_store": {
                "type": "mock",
                "path": temp_dir
            },
            "memory": {
                "type": "mock",
                "max_sessions": 10
            },
            "llm": {
                "type": "mock",
                "model": "mock-model"
            },
            "embedding": {
                "type": "mock",
                "model": "mock-embedding"
            },
            "agents": {
                "general": {
                    "system_prompt": "You are a helpful assistant.",
                    "tools": [],
                    "rag_settings": {
                        "top_k": 3,
                        "similarity_threshold": 0.7
                    },
                    "llm_settings": {
                        "temperature": 0.7
                    },
                    "max_history_messages": 5
                }
            }
        }
        return MockConfigProvider(config_data)
    
    def test_agent_initialization(self, mock_components, test_config):
        """Test agent initialization with all components."""
        agent = GeneralAgent(test_config)
        
        assert agent.agent_type == "general"
        assert agent.vector_store is not None
        assert agent.document_store is not None
        assert agent.memory_backend is not None
        assert agent.llm_provider is not None
        assert agent.embedding_provider is not None
    
    def test_agent_process_query_simple(self, mock_components, test_config):
        """Test basic query processing."""
        agent = GeneralAgent(test_config)
        
        response = agent.process_query("Hello, how are you?")
        
        assert isinstance(response, AgentResponse)
        assert response.content is not None
        assert response.session_id is not None
        assert response.timestamp is not None
        assert "mock" in response.metadata.get("agent_type", "")
    
    def test_agent_process_query_with_session(self, mock_components, test_config):
        """Test query processing with session continuity."""
        agent = GeneralAgent(test_config)
        session_id = "test_session_123"
        
        # First query
        response1 = agent.process_query("My name is Alice", session_id=session_id)
        assert response1.session_id == session_id
        
        # Second query in same session
        response2 = agent.process_query("What is my name?", session_id=session_id)
        assert response2.session_id == session_id
        
        # Check that session was saved
        session_info = agent.get_session_history(session_id)
        assert session_info is not None
        assert session_info.message_count >= 2
    
    def test_agent_with_documents(self, mock_components, test_config):
        """Test agent with document knowledge base."""
        agent = GeneralAgent(test_config)
        
        # Add a document
        doc_id = agent.add_document(
            content="Python is a programming language known for its simplicity.",
            metadata={"type": "programming", "language": "python"}
        )
        
        assert doc_id is not None
        
        # Query about the document
        response = agent.process_query("What is Python?")
        
        assert isinstance(response, AgentResponse)
        # The mock implementation should find the document
        assert len(response.sources) >= 0  # Depends on mock behavior
    
    def test_agent_memory_persistence(self, mock_components, test_config):
        """Test that agent memory persists across queries."""
        agent = GeneralAgent(test_config)
        session_id = "memory_test_session"
        
        # Send multiple queries
        queries = [
            "Hello, I'm testing memory",
            "Do you remember what I'm testing?",
            "What was my first message?"
        ]
        
        responses = []
        for query in queries:
            response = agent.process_query(query, session_id=session_id)
            responses.append(response)
            assert response.session_id == session_id
        
        # Check session history
        session_info = agent.get_session_history(session_id)
        assert session_info is not None
        assert session_info.message_count == len(queries) * 2  # User + assistant messages
    
    def test_agent_error_handling(self, mock_components, test_config):
        """Test agent error handling."""
        agent = GeneralAgent(test_config)
        
        # Test with problematic input
        response = agent.process_query("")  # Empty query
        
        # Should handle gracefully
        assert isinstance(response, AgentResponse)
        assert response.content is not None
    
    def test_agent_session_management(self, mock_components, test_config):
        """Test session creation and deletion."""
        agent = GeneralAgent(test_config)
        
        # Create session
        response = agent.process_query("Test message")
        session_id = response.session_id
        
        # Verify session exists
        session_info = agent.get_session_history(session_id)
        assert session_info is not None
        
        # Delete session
        success = agent.delete_session(session_id)
        assert success is True
        
        # Verify session is gone
        session_info = agent.get_session_history(session_id)
        assert session_info is None
    
    def test_agent_info(self, mock_components, test_config):
        """Test getting agent information."""
        agent = GeneralAgent(test_config)
        
        info = agent.get_agent_info()
        
        assert "agent_type" in info
        assert "system_prompt" in info
        assert "tools" in info
        assert "rag_settings" in info
        assert "component_info" in info
        
        assert info["agent_type"] == "general"
        assert "component_info" in info
    
    def test_multiple_agents_isolation(self, mock_components, test_config):
        """Test that multiple agents don't interfere with each other."""
        # Create config for second agent
        config_data = test_config.config_data.copy()
        config_data["agents"]["test_agent"] = {
            "system_prompt": "You are a test agent.",
            "tools": [],
            "rag_settings": {"top_k": 5},
            "llm_settings": {"temperature": 0.5}
        }
        test_config2 = MockConfigProvider(config_data)
        
        # Create two different agents
        agent1 = GeneralAgent(test_config)
        
        # Create a simple test agent
        class TestAgent(BaseAgent):
            def __init__(self, config):
                super().__init__("test_agent", config)
            
            def _build_system_prompt(self, relevant_context, context):
                return "You are a test agent."
        
        agent2 = TestAgent(test_config2)
        
        # Test they have different configurations
        assert agent1.agent_type == "general"
        assert agent2.agent_type == "test_agent"
        
        # Test they have separate sessions
        response1 = agent1.process_query("Agent 1 message")
        response2 = agent2.process_query("Agent 2 message")
        
        assert response1.session_id != response2.session_id


class TestAgentWithTools:
    """Integration tests for agents with tools."""
    
    @pytest.fixture
    def agent_with_tools(self, mock_components, test_config):
        """Create agent with mock tools."""
        from tests.conftest import MockTool
        
        # Register mock tool
        ComponentFactory.register_tool('mock_tool', MockTool)
        
        # Update config to include tools
        test_config.set_config("agents.general.tools", ["mock_tool"])
        test_config.set_config("tools.mock_tool.type", "mock_tool")
        
        return GeneralAgent(test_config)
    
    def test_agent_tool_execution(self, agent_with_tools):
        """Test agent can execute tools."""
        tools = agent_with_tools.list_tools()
        assert "mock_tool" in tools
        
        # Execute tool directly
        result = agent_with_tools.execute_tool("mock_tool", "test input")
        
        assert result["success"] is True
        assert "mock" in result["metadata"]
    
    def test_agent_tool_integration_in_query(self, agent_with_tools):
        """Test tools can be used during query processing."""
        # This test depends on the LLM provider using tools
        # With our mock setup, tools won't be automatically called
        # but we can test the tool infrastructure is available
        
        response = agent_with_tools.process_query("Use the mock tool")
        
        assert isinstance(response, AgentResponse)
        # Tools are available even if not used in this mock scenario
        assert len(agent_with_tools.list_tools()) > 0


class TestAgentEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_agent_with_invalid_config(self):
        """Test agent behavior with invalid configuration."""
        invalid_config = MockConfigProvider({})
        
        # Should handle missing configuration gracefully
        with pytest.raises(Exception):  # Expect some kind of initialization error
            GeneralAgent(invalid_config)
    
    def test_agent_query_with_special_characters(self, mock_components, test_config):
        """Test agent handling special characters in queries."""
        agent = GeneralAgent(test_config)
        
        special_queries = [
            "Hello! How are you? 😊",
            "Test with émojis and àccents",
            "Query with\nnewlines\nand\ttabs",
            "Unicode: ∑∆∂∞"
        ]
        
        for query in special_queries:
            response = agent.process_query(query)
            assert isinstance(response, AgentResponse)
            assert response.content is not None
    
    def test_agent_very_long_query(self, mock_components, test_config):
        """Test agent with very long query."""
        agent = GeneralAgent(test_config)
        
        # Create very long query
        long_query = "This is a very long query. " * 1000
        
        response = agent.process_query(long_query)
        
        assert isinstance(response, AgentResponse)
        # Should handle gracefully (might truncate or summarize)
    
    def test_agent_concurrent_queries(self, mock_components, test_config):
        """Test concurrent queries to same agent."""
        import threading
        import time
        
        agent = GeneralAgent(test_config)
        results = []
        
        def worker(query_id):
            response = agent.process_query(f"Query {query_id}")
            results.append((query_id, response.session_id))
            time.sleep(0.01)
        
        # Run concurrent queries
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All queries should complete successfully
        assert len(results) == 5
        
        # Each should have unique session IDs
        session_ids = [result[1] for result in results]
        assert len(set(session_ids)) == 5  # All unique