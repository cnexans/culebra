from dataclasses import dataclass
from typing import Any
from enum import Enum, auto

class BaseType:
    """Base class for Culebra types."""
    def __eq__(self, other: Any) -> bool:
        return type(self) is type(other)

    def __repr__(self) -> str:
        return self.__class__.__name__

class IntType(BaseType):
    pass

class FloatType(BaseType):
    pass

class BoolType(BaseType):
    pass

class StringType(BaseType):
    pass

@dataclass
class ArrayType(BaseType):
    element_type: BaseType

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ArrayType) and self.element_type == other.element_type

    def __repr__(self) -> str:
        return f"ArrayType({self.element_type})"

class FunctionType(BaseType):
    pass

class UnknownType(BaseType):
    pass

# Predefined singleton instances
INT = IntType()
FLOAT = FloatType()
BOOL = BoolType()
STRING = StringType()
UNKNOWN = UnknownType()
