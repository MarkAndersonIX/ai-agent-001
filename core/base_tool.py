from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain.tools import BaseTool as LCBaseTool


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    success: bool
    content: str
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of this tool.

        Returns:
            Tool name
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get a description of what this tool does.

        Returns:
            Tool description
        """
        pass

    @abstractmethod
    def execute(self, input_text: str, **kwargs) -> ToolResult:
        """
        Execute the tool with the given input.

        Args:
            input_text: Input text/query for the tool
            **kwargs: Additional tool-specific parameters

        Returns:
            ToolResult with execution outcome
        """
        pass

    def validate_input(self, input_text: str, **kwargs) -> bool:
        """
        Validate tool input before execution.

        Args:
            input_text: Input text to validate
            **kwargs: Additional parameters to validate

        Returns:
            True if input is valid, False otherwise
        """
        return bool(input_text and input_text.strip())

    def get_usage_examples(self) -> List[str]:
        """
        Get examples of how to use this tool.

        Returns:
            List of usage examples
        """
        return []

    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get schema for tool parameters.

        Returns:
            JSON schema describing tool parameters
        """
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input text for the tool"}
            },
            "required": ["input"],
        }

    def to_langchain_tool(self) -> LCBaseTool:
        """
        Convert this tool to a LangChain tool.

        Returns:
            LangChain BaseTool instance
        """

        def tool_func(input_text: str) -> str:
            """Wrapper function for LangChain compatibility."""
            result = self.execute(input_text)
            if result.success:
                return result.content
            else:
                error_msg = result.error_message or "Tool execution failed"
                return f"Error: {error_msg}"

        # Create LangChain tool with proper attributes
        langchain_tool = LCBaseTool(
            name=self.name, description=self.description, func=tool_func
        )

        return langchain_tool

    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return f"{self.__class__.__name__}(name='{self.name}')"


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool to register
        """
        self._tools[tool.name] = tool

    def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if tool was found and removed, False otherwise
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of tool to retrieve

        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools.

        Returns:
            List of tool instances
        """
        return list(self._tools.values())

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        Get tools that belong to a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of tools in the category
        """
        # This assumes tools have a category attribute or metadata
        tools = []
        for tool in self._tools.values():
            tool_category = getattr(tool, "category", None)
            if tool_category == category:
                tools.append(tool)
        return tools

    def to_langchain_tools(
        self, tool_names: Optional[List[str]] = None
    ) -> List[LCBaseTool]:
        """
        Convert registered tools to LangChain format.

        Args:
            tool_names: Optional list of specific tools to convert

        Returns:
            List of LangChain tools
        """
        if tool_names is None:
            tools = self.get_all_tools()
        else:
            tools = [self.get_tool(name) for name in tool_names if self.get_tool(name)]

        return [tool.to_langchain_tool() for tool in tools]
