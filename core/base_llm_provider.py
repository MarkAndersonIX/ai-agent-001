from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Represents a response from an LLM provider."""

    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None  # Token usage, cost, etc.
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMMessage:
    """Represents a message in LLM conversation format."""

    role: str  # 'system', 'user', 'assistant'
    content: str
    name: Optional[str] = None  # For function calling


class LLMProvider(ABC):
    """Abstract base class for Large Language Model providers."""

    @abstractmethod
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)

        Returns:
            LLM response with content and metadata
        """
        pass

    @abstractmethod
    def generate_stream(self, messages: List[LLMMessage], **kwargs) -> Iterator[str]:
        """
        Generate a streaming response from the LLM.

        Args:
            messages: List of conversation messages
            **kwargs: Provider-specific parameters

        Yields:
            Chunks of the response as they become available
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in the given text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    def count_message_tokens(self, messages: List[LLMMessage]) -> int:
        """
        Count tokens in a list of messages.

        Args:
            messages: List of messages to count tokens for

        Returns:
            Total number of tokens
        """
        total = 0
        for message in messages:
            # Add tokens for role and content
            total += self.count_tokens(f"{message.role}: {message.content}")
            # Add overhead for message formatting
            total += 4  # Approximate overhead per message
        return total

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information (name, context_length, etc.)
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration parameters for this provider.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    def create_system_message(self, content: str) -> LLMMessage:
        """
        Create a system message.

        Args:
            content: System message content

        Returns:
            Formatted system message
        """
        return LLMMessage(role="system", content=content)

    def create_user_message(self, content: str) -> LLMMessage:
        """
        Create a user message.

        Args:
            content: User message content

        Returns:
            Formatted user message
        """
        return LLMMessage(role="user", content=content)

    def create_assistant_message(self, content: str) -> LLMMessage:
        """
        Create an assistant message.

        Args:
            content: Assistant message content

        Returns:
            Formatted assistant message
        """
        return LLMMessage(role="assistant", content=content)

    def format_messages_for_prompt(self, messages: List[LLMMessage]) -> str:
        """
        Format messages into a single prompt string.

        Args:
            messages: List of messages to format

        Returns:
            Formatted prompt string
        """
        formatted_parts = []
        for message in messages:
            if message.role == "system":
                formatted_parts.append(f"System: {message.content}")
            elif message.role == "user":
                formatted_parts.append(f"Human: {message.content}")
            elif message.role == "assistant":
                formatted_parts.append(f"Assistant: {message.content}")

        return "\n\n".join(formatted_parts)

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if this provider supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise
        """
        pass

    @abstractmethod
    def supports_function_calling(self) -> bool:
        """
        Check if this provider supports function calling.

        Returns:
            True if function calling is supported, False otherwise
        """
        pass
