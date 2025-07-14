"""
Unit tests for InMemoryBackend.
"""

import pytest
from datetime import datetime, timedelta
from providers.in_memory_backend import InMemoryBackend
from core.base_memory_backend import ChatMessage


class TestInMemoryBackend:
    """Test InMemoryBackend functionality."""

    @pytest.fixture
    def memory_backend(self):
        """Create memory backend instance."""
        config = {"max_sessions": 100, "session_timeout_hours": 24}
        return InMemoryBackend(config)

    @pytest.fixture
    def sample_messages(self):
        """Create sample chat messages."""
        now = datetime.now()
        return [
            ChatMessage(role="user", content="Hello", timestamp=now),
            ChatMessage(role="assistant", content="Hi there!", timestamp=now),
            ChatMessage(role="user", content="How are you?", timestamp=now),
        ]

    def test_backend_initialization(self, memory_backend):
        """Test backend initialization."""
        assert memory_backend.max_sessions == 100
        assert memory_backend.default_session_timeout_hours == 24
        assert len(memory_backend.sessions) == 0
        assert len(memory_backend.session_info) == 0

    def test_save_session(self, memory_backend, sample_messages):
        """Test saving a session."""
        session_id = "test_session_1"
        agent_type = "test_agent"

        success = memory_backend.save_session(
            session_id=session_id,
            messages=sample_messages,
            agent_type=agent_type,
            user_id="user123",
            metadata={"test": "data"},
        )

        assert success is True
        assert session_id in memory_backend.sessions
        assert session_id in memory_backend.session_info

        # Check saved messages
        saved_messages = memory_backend.sessions[session_id]
        assert len(saved_messages) == 3
        assert saved_messages[0].content == "Hello"

        # Check session info
        session_info = memory_backend.session_info[session_id]
        assert session_info.agent_type == agent_type
        assert session_info.user_id == "user123"
        assert session_info.message_count == 3
        assert session_info.metadata == {"test": "data"}

    def test_load_session(self, memory_backend, sample_messages):
        """Test loading a session."""
        session_id = "test_session_2"

        # Save first
        memory_backend.save_session(session_id, sample_messages, "test_agent")

        # Load
        loaded_messages = memory_backend.load_session(session_id)

        assert loaded_messages is not None
        assert len(loaded_messages) == 3
        assert loaded_messages[0].content == "Hello"
        assert loaded_messages[1].role == "assistant"

    def test_load_nonexistent_session(self, memory_backend):
        """Test loading non-existent session."""
        result = memory_backend.load_session("nonexistent_session")
        assert result is None

    def test_get_session_info(self, memory_backend, sample_messages):
        """Test getting session information."""
        session_id = "test_session_3"

        memory_backend.save_session(
            session_id, sample_messages, "test_agent", "user123"
        )

        session_info = memory_backend.get_session_info(session_id)

        assert session_info is not None
        assert session_info.session_id == session_id
        assert session_info.agent_type == "test_agent"
        assert session_info.user_id == "user123"
        assert session_info.message_count == 3

    def test_delete_session(self, memory_backend, sample_messages):
        """Test deleting a session."""
        session_id = "test_session_4"

        # Save first
        memory_backend.save_session(session_id, sample_messages, "test_agent")
        assert session_id in memory_backend.sessions

        # Delete
        success = memory_backend.delete_session(session_id)

        assert success is True
        assert session_id not in memory_backend.sessions
        assert session_id not in memory_backend.session_info

    def test_append_message(self, memory_backend, sample_messages):
        """Test appending a message to existing session."""
        session_id = "test_session_5"

        # Save initial messages
        memory_backend.save_session(session_id, sample_messages[:2], "test_agent")

        # Append new message
        new_message = ChatMessage(
            role="user", content="New message", timestamp=datetime.now()
        )
        success = memory_backend.append_message(session_id, new_message, "test_agent")

        assert success is True

        # Check updated session
        messages = memory_backend.load_session(session_id)
        assert len(messages) == 3
        assert messages[-1].content == "New message"

        # Check updated session info
        session_info = memory_backend.get_session_info(session_id)
        assert session_info.message_count == 3

    def test_append_message_new_session(self, memory_backend):
        """Test appending message creates new session."""
        session_id = "new_session"
        message = ChatMessage(
            role="user", content="First message", timestamp=datetime.now()
        )

        success = memory_backend.append_message(session_id, message, "test_agent")

        assert success is True
        assert session_id in memory_backend.sessions

        messages = memory_backend.load_session(session_id)
        assert len(messages) == 1
        assert messages[0].content == "First message"

    def test_get_recent_messages(self, memory_backend, sample_messages):
        """Test getting recent messages."""
        session_id = "test_session_6"

        # Create more messages
        many_messages = sample_messages + [
            ChatMessage(
                role="assistant", content="Message 4", timestamp=datetime.now()
            ),
            ChatMessage(role="user", content="Message 5", timestamp=datetime.now()),
        ]

        memory_backend.save_session(session_id, many_messages, "test_agent")

        # Get recent messages
        recent = memory_backend.get_recent_messages(session_id, limit=3)

        assert len(recent) == 3
        assert recent[-1].content == "Message 5"  # Most recent should be last

    def test_list_sessions(self, memory_backend, sample_messages):
        """Test listing sessions."""
        # Create multiple sessions
        sessions_data = [
            ("session1", "agent1", "user1"),
            ("session2", "agent1", "user2"),
            ("session3", "agent2", "user1"),
        ]

        for session_id, agent_type, user_id in sessions_data:
            memory_backend.save_session(
                session_id, sample_messages, agent_type, user_id
            )

        # List all sessions
        all_sessions = memory_backend.list_sessions()
        assert len(all_sessions) == 3

        # List by user
        user1_sessions = memory_backend.list_sessions(user_id="user1")
        assert len(user1_sessions) == 2

        # List by agent type
        agent1_sessions = memory_backend.list_sessions(agent_type="agent1")
        assert len(agent1_sessions) == 2

        # List with pagination
        limited_sessions = memory_backend.list_sessions(limit=2)
        assert len(limited_sessions) == 2

        offset_sessions = memory_backend.list_sessions(offset=1, limit=2)
        assert len(offset_sessions) == 2

    def test_count_sessions(self, memory_backend, sample_messages):
        """Test counting sessions."""
        assert memory_backend.count_sessions() == 0

        # Add sessions
        memory_backend.save_session("s1", sample_messages, "agent1", "user1")
        memory_backend.save_session("s2", sample_messages, "agent1", "user2")
        memory_backend.save_session("s3", sample_messages, "agent2", "user1")

        assert memory_backend.count_sessions() == 3
        assert memory_backend.count_sessions(user_id="user1") == 2
        assert memory_backend.count_sessions(agent_type="agent1") == 2
        assert memory_backend.count_sessions(user_id="user1", agent_type="agent1") == 1

    def test_cleanup_expired_sessions(self, memory_backend):
        """Test cleaning up expired sessions."""
        now = datetime.now()
        old_time = now - timedelta(hours=25)  # Older than 24 hours

        # Create sessions with different ages
        old_messages = [ChatMessage(role="user", content="Old", timestamp=old_time)]
        new_messages = [ChatMessage(role="user", content="New", timestamp=now)]

        memory_backend.save_session("old_session", old_messages, "test_agent")
        memory_backend.save_session("new_session", new_messages, "test_agent")

        # Manually set old timestamp for old session
        memory_backend.session_info["old_session"].last_active = old_time

        # Cleanup expired (older than 24 hours)
        cleaned_count = memory_backend.cleanup_expired_sessions(max_age_hours=24)

        assert cleaned_count == 1
        assert "old_session" not in memory_backend.sessions
        assert "new_session" in memory_backend.sessions

    def test_max_sessions_limit(self, memory_backend, sample_messages):
        """Test max sessions limit enforcement."""
        # Set low limit for testing
        memory_backend.max_sessions = 3

        # Add sessions beyond limit
        for i in range(5):
            session_id = f"session_{i}"
            memory_backend.save_session(session_id, sample_messages, "test_agent")

        # Should only keep max_sessions
        assert len(memory_backend.sessions) == 3
        assert len(memory_backend.session_info) == 3

        # Older sessions should be removed
        assert "session_0" not in memory_backend.sessions
        assert "session_1" not in memory_backend.sessions
        assert "session_4" in memory_backend.sessions  # Most recent should remain

    def test_get_stats(self, memory_backend, sample_messages):
        """Test getting backend statistics."""
        # Add some sessions
        memory_backend.save_session("s1", sample_messages[:2], "test_agent")
        memory_backend.save_session("s2", sample_messages, "test_agent")

        stats = memory_backend.get_stats()

        assert stats["total_sessions"] == 2
        assert stats["total_messages"] == 5  # 2 + 3 messages
        assert stats["max_sessions"] == 100
        assert stats["average_messages_per_session"] == 2.5

    def test_thread_safety_basic(self, memory_backend, sample_messages):
        """Test basic thread safety (using lock)."""
        import threading
        import time

        session_id = "thread_test"
        results = []

        def worker():
            try:
                memory_backend.save_session(session_id, sample_messages, "test_agent")
                time.sleep(0.01)  # Small delay
                messages = memory_backend.load_session(session_id)
                results.append(len(messages) if messages else 0)
            except Exception as e:
                results.append(f"Error: {e}")

        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should succeed (no errors)
        assert all(isinstance(result, int) for result in results)
        assert all(result == 3 for result in results)  # All should see 3 messages

    def test_error_handling(self, memory_backend):
        """Test error handling in various scenarios."""
        # Test with None values
        success = memory_backend.save_session(None, [], "test_agent")
        assert success is False

        # Test delete non-existent session
        success = memory_backend.delete_session("nonexistent")
        assert success is True  # Should not fail

        # Test append to invalid session with invalid data
        success = memory_backend.append_message("", None, "")
        assert success is False


