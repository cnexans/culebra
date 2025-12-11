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
            elif isinstance(node, ast.Map):
                return self.evaluate_map(node, environment)
            elif isinstance(node, ast.Set):
                return self.evaluate_set(node, environment)
            elif isinstance(node, ast.Tuple):
                return self.evaluate_tuple(node, environment)
            elif isinstance(node, ast.DotAccess):
                return self.evaluate_dot_access(node, environment)
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
        
        # Handle maps (dicts) - key can be any hashable type
        if isinstance(target, dict):
            if not isinstance(index, (str, int, float, bool, tuple)):
                raise TypeError(f"Map keys must be hashable (string, number, bool, or tuple), got {type(index).__name__}")
            if index not in target:
                raise KeyError(f"Key not found: {index}")
            return target[index]
        
        # Handle arrays, strings, and tuples - index must be an integer
        if isinstance(target, (str, list, tuple)):
            if not isinstance(index, int):
                raise TypeError(f"Index must be an integer, got {type(index).__name__}")
            
            # Check index bounds
            if index < 0 or index >= len(target):
                raise IndexError(f"Index {index} out of range for {type(target).__name__} of length {len(target)}")
            
            return target[index]
        
        # Unsupported type
        raise TypeError(f"Bracket access only supports arrays, strings, tuples, and maps, got {type(target).__name__}")

    def evaluate_array(self, node, environment):
        # Evaluate each element in the array
        return [self.eval_node(element, environment) for element in node.elements]

    def evaluate_map(self, node, environment):
        # Evaluate each key-value pair in the map
        result = {}
        for key_node, value_node in node.pairs:
            key = self.eval_node(key_node, environment)
            value = self.eval_node(value_node, environment)
            # Keys must be hashable (strings, numbers, tuples, bools)
            if not isinstance(key, (str, int, float, bool, tuple)):
                raise TypeError(f"Map keys must be hashable (string, number, bool, or tuple), got {type(key).__name__}")
            result[key] = value
        return result

    def evaluate_set(self, node, environment):
        # Evaluate each element in the set
        result = set()
        for element_node in node.elements:
            element = self.eval_node(element_node, environment)
            # Set elements must be hashable
            if not isinstance(element, (str, int, float, bool, tuple)):
                raise TypeError(f"Set elements must be hashable (string, number, bool, or tuple), got {type(element).__name__}")
            result.add(element)
        return result

    def evaluate_tuple(self, node, environment):
        # Evaluate each element in the tuple and return as Python tuple
        return tuple(self.eval_node(element, environment) for element in node.elements)

    def evaluate_dot_access(self, node, environment):
        # This will be implemented in the next step with method dispatch
        target = self.eval_node(node.target, environment)
        method_name = node.method_name
        arguments = [self.eval_node(arg, environment) for arg in node.arguments]
        
        # Dispatch to the appropriate method based on the target type and method name
        return self.dispatch_method(target, method_name, arguments)

    def dispatch_method(self, target, method_name, arguments):
        """Dispatch method calls based on target type and method name."""
        target_type = type(target).__name__
        
        # Array methods
        if isinstance(target, list):
            if method_name == "push":
                if len(arguments) != 1:
                    raise TypeError(f"push() takes exactly 1 argument ({len(arguments)} given)")
                target.append(arguments[0])
                return None
            elif method_name == "pop":
                if len(arguments) != 0:
                    raise TypeError(f"pop() takes no arguments ({len(arguments)} given)")
                if len(target) == 0:
                    raise IndexError("pop from empty list")
                return target.pop()
            elif method_name == "sort":
                if len(arguments) != 0:
                    raise TypeError(f"sort() takes no arguments ({len(arguments)} given)")
                target.sort()
                return None
            else:
                raise AttributeError(f"Array has no method '{method_name}'")
        
        # Map (dict) methods
        elif isinstance(target, dict):
            if method_name == "get":
                if len(arguments) != 1:
                    raise TypeError(f"get() takes exactly 1 argument ({len(arguments)} given)")
                key = arguments[0]
                return target.get(key, None)
            elif method_name == "set":
                if len(arguments) != 2:
                    raise TypeError(f"set() takes exactly 2 arguments ({len(arguments)} given)")
                key, value = arguments
                if not isinstance(key, (str, int, float, bool, tuple)):
                    raise TypeError(f"Map keys must be hashable (string, number, bool, or tuple), got {type(key).__name__}")
                target[key] = value
                return None
            elif method_name == "has":
                if len(arguments) != 1:
                    raise TypeError(f"has() takes exactly 1 argument ({len(arguments)} given)")
                key = arguments[0]
                return key in target
            elif method_name == "remove":
                if len(arguments) != 1:
                    raise TypeError(f"remove() takes exactly 1 argument ({len(arguments)} given)")
                key = arguments[0]
                if key in target:
                    del target[key]
                    return None
                else:
                    raise KeyError(f"Key not found: {key}")
            else:
                raise AttributeError(f"Map has no method '{method_name}'")
        
        # Set methods
        elif isinstance(target, set):
            if method_name == "add":
                if len(arguments) != 1:
                    raise TypeError(f"add() takes exactly 1 argument ({len(arguments)} given)")
                element = arguments[0]
                if not isinstance(element, (str, int, float, bool, tuple)):
                    raise TypeError(f"Set elements must be hashable (string, number, bool, or tuple), got {type(element).__name__}")
                target.add(element)
                return None
            elif method_name == "remove":
                if len(arguments) != 1:
                    raise TypeError(f"remove() takes exactly 1 argument ({len(arguments)} given)")
                element = arguments[0]
                if element in target:
                    target.remove(element)
                    return None
                else:
                    raise KeyError(f"Element not found: {element}")
            elif method_name == "has":
                if len(arguments) != 1:
                    raise TypeError(f"has() takes exactly 1 argument ({len(arguments)} given)")
                element = arguments[0]
                return element in target
            else:
                raise AttributeError(f"Set has no method '{method_name}'")
        
        # String methods
        elif isinstance(target, str):
            if method_name == "split":
                if len(arguments) != 1:
                    raise TypeError(f"split() takes exactly 1 argument ({len(arguments)} given)")
                delimiter = arguments[0]
                if not isinstance(delimiter, str):
                    raise TypeError(f"split() delimiter must be a string, got {type(delimiter).__name__}")
                return target.split(delimiter)
            else:
                raise AttributeError(f"String has no method '{method_name}'")
        
        # Tuple methods
        elif isinstance(target, tuple):
            raise AttributeError(f"Tuple has no method '{method_name}' (tuples are immutable)")
        
        else:
            raise TypeError(f"Type '{target_type}' has no methods")

    def load_builtins(self):
        # Add built-in functions to the global environment.
        self.root_environment.assign("print", BuiltinFunction(builtin_print))
        self.root_environment.assign("input", BuiltinFunction(builtin_input))
        self.root_environment.assign("len", BuiltinFunction(builtin_len))
        self.root_environment.assign("chr", BuiltinFunction(builtin_chr))
        self.root_environment.assign("ord", BuiltinFunction(builtin_ord))
        self.root_environment.assign("Map", BuiltinFunction(builtin_map))
        self.root_environment.assign("Set", BuiltinFunction(builtin_set))
        self.root_environment.assign("read_file", BuiltinFunction(builtin_read_file))
        self.root_environment.assign("read_lines", BuiltinFunction(builtin_read_lines))
        self.root_environment.assign("int", BuiltinFunction(builtin_int))
        self.root_environment.assign("float", BuiltinFunction(builtin_float))
        self.root_environment.assign("str", BuiltinFunction(builtin_str))
        self.root_environment.assign("abs", BuiltinFunction(builtin_abs))

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

