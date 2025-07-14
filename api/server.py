from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from core.base_config_provider import (
    ConfigProvider,
    CompositeConfigProvider,
    EnvironmentConfigProvider,
)
from providers.yaml_config_provider import (
    YAMLConfigProvider,
    create_default_config_file,
)
from core.component_factory import ComponentFactory
from agents.general_agent import GeneralAgent
from agents.code_assistant_agent import CodeAssistantAgent
from agents.research_agent import ResearchAgent
from agents.document_qa_agent import DocumentQAAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentAPI:
    """Flask API for AI Agent Base."""

    def __init__(self, config: ConfigProvider):
        """Initialize the API server."""
        self.config = config
        self.app = Flask(__name__)

        # Configure CORS
        api_config = self.config.get_section("api")
        if api_config.get("cors_enabled", True):
            CORS(self.app)

        # Initialize agents
        self.agents = self._initialize_agents()

        # Register routes
        self._register_routes()

        logger.info("Agent API initialized successfully")

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all available agents."""
        agents = {}

        try:
            # Initialize each agent type
            agent_classes = {
                "general": GeneralAgent,
                "code_assistant": CodeAssistantAgent,
                "research_agent": ResearchAgent,
                "document_qa": DocumentQAAgent,
            }

            for agent_type, agent_class in agent_classes.items():
                try:
                    agents[agent_type] = agent_class(self.config)
                    logger.info(f"Initialized {agent_type} agent")
                except Exception as e:
                    logger.error(f"Failed to initialize {agent_type} agent: {str(e)}")

            return agents

        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            return {}

    def _register_routes(self) -> None:
        """Register API routes."""

        @self.app.route("/health", methods=["GET"])
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "agents": list(self.agents.keys()),
                }
            )

        @self.app.route("/agents", methods=["GET"])
        def list_agents():
            """List available agents."""
            agent_info = {}
            for agent_type, agent in self.agents.items():
                agent_info[agent_type] = agent.get_agent_info()

            return jsonify({"agents": agent_info, "count": len(agent_info)})

        @self.app.route("/agents/<agent_type>/chat", methods=["POST"])
        def chat_with_agent(agent_type):
            """Chat with a specific agent."""
            try:
                # Validate agent type
                if agent_type not in self.agents:
                    return (
                        jsonify(
                            {
                                "error": f'Agent type "{agent_type}" not found',
                                "available_agents": list(self.agents.keys()),
                            }
                        ),
                        404,
                    )

                # Get request data
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                message = data.get("message")
                if not message:
                    return jsonify({"error": "Message is required"}), 400

                session_id = data.get("session_id")
                user_id = data.get("user_id")
                context = data.get("context", {})

                # Process query with agent
                agent = self.agents[agent_type]
                response = agent.process_query(
                    query=message,
                    session_id=session_id,
                    user_id=user_id,
                    context=context,
                )

                return jsonify(
                    {
                        "response": response.content,
                        "session_id": response.session_id,
                        "sources": response.sources,
                        "metadata": response.metadata,
                        "timestamp": response.timestamp.isoformat(),
                    }
                )

            except Exception as e:
                logger.error(f"Error in chat endpoint: {str(e)}")
                logger.error(traceback.format_exc())
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route("/agents/<agent_type>/sessions/<session_id>", methods=["GET"])
        def get_session(agent_type, session_id):
            """Get session information."""
            try:
                if agent_type not in self.agents:
                    return (
                        jsonify({"error": f'Agent type "{agent_type}" not found'}),
                        404,
                    )

                agent = self.agents[agent_type]
                session_info = agent.get_session_history(session_id)

                if not session_info:
                    return jsonify({"error": "Session not found"}), 404

                # Load session messages
                messages = agent.memory_backend.load_session(session_id)

                return jsonify(
                    {
                        "session_id": session_info.session_id,
                        "agent_type": session_info.agent_type,
                        "created_at": session_info.created_at.isoformat(),
                        "last_active": session_info.last_active.isoformat(),
                        "message_count": session_info.message_count,
                        "user_id": session_info.user_id,
                        "metadata": session_info.metadata,
                        "messages": [
                            {
                                "role": msg.role,
                                "content": msg.content,
                                "timestamp": msg.timestamp.isoformat(),
                                "metadata": msg.metadata,
                            }
                            for msg in (messages or [])
                        ],
                    }
                )

            except Exception as e:
                logger.error(f"Error getting session: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route(
            "/agents/<agent_type>/sessions/<session_id>", methods=["DELETE"]
        )
        def delete_session(agent_type, session_id):
            """Delete a session."""
            try:
                if agent_type not in self.agents:
                    return (
                        jsonify({"error": f'Agent type "{agent_type}" not found'}),
                        404,
                    )

                agent = self.agents[agent_type]
                success = agent.delete_session(session_id)

                if success:
                    return jsonify({"message": "Session deleted successfully"})
                else:
                    return (
                        jsonify({"error": "Session not found or could not be deleted"}),
                        404,
                    )

            except Exception as e:
                logger.error(f"Error deleting session: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route("/agents/<agent_type>/sessions", methods=["GET"])
        def list_sessions(agent_type):
            """List sessions for an agent."""
            try:
                if agent_type not in self.agents:
                    return (
                        jsonify({"error": f'Agent type "{agent_type}" not found'}),
                        404,
                    )

                # Get query parameters
                user_id = request.args.get("user_id")
                limit = request.args.get("limit", 50, type=int)
                offset = request.args.get("offset", 0, type=int)

                agent = self.agents[agent_type]
                sessions = agent.memory_backend.list_sessions(
                    user_id=user_id, agent_type=agent_type, limit=limit, offset=offset
                )

                return jsonify(
                    {
                        "sessions": [
                            {
                                "session_id": session.session_id,
                                "agent_type": session.agent_type,
                                "created_at": session.created_at.isoformat(),
                                "last_active": session.last_active.isoformat(),
                                "message_count": session.message_count,
                                "user_id": session.user_id,
                                "metadata": session.metadata,
                            }
                            for session in sessions
                        ],
                        "count": len(sessions),
                        "limit": limit,
                        "offset": offset,
                    }
                )

            except Exception as e:
                logger.error(f"Error listing sessions: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route("/agents/<agent_type>/documents", methods=["POST"])
        def add_document(agent_type):
            """Add a document to an agent's knowledge base."""
            try:
                if agent_type not in self.agents:
                    return (
                        jsonify({"error": f'Agent type "{agent_type}" not found'}),
                        404,
                    )

                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                content = data.get("content")
                if not content:
                    return jsonify({"error": "Content is required"}), 400

                metadata = data.get("metadata", {})
                file_path = data.get("file_path")

                agent = self.agents[agent_type]
                doc_id = agent.add_document(content, metadata, file_path)

                return (
                    jsonify(
                        {
                            "document_id": doc_id,
                            "message": "Document added successfully",
                        }
                    ),
                    201,
                )

            except Exception as e:
                logger.error(f"Error adding document: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route("/agents/<agent_type>/tools", methods=["GET"])
        def list_tools(agent_type):
            """List available tools for an agent."""
            try:
                if agent_type not in self.agents:
                    return (
                        jsonify({"error": f'Agent type "{agent_type}" not found'}),
                        404,
                    )

                agent = self.agents[agent_type]
                tools = agent.list_tools()

                # Get detailed tool information
                tool_details = {}
                for tool_name in tools:
                    tool = agent.tool_registry.get_tool(tool_name)
                    if tool:
                        tool_details[tool_name] = {
                            "name": tool.name,
                            "description": tool.description,
                            "examples": tool.get_usage_examples(),
                            "schema": tool.get_parameter_schema(),
                        }

                return jsonify(
                    {"tools": tools, "tool_details": tool_details, "count": len(tools)}
                )

            except Exception as e:
                logger.error(f"Error listing tools: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route("/agents/<agent_type>/tools/<tool_name>", methods=["POST"])
        def execute_tool(agent_type, tool_name):
            """Execute a specific tool."""
            try:
                if agent_type not in self.agents:
                    return (
                        jsonify({"error": f'Agent type "{agent_type}" not found'}),
                        404,
                    )

                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                input_text = data.get("input")
                if not input_text:
                    return jsonify({"error": "Input is required"}), 400

                kwargs = data.get("parameters", {})

                agent = self.agents[agent_type]
                result = agent.execute_tool(tool_name, input_text, **kwargs)

                return jsonify(result)

            except Exception as e:
                logger.error(f"Error executing tool: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.route("/config", methods=["GET"])
        def get_config():
            """Get current configuration (sanitized)."""
            try:
                # Return sanitized config (no API keys)
                config_info = {
                    "vector_store": {
                        "type": self.config.get_config("vector_store.type"),
                        "path": self.config.get_config("vector_store.path"),
                    },
                    "memory": {"type": self.config.get_config("memory.type")},
                    "llm": {
                        "type": self.config.get_config("llm.type"),
                        "model": self.config.get_config("llm.model"),
                    },
                    "api": self.config.get_section("api"),
                    "agents": list(self.agents.keys()),
                }

                return jsonify(config_info)

            except Exception as e:
                logger.error(f"Error getting config: {str(e)}")
                return (
                    jsonify({"error": "Internal server error", "details": str(e)}),
                    500,
                )

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "Endpoint not found"}), 404

        @self.app.errorhandler(405)
        def method_not_allowed(error):
            return jsonify({"error": "Method not allowed"}), 405

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({"error": "Internal server error"}), 500

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        debug: Optional[bool] = None,
    ):
        """Run the Flask server."""
        api_config = self.config.get_section("api")

        host = host or api_config.get("host", "0.0.0.0")
        port = port or api_config.get("port", 8000)
        debug = debug if debug is not None else api_config.get("debug", False)

        logger.info(f"Starting Agent API server on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app(config_path: Optional[str] = None) -> AgentAPI:
    """Create and configure the Flask application."""

    # Ensure default config exists
    create_default_config_file()

    # Initialize configuration
    config_paths = [
        "./config/default.yaml",
        "./config/local.yaml",
        "./config/production.yaml",
    ]

    if config_path:
        config_paths.append(config_path)

    # Create composite config provider
    providers = [EnvironmentConfigProvider(), YAMLConfigProvider(config_paths)]

    config = CompositeConfigProvider(providers)

    # Auto-register all implementations
    ComponentFactory.auto_register_implementations()

    # Create and return API instance
    return AgentAPI(config)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI Agent Base API Server")
    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--config", help="Path to additional config file")

    args = parser.parse_args()

    try:
        app = create_app(args.config)
        app.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        exit(1)
