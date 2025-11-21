from enum import Enum, auto, unique
from typing import NamedTuple, Optional


@unique
class TokenType(Enum):
    # Single-character tokens
    ASSIGN  = auto()
    COMMA   = auto()
    COLON   = auto()
    DOT     = auto()
    LPAREN  = auto()
    RPAREN  = auto()
    LBRACE  = auto()
    RBRACE  = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    NEWLINE = auto()

    # Indentation
    INDENT   = auto()
    DEDENT = auto()

    # Literals
    IDENTIFIER = auto()
    NUMBER     = auto()
    STRING     = auto()
    FLOAT      = auto()
    BOOLEAN    = auto()

    # Keywords
    IF       = auto()
    ELSE     = auto()
    RETURN   = auto()
    ELIF   = auto()
    WHILE    = auto()
    FOR      = auto()
    BREAK    = auto()
    CONTINUE = auto()
    FUNCTION_DEFINITION   = auto()

    # Operators
    PLUS     = auto()
    MINUS    = auto()
    MUL      = auto()
    DIV      = auto()

    # Comparison operators
    EQUAL    = auto()
    NOT_EQUAL = auto()
    LESS     = auto()
    GREATER  = auto()
    LESS_EQ  = auto()
    GREATER_EQ = auto()

    # Logical operators
    AND      = auto()
    OR       = auto()
    NOT = auto()

    # Expressions
    FUNCTION_CALL = auto()

    # End of file
    EOF      = auto()

    # Errors
    ILLEGAL_CHARACTER = auto()
    INVALID_IDENTIFIER = auto()
    WHITESPACE = auto()

    LINE_COMMENT = auto()

class Token:
    type: TokenType
    literal: Optional[str]
    pos: int

    def __init__(self, type: TokenType, literal: Optional[str], pos: int):
        self.type = type
        self.literal = literal
        self.pos = pos

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.literal == other.literal

    def __repr__(self):
        if self.type in [TokenType.NEWLINE, TokenType.DEDENT]:
            return f"{self.type.name}"
        return f"{self.type.name} {self.literal}"
