"""
Built-in Function Declarations for Culebra LLVM Compiler

This module defines LLVM declarations for built-in functions
that are implemented in the C runtime library.
"""

from typing import Dict, List, Tuple


# Built-in function declarations in LLVM IR
# Format: function_name -> (return_type, param_types, is_variadic)
BUILTIN_FUNCTIONS: Dict[str, Tuple[str, List[str], bool]] = {
    # I/O functions
    'print': ('void', ['i32'], True),  # variadic (dummy first param required by C)
    'input': ('i8*', ['i8*'], False),
    
    # String/Array functions
    'len': ('i64', ['i8*'], False),
    'chr': ('i8*', ['i64'], False),
    'ord': ('i64', ['i8*'], False),
    
    # Memory management (internal)
    '_malloc': ('i8*', ['i64'], False),
    '_free': ('void', ['i8*'], False),
}


def get_builtin_declarations() -> str:
    """
    Generate LLVM IR declarations for all built-in functions.
    
    Returns:
        String containing all LLVM declare statements
    """
    declarations = []
    
    for func_name, (return_type, param_types, is_variadic) in BUILTIN_FUNCTIONS.items():
        params_str = ', '.join(param_types)
        if is_variadic:
            if params_str:
                params_str += ', ...'
            else:
                params_str = '...'
        
        # Use culebra_ prefix for C functions
        c_name = f"culebra_{func_name}" if not func_name.startswith('_') else func_name[1:]
        declaration = f"declare {return_type} @{c_name}({params_str})"
        declarations.append(declaration)
    
    return '\n'.join(declarations)


def is_builtin(name: str) -> bool:
    """Check if a function name is a built-in."""
    return name in BUILTIN_FUNCTIONS


def get_builtin_signature(name: str) -> Tuple[str, List[str], bool]:
    """
    Get the signature of a built-in function.
    
    Returns:
        Tuple of (return_type, param_types, is_variadic)
    """
    return BUILTIN_FUNCTIONS.get(name, ('void', [], False))


# Additional built-in declarations can be added here
# Users can extend this dictionary to add custom C functions
CUSTOM_DECLARATIONS: Dict[str, str] = {}


def register_custom_builtin(name: str, return_type: str, param_types: List[str], is_variadic: bool = False):
    """
    Register a custom built-in function.
    
    Args:
        name: Function name (without culebra_ prefix)
        return_type: LLVM return type
        param_types: List of LLVM parameter types
        is_variadic: Whether the function is variadic
    """
    BUILTIN_FUNCTIONS[name] = (return_type, param_types, is_variadic)


def get_all_declarations() -> str:
    """Get all built-in and custom declarations."""
    declarations = [get_builtin_declarations()]
    
    if CUSTOM_DECLARATIONS:
        declarations.append('\n'.join(CUSTOM_DECLARATIONS.values()))
    
    return '\n\n'.join(declarations)

