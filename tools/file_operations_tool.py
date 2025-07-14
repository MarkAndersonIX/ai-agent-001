import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.base_tool import BaseTool, ToolResult


class FileOperationsTool(BaseTool):
    """Tool for basic file system operations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize file operations tool."""
        self.config = config

        # Security: Define allowed paths
        self.allowed_paths = config.get("allowed_paths", ["./workspace/", "./data/"])
        self.max_file_size = config.get(
            "max_file_size", 10 * 1024 * 1024
        )  # 10MB default
        self.allowed_extensions = config.get(
            "allowed_extensions",
            [
                ".txt",
                ".md",
                ".json",
                ".yaml",
                ".yml",
                ".csv",
                ".py",
                ".js",
                ".html",
                ".css",
            ],
        )

    @property
    def name(self) -> str:
        """Get the name of this tool."""
        return "file_operations"

    @property
    def description(self) -> str:
        """Get a description of what this tool does."""
        return (
            "Performs file system operations like reading, writing, listing files and directories. "
            "Supports operations: read, write, list, mkdir, exists, delete. "
            "Example: 'read file.txt' or 'list ./data/' or 'write content to output.txt'"
        )

    def execute(self, input_text: str, **kwargs) -> ToolResult:
        """Execute file operation based on input text."""
        try:
            # Parse the operation from input text
            operation, params = self._parse_operation(input_text)

            if not operation:
                return ToolResult(
                    success=False,
                    content="",
                    error_message="Please specify a file operation (read, write, list, mkdir, exists, delete).",
                )

            # Execute the appropriate operation
            if operation == "read":
                return self._read_file(params.get("path"))
            elif operation == "write":
                return self._write_file(params.get("path"), params.get("content"))
            elif operation == "list":
                return self._list_directory(params.get("path", "."))
            elif operation == "mkdir":
                return self._make_directory(params.get("path"))
            elif operation == "exists":
                return self._check_exists(params.get("path"))
            elif operation == "delete":
                return self._delete_file(params.get("path"))
            else:
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"Unsupported operation: {operation}",
                )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"File operation error: {str(e)}",
            )

    def _parse_operation(self, input_text: str) -> tuple[Optional[str], Dict[str, Any]]:
        """Parse operation and parameters from input text."""
        input_text = input_text.strip().lower()

        # Pattern matching for different operations
        if input_text.startswith("read "):
            path = input_text[5:].strip()
            return "read", {"path": path}

        elif input_text.startswith("write "):
            # Handle "write content to file.txt" or "write file.txt: content"
            remaining = input_text[6:].strip()
            if " to " in remaining:
                content, path = remaining.split(" to ", 1)
                return "write", {"path": path.strip(), "content": content.strip()}
            elif ": " in remaining:
                path, content = remaining.split(": ", 1)
                return "write", {"path": path.strip(), "content": content.strip()}
            else:
                return "write", {"path": remaining, "content": ""}

        elif input_text.startswith("list "):
            path = input_text[5:].strip() or "."
            return "list", {"path": path}

        elif input_text.startswith("mkdir "):
            path = input_text[6:].strip()
            return "mkdir", {"path": path}

        elif input_text.startswith("exists "):
            path = input_text[7:].strip()
            return "exists", {"path": path}

        elif input_text.startswith("delete "):
            path = input_text[7:].strip()
            return "delete", {"path": path}

        # Try to infer operation from context
        if input_text.startswith("ls ") or input_text == "ls":
            path = input_text[3:].strip() if len(input_text) > 2 else "."
            return "list", {"path": path}

        return None, {}

    def _is_path_allowed(self, path: str) -> bool:
        """Check if the path is within allowed directories."""
        try:
            abs_path = os.path.abspath(path)

            for allowed_path in self.allowed_paths:
                allowed_abs = os.path.abspath(allowed_path)
                if abs_path.startswith(allowed_abs):
                    return True

            return False
        except Exception:
            return False

    def _is_extension_allowed(self, path: str) -> bool:
        """Check if the file extension is allowed."""
        if not self.allowed_extensions:
            return True  # No restrictions

        ext = Path(path).suffix.lower()
        return ext in self.allowed_extensions

    def _read_file(self, path: str) -> ToolResult:
        """Read content from a file."""
        if not path:
            return ToolResult(
                success=False,
                content="",
                error_message="File path is required for read operation.",
            )

        if not self._is_path_allowed(path):
            return ToolResult(
                success=False,
                content="",
                error_message=f"Access denied: Path '{path}' is not in allowed directories.",
            )

        try:
            if not os.path.exists(path):
                return ToolResult(
                    success=False, content="", error_message=f"File not found: {path}"
                )

            if os.path.getsize(path) > self.max_file_size:
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"File too large (max {self.max_file_size} bytes).",
                )

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return ToolResult(
                success=True,
                content=content,
                metadata={"path": path, "size": len(content), "operation": "read"},
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                content="",
                error_message="Cannot read file: Not a text file or encoding issue.",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Failed to read file: {str(e)}",
            )

    def _write_file(self, path: str, content: str) -> ToolResult:
        """Write content to a file."""
        if not path:
            return ToolResult(
                success=False,
                content="",
                error_message="File path is required for write operation.",
            )

        if not self._is_path_allowed(path):
            return ToolResult(
                success=False,
                content="",
                error_message=f"Access denied: Path '{path}' is not in allowed directories.",
            )

        if not self._is_extension_allowed(path):
            return ToolResult(
                success=False,
                content="",
                error_message=f"File extension not allowed: {Path(path).suffix}",
            )

        try:
            # Create parent directories if needed
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content or "")

            return ToolResult(
                success=True,
                content=f"Successfully wrote {len(content or '')} characters to {path}",
                metadata={
                    "path": path,
                    "size": len(content or ""),
                    "operation": "write",
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Failed to write file: {str(e)}",
            )

    def _list_directory(self, path: str) -> ToolResult:
        """List contents of a directory."""
        if not self._is_path_allowed(path):
            return ToolResult(
                success=False,
                content="",
                error_message=f"Access denied: Path '{path}' is not in allowed directories.",
            )

        try:
            if not os.path.exists(path):
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"Directory not found: {path}",
                )

            if not os.path.isdir(path):
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"Path is not a directory: {path}",
                )

            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                items.append(
                    {
                        "name": item,
                        "type": item_type,
                        "size": (
                            os.path.getsize(item_path) if item_type == "file" else None
                        ),
                    }
                )

            # Sort: directories first, then files, both alphabetically
            items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))

            # Format output
            content_lines = []
            for item in items:
                if item["type"] == "directory":
                    content_lines.append(f"📁 {item['name']}/")
                else:
                    size_str = (
                        f" ({item['size']} bytes)" if item["size"] is not None else ""
                    )
                    content_lines.append(f"📄 {item['name']}{size_str}")

            content = (
                "\n".join(content_lines) if content_lines else "Directory is empty"
            )

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "path": path,
                    "item_count": len(items),
                    "items": items,
                    "operation": "list",
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Failed to list directory: {str(e)}",
            )

    def _make_directory(self, path: str) -> ToolResult:
        """Create a directory."""
        if not path:
            return ToolResult(
                success=False,
                content="",
                error_message="Directory path is required for mkdir operation.",
            )

        if not self._is_path_allowed(path):
            return ToolResult(
                success=False,
                content="",
                error_message=f"Access denied: Path '{path}' is not in allowed directories.",
            )

        try:
            Path(path).mkdir(parents=True, exist_ok=True)

            return ToolResult(
                success=True,
                content=f"Directory created: {path}",
                metadata={"path": path, "operation": "mkdir"},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Failed to create directory: {str(e)}",
            )

    def _check_exists(self, path: str) -> ToolResult:
        """Check if a file or directory exists."""
        if not path:
            return ToolResult(
                success=False,
                content="",
                error_message="Path is required for exists operation.",
            )

        try:
            exists = os.path.exists(path)
            if exists:
                item_type = "directory" if os.path.isdir(path) else "file"
                content = f"Yes, {item_type} exists: {path}"
            else:
                content = f"No, path does not exist: {path}"

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "path": path,
                    "exists": exists,
                    "type": item_type if exists else None,
                    "operation": "exists",
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Failed to check existence: {str(e)}",
            )

    def _delete_file(self, path: str) -> ToolResult:
        """Delete a file."""
        if not path:
            return ToolResult(
                success=False,
                content="",
                error_message="File path is required for delete operation.",
            )

        if not self._is_path_allowed(path):
            return ToolResult(
                success=False,
                content="",
                error_message=f"Access denied: Path '{path}' is not in allowed directories.",
            )

        try:
            if not os.path.exists(path):
                return ToolResult(
                    success=False, content="", error_message=f"File not found: {path}"
                )

            if os.path.isdir(path):
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"Cannot delete directory with this tool: {path}",
                )

            os.remove(path)

            return ToolResult(
                success=True,
                content=f"File deleted: {path}",
                metadata={"path": path, "operation": "delete"},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Failed to delete file: {str(e)}",
            )

    def get_usage_examples(self) -> List[str]:
        """Get examples of how to use this tool."""
        return [
            "read config.txt",
            "write Hello World to output.txt",
            "list ./data/",
            "mkdir new_folder",
            "exists myfile.txt",
            "delete old_file.txt",
        ]

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "File operation command",
                    "examples": [
                        "read config.txt",
                        "write content to file.txt",
                        "list ./data/",
                    ],
                }
            },
            "required": ["input"],
        }


# Register with factory
from core.component_factory import ComponentFactory

ComponentFactory.register_tool("file_operations", FileOperationsTool)
