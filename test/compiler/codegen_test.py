"""
Unit tests for LLVM IR code generation.

Tests individual AST nodes and their LLVM IR generation.
"""

import unittest
from culebra.lexer import Lexer
from culebra.parser import Parser
from culebra.compiler.codegen import LLVMCodeGenerator


class CodeGenTest(unittest.TestCase):
    """Test LLVM IR code generation."""
    
    def _compile(self, source: str) -> str:
        """Helper to compile source to LLVM IR."""
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        parser = Parser(tokens)
        program = parser.parse()
        
        self.assertFalse(parser.has_error, f"Parser error: {parser.last_error}")
        
        codegen = LLVMCodeGenerator()
        return codegen.generate(program)
    
    def test_integer_literal(self):
        """Test integer literal generation."""
        source = "x = 42"
        ir = self._compile(source)
        
        self.assertIn("store i64 42", ir)
        self.assertIn("alloca i64", ir)
    
    def test_float_literal(self):
        """Test float literal generation."""
        source = "x = 3.14"
        ir = self._compile(source)
        
        self.assertIn("3.14", ir)
        self.assertIn("alloca double", ir)
    
    def test_string_literal(self):
        """Test string literal generation."""
        source = 'msg = "Hello"'
        ir = self._compile(source)
        
        self.assertIn("Hello", ir)
        self.assertIn("getelementptr", ir)
    
    def test_bool_literal(self):
        """Test boolean literal generation."""
        source = "flag = true"
        ir = self._compile(source)
        
        self.assertIn("store i1 1", ir)
    
    def test_arithmetic_operations(self):
        """Test arithmetic operations."""
        test_cases = [
            ("x = 1 + 2", "add i64"),
            ("x = 5 - 3", "sub i64"),
            ("x = 4 * 3", "mul i64"),
            ("x = 10 / 2", "sdiv i64"),
        ]
        
        for source, expected in test_cases:
            with self.subTest(source=source):
                ir = self._compile(source)
                self.assertIn(expected, ir)
    
    def test_comparison_operations(self):
        """Test comparison operations."""
        test_cases = [
            ("x = 5 > 3", "icmp sgt"),
            ("x = 5 < 3", "icmp slt"),
            ("x = 5 >= 3", "icmp sge"),
            ("x = 5 <= 3", "icmp sle"),
            ("x = 5 == 3", "icmp eq"),
            ("x = 5 != 3", "icmp ne"),
        ]
        
        for source, expected in test_cases:
            with self.subTest(source=source):
                ir = self._compile(source)
                self.assertIn(expected, ir)
    
    def test_logical_operations(self):
        """Test logical operations."""
        test_cases = [
            ("x = true and false", "and i1"),
            ("x = true or false", "or i1"),
        ]
        
        for source, expected in test_cases:
            with self.subTest(source=source):
                ir = self._compile(source)
                self.assertIn(expected, ir)
    
    def test_variable_assignment_and_load(self):
        """Test variable assignment and loading."""
        source = """
x = 10
y = x
"""
        ir = self._compile(source)
        
        # Should have alloca for both variables
        self.assertEqual(ir.count("alloca i64"), 2)
        # Should have store for both assignments
        self.assertIn("store i64 10", ir)
        # Should have load for reading x
        self.assertIn("load i64", ir)
    
    def test_if_statement(self):
        """Test if statement generation."""
        source = """
if 5 > 3:
    x = 1
"""
        ir = self._compile(source)
        
        self.assertIn("br i1", ir)
        self.assertIn("label %then", ir)
        self.assertIn("label %merge", ir)
    
    def test_if_else_statement(self):
        """Test if-else statement generation."""
        source = """
if 5 > 3:
    x = 1
else:
    x = 2
"""
        ir = self._compile(source)
        
        self.assertIn("label %then", ir)
        self.assertIn("label %else", ir)
        self.assertIn("label %merge", ir)
    
    def test_while_loop(self):
        """Test while loop generation."""
        source = """
x = 5
while x > 0:
    x = x - 1
"""
        ir = self._compile(source)
        
        self.assertIn("label %while_cond", ir)
        self.assertIn("label %while_body", ir)
        self.assertIn("label %while_end", ir)
    
    def test_for_loop(self):
        """Test for loop generation."""
        source = """
for i = 0; i < 5; i = i + 1:
    x = i
"""
        ir = self._compile(source)
        
        self.assertIn("label %for_cond", ir)
        self.assertIn("label %for_body", ir)
        self.assertIn("label %for_post", ir)
        self.assertIn("label %for_end", ir)
    
    def test_function_definition(self):
        """Test function definition."""
        source = """
def add(a, b):
    return a + b
"""
        ir = self._compile(source)
        
        self.assertIn("define i64 @add(i64 %a, i64 %b)", ir)
        self.assertIn("ret i64", ir)
    
    def test_function_call(self):
        """Test function call."""
        source = """
def square(x):
    return x * x

result = square(5)
"""
        ir = self._compile(source)
        
        self.assertIn("call i64 @square(i64 5)", ir)
    
    def test_print_builtin(self):
        """Test print built-in function."""
        source = 'print("Hello")'
        ir = self._compile(source)
        
        self.assertIn("culebra_print", ir)
    
    def test_array_creation(self):
        """Test array creation."""
        source = "arr = [1, 2, 3]"
        ir = self._compile(source)
        
        self.assertIn("call %array* @culebra_create_array", ir)
        self.assertIn("call void @culebra_array_set", ir)
    
    def test_array_access(self):
        """Test array element access."""
        source = """
arr = [1, 2, 3]
x = arr[0]
"""
        ir = self._compile(source)
        
        self.assertIn("call i8* @culebra_array_get", ir)
    
    def test_nested_expressions(self):
        """Test nested expressions."""
        source = "x = (5 + 3) * (10 - 2)"
        ir = self._compile(source)
        
        self.assertIn("add i64", ir)
        self.assertIn("sub i64", ir)
        self.assertIn("mul i64", ir)
    
    def test_string_constants(self):
        """Test string constant generation."""
        source = """
a = "Hello"
b = "World"
c = "Hello"
"""
        ir = self._compile(source)
        
        # Should reuse string constants
        self.assertIn("Hello", ir)
        self.assertIn("World", ir)
        # Count string constant definitions
        hello_count = ir.count('c"Hello\\00"')
        self.assertEqual(hello_count, 1, "String constant should be reused")
    
    def test_type_conversion(self):
        """Test automatic type conversion."""
        source = "x = 5 + 3.14"
        ir = self._compile(source)
        
        # Integer should be converted to float
        self.assertIn("sitofp i64", ir)
        self.assertIn("fadd double", ir)


