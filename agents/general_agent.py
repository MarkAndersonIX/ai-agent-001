from typing import Dict, Any
from core.base_agent import BaseAgent
from core.base_config_provider import ConfigProvider


class GeneralAgent(BaseAgent):
    """General-purpose conversational AI agent."""

    def __init__(self, config: ConfigProvider):
        """Initialize the general agent."""
        super().__init__("general", config)

    def _build_system_prompt(
        self, relevant_context: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Build the system prompt for the general agent."""

        # Get base system prompt from configuration
        base_prompt = self.agent_config.get(
            "system_prompt",
            "You are a helpful AI assistant that can answer questions and help with various tasks.",
        )

        # Add context information if available
        context_parts = [base_prompt]

        if relevant_context.get("context"):
            context_parts.append(
                "\nRelevant information from knowledge base:\n"
                + relevant_context["context"]
            )

        # Add source attribution if available
        if relevant_context.get("sources"):
            context_parts.append(
                "\nWhen referencing information from the knowledge base, "
                "please cite your sources appropriately."
            )

        # Add tool usage instructions if tools are available
        available_tools = self.list_tools()
        if available_tools:
            context_parts.append(
                f"\nYou have access to the following tools: {', '.join(available_tools)}. "
                "Use them when they would be helpful for answering the user's question."
            )

        # Add conversation guidelines
        context_parts.append(
            "\nGuidelines:\n"
            "- Be helpful, accurate, and concise\n"
            "- If you're unsure about something, say so\n"
            "- Use the provided context when relevant\n"
            "- Cite sources when using external information"
        )

        return "\n".join(context_parts)
