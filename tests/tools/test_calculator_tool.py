"""
Unit tests for CalculatorTool.
"""

import pytest

from tools.calculator_tool import CalculatorTool


class TestCalculatorTool:
    """Test CalculatorTool functionality."""

    @pytest.fixture
    def calculator(self):
        """Create calculator tool instance."""
        config = {}
        return CalculatorTool(config)

    def test_tool_properties(self, calculator):
        """Test tool name and description."""
        assert calculator.name == "calculator"
        assert "mathematical calculations" in calculator.description.lower()

    def test_simple_addition(self, calculator):
        """Test simple addition."""
        result = calculator.execute("2 + 3")

        assert result.success is True
        assert "5" in result.content
        assert result.metadata["result"] == 5

    def test_simple_subtraction(self, calculator):
        """Test simple subtraction."""
        result = calculator.execute("10 - 4")

        assert result.success is True
        assert "6" in result.content
        assert result.metadata["result"] == 6

    def test_multiplication(self, calculator):
        """Test multiplication."""
        result = calculator.execute("6 * 7")

        assert result.success is True
        assert "42" in result.content
        assert result.metadata["result"] == 42

    def test_division(self, calculator):
        """Test division."""
        result = calculator.execute("15 / 3")

        assert result.success is True
        assert "5" in result.content
        assert result.metadata["result"] == 5.0

    def test_complex_expression(self, calculator):
        """Test complex mathematical expression."""
        result = calculator.execute("(2 + 3) * 4 - 1")

        assert result.success is True
        assert result.metadata["result"] == 19

    def test_exponentiation(self, calculator):
        """Test exponentiation."""
        result = calculator.execute("2 ** 3")

        assert result.success is True
        assert result.metadata["result"] == 8

    def test_modulo(self, calculator):
        """Test modulo operation."""
        result = calculator.execute("10 % 3")

        assert result.success is True
        assert result.metadata["result"] == 1

    def test_functions(self, calculator):
        """Test mathematical functions."""
        # Test abs function
        result = calculator.execute("abs(-5)")
        assert result.success is True
        assert result.metadata["result"] == 5

        # Test round function
        result = calculator.execute("round(3.14159, 2)")
        assert result.success is True
        assert result.metadata["result"] == 3.14

        # Test max function
        result = calculator.execute("max(1, 5, 3)")
        assert result.success is True
        assert result.metadata["result"] == 5

    def test_normalize_expression(self, calculator):
        """Test expression normalization."""
        # Test removing prefixes
        assert calculator._normalize_expression("calculate 2 + 2") == "2+2"
        assert calculator._normalize_expression("compute 5 * 3") == "5*3"
        assert calculator._normalize_expression("eval 10 / 2") == "10/2"

        # Test symbol replacement
        assert calculator._normalize_expression("2 x 3") == "2*3"
        assert calculator._normalize_expression("4 ÷ 2") == "4/2"
        assert calculator._normalize_expression("2 ^ 3") == "2**3"

    def test_input_validation(self, calculator):
        """Test input validation."""
        # Valid input
        assert calculator.validate_input("2 + 2") is True
        assert calculator.validate_input("calculate sqrt(16)") is True

        # Invalid input
        assert calculator.validate_input("") is False
        assert calculator.validate_input("   ") is False

    def test_empty_input(self, calculator):
        """Test handling empty input."""
        result = calculator.execute("")

        assert result.success is False
        assert "provide a mathematical expression" in result.error_message.lower()

    def test_invalid_expression(self, calculator):
        """Test handling invalid mathematical expressions."""
        result = calculator.execute("2 + * 3")  # Actually invalid syntax

        assert result.success is False
        assert (
            "invalid" in result.error_message.lower()
            or "error" in result.error_message.lower()
        )

    def test_unsafe_operations(self, calculator):
        """Test handling of potentially unsafe operations."""
        # Test division by zero
        result = calculator.execute("1 / 0")

        assert result.success is False
        assert result.error_message is not None

    def test_format_result(self, calculator):
        """Test result formatting."""
        # Integer result
        assert calculator._format_result(5.0) == "5"
        assert calculator._format_result(5) == "5"

        # Float result
        formatted = calculator._format_result(3.14159)
        assert "3.14159" in formatted

        # Very small float
        formatted = calculator._format_result(0.000001)
        assert "1e-06" in formatted or "0.000001" in formatted

    def test_usage_examples(self, calculator):
        """Test that usage examples are valid."""
        examples = calculator.get_usage_examples()

        assert len(examples) > 0

        # Test that examples are actually valid
        for example in examples[:3]:  # Test first 3 examples
            if any(char in example for char in "+-*/()"):  # Skip non-math examples
                result = calculator.execute(example)
                # Should either succeed or fail gracefully
                assert isinstance(result.success, bool)

    def test_parameter_schema(self, calculator):
        """Test parameter schema."""
        schema = calculator.get_parameter_schema()

        assert "type" in schema
        assert "properties" in schema
        assert "input" in schema["properties"]
        assert "required" in schema
        assert "input" in schema["required"]

    def test_scientific_notation(self, calculator):
        """Test scientific notation handling."""
        result = calculator.execute("1e3 + 1e2")

        assert result.success is True
        assert result.metadata["result"] == 1100

    def test_negative_numbers(self, calculator):
        """Test negative number handling."""
        result = calculator.execute("-5 + 3")

        assert result.success is True
        assert result.metadata["result"] == -2

    def test_parentheses(self, calculator):
        """Test parentheses handling."""
        result = calculator.execute("(2 + 3) * (4 - 1)")

        assert result.success is True
        assert result.metadata["result"] == 15


