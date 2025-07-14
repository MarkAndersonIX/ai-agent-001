import ast
import operator
import re
from typing import Any, Dict, List

from core.base_tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Simple calculator tool for mathematical expressions."""

    # Supported operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Supported functions
    FUNCTIONS = {
        "abs": abs,
        "round": round,
        "max": max,
        "min": min,
        "sum": sum,
    }

    def __init__(self, config: Dict[str, Any]):
        """Initialize calculator tool."""
        self.config = config

    @property
    def name(self) -> str:
        """Get the name of this tool."""
        return "calculator"

    @property
    def description(self) -> str:
        """Get a description of what this tool does."""
        return (
            "Performs mathematical calculations. Supports basic arithmetic operations "
            "(+, -, *, /, **, %), parentheses, and functions like abs, round, max, min, sum. "
            "Example: 'calculate 2 + 3 * 4' or 'sqrt(16) + 2'"
        )

    def execute(self, input_text: str, **kwargs) -> ToolResult:
        """Execute the calculator with the given mathematical expression."""
        try:
            # Clean and normalize the input
            expression = self._normalize_expression(input_text)

            if not expression:
                return ToolResult(
                    success=False,
                    content="",
                    error_message="Please provide a mathematical expression to calculate.",
                )

            # Validate and evaluate the expression
            result = self._safe_eval(expression)

            if result is None:
                return ToolResult(
                    success=False,
                    content="",
                    error_message="Invalid mathematical expression or unsupported operation.",
                )

            # Format the result
            formatted_result = self._format_result(result)

            return ToolResult(
                success=True,
                content=f"{expression} = {formatted_result}",
                metadata={
                    "expression": expression,
                    "result": result,
                    "formatted_result": formatted_result,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False, content="", error_message=f"Calculation error: {str(e)}"
            )

    def _normalize_expression(self, input_text: str) -> str:
        """Normalize and clean the mathematical expression."""
        # Remove common prefixes
        expression = re.sub(
            r"^(calculate|compute|eval|evaluate)\s+",
            "",
            input_text.strip(),
            flags=re.IGNORECASE,
        )

        # Remove extra whitespace
        expression = re.sub(r"\s+", "", expression)

        # Replace common mathematical notation
        replacements = {
            "x": "*",  # 'x' as multiplication
            "×": "*",  # multiplication symbol
            "÷": "/",  # division symbol
            "^": "**",  # exponentiation
        }

        for old, new in replacements.items():
            expression = expression.replace(old, new)

        # Add basic math functions
        math_functions = {
            "sqrt": "pow({}, 0.5)",
            "square": "pow({}, 2)",
            "cube": "pow({}, 3)",
        }

        # Handle sqrt, square, cube functions
        for func, replacement in math_functions.items():
            pattern = f"{func}\\(([^)]+)\\)"
            matches = re.findall(pattern, expression)
            for match in matches:
                expression = expression.replace(
                    f"{func}({match})", replacement.format(match)
                )

        return expression

    def _safe_eval(self, expression: str):
        """Safely evaluate a mathematical expression using AST."""
        try:
            # Parse the expression into an AST
            node = ast.parse(expression, mode="eval")
            return self._eval_node(node.body)
        except Exception:
            return None

    def _eval_node(self, node):
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            operator_func = self.OPERATORS.get(type(node.op))
            if operator_func:
                return operator_func(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            operator_func = self.OPERATORS.get(type(node.op))
            if operator_func:
                return operator_func(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name in self.FUNCTIONS:
                args = [self._eval_node(arg) for arg in node.args]
                return self.FUNCTIONS[func_name](*args)
        elif isinstance(node, ast.Name):
            # Handle constants like 'pi' or 'e'
            constants = {"pi": 3.141592653589793, "e": 2.718281828459045}
            return constants.get(node.id)

        raise ValueError(f"Unsupported operation: {type(node)}")

    def _format_result(self, result) -> str:
        """Format the calculation result for display."""
        if isinstance(result, float):
            # Check if it's effectively an integer
            if result.is_integer():
                return str(int(result))
            else:
                # Round to reasonable precision
                return f"{result:.10g}"
        else:
            return str(result)

    def validate_input(self, input_text: str, **kwargs) -> bool:
        """Validate calculator input."""
        if not input_text or not input_text.strip():
            return False

        # Check for basic mathematical characters
        valid_chars = set(
            "0123456789+-*/().%^×÷ abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )
        return all(c in valid_chars for c in input_text)

    def get_usage_examples(self) -> List[str]:
        """Get examples of how to use this tool."""
        return [
            "2 + 3 * 4",
            "sqrt(16) + 2",
            "(10 + 5) / 3",
            "2 ** 3",
            "abs(-15)",
            "round(3.14159, 2)",
            "max(10, 20, 5)",
            "calculate 15% of 200",
        ]

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get schema for tool parameters."""
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Mathematical expression to calculate",
                    "examples": ["2 + 3 * 4", "sqrt(16) + 2", "(10 + 5) / 3"],
                }
            },
            "required": ["input"],
        }


# Register with factory
from core.component_factory import ComponentFactory

ComponentFactory.register_tool("calculator", CalculatorTool)
