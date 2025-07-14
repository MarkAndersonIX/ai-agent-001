from typing import Any, Dict

from core.base_agent import BaseAgent
from core.base_config_provider import ConfigProvider


class CodeAssistantAgent(BaseAgent):
    """Code assistant agent specialized for programming help."""

    def __init__(self, config: ConfigProvider):
        """Initialize the code assistant agent."""
        super().__init__("code_assistant", config)

    def _build_system_prompt(
        self, relevant_context: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Build the system prompt for the code assistant agent."""

        # Get base system prompt from configuration
        base_prompt = self.agent_config.get(
            "system_prompt",
            "You are an expert code assistant that helps developers write clean, "
            "efficient code following best practices.",
        )

        # Add context information if available
        context_parts = [base_prompt]

        if relevant_context.get("context"):
            context_parts.append(
                "\nRelevant code documentation and examples:\n"
                + relevant_context["context"]
            )

        # Add specialized code assistant instructions
        context_parts.append(
            "\nCode Assistant Guidelines:\n"
            "- Provide clear, well-commented code examples\n"
            "- Explain the reasoning behind your solutions\n"
            "- Suggest best practices and common patterns\n"
            "- Include error handling where appropriate\n"
            "- Mention potential pitfalls or edge cases\n"
            "- Provide alternative approaches when relevant"
        )

        # Add tool usage instructions
        available_tools = self.list_tools()
        if available_tools:
            tool_instructions = []

            if "file_operations" in available_tools:
                tool_instructions.append(
                    "- Use file_operations to read/write code files when needed"
                )

            if "code_execution" in available_tools:
                tool_instructions.append(
                    "- Use code_execution to run and test code examples"
                )

            if "web_search" in available_tools:
                tool_instructions.append(
                    "- Use web_search to find up-to-date documentation or examples"
                )

            if tool_instructions:
                context_parts.append(
                    f"\nAvailable tools: {', '.join(available_tools)}\n"
                    + "\n".join(tool_instructions)
                )

        # Add language-specific guidance
        context_parts.append(
            "\nLanguage-Specific Considerations:\n"
            "- Python: Follow PEP 8, use type hints, prefer list comprehensions\n"
            "- JavaScript: Use modern ES6+ features, prefer const/let over var\n"
            "- Java: Follow naming conventions, use appropriate design patterns\n"
            "- Always specify the programming language in code blocks"
        )

        # Add formatting instructions
        context_parts.append(
            "\nFormatting:\n"
            "- Use markdown code blocks with language specification\n"
            "- Include brief explanations before and after code\n"
            "- Highlight important parts of the code\n"
            "- Provide usage examples when applicable"
        )

        # Add source attribution
        if relevant_context.get("sources"):
            context_parts.append(
                "\nWhen using information from documentation or examples, "
                "cite the relevant sources."
            )

        return "\n".join(context_parts)
