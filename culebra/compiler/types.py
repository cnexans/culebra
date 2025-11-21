"""
LLVM Type System for Culebra

Maps Culebra runtime types to LLVM IR types.
"""

from enum import Enum
from typing import Optional


class CulebraType(Enum):
    """Culebra runtime type enumeration."""
    INTEGER = "int"
    FLOAT = "float"
    BOOL = "bool"
    STRING = "string"
    ARRAY = "array"
    VOID = "void"
    FUNCTION = "function"
    UNKNOWN = "unknown"


class LLVMType:
    """Represents an LLVM type."""
    
    def __init__(self, llvm_repr: str, culebra_type: CulebraType):
        self.llvm_repr = llvm_repr
        self.culebra_type = culebra_type
    
    def __str__(self) -> str:
        return self.llvm_repr
    
    def __repr__(self) -> str:
        return f"LLVMType({self.llvm_repr}, {self.culebra_type})"


# Standard LLVM type mappings
I64 = LLVMType("i64", CulebraType.INTEGER)
DOUBLE = LLVMType("double", CulebraType.FLOAT)
I1 = LLVMType("i1", CulebraType.BOOL)
I8_PTR = LLVMType("i8*", CulebraType.STRING)
VOID = LLVMType("void", CulebraType.VOID)

# Array type: struct { i64 length, i8* data }
ARRAY_STRUCT = LLVMType("%array", CulebraType.ARRAY)
ARRAY_PTR = LLVMType("%array*", CulebraType.ARRAY)


def get_llvm_type(culebra_type: CulebraType) -> LLVMType:
    """Get LLVM type from Culebra type."""
    mapping = {
        CulebraType.INTEGER: I64,
        CulebraType.FLOAT: DOUBLE,
        CulebraType.BOOL: I1,
        CulebraType.STRING: I8_PTR,
        CulebraType.ARRAY: ARRAY_PTR,
        CulebraType.VOID: VOID,
    }
    return mapping.get(culebra_type, I64)


def infer_type_from_value(value) -> CulebraType:
    """Infer Culebra type from Python value."""
    if isinstance(value, bool):
        return CulebraType.BOOL
    elif isinstance(value, int):
        return CulebraType.INTEGER
    elif isinstance(value, float):
        return CulebraType.FLOAT
    elif isinstance(value, str):
        return CulebraType.STRING
    elif isinstance(value, list):
        return CulebraType.ARRAY
    return CulebraType.UNKNOWN


def get_binary_result_type(left_type: CulebraType, right_type: CulebraType, op: str) -> CulebraType:
    """
    Determine result type of binary operation.
    
    Handles type coercion:
    - int op int -> int
    - float op float -> float
    - int op float -> float
    - float op int -> float
    - Comparison ops always return bool
    - Logical ops always return bool
    """
    # Comparison and logical operations always return bool
    comparison_ops = ['==', '!=', '<', '>', '<=', '>=']
    logical_ops = ['and', 'or']
    
    if op in comparison_ops or op in logical_ops:
        return CulebraType.BOOL
    
    # Arithmetic operations - float takes precedence
    if left_type == CulebraType.FLOAT or right_type == CulebraType.FLOAT:
        return CulebraType.FLOAT
    
    # String concatenation
    if left_type == CulebraType.STRING or right_type == CulebraType.STRING:
        if op == '+':
            return CulebraType.STRING
    
    # Default to integer
    return CulebraType.INTEGER


def needs_type_conversion(from_type: CulebraType, to_type: CulebraType) -> bool:
    """Check if type conversion is needed."""
    return from_type != to_type and from_type != CulebraType.UNKNOWN and to_type != CulebraType.UNKNOWN


def get_conversion_instruction(from_type: CulebraType, to_type: CulebraType) -> Optional[str]:
    """
    Get LLVM instruction for type conversion.
    Returns instruction name (e.g., 'sitofp', 'fptosi').
    """
    if from_type == to_type:
        return None
    
    conversions = {
        (CulebraType.INTEGER, CulebraType.FLOAT): 'sitofp',  # signed int to float
        (CulebraType.FLOAT, CulebraType.INTEGER): 'fptosi',  # float to signed int
        (CulebraType.INTEGER, CulebraType.BOOL): 'trunc',    # int to bool
        (CulebraType.BOOL, CulebraType.INTEGER): 'zext',     # bool to int (zero extend)
    }
    
    return conversions.get((from_type, to_type))

