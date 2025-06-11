from culebra import ast
from culebra.interpreter.environment import Environment
from culebra.token import TokenType
from culebra.type_checker import TypeChecker, TypeErrorException

"""
Culebra Interpreter Implementation
================================

Execution Model:
┌─────────────────────────────────────────────────────────────────┐
│                        Interpreter                              │
│  ┌─────────────┐    ┌────────────┐    ┌──────────────────┐      │
│  │    AST      │ -> │ Evaluator  │ -> │    Runtime       │      │
│  │   Nodes     │    │  Methods   │    │   Environment    │      │
│  └─────────────┘    └────────────┘    └──────────────────┘      │
│         │                 │                    │                │
│     Programs        visit_methods          Variables            │
│    Statements       Expressions             Functions           │
│    Expressions      Operations             Call Stack           │
└─────────────────────────────────────────────────────────────────┘

Environment Stack:
┌────────────────┐    ┌─────────────────────┐
│  Call Frames   │    │    Scope Example    │
├────────────────┤    ├─────────────────────┤
│  Global Scope  │    │ def foo(x):         │
│  Function foo  │    │   y = 2             │
│  Function bar  │    │   def bar():        │
└────────────────┘    │     return x + y    │
        ▲             │   return bar()      │
        │             └─────────────────────┘
        └── Each frame contains its own symbol table

Memory Model:
┌──────────────────────┐
│   Runtime Memory     │
├──────────────────────┤
│ ┌────────────────┐   │    ┌─────────────────┐
│ │  Value Stack   │   │    │  Value Types    │
│ ├────────────────┤   │    ├─────────────────┤
│ │ Temp Results   │   │    │ Number          │
│ │ Function Args  │   │    │ String          │
│ │ Return Values  │   │    │ Boolean         │
│ └────────────────┘   │    │ Function        │
│                      │    │ None            │
│ ┌────────────────┐   │    └─────────────────┘
│ │ Symbol Tables  │   │
│ ├────────────────┤   │
│ │ Variables      │   │
│ │ Functions      │   │
│ └────────────────┘   │
└──────────────────────┘

Execution Flow:
┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐
│   AST   │   │ Visit   │   │ Evaluate │   │ Update   │
│  Node   │-->│ Method  │-->│ Children │-->│  State   │
└─────────┘   └─────────┘   └──────────┘   └──────────┘

Error Handling:
┌────────────────────┐   ┌────────────────────┐
│  Runtime Errors    │   │   Error Types      │
├────────────────────┤   ├────────────────────┤
│ Type Mismatches    │   │ TypeError          │
│ Undefined Names    │   │ NameError          │
│ Division by Zero   │   │ ZeroDivisionError  │
│ Stack Overflow     │   │ RuntimeError       │
└────────────────────┘   └────────────────────┘

Implementation Notes:
- Visitor pattern used to traverse and evaluate AST nodes
- Environment maintains lexical scoping through stack-based frames
- Each function call creates a new environment frame
- Variables and functions stored in symbol tables
- Runtime errors include stack traces and line numbers
- Built-in functions implemented as native Python callables
"""

# Create a custom exception for function returns.
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

# Function object stores the function definition with its closure.
class Function:
    def __init__(self, name, arguments, body, closure):
        self.name = name
        self.arguments = arguments  # list of parameter names
        self.body = body            # AST node representing the function body
        self.closure = closure      # environment at the time of definition

    def call(self, interpreter, arguments):
        # Create a child environment for the function execution.
        function_env = self.closure.create_child()
        for arg_name, arg_value in zip(self.arguments, arguments):
            function_env.assign(arg_name, arg_value)
        try:
            interpreter.eval_node(self.body, function_env)
        except ReturnValue as rv:
            return rv.value
        return None

