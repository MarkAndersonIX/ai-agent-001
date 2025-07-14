import subprocess
import tempfile
import os
import time
import signal
from typing import Dict, Any, List, Optional
from pathlib import Path
import shlex

from core.base_tool import BaseTool, ToolResult


class CodeExecutionTool(BaseTool):
    """Safe code execution tool with language support and sandboxing."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize code execution tool."""
        self.config = config

        # Execution settings
        self.timeout_seconds = config.get("timeout_seconds", 30)
        self.max_output_length = config.get("max_output_length", 10000)
        self.allowed_languages = config.get(
            "allowed_languages", ["python", "javascript", "bash"]
        )
        self.working_directory = config.get("working_directory", tempfile.gettempdir())

        # Security settings
        self.enable_network = config.get("enable_network", False)
        self.max_memory_mb = config.get("max_memory_mb", 128)
        self.max_cpu_time = config.get("max_cpu_time", 10)

        # Language configurations
        self.language_configs = {
            "python": {
                "command": ["python3", "-c"],
                "file_extension": ".py",
                "unsafe_imports": [
                    "os",
                    "subprocess",
                    "sys",
                    "socket",
                    "urllib",
                    "requests",
                ],
            },
            "javascript": {
                "command": ["node", "-e"],
                "file_extension": ".js",
                "unsafe_patterns": [
                    'require("fs")',
                    'require("child_process")',
                    'require("net")',
                ],
            },
            "bash": {
                "command": ["bash", "-c"],
                "file_extension": ".sh",
                "unsafe_commands": [
                    "rm",
                    "mv",
                    "cp",
                    "chmod",
                    "sudo",
                    "su",
                    "wget",
                    "curl",
                ],
            },
        }

    @property
    def name(self) -> str:
        """Get the name of this tool."""
        return "code_execution"

    @property
    def description(self) -> str:
        """Get a description of what this tool does."""
        return (
            "Executes code in a sandboxed environment. Supports Python, JavaScript, and Bash. "
            "Includes safety restrictions and timeout limits. "
            "Example: 'run python: print(2 + 2)' or 'execute: console.log(\"Hello World\")'"
        )

    def execute(self, input_text: str, **kwargs) -> ToolResult:
        """Execute code with safety checks and sandboxing."""
        try:
            # Parse code and language from input
            language, code = self._parse_code_input(input_text)

            if not language or not code:
                return ToolResult(
                    success=False,
                    content="",
                    error_message="Please specify the programming language and code to execute.",
                )

            if language not in self.allowed_languages:
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"Language '{language}' not supported. Allowed: {', '.join(self.allowed_languages)}",
                )

            # Security validation
            security_check = self._validate_code_security(language, code)
            if not security_check["safe"]:
                return ToolResult(
                    success=False,
                    content="",
                    error_message=f"Security violation: {security_check['reason']}",
                )

            # Execute code
            result = self._execute_code_safely(language, code)

            return ToolResult(
                success=result["success"],
                content=result["output"],
                metadata={
                    "language": language,
                    "execution_time": result.get("execution_time", 0),
                    "exit_code": result.get("exit_code", 0),
                    "timeout": result.get("timeout", False),
                },
                error_message=result.get("error"),
            )

        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error_message=f"Code execution error: {str(e)}",
            )

    def _parse_code_input(self, input_text: str) -> tuple[Optional[str], Optional[str]]:
        """Parse language and code from input text."""
        input_text = input_text.strip()

        # Try to detect language and code from various formats

        # Format 1: "run python: code"
        if input_text.startswith(("run ", "execute ")):
            parts = input_text.split(":", 1)
            if len(parts) == 2:
                language_part = parts[0].strip()
                code = parts[1].strip()

                # Extract language
                for lang in self.allowed_languages:
                    if lang in language_part.lower():
                        return lang, code

        # Format 2: "python\ncode" or "```python\ncode\n```"
        if input_text.startswith("```"):
            lines = input_text.split("\n")
            if len(lines) > 1:
                language = lines[0].replace("```", "").strip()
                code_lines = lines[1:]
                if code_lines and code_lines[-1].strip() == "```":
                    code_lines = code_lines[:-1]
                code = "\n".join(code_lines)

                if language in self.allowed_languages:
                    return language, code

        # Format 3: Try to detect from content
        for lang in self.allowed_languages:
            if input_text.lower().startswith(lang):
                code = input_text[len(lang) :].strip()
                if code.startswith(":"):
                    code = code[1:].strip()
                return lang, code

        # Format 4: Assume Python if no language specified but looks like code
        if any(
            indicator in input_text
            for indicator in ["print(", "def ", "import ", "for ", "if "]
        ):
            return "python", input_text

        # Format 5: Assume JavaScript if looks like JS
        if any(
            indicator in input_text
            for indicator in ["console.log", "function ", "const ", "let ", "var "]
        ):
            return "javascript", input_text

        return None, None

    def _validate_code_security(self, language: str, code: str) -> Dict[str, Any]:
        """Validate code for security issues."""
        config = self.language_configs.get(language, {})

        # Check for unsafe imports/requires
        if language == "python":
            unsafe_imports = config.get("unsafe_imports", [])
            for unsafe_import in unsafe_imports:
                if f"import {unsafe_import}" in code or f"from {unsafe_import}" in code:
                    return {
                        "safe": False,
                        "reason": f"Unsafe import detected: {unsafe_import}",
                    }

        elif language == "javascript":
            unsafe_patterns = config.get("unsafe_patterns", [])
            for pattern in unsafe_patterns:
                if pattern in code:
                    return {
                        "safe": False,
                        "reason": f"Unsafe pattern detected: {pattern}",
                    }

        elif language == "bash":
            unsafe_commands = config.get("unsafe_commands", [])
            for command in unsafe_commands:
                if command in code:
                    return {
                        "safe": False,
                        "reason": f"Unsafe command detected: {command}",
                    }

        # Check for file system operations
        dangerous_patterns = [
            "open(",
            "file(",
            "write(",
            "delete",
            "remove",
            "/etc/",
            "/var/",
            "/usr/",
            "/bin/",
            "/sbin/",
            "__import__",
            "eval(",
            "exec(",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                return {
                    "safe": False,
                    "reason": f"Potentially dangerous operation: {pattern}",
                }

        # Check code length
        if len(code) > 10000:  # 10KB limit
            return {"safe": False, "reason": "Code too long (max 10KB)"}

        return {"safe": True}

    def _execute_code_safely(self, language: str, code: str) -> Dict[str, Any]:
        """Execute code with safety measures."""
        config = self.language_configs[language]
        start_time = time.time()

        try:
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=config["file_extension"],
                delete=False,
                dir=self.working_directory,
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            try:
                # Prepare command
                if language == "python":
                    cmd = ["python3", temp_file_path]
                elif language == "javascript":
                    cmd = ["node", temp_file_path]
                elif language == "bash":
                    cmd = ["bash", temp_file_path]
                else:
                    cmd = config["command"] + [code]

                # Set up environment with restrictions
                env = os.environ.copy()
                if not self.enable_network:
                    # Disable network (basic)
                    env["http_proxy"] = "localhost:1"
                    env["https_proxy"] = "localhost:1"

                # Execute with timeout and limits
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env,
                    cwd=self.working_directory,
                    preexec_fn=os.setsid if os.name != "nt" else None,
                )

                try:
                    stdout, stderr = process.communicate(timeout=self.timeout_seconds)
                    execution_time = time.time() - start_time

                    # Combine output
                    output = stdout
                    if stderr:
                        output += f"\nSTDERR:\n{stderr}"

                    # Truncate output if too long
                    if len(output) > self.max_output_length:
                        output = (
                            output[: self.max_output_length]
                            + "\n... (output truncated)"
                        )

                    return {
                        "success": process.returncode == 0,
                        "output": output,
                        "execution_time": execution_time,
                        "exit_code": process.returncode,
                        "timeout": False,
                        "error": stderr if process.returncode != 0 else None,
                    }

                except subprocess.TimeoutExpired:
                    # Kill the process group
                    if os.name != "nt":
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()

                    execution_time = time.time() - start_time

                    return {
                        "success": False,
                        "output": f"Execution timed out after {self.timeout_seconds} seconds",
                        "execution_time": execution_time,
                        "exit_code": -1,
                        "timeout": True,
                        "error": "Timeout",
                    }

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "output": "",
                "execution_time": execution_time,
                "exit_code": -1,
                "timeout": False,
                "error": str(e),
            }

    def validate_input(self, input_text: str, **kwargs) -> bool:
        """Validate code execution input."""
        if not input_text or not input_text.strip():
            return False

        language, code = self._parse_code_input(input_text)
        return language is not None and code is not None

    def get_usage_examples(self) -> List[str]:
        """Get examples of how to use this tool."""
        return [
            "run python: print('Hello, World!')",
            "execute javascript: console.log(2 + 2)",
            "```python\nfor i in range(5):\n    print(i)\n```",
            "bash: echo 'Current date:'; date",
            "python: import math; print(math.sqrt(16))",
        ]

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Code to execute with optional language specification",
                    "examples": [
                        "run python: print('Hello World')",
                        "execute: console.log('Hello')",
                        "```python\nprint(2+2)\n```",
                    ],
                }
            },
            "required": ["input"],
        }

    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.allowed_languages)

    def test_environment(self) -> Dict[str, Any]:
        """Test the execution environment for each supported language."""
        results = {}

        for language in self.allowed_languages:
            try:
                if language == "python":
                    test_code = "print('Python OK')"
                elif language == "javascript":
                    test_code = "console.log('JavaScript OK')"
                elif language == "bash":
                    test_code = "echo 'Bash OK'"
                else:
                    continue

                result = self._execute_code_safely(language, test_code)
                results[language] = {
                    "available": result["success"],
                    "output": result["output"],
                    "error": result.get("error"),
                }

            except Exception as e:
                results[language] = {"available": False, "error": str(e)}

        return results


# Register with factory
from core.component_factory import ComponentFactory

ComponentFactory.register_tool("code_execution", CodeExecutionTool)
