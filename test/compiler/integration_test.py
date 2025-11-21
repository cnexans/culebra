"""
Integration tests for the Culebra compiler.

These tests compile and execute complete programs, comparing output
with the interpreter.
"""

import unittest
import tempfile
import subprocess
import os
from pathlib import Path
from culebra.compiler.compiler import compile_to_executable
from culebra.interpreter.interpreter import Interpreter
from culebra.lexer import Lexer
from culebra.parser import Parser
from io import StringIO
import sys


class IntegrationTest(unittest.TestCase):
    """Integration tests for compiler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _compile_and_run(self, source: str) -> str:
        """
        Compile source code and run the resulting executable.
        
        Returns stdout from the executable.
        """
        # Write source to temporary file
        source_file = os.path.join(self.temp_dir, "test.culebra")
        with open(source_file, 'w') as f:
            f.write(source)
        
        # Compile
        output_file = os.path.join(self.temp_dir, "test_program")
        success = compile_to_executable(
            source_file=source_file,
            output_file=output_file,
            optimize=False
        )
        
        self.assertTrue(success, "Compilation should succeed")
        self.assertTrue(os.path.exists(output_file), "Executable should be created")
        
        # Run
        result = subprocess.run(
            [output_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        self.assertEqual(result.returncode, 0, f"Program should exit successfully. stderr: {result.stderr}")
        return result.stdout
    
    def _interpret(self, source: str) -> str:
        """
        Interpret source code and capture output.
        
        Returns captured stdout.
        """
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            lexer = Lexer()
            tokens = lexer.tokenize(source)
            parser = Parser(tokens)
            program = parser.parse()
            
            interpreter = Interpreter()
            interpreter.evaluate(program)
            
            output = sys.stdout.getvalue()
            return output
        finally:
            sys.stdout = old_stdout
    
    def test_hello_world(self):
        """Test simple hello world program."""
        source = 'print("Hello, World!")'
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "Hello, World!")
    
    def test_arithmetic(self):
        """Test arithmetic operations."""
        source = """
print(5 + 3)
print(10 - 4)
print(6 * 7)
print(20 / 4)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
    
    def test_variables(self):
        """Test variable assignment and usage."""
        source = """
x = 10
y = 20
z = x + y
print(z)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "30")
    
    def test_conditionals(self):
        """Test if-else statements."""
        source = """
x = 10
if x > 5:
    print("x is greater than 5")
else:
    print("x is not greater than 5")
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
    
    def test_while_loop(self):
        """Test while loops."""
        source = """
x = 5
sum = 0
while x > 0:
    sum = sum + x
    x = x - 1
print(sum)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "15")
    
    def test_for_loop(self):
        """Test for loops."""
        source = """
sum = 0
for i = 1; i <= 5; i = i + 1:
    sum = sum + i
print(sum)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "15")
    
    def test_functions(self):
        """Test function definitions and calls."""
        source = """
def square(x):
    return x * x

def add(a, b):
    return a + b

print(square(5))
print(add(3, 7))
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
    
    def test_recursive_function(self):
        """Test recursive functions."""
        source = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "120")
    
    def test_fibonacci(self):
        """Test Fibonacci function."""
        source = """
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(7))
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "13")
    
    def test_comparison_operators(self):
        """Test comparison operators."""
        source = """
print(5 > 3)
print(5 < 3)
print(5 >= 5)
print(5 <= 5)
print(5 == 5)
print(5 != 3)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
    
    def test_logical_operators(self):
        """Test logical operators."""
        source = """
print(true and true)
print(true and false)
print(false or true)
print(false or false)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
    
    def test_nested_loops(self):
        """Test nested loops."""
        source = """
sum = 0
for i = 1; i <= 3; i = i + 1:
    for j = 1; j <= 3; j = j + 1:
        sum = sum + 1
print(sum)
"""
        
        compiled_output = self._compile_and_run(source)
        interpreted_output = self._interpret(source)
        
        self.assertEqual(compiled_output, interpreted_output)
        self.assertEqual(compiled_output.strip(), "9")
    
    def test_mixed_types(self):
        """Test mixed type operations."""
        source = """
x = 5
y = 3.14
z = x + y
print(z)
"""
        
        # Note: This might have slight floating point differences
        compiled_output = self._compile_and_run(source)
        self.assertIn("8.14", compiled_output)


class ExampleProgramsTest(unittest.TestCase):
    """Test compilation of example programs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.examples_dir = Path(__file__).parent.parent.parent / 'examples'
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _test_example(self, example_file: str, expected_substring: str = None):
        """
        Test compilation of an example file.
        
        Args:
            example_file: Name of example file
            expected_substring: Optional substring to check in output
        """
        source_file = self.examples_dir / example_file
        
        if not source_file.exists():
            self.skipTest(f"Example file {example_file} not found")
        
        output_file = os.path.join(self.temp_dir, "example_program")
        
        success = compile_to_executable(
            source_file=str(source_file),
            output_file=output_file,
            optimize=True
        )
        
        self.assertTrue(success, f"Compilation of {example_file} should succeed")
        self.assertTrue(os.path.exists(output_file), "Executable should be created")
        
        # Note: Can't run examples that require input without mocking
        # Just verify compilation succeeds for now
    
    def test_hello_world_example(self):
        """Test hello_world.culebra example."""
        self._test_example("hello_world.culebra")
    
    def test_loops_example(self):
        """Test loops.culebra example."""
        self._test_example("loops.culebra")
    
    def test_fibonacci_example(self):
        """Test fibunacci.culebra example."""
        self._test_example("fibunacci.culebra")


if __name__ == '__main__':
    unittest.main()

