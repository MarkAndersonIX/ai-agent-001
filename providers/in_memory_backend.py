from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import threading
from core.base_memory_backend import MemoryBackend, ChatMessage, ConversationSession


class InMemoryBackend(MemoryBackend):
    """Simple in-memory implementation of memory backend."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize in-memory backend.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.sessions: Dict[str, List[ChatMessage]] = {}
        self.session_info: Dict[str, ConversationSession] = {}
        self._lock = threading.RLock()  # Thread-safe operations

        # Configuration
        self.max_sessions = config.get("max_sessions", 1000)
        self.default_session_timeout_hours = config.get("session_timeout_hours", 24)

    def save_session(
        self,
        session_id: str,
        messages: List[ChatMessage],
        agent_type: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Save or update a conversation session."""
        try:
            with self._lock:
                now = datetime.now()

                # Update messages
                self.sessions[session_id] = messages.copy()

                # Update or create session info
                if session_id in self.session_info:
                    session_info = self.session_info[session_id]
                    session_info.last_active = now
                    session_info.message_count = len(messages)
                    if metadata:
                        session_info.metadata = metadata
                else:
                    session_info = ConversationSession(
                        session_id=session_id,
                        agent_type=agent_type,
                        created_at=now,
                        last_active=now,
                        message_count=len(messages),
                        user_id=user_id,
                        metadata=metadata,
                    )
                    self.session_info[session_id] = session_info

                # Cleanup old sessions if we exceed max
                self._cleanup_excess_sessions()

                return True
        except Exception:
            return False

    def load_session(self, session_id: str) -> Optional[List[ChatMessage]]:
        """Load messages from a conversation session."""
        with self._lock:
            return self.sessions.get(session_id)

    def get_session_info(self, session_id: str) -> Optional[ConversationSession]:
        """Get session metadata without loading all messages."""
        with self._lock:
            return self.session_info.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session."""
        try:
            with self._lock:
                # Remove from both dictionaries
                self.sessions.pop(session_id, None)
                self.session_info.pop(session_id, None)
                return True
        except Exception:
            return False

    def list_sessions(
        self,
        user_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ConversationSession]:
        """List conversation sessions with optional filtering."""
        with self._lock:
            sessions = list(self.session_info.values())

            # Apply filters
            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]
            if agent_type:
                sessions = [s for s in sessions if s.agent_type == agent_type]

            # Sort by last_active (most recent first)
            sessions.sort(key=lambda s: s.last_active, reverse=True)

            # Apply pagination
            if offset:
                sessions = sessions[offset:]
            if limit:
                sessions = sessions[:limit]

            return sessions

    def append_message(
        self, session_id: str, message: ChatMessage, agent_type: str
    ) -> bool:
        """Append a single message to an existing session."""
        try:
            with self._lock:
                # Get existing messages or create new list
                messages = self.sessions.get(session_id, [])
                messages.append(message)

                # Save updated session
                return self.save_session(
                    session_id=session_id, messages=messages, agent_type=agent_type
                )
        except Exception:
            return False

    def get_recent_messages(
        self, session_id: str, limit: int = 10
    ) -> List[ChatMessage]:
        """Get the most recent messages from a session."""
        with self._lock:
            messages = self.sessions.get(session_id, [])
            return messages[-limit:] if messages else []

    def count_sessions(
        self, user_id: Optional[str] = None, agent_type: Optional[str] = None
    ) -> int:
        """Count sessions matching the given criteria."""
        with self._lock:
            sessions = list(self.session_info.values())

            if user_id:
                sessions = [s for s in sessions if s.user_id == user_id]
            if agent_type:
                sessions = [s for s in sessions if s.agent_type == agent_type]

            return len(sessions)

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Remove sessions older than the specified age."""
        try:
            with self._lock:
                cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
                expired_sessions = []

                for session_id, session_info in self.session_info.items():
                    if session_info.last_active < cutoff_time:
                        expired_sessions.append(session_id)

                # Remove expired sessions
                for session_id in expired_sessions:
                    self.sessions.pop(session_id, None)
                    self.session_info.pop(session_id, None)

                return len(expired_sessions)
        except Exception:
            return 0

    def _cleanup_excess_sessions(self) -> None:
        """Remove oldest sessions if we exceed max_sessions limit."""
        if len(self.session_info) <= self.max_sessions:
            return

        # Get sessions sorted by last_active (oldest first)
        sessions = sorted(self.session_info.items(), key=lambda x: x[1].last_active)

        # Remove oldest sessions
        excess_count = len(self.session_info) - self.max_sessions
        for i in range(excess_count):
            session_id = sessions[i][0]
            self.sessions.pop(session_id, None)
            self.session_info.pop(session_id, None)

    def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics."""
        with self._lock:
            total_messages = sum(len(messages) for messages in self.sessions.values())

            return {
                "total_sessions": len(self.session_info),
                "total_messages": total_messages,
                "max_sessions": self.max_sessions,
                "average_messages_per_session": (
                    total_messages / len(self.session_info) if self.session_info else 0
                ),
            }


# Register with factory
from core.component_factory import ComponentFactory

ComponentFactory.register_memory_backend("in_memory", InMemoryBackend)
