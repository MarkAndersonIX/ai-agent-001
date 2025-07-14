from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """Represents a chat message in a conversation."""

    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConversationSession:
    """Represents a conversation session."""

    session_id: str
    agent_type: str
    created_at: datetime
    last_active: datetime
    message_count: int
    total_tokens: Optional[int] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryBackend(ABC):
    """Abstract base class for memory storage implementations."""

    @abstractmethod
    def save_session(
        self,
        session_id: str,
        messages: List[ChatMessage],
        agent_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save or update a conversation session.

        Args:
            session_id: Unique session identifier
            messages: List of chat messages
            agent_type: Type of agent for this session
            user_id: Optional user identifier
            metadata: Optional session metadata

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_session(self, session_id: str) -> Optional[List[ChatMessage]]:
        """
        Load messages from a conversation session.

        Args:
            session_id: Session identifier to load

        Returns:
            List of chat messages if session exists, None otherwise
        """
        pass

    @abstractmethod
    def get_session_info(self, session_id: str) -> Optional[ConversationSession]:
        """
        Get session metadata without loading all messages.

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession info if exists, None otherwise
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session.

        Args:
            session_id: Session identifier to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ConversationSession]:
        """
        List conversation sessions with optional filtering.

        Args:
            user_id: Optional filter by user
            agent_type: Optional filter by agent type
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of conversation sessions
        """
        pass

    @abstractmethod
    def append_message(
        self, session_id: str, message: ChatMessage, agent_type: str
    ) -> bool:
        """
        Append a single message to an existing session.

        Args:
            session_id: Session to append to
            message: Message to append
            agent_type: Agent type for the session

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_recent_messages(
        self, session_id: str, limit: int = 10
    ) -> List[ChatMessage]:
        """
        Get the most recent messages from a session.

        Args:
            session_id: Session identifier
            limit: Number of recent messages to return

        Returns:
            List of recent chat messages
        """
        pass

    @abstractmethod
    def count_sessions(
        self, user_id: Optional[str] = None, agent_type: Optional[str] = None
    ) -> int:
        """
        Count sessions matching the given criteria.

        Args:
            user_id: Optional filter by user
            agent_type: Optional filter by agent type

        Returns:
            Number of sessions matching criteria
        """
        pass

    @abstractmethod
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove sessions older than the specified age.

        Args:
            max_age_hours: Maximum age in hours before cleanup

        Returns:
            Number of sessions cleaned up
        """
        pass
