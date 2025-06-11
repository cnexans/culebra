from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from culebra import ast
from culebra.token import TokenType
from culebra.type_system import (
    BaseType,
    INT,
    FLOAT,
    BOOL,
    STRING,
    ArrayType,
    FunctionType,
    UNKNOWN,
)

class TypeErrorException(Exception):
    pass

@dataclass
class TypeEnvironment:
    values: Dict[str, BaseType]
    parent: 'TypeEnvironment | None' = None

    def get(self, name: str) -> BaseType:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        return UNKNOWN

    def assign(self, name: str, typ: BaseType):
        if name in self.values:
            self.values[name] = typ
        elif self.parent and name in self.parent.values:
            self.parent.assign(name, typ)
        else:
            self.values[name] = typ

    def create_child(self) -> 'TypeEnvironment':
        return TypeEnvironment({}, self)

class TypeChecker:
    def __init__(self):
        self.env = TypeEnvironment({})

    def check(self, node: ast.ASTNode):
        for cls in type(node).__mro__:
            method_name = f'check_{cls.__name__}'
            method = getattr(self, method_name, None)
            if method:
                return method(node)
        return self.generic_check(node)

    def generic_check(self, node: ast.ASTNode):
        raise TypeErrorException(f'No type check method for {type(node)}')

    # Program / Block
    def check_Program(self, node: ast.Program):
        for stmt in node.statements:
            self.check(stmt)
        return None

    def check_Block(self, node: ast.Block):
        for stmt in node.statements:
            self.check(stmt)
        return None

    # Literals
    def check_Integer(self, node: ast.Integer):
        return INT

    def check_Float(self, node: ast.Float):
        return FLOAT

    def check_String(self, node: ast.String):
        return STRING

    def check_Bool(self, node: ast.Bool):
        return BOOL

    def check_Array(self, node: ast.Array):
        if not node.elements:
            return ArrayType(UNKNOWN)
        element_types = [self.check(elem) for elem in node.elements]
        first = element_types[0]
        for i, t in enumerate(element_types[1:], start=1):
            if t != first:
                raise TypeErrorException(
                    f'Array elements must be of the same type: expected {first}, got {t} at index {i}'
                )
        return ArrayType(first)

    def check_Identifier(self, node: ast.Identifier):
        return self.env.get(node.value)

    def check_Assignment(self, node: ast.Assignment):
        value_type = self.check(node.value)
        if isinstance(node.identifier, ast.Identifier):
            self.env.assign(node.identifier.value, value_type)
        elif isinstance(node.identifier, ast.BracketAccess):
            target_type = self.check(node.identifier.target)
            index_type = self.check(node.identifier.index)
            if index_type not in (INT, UNKNOWN):
                raise TypeErrorException(
                    f'Index expression must be INT, got {index_type}'
                )
            if isinstance(target_type, ArrayType):
                if target_type.element_type != value_type:
                    raise TypeErrorException(
                        f'Cannot assign {value_type} to array of {target_type.element_type}'
                    )
            else:
                raise TypeErrorException(
                    f'Bracket assignment only valid for arrays, got {target_type}'
                )
        return None

    def check_BracketAccess(self, node: ast.BracketAccess):
        target_type = self.check(node.target)
        index_type = self.check(node.index)
        if index_type not in (INT, UNKNOWN):
            raise TypeErrorException(
                f'Index expression must be INT, got {index_type}'
            )
        if isinstance(target_type, ArrayType):
            return target_type.element_type
        if target_type == STRING:
            return STRING
        if target_type == UNKNOWN:
            return UNKNOWN
        raise TypeErrorException(
            f'Bracket access only valid on arrays or strings, got {target_type}'
        )

    # Operations
    def check_BinaryOperation(self, node: ast.BinaryOperation):
        left = self.check(node.left)
        right = self.check(node.right)
        op = node.token.type

        if op in [TokenType.PLUS, TokenType.MINUS, TokenType.MUL, TokenType.DIV]:
            if UNKNOWN in (left, right):
                other = right if left is UNKNOWN else left
                if other in (INT, FLOAT):
                    return other
                if op == TokenType.PLUS and other == STRING:
                    return STRING
                return UNKNOWN
            if left != right:
                raise TypeErrorException(
                    f'Operands for {op.name} must have the same type, got {left} and {right}'
                )
            if left not in (INT, FLOAT):
                if op == TokenType.PLUS and left == STRING:
                    return STRING
                raise TypeErrorException(
                    f'Operator {op.name} not supported for {left}'
                )
            return left

        if op in [TokenType.EQUAL, TokenType.NOT_EQUAL]:
            if UNKNOWN in (left, right):
                return BOOL
            if left != right:
                raise TypeErrorException(
                    f'Operands for {op.name} must be of the same type, got {left} and {right}'
                )
            return BOOL

        if op in [TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ]:
            if UNKNOWN in (left, right):
                other = right if left is UNKNOWN else left
                if other in (INT, FLOAT):
                    return BOOL
                return BOOL
            if left != right or left not in (INT, FLOAT):
                raise TypeErrorException(
                    f'Comparison {op.name} requires numeric operands of the same type, got {left} and {right}'
                )
            return BOOL

        if op in [TokenType.AND, TokenType.OR]:
            if UNKNOWN in (left, right):
                return BOOL
            if left != BOOL or right != BOOL:
                raise TypeErrorException(
                    f'Logical operator {op.name} requires boolean operands, got {left} and {right}'
                )
            return BOOL

        raise TypeErrorException(f'Unsupported binary operator {op}')

    def check_PrefixOperation(self, node: ast.PrefixOperation):
        value_type = self.check(node.value)
        op = node.token.type
        if op == TokenType.MINUS:
            if value_type is UNKNOWN:
                return UNKNOWN
            if value_type not in (INT, FLOAT):
                raise TypeErrorException(
                    f'Unary - expects INT or FLOAT, got {value_type}'
                )
            return value_type
        if op == TokenType.NOT:
            if value_type is UNKNOWN:
                return BOOL
            if value_type != BOOL:
                raise TypeErrorException(
                    f'not operator requires BOOL, got {value_type}'
                )
            return BOOL
        raise TypeErrorException(f'Unsupported prefix operator {op}')

    def check_Conditional(self, node: ast.Conditional):
        cond_type = self.check(node.condition)
        if cond_type != BOOL:
            raise TypeErrorException(
                f'Condition expression must be BOOL, got {cond_type}'
            )
        self.check(node.body)
        if node.otherwise:
            self.check(node.otherwise)
        return None

    def check_While(self, node: ast.While):
        cond_type = self.check(node.condition)
        if cond_type != BOOL:
            raise TypeErrorException(
                f'Condition expression must be BOOL, got {cond_type}'
            )
        self.check(node.body)
        return None

    def check_For(self, node: ast.For):
        self.check(node.pre)
        cond_type = self.check(node.condition)
        if cond_type != BOOL:
            raise TypeErrorException(
                f'Condition expression must be BOOL, got {cond_type}'
            )
        self.check(node.post)
        self.check(node.body)
        return None

    def check_FunctionDefinition(self, node: ast.FunctionDefinition):
        # Register function but skip body type checking for simplicity
        self.env.assign(node.name.value, FunctionType())
        child = self.env.create_child()
        self.check(node.body)
        return None

    def check_FunctionCall(self, node: ast.FunctionCall):
        self.check(node.function)
        for arg in node.arguments:
            self.check(arg)
        return UNKNOWN

    def check_ReturnStatement(self, node: ast.ReturnStatement):
        self.check(node.value)
        return None

