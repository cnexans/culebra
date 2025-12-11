from unittest import TestCase

from culebra.interpreter.interpreter import Interpreter
from culebra.lexer import Lexer
from culebra.parser import Parser
from culebra.type_checker import TypeErrorException

class TestTypeChecker(TestCase):
    def _run_error(self, source, msg):
        tokens = Lexer().tokenize(source)
        parser = Parser(tokens)
        program = parser.parse()
        interpreter = Interpreter()
        with self.assertRaisesRegex(TypeErrorException, msg):
            interpreter.evaluate(program)

    def _run_ok(self, source):
        tokens = Lexer().tokenize(source)
        parser = Parser(tokens)
        program = parser.parse()
        interpreter = Interpreter()
        try:
            interpreter.evaluate(program)
        except TypeErrorException as e:
            self.fail(f"Unexpected type error: {e}")

    def test_array_mixed_types(self):
        source = "a = [1, true]"
        self._run_error(source, "Array elements must be of the same type")

    def test_binary_type_mismatch(self):
        source = "a = 1 + true"
        self._run_error(source, "Operands for PLUS must have the same type")

    def test_array_assignment_mismatch(self):
        source = """
arr = [1,2]
arr[0] = "x"
"""
        self._run_error(source, "Cannot assign StringType to array of IntType")

    def test_valid_cases(self):
        self._run_ok("a = [1,2]")
        self._run_ok("b = 1 + 2")
        self._run_ok("""
arr = [1,2]
arr[0] = 3
""")