class BuiltinFunctionsTest(unittest.TestCase):
    """Test built-in function code generation."""
    
    def _compile(self, source: str) -> str:
        """Helper to compile source to LLVM IR."""
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        parser = Parser(tokens)
        program = parser.parse()
        
        codegen = LLVMCodeGenerator()
        return codegen.generate(program)
    
    def test_print_single_arg(self):
        """Test print with single argument."""
        source = "print(42)"
        ir = self._compile(source)
        self.assertIn("culebra_print_int", ir)
    
    def test_print_multiple_args(self):
        """Test print with multiple arguments."""
        source = 'print("Hello", 42)'
        ir = self._compile(source)
        self.assertIn("culebra_print_multi", ir)
    
    def test_input_function(self):
        """Test input function."""
        source = 'x = input("Enter: ")'
        ir = self._compile(source)
        self.assertIn("call i8* @culebra_input", ir)
    
    def test_len_function(self):
        """Test len function."""
        source = 'x = len("Hello")'
        ir = self._compile(source)
        self.assertIn("call i64 @culebra_len", ir)
    
    def test_chr_function(self):
        """Test chr function."""
        source = "x = chr(65)"
        ir = self._compile(source)
        self.assertIn("call i8* @culebra_chr", ir)
    
    def test_ord_function(self):
        """Test ord function."""
        source = 'x = ord("A")'
        ir = self._compile(source)
        self.assertIn("call i64 @culebra_ord", ir)


if __name__ == '__main__':
    unittest.main()