def builtin_map():
    """Create an empty map (dict)"""
    return {}

def builtin_set():
    """Create an empty set"""
    return set()

def builtin_read_file(path):
    """Read entire file as a single string"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except IOError as e:
        raise IOError(f"Error reading file {path}: {e}")

def builtin_read_lines(path):
    """Read file as an array of lines (without newline characters)"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Read lines and strip newline characters
            return [line.rstrip('\n\r') for line in f.readlines()]
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except IOError as e:
        raise IOError(f"Error reading file {path}: {e}")

def builtin_int(value):
    """Convert value to integer"""
    try:
        if isinstance(value, str):
            return int(value)
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            raise TypeError(f"Cannot convert {type(value).__name__} to int")
    except ValueError as e:
        raise ValueError(f"Invalid literal for int(): {value}")

def builtin_float(value):
    """Convert value to float"""
    try:
        if isinstance(value, str):
            return float(value)
        elif isinstance(value, (int, float)):
            return float(value)
        else:
            raise TypeError(f"Cannot convert {type(value).__name__} to float")
    except ValueError as e:
        raise ValueError(f"Invalid literal for float(): {value}")

def builtin_str(value):
    """Convert value to string"""
    return str(value)

def builtin_abs(value):
    """Return absolute value of a number"""
    if not isinstance(value, (int, float)):
        raise TypeError(f"abs() requires numeric argument, got {type(value).__name__}")
    return abs(value)