# Alternative unittest.TestCase version would look like this:
"""
import unittest
from datetime import datetime
from providers.in_memory_backend import InMemoryBackend
from core.base_memory_backend import ChatMessage

class TestInMemoryBackendUnittest(unittest.TestCase):
    '''Example unittest.TestCase version'''
    
    def setUp(self):
        '''Set up test fixtures.'''
        config = {'max_sessions': 100, 'session_timeout_hours': 24}
        self.backend = InMemoryBackend(config)
        
        now = datetime.now()
        self.sample_messages = [
            ChatMessage(role="user", content="Hello", timestamp=now),
            ChatMessage(role="assistant", content="Hi!", timestamp=now)
        ]
    
    def tearDown(self):
        '''Clean up after tests.'''
        self.backend = None
    
    def test_save_and_load_session(self):
        '''Test saving and loading sessions.'''
        session_id = "test_session"
        
        success = self.backend.save_session(
            session_id, self.sample_messages, "test_agent"
        )
        
        self.assertTrue(success)
        
        loaded = self.backend.load_session(session_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].content, "Hello")
    
    def test_session_count(self):
        '''Test session counting.'''
        self.assertEqual(self.backend.count_sessions(), 0)
        
        self.backend.save_session("s1", self.sample_messages, "agent1")
        self.assertEqual(self.backend.count_sessions(), 1)

if __name__ == '__main__':
    unittest.main()
"""
