from abc import ABC, abstractmethod
from culebra.token import Token, TokenType
from typing import List, Optional, Union, TypeVar, Generic

T = TypeVar('T')


class ASTNode(ABC):
    @abstractmethod
    def __repr__(self) -> str:
        pass

    @property
    @abstractmethod
    def children(self) -> List['ASTNode']:
        pass

    @property
    def node_name(self) -> str:
        return self.__class__.__name__

    def pretty(self, level: int = 1) -> str:
        is_last = len(self.children) == 0
        if is_last:
            prefix = "    " * (level - 1)
            return f"{prefix}└──{repr(self)}"

        prefix = "    " * (level - 1) +  "├── "
        result = prefix + self.node_name

        for i, child in enumerate(self.children):
            result += "\n" + child.pretty(level + 1)

        return result

class TokenizedASTNode(ASTNode, ABC):
    @abstractmethod
    def token_literal(self) -> str:
        pass

    @abstractmethod
    def token_type(self) -> TokenType:
        pass

class Statement(TokenizedASTNode, ABC):
    def __init__(self, token: Token):
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal

    def token_type(self) -> TokenType:
        return self.token.type

class Expression(Statement, ABC):
    def __init__(self, token: Token):
        super().__init__(token)
        self.token = token

    def token_literal(self) -> str:
        return self.token.literal

    def token_type(self) -> TokenType:
        return self.token.type

class Block(ASTNode):
    def __init__(self, statements: List[Statement]):
        self.statements = statements

    def __repr__(self) -> str:
        return "\n".join([str(stmt) for stmt in self.statements])

    @property
    def children(self) -> List['ASTNode']:
        return self.statements

class Program(Block):
    def __init__(self, statements: List[Statement]):
        super().__init__(statements)

class LiteralValue(Generic[T], Expression, ABC):
    def __init__(self, token: Token, value: T):
        super().__init__(token)
        self.value = value

    def __repr__(self) -> str:
        return f"{self.node_name}({self.value})"

    @property
    def children(self) -> List['ASTNode']:
        return []

class Identifier(LiteralValue[str]):
    def __init__(self, token: Token, value: str):
        super().__init__(token, value)

class BracketAccess(Expression):
    def __init__(self, token: Token, target: Expression, index: Expression):
        super().__init__(token)
        self.target = target
        self.index = index

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.target}, {self.index})"

    @property
    def children(self) -> List['ASTNode']:
        return [self.target, self.index]

class Assignment(Statement):
    def __init__(self, token: Token, identifier: Union[Identifier, BracketAccess], value: Expression):
        super().__init__(token)
        self.identifier = identifier
        self.value = value

    def __repr__(self) -> str:
        return f"{self.node_name}({self.identifier}, {self.value})"

    @property
    def children(self) -> List['ASTNode']:
        return [self.identifier, self.value]

class Integer(LiteralValue[int]):
    def __init__(self, token: Token, value: int):
        super().__init__(token, value)

class Float(LiteralValue[float]):
    def __init__(self, token: Token, value: float):
        super().__init__(token, value)

class String(LiteralValue[str]):
    def __init__(self, token: Token, value: str):
        super().__init__(token, value)

class Bool(LiteralValue[bool]):
    def __init__(self, token: Token, value: bool):
        super().__init__(token, value)

class BinaryOperation(Expression, ABC):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token)
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"{self.node_name}({self.left}, {self.right})"

    @property
    def children(self) -> List['ASTNode']:
        return [self.left, self.right]

class PlusOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class MinusOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class MultiplicationOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class DivisionOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class AndOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class OrOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class GreaterOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class GreaterOrEqualOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class LessOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class LessOrEqualOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class EqualOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class NotEqualOperation(BinaryOperation):
    def __init__(self, token: Token, left: Expression, right: Expression):
        super().__init__(token, left, right)

class PrefixOperation(Expression, ABC):
    def __init__(self, token: Token, value: Expression):
        super().__init__(token)
        self.value = value

    def __repr__(self) -> str:
        return f"{self.node_name}({self.value})"

    @property
    def children(self) -> List['ASTNode']:
        return [self.value]

class NegativeOperation(PrefixOperation):
    def __init__(self, token: Token, value: Expression):
        super().__init__(token, value)

class NotOperation(PrefixOperation):
    def __init__(self, token: Token, value: Expression):
        super().__init__(token, value)

class FunctionCall(Expression, ABC):
    def __init__(self, token: Token, function: Identifier, arguments: List[Expression]):
        super().__init__(token)
        self.function = function
        self.arguments = arguments

    @property
    def children(self) -> List['ASTNode']:
        return self.arguments

    @property
    def node_name(self) -> str:
        return f"{self.__class__.__name__}({self.function})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.function}, {self.arguments})"

class FunctionDefinition(Statement):
    def __init__(self, token: Token, name: Identifier, arguments: List[Identifier], body: Block):
        super().__init__(token)
        self.name = name
        self.arguments = arguments
        self.body = body

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.arguments}, {self.body.statements})"

    @property
    def node_name(self) -> str:
        return f"{self.__class__.__name__}({self.name}, {self.arguments})"

    @property
    def children(self) -> List['ASTNode']:
        return self.body.children

class ReturnStatement(Statement):
    def __init__(self, token: Token, value: Expression):
        super().__init__(token)
        self.value = value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"

    @property
    def children(self) -> List['ASTNode']:
        return [self.value]

class Conditional(Statement):
    def __init__(self, token: Token, condition: Expression, body: Block, otherwise: Optional['Conditional']):
        super().__init__(token)
        self.condition = condition
        self.body = body
        self.otherwise = otherwise

    def __repr__(self) -> str:
        if self.otherwise:
            return f"{self.__class__.__name__}({self.condition}) Then [{self.body}] Else [{self.otherwise}]"
        return f"{self.__class__.__name__}({self.condition}) Then [{self.body}]"

    @property
    def children(self) -> List['ASTNode']:
        if self.otherwise:
            return [self.body, self.otherwise]

        return [self.body]

class While(Statement):
    def __init__(self, token: Token, condition: Expression, body: Block):
        super().__init__(token)
        self.condition = condition
        self.body = body

    @property
    def children(self):
        return [self.condition, self.body]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.condition}) Then [{self.body}]"

class For(Statement):
    def __init__(self, token: Token, condition: Expression, body: Block, post: Statement, pre: Statement):
        super().__init__(token)
        self.condition = condition
        self.body = body
        self.post = post
        self.pre = pre
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.pre}; {self.condition}; {self.post}) Then [{self.body}]"

    @property
    def children(self) -> List['ASTNode']:
        return [self.condition, self.pre, self.condition, self.post]

class Array(Expression):
    def __init__(self, token: Token, elements: List[Expression]):
        super().__init__(token)
        self.elements = elements

    def __repr__(self) -> str:
        elements_str = ", ".join(str(elem) for elem in self.elements)
        return f"{self.node_name}([{elements_str}])"

    @property
    def children(self) -> List['ASTNode']:
        return self.elements