"""
Integration tests for Flask API endpoints.
"""

import json
from unittest.mock import Mock, patch

import pytest


class TestAPIIntegration:
    """Integration tests for the Flask API."""

    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get("/health")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "status" in data
        assert "timestamp" in data
        assert "agents" in data
        assert data["status"] == "healthy"

    def test_list_agents_endpoint(self, api_client):
        """Test listing available agents."""
        response = api_client.get("/agents")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "agents" in data
        assert "count" in data
        assert isinstance(data["agents"], dict)
        assert data["count"] >= 0

    @patch("agents.general_agent.GeneralAgent")
    def test_chat_endpoint_success(self, mock_agent_class, api_client):
        """Test successful chat interaction."""
        # Mock agent instance
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.content = "Hello! How can I help you?"
        mock_response.session_id = "test_session_123"
        mock_response.sources = []
        mock_response.metadata = {"model": "mock-model"}
        mock_response.timestamp.isoformat.return_value = "2024-01-01T00:00:00"

        mock_agent.process_query.return_value = mock_response
        mock_agent_class.return_value = mock_agent

        # Mock the agents dictionary in the API
        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.post(
                "/agents/general/chat",
                json={"message": "Hello", "session_id": "test_session"},
            )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "response" in data
        assert "session_id" in data
        assert data["response"] == "Hello! How can I help you?"
        assert data["session_id"] == "test_session_123"

    def test_chat_endpoint_missing_message(self, api_client):
        """Test chat endpoint with missing message."""
        response = api_client.post("/agents/general/chat", json={"session_id": "test"})

        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "required" in data["error"].lower()

    def test_chat_endpoint_invalid_agent(self, api_client):
        """Test chat endpoint with invalid agent type."""
        response = api_client.post(
            "/agents/nonexistent/chat", json={"message": "Hello"}
        )

        assert response.status_code == 404

        data = json.loads(response.data)
        assert "error" in data
        assert "not found" in data["error"].lower()

    def test_chat_endpoint_no_json(self, api_client):
        """Test chat endpoint with no JSON data."""
        response = api_client.post("/agents/general/chat")

        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data

    @patch("agents.general_agent.GeneralAgent")
    def test_get_session_endpoint(self, mock_agent_class, api_client):
        """Test getting session information."""
        # Mock agent and session info
        mock_agent = Mock()
        mock_session = Mock()
        mock_session.session_id = "test_session"
        mock_session.agent_type = "general"
        mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_session.last_active.isoformat.return_value = "2024-01-01T00:05:00"
        mock_session.message_count = 4
        mock_session.user_id = "user123"
        mock_session.metadata = {"test": "data"}

        mock_agent.get_session_history.return_value = mock_session
        mock_agent.memory_backend.load_session.return_value = []
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.get("/agents/general/sessions/test_session")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["session_id"] == "test_session"
        assert data["agent_type"] == "general"
        assert data["message_count"] == 4
        assert data["user_id"] == "user123"

    @patch("agents.general_agent.GeneralAgent")
    def test_get_session_not_found(self, mock_agent_class, api_client):
        """Test getting non-existent session."""
        mock_agent = Mock()
        mock_agent.get_session_history.return_value = None
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.get("/agents/general/sessions/nonexistent")

        assert response.status_code == 404

        data = json.loads(response.data)
        assert "error" in data
        assert "not found" in data["error"].lower()

    @patch("agents.general_agent.GeneralAgent")
    def test_delete_session_endpoint(self, mock_agent_class, api_client):
        """Test deleting a session."""
        mock_agent = Mock()
        mock_agent.delete_session.return_value = True
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.delete("/agents/general/sessions/test_session")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "message" in data
        assert "deleted" in data["message"].lower()

    @patch("agents.general_agent.GeneralAgent")
    def test_list_sessions_endpoint(self, mock_agent_class, api_client):
        """Test listing sessions for an agent."""
        mock_agent = Mock()
        mock_session = Mock()
        mock_session.session_id = "session1"
        mock_session.agent_type = "general"
        mock_session.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_session.last_active.isoformat.return_value = "2024-01-01T00:05:00"
        mock_session.message_count = 2
        mock_session.user_id = "user1"
        mock_session.metadata = {}

        mock_agent.memory_backend.list_sessions.return_value = [mock_session]
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.get("/agents/general/sessions?limit=10&offset=0")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "sessions" in data
        assert "count" in data
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["session_id"] == "session1"

    @patch("agents.general_agent.GeneralAgent")
    def test_add_document_endpoint(self, mock_agent_class, api_client):
        """Test adding a document."""
        mock_agent = Mock()
        mock_agent.add_document.return_value = "doc_123"
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.post(
                "/agents/general/documents",
                json={
                    "content": "Test document content",
                    "metadata": {"type": "test"},
                    "file_path": "/path/to/doc.txt",
                },
            )

        assert response.status_code == 201

        data = json.loads(response.data)
        assert "document_id" in data
        assert data["document_id"] == "doc_123"
        assert "message" in data

    def test_add_document_missing_content(self, api_client):
        """Test adding document without content."""
        response = api_client.post(
            "/agents/general/documents", json={"metadata": {"type": "test"}}
        )

        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "required" in data["error"].lower()

    @patch("agents.general_agent.GeneralAgent")
    def test_list_tools_endpoint(self, mock_agent_class, api_client):
        """Test listing tools for an agent."""
        from tests.conftest import MockTool

        mock_agent = Mock()
        mock_agent.list_tools.return_value = ["calculator", "web_search"]

        mock_tool = MockTool()
        mock_agent.tool_registry.get_tool.return_value = mock_tool

        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.get("/agents/general/tools")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "tools" in data
        assert "tool_details" in data
        assert "count" in data
        assert len(data["tools"]) == 2

    @patch("agents.general_agent.GeneralAgent")
    def test_execute_tool_endpoint(self, mock_agent_class, api_client):
        """Test executing a tool."""
        mock_agent = Mock()
        mock_agent.execute_tool.return_value = {
            "success": True,
            "content": "Tool executed successfully",
            "metadata": {"tool": "calculator"},
        }
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.post(
                "/agents/general/tools/calculator",
                json={"input": "2 + 2", "parameters": {}},
            )

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert "content" in data
        assert "metadata" in data

    def test_execute_tool_missing_input(self, api_client):
        """Test executing tool without input."""
        response = api_client.post(
            "/agents/general/tools/calculator", json={"parameters": {}}
        )

        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "required" in data["error"].lower()

    def test_get_config_endpoint(self, api_client):
        """Test getting sanitized configuration."""
        response = api_client.get("/config")

        assert response.status_code == 200

        data = json.loads(response.data)
        assert "vector_store" in data
        assert "memory" in data
        assert "llm" in data
        assert "api" in data
        assert "agents" in data

        # Should not contain sensitive information
        assert "api_key" not in str(data)

    def test_404_endpoint(self, api_client):
        """Test 404 error handling."""
        response = api_client.get("/nonexistent/endpoint")

        assert response.status_code == 404

        data = json.loads(response.data)
        assert "error" in data
        assert "not found" in data["error"].lower()

    def test_405_method_not_allowed(self, api_client):
        """Test 405 error handling."""
        response = api_client.patch("/health")  # PATCH not allowed on health

        assert response.status_code == 405

        data = json.loads(response.data)
        assert "error" in data
        assert "not allowed" in data["error"].lower()


