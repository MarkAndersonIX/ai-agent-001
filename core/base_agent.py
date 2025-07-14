from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import uuid

from .base_vector_store import VectorStore, Document, SearchResult
from .base_document_store import DocumentStore
from .base_memory_backend import MemoryBackend, ChatMessage, ConversationSession
from .base_config_provider import ConfigProvider
from .base_llm_provider import LLMProvider, LLMMessage, LLMResponse
from .base_embedding_provider import EmbeddingProvider
from .base_tool import BaseTool, ToolRegistry
from .component_factory import ComponentFactory

logger = logging.getLogger(__name__)


class AgentResponse:
    """Represents a response from an agent."""

    def __init__(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ):
        self.content = content
        self.sources = sources or []
        self.metadata = metadata or {}
        self.session_id = session_id
        self.timestamp = datetime.now()


class BaseAgent(ABC):
    """Base class for all AI agents."""

    def __init__(self, agent_type: str, config: ConfigProvider):
        """
        Initialize the base agent.

        Args:
            agent_type: Type identifier for this agent
            config: Configuration provider instance
        """
        self.agent_type = agent_type
        self.config = config

        # Initialize components from configuration
        self._initialize_components()

        # Load agent-specific configuration
        self.agent_config = self.config.get_section(f"agents.{agent_type}")

        # Initialize tools
        self._initialize_tools()

        logger.info(f"Initialized {agent_type} agent")

    def _initialize_components(self) -> None:
        """Initialize all component dependencies."""
        try:
            # Vector store
            vector_config = self.config.get_section("vector_store")
            self.vector_store: VectorStore = ComponentFactory.create_vector_store(
                vector_config
            )

            # Document store
            doc_config = self.config.get_section("document_store")
            self.document_store: DocumentStore = ComponentFactory.create_document_store(
                doc_config
            )

            # Memory backend
            memory_config = self.config.get_section("memory")
            self.memory_backend: MemoryBackend = ComponentFactory.create_memory_backend(
                memory_config
            )

            # LLM provider
            llm_config = self.config.get_section("llm")
            self.llm_provider: LLMProvider = ComponentFactory.create_llm_provider(
                llm_config
            )

            # Embedding provider
            embedding_config = self.config.get_section("embedding")
            self.embedding_provider: EmbeddingProvider = (
                ComponentFactory.create_embedding_provider(embedding_config)
            )

            logger.debug("All components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise RuntimeError(f"Component initialization failed: {str(e)}")

    def _initialize_tools(self) -> None:
        """Initialize tools for this agent."""
        try:
            # Get tool configurations for this agent
            tool_names = self.agent_config.get("tools", [])
            tool_configs = []

            for tool_name in tool_names:
                tool_config = self.config.get_section(f"tools.{tool_name}")
                tool_config["type"] = tool_name
                tool_configs.append(tool_config)

            # Create tool registry
            self.tool_registry = ComponentFactory.create_tool_registry(tool_configs)

            logger.debug(f"Initialized {len(tool_names)} tools for {self.agent_type}")

        except Exception as e:
            logger.warning(f"Failed to initialize tools: {str(e)}")
            self.tool_registry = ToolRegistry()  # Empty registry as fallback

    def process_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """
        Process a user query and generate a response.

        Args:
            query: User input query
            session_id: Optional session identifier
            user_id: Optional user identifier
            context: Optional additional context

        Returns:
            AgentResponse with generated content and metadata
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = f"{self.agent_type}_{uuid.uuid4().hex[:8]}"

            # Load conversation history
            conversation_history = self._load_conversation_history(session_id)

            # Retrieve relevant context from knowledge base
            relevant_context = self._retrieve_context(query, context or {})

            # Generate response using LLM
            response = self._generate_response(
                query=query,
                conversation_history=conversation_history,
                relevant_context=relevant_context,
                context=context or {},
            )

            # Save conversation to memory
            self._save_conversation_turn(session_id, query, response.content, user_id)

            # Create agent response
            agent_response = AgentResponse(
                content=response.content,
                sources=relevant_context.get("sources", []),
                metadata={
                    "model": response.model,
                    "usage": response.usage,
                    "context_sources": len(relevant_context.get("sources", [])),
                    "agent_type": self.agent_type,
                },
                session_id=session_id,
            )

            return agent_response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return AgentResponse(
                content="I apologize, but I encountered an error processing your request. Please try again.",
                metadata={"error": str(e), "agent_type": self.agent_type},
                session_id=session_id,
            )

    def _load_conversation_history(self, session_id: str) -> List[ChatMessage]:
        """Load conversation history for the session."""
        try:
            messages = self.memory_backend.load_session(session_id)
            return messages or []
        except Exception as e:
            logger.warning(f"Failed to load conversation history: {str(e)}")
            return []

    def _retrieve_context(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant context from knowledge base and documents."""
        try:
            # Get RAG settings for this agent
            rag_settings = self.agent_config.get("rag_settings", {})
            top_k = rag_settings.get("top_k", 5)
            similarity_threshold = rag_settings.get("similarity_threshold", 0.7)

            # Search vector store for relevant documents
            search_results = self.vector_store.similarity_search(
                query=query, k=top_k, filters={"agent_type": self.agent_type}
            )

            # Filter by similarity threshold
            relevant_results = [
                result
                for result in search_results
                if result.score >= similarity_threshold
            ]

            # Format context and sources
            context_parts = []
            sources = []

            for result in relevant_results:
                context_parts.append(result.document.content)

                # Extract source information
                metadata = result.document.metadata
                source_info = {
                    "content": (
                        result.document.content[:200] + "..."
                        if len(result.document.content) > 200
                        else result.document.content
                    ),
                    "score": result.score,
                    "metadata": metadata,
                }

                # Add URL if available (for web search results)
                if "source_url" in metadata:
                    source_info["url"] = metadata["source_url"]
                    source_info["title"] = metadata.get(
                        "original_title", "Web Document"
                    )

                sources.append(source_info)

            return {
                "context": "\n\n".join(context_parts),
                "sources": sources,
                "num_sources": len(relevant_results),
            }

        except Exception as e:
            logger.warning(f"Failed to retrieve context: {str(e)}")
            return {"context": "", "sources": [], "num_sources": 0}

    def _generate_response(
        self,
        query: str,
        conversation_history: List[ChatMessage],
        relevant_context: Dict[str, Any],
        context: Dict[str, Any],
    ) -> LLMResponse:
        """Generate response using the LLM provider."""
        try:
            # Build message history for LLM
            messages = []

            # Add system prompt
            system_prompt = self._build_system_prompt(relevant_context, context)
            messages.append(self.llm_provider.create_system_message(system_prompt))

            # Add conversation history (last N messages)
            max_history = self.agent_config.get("max_history_messages", 10)
            recent_history = (
                conversation_history[-max_history:] if conversation_history else []
            )

            for msg in recent_history:
                if msg.role == "user":
                    messages.append(self.llm_provider.create_user_message(msg.content))
                elif msg.role == "assistant":
                    messages.append(
                        self.llm_provider.create_assistant_message(msg.content)
                    )

            # Add current query
            messages.append(self.llm_provider.create_user_message(query))

            # Get LLM settings for this agent
            llm_settings = self.agent_config.get("llm_settings", {})

            # Generate response
            response = self.llm_provider.generate(messages, **llm_settings)

            return response

        except Exception as e:
            logger.error(f"Failed to generate LLM response: {str(e)}")
            # Return a fallback response
            return LLMResponse(
                content="I apologize, but I'm having trouble generating a response right now. Please try again.",
                model="fallback",
                metadata={"error": str(e)},
            )

    @abstractmethod
    def _build_system_prompt(
        self, relevant_context: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """
        Build the system prompt for this agent type.

        Args:
            relevant_context: Retrieved context from knowledge base
            context: Additional context from the request

        Returns:
            System prompt string
        """
        pass

    def _save_conversation_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Save a conversation turn to memory."""
        try:
            now = datetime.now()

            # Create chat messages
            user_msg = ChatMessage(role="user", content=user_message, timestamp=now)

            assistant_msg = ChatMessage(
                role="assistant", content=assistant_message, timestamp=now
            )

            # Append to session
            self.memory_backend.append_message(session_id, user_msg, self.agent_type)
            self.memory_backend.append_message(
                session_id, assistant_msg, self.agent_type
            )

        except Exception as e:
            logger.warning(f"Failed to save conversation turn: {str(e)}")

    def add_document(
        self, content: str, metadata: Dict[str, Any], file_path: Optional[str] = None
    ) -> str:
        """
        Add a document to the agent's knowledge base.

        Args:
            content: Document content
            metadata: Document metadata
            file_path: Optional original file path

        Returns:
            Document ID
        """
        try:
            # Add agent type to metadata
            metadata["agent_type"] = self.agent_type
            metadata["added_at"] = datetime.now().isoformat()

            # Store document
            doc_id = self.document_store.store_document(content, metadata, file_path)

            # Create embedding and add to vector store
            embedding = self.embedding_provider.embed_text(content)
            vector_doc = Document(content=content, metadata=metadata, doc_id=doc_id)
            vector_doc.embedding = embedding

            self.vector_store.add_documents([vector_doc])

            logger.info(f"Added document {doc_id} to {self.agent_type} knowledge base")
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            raise RuntimeError(f"Document addition failed: {str(e)}")

    def get_session_history(self, session_id: str) -> Optional[ConversationSession]:
        """Get session information and history."""
        try:
            return self.memory_backend.get_session_info(session_id)
        except Exception as e:
            logger.warning(f"Failed to get session history: {str(e)}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        try:
            return self.memory_backend.delete_session(session_id)
        except Exception as e:
            logger.warning(f"Failed to delete session: {str(e)}")
            return False

    def list_tools(self) -> List[str]:
        """List available tools for this agent."""
        return self.tool_registry.list_tools()

    def execute_tool(self, tool_name: str, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            input_text: Input for the tool
            **kwargs: Additional tool parameters

        Returns:
            Tool execution result
        """
        try:
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return {"success": False, "error": f"Tool '{tool_name}' not found"}

            result = tool.execute(input_text, **kwargs)

            return {
                "success": result.success,
                "content": result.content,
                "metadata": result.metadata,
                "error": result.error_message,
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent."""
        return {
            "agent_type": self.agent_type,
            "system_prompt": self.agent_config.get("system_prompt", ""),
            "tools": self.list_tools(),
            "rag_settings": self.agent_config.get("rag_settings", {}),
            "llm_settings": self.agent_config.get("llm_settings", {}),
            "component_info": {
                "vector_store": type(self.vector_store).__name__,
                "document_store": type(self.document_store).__name__,
                "memory_backend": type(self.memory_backend).__name__,
                "llm_provider": type(self.llm_provider).__name__,
                "embedding_provider": type(self.embedding_provider).__name__,
            },
        }