class TestCalculatorToolSafety:
    """Test calculator tool safety features."""

    @pytest.fixture
    def calculator(self):
        """Create calculator tool instance."""
        return CalculatorTool({})

    def test_no_import_allowed(self, calculator):
        """Test that import statements are not allowed."""
        result = calculator.execute("import os")

        assert result.success is False

    def test_no_exec_allowed(self, calculator):
        """Test that exec is not allowed."""
        result = calculator.execute("exec('print(1)')")

        assert result.success is False

    def test_no_eval_allowed(self, calculator):
        """Test that eval is not allowed in unsafe ways."""
        result = calculator.execute("eval('2+2')")

        assert result.success is False

    def test_safe_mathematical_operations_only(self, calculator):
        """Test that only safe mathematical operations are allowed."""
        safe_operations = [
            "2 + 2",
            "3.14 * 2",
            "abs(-5)",
            "round(3.14159, 2)",
            "max(1, 2, 3)",
            "min(1, 2, 3)",
            "sum([1, 2, 3])",
        ]

        for operation in safe_operations:
            result = calculator.execute(operation)
            assert result.success is True, f"Safe operation failed: {operation}"


# Example unittest.TestCase version (commented out)
"""
import unittest
from tools.calculator_tool import CalculatorTool

class TestCalculatorToolUnittest(unittest.TestCase):
    '''Example unittest.TestCase version'''

    def setUp(self):
        '''Set up calculator for each test.'''
        self.calculator = CalculatorTool({})

    def test_simple_addition(self):
        '''Test simple addition.'''
        result = self.calculator.execute("2 + 3")

        self.assertTrue(result.success)
        self.assertIn("5", result.content)
        self.assertEqual(result.metadata['result'], 5)

    def test_invalid_expression(self):
        '''Test invalid expression handling.'''
        result = self.calculator.execute("2 + + 3")

        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)

    def test_tool_properties(self):
        '''Test tool properties.'''
        self.assertEqual(self.calculator.name, "calculator")
        self.assertIn("mathematical", self.calculator.description.lower())

if __name__ == '__main__':
    unittest.main()
"""