class TestAPIErrorHandling:
    """Test API error handling scenarios."""

    @patch("agents.general_agent.GeneralAgent")
    def test_chat_endpoint_agent_error(self, mock_agent_class, api_client):
        """Test chat endpoint when agent raises exception."""
        mock_agent = Mock()
        mock_agent.process_query.side_effect = Exception("Agent error")
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.post(
                "/agents/general/chat", json={"message": "Hello"}
            )

        assert response.status_code == 500

        data = json.loads(response.data)
        assert "error" in data
        assert "internal server error" in data["error"].lower()

    @patch("agents.general_agent.GeneralAgent")
    def test_add_document_agent_error(self, mock_agent_class, api_client):
        """Test add document endpoint when agent raises exception."""
        mock_agent = Mock()
        mock_agent.add_document.side_effect = Exception("Document error")
        mock_agent_class.return_value = mock_agent

        with patch("api.server.AgentAPI._initialize_agents") as mock_init:
            mock_init.return_value = {"general": mock_agent}

            response = api_client.post(
                "/agents/general/documents",
                json={"content": "Test content", "metadata": {}},
            )

        assert response.status_code == 500

        data = json.loads(response.data)
        assert "error" in data

    def test_invalid_json(self, api_client):
        """Test endpoints with invalid JSON."""
        response = api_client.post(
            "/agents/general/chat", data="invalid json", content_type="application/json"
        )

        assert response.status_code == 400


class TestAPIValidation:
    """Test API input validation."""

    def test_chat_empty_message(self, api_client):
        """Test chat with empty message."""
        response = api_client.post("/agents/general/chat", json={"message": ""})

        assert response.status_code == 400

    def test_chat_whitespace_only_message(self, api_client):
        """Test chat with whitespace-only message."""
        response = api_client.post("/agents/general/chat", json={"message": "   "})

        assert response.status_code == 400

    def test_add_document_empty_content(self, api_client):
        """Test adding document with empty content."""
        response = api_client.post(
            "/agents/general/documents", json={"content": "", "metadata": {}}
        )

        assert response.status_code == 400

    def test_execute_tool_empty_input(self, api_client):
        """Test executing tool with empty input."""
        response = api_client.post(
            "/agents/general/tools/calculator", json={"input": ""}
        )

        assert response.status_code == 400


class TestAPICORS:
    """Test CORS functionality."""

    def test_cors_headers_present(self, api_client):
        """Test that CORS headers are present."""
        response = api_client.options("/health")

        # CORS headers should be present if enabled
        # This test depends on Flask-CORS configuration
        assert response.status_code in [200, 204]  # OPTIONS requests


class TestAPIContentTypes:
    """Test API content type handling."""

    def test_json_content_type_required(self, api_client):
        """Test that JSON content type is required for POST requests."""
        response = api_client.post(
            "/agents/general/chat",
            data="message=hello",
            content_type="application/x-www-form-urlencoded",
        )

        # Should expect JSON
        assert response.status_code == 400

    def test_json_response_content_type(self, api_client):
        """Test that responses have correct content type."""
        response = api_client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.content_type