class Interpreter:
    def __init__(self):
        self.root_environment = Environment()
        self.load_builtins()  # Load built-in functions into the environment
        self.last_error = None
        self.last_node = None

    @property
    def has_error(self):
        return self.last_error is not None

    def evaluate(self, program: ast.Program):
        self.last_error = None
        self.last_node = None
        # Run type checker before interpretation
        try:
            TypeChecker().check(program)
        except TypeErrorException as e:
            self.last_error = e
            raise e
        return self.eval_node(program, self.root_environment)

    def eval_node(self, node, environment):
        try:
            # Dispatch evaluation based on the type of AST node.
            if isinstance(node, ast.Identifier):
                return self.evaluate_identifier(node, environment)
            elif isinstance(node, ast.Assignment):
                return self.evaluate_assignment(node, environment)
            elif isinstance(node, ast.LiteralValue):
                return self.evaluate_literal(node, environment)
            elif isinstance(node, (ast.Program, ast.Block)):
                return self.evaluate_block(node, environment)
            elif isinstance(node, ast.BinaryOperation):
                return self.evaluate_binary_operation(node, environment)
            elif isinstance(node, ast.PrefixOperation):
                return self.evaluate_prefix_operation(node, environment)
            elif isinstance(node, ast.Conditional):
                return self.evaluate_conditional(node, environment)
            elif isinstance(node, ast.While):
                return self.evaluate_while(node, environment)
            elif isinstance(node, ast.For):
                return self.evaluate_for(node, environment)
            elif isinstance(node, ast.FunctionDefinition):
                return self.evaluate_function_definition(node, environment)
            elif isinstance(node, ast.FunctionCall):
                return self.evaluate_function_call(node, environment)
            elif isinstance(node, ast.ReturnStatement):
                return self.evaluate_return(node, environment)
            elif isinstance(node, ast.BracketAccess):
                return self.evaluate_bracket_access(node, environment)
            elif isinstance(node, ast.Array):
                return self.evaluate_array(node, environment)
            else:
                raise TypeError(f"Unexpected AST node type: {type(node)}")
        except Exception as e:
            if not self.has_error:
                self.last_error = e
                self.last_node = node
            raise e

    def evaluate_identifier(self, node, environment):
        # AST Identifier: node.value holds the variable name.
        return environment.get(node.value)

    def evaluate_assignment(self, node, environment):
        assert type(node.identifier) in [ast.Identifier, ast.BracketAccess]
        if isinstance(node.identifier, ast.Identifier):
            # Evaluate the value and assign it to the variable in the current environment.
            value = self.eval_node(node.value, environment)
            environment.assign(node.identifier.value, value)
        else:
            # Evaluate the value and assign it to the array in the current environment.
            value = self.eval_node(node.value, environment)
            container = self.eval_node(node.identifier.target, environment)
            index = self.eval_node(node.identifier.index, environment)
            environment.assign_bracket(container, index, value)

        return None

    def evaluate_literal(self, node, environment):
        return node.value

    def evaluate_block(self, node, environment):
        result = None
        for stmt in node.statements:
            result = self.eval_node(stmt, environment)
        return result

    def evaluate_binary_operation(self, node, environment):
        left = self.eval_node(node.left, environment)
        right = self.eval_node(node.right, environment)
        tt = node.token.type

        # Arithmetic
        if tt == TokenType.PLUS:
            return left + right
        elif tt == TokenType.MINUS:
            return left - right
        elif tt == TokenType.MUL:
            return left * right
        elif tt == TokenType.DIV:
            return left / right

        # Comparison
        elif tt == TokenType.EQUAL:
            return left == right
        elif tt == TokenType.NOT_EQUAL:
            return left != right
        elif tt == TokenType.LESS:
            return left < right
        elif tt == TokenType.GREATER:
            return left > right
        elif tt == TokenType.LESS_EQ:
            return left <= right
        elif tt == TokenType.GREATER_EQ:
            return left >= right

        # Logical
        elif tt == TokenType.OR:
            return left or right
        elif tt == TokenType.AND:
            return left and right

        raise AssertionError(f"Unexpected binary operation token {node.token}")

    def evaluate_prefix_operation(self, node, environment):
        operand = self.eval_node(node.value, environment)
        tt = node.token.type
        if tt == TokenType.MINUS:
            return -operand
        elif tt == TokenType.NOT:
            return not operand
        raise AssertionError(f"Unexpected prefix operation token {node.token}")

    def evaluate_conditional(self, node, environment):
        condition = self.eval_node(node.condition, environment)
        if condition:
            return self.eval_node(node.body, environment)
        elif node.otherwise:
            return self.eval_node(node.otherwise, environment)
        return None

    def evaluate_while(self, node, environment):
        while self.eval_node(node.condition, environment):
            self.eval_node(node.body, environment)
        return None

    def evaluate_for(self, node, environment):
        self.eval_node(node.pre, environment)
        while self.eval_node(node.condition, environment):
            self.eval_node(node.body, environment)
            self.eval_node(node.post, environment)
        return None

    def evaluate_function_definition(self, node, environment):
        name = node.name.value
        arguments = [arg.value for arg in node.arguments]
        function = Function(name, arguments, node.body, environment)
        environment.assign(name, function)
        return None

    def evaluate_function_call(self, node, environment):
        function_obj = environment.get(node.function.value)
        if not hasattr(function_obj, "call"):
            raise Exception(f"{node.function.value} is not callable")
        evaluated_args = [self.eval_node(arg, environment) for arg in node.arguments]
        return function_obj.call(self, evaluated_args)

    def evaluate_return(self, node, environment):
        value = self.eval_node(node.value, environment)
        raise ReturnValue(value)

    def evaluate_bracket_access(self, node, environment):
        target = self.eval_node(node.target, environment)
        index = self.eval_node(node.index, environment)
        
        # Ensure index is an integer
        if not isinstance(index, int):
            raise TypeError(f"Index must be an integer, got {type(index)}")
        
        # Support both strings and arrays
        if not isinstance(target, (str, list)):
            raise TypeError(f"Bracket access only supports strings and arrays, got {type(target)}")
        
        # Check index bounds
        if index < 0 or index >= len(target):
            raise IndexError(f"Index {index} out of range for {type(target)} of length {len(target)}")
        
        return target[index]

    def evaluate_array(self, node, environment):
        # Evaluate each element in the array
        return [self.eval_node(element, environment) for element in node.elements]

    def load_builtins(self):
        # Add built-in functions to the global environment.
        self.root_environment.assign("print", BuiltinFunction(builtin_print))
        self.root_environment.assign("input", BuiltinFunction(builtin_input))
        self.root_environment.assign("len", BuiltinFunction(builtin_len))
        self.root_environment.assign("chr", BuiltinFunction(builtin_chr))
        self.root_environment.assign("ord", BuiltinFunction(builtin_ord))

##############################
# Built-in function wrapper and definitions
##############################
class BuiltinFunction:
    def __init__(self, func):
        self.func = func

    def call(self, interpreter, arguments):
        return self.func(*arguments)

def builtin_print(*args):
    print(*args)
    return None

def builtin_input(prompt=""):
    return input(prompt)

def builtin_len(x):
    return len(x)

def builtin_chr(x):
    return chr(x)

def builtin_ord(x):
    return ord(x)

