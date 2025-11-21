#!/usr/bin/env python3

"""
Lexer: Converts source text into a sequence of tokens

Process:
┌──────────────┐
│  Input Text  │ "if x > 5:\n    print('hello')"
└──────┬───────┘
       │
       ▼
┌──────────────┐  Matches against regex patterns:
│  Tokenizer   │  • Keywords (if, else, while...)
│   Process    │  • Operators (+, -, *, /, >, <...)
│              │  • Literals (numbers, strings...)
└──────┬───────┘  • Special chars ({, }, (, )...)
       │
       ▼
┌──────────────┐  [
│   Tokens     │   Token(IF, "if", pos=0),
│    List      │   Token(IDENTIFIER, "x", pos=3),
│              │   Token(GREATER, ">", pos=5),
└──────────────┘   Token(NUMBER, "5", pos=7),
                   ...
                 ]

Indentation Handling:
└─ Level 0    if x > 5:
   └─ Level 1     print('hello')  # INDENT token added
                                 # DEDENT token added at end

Indentation Stack Example:
┌─────────────┐  ┌──────────────┐
│ Source Code │  │ Indent Stack │
├─────────────┤  ├──────────────┤
│ def foo():  │  │ [0]          │
│   if x:     │  │ [0,4]        │
│     print() │  │ [0,4,8]      │
│   else:     │  │ [0,4]        │
│     print() │  │ [0,4,8]      │
│   print()   │  │ [0,4]        │
│ print()     │  │ [0]          │
└─────────────┘  └──────────────┘

Stack Operations:
• Stack always starts with [0]
• INDENT: Push new level when indent increases
• DEDENT: Pop levels when indent decreases
• Multiple DEDENTs may be generated for one line
• Final DEDENTs generated at EOF if needed
• Error if indent doesn't match any previous level

Generated Tokens Include:
INDENT  - When pushing new level
DEDENT  - When popping levels
NEWLINE - At end of each line

Token Matching Algorithm:
• Uses Maximal Munch (Longest Match) principle
• Tries patterns in order of precedence:
  1. Whitespace and comments
  2. Keywords (to prevent 'if' being tokenized as identifier)
  3. Multi-character operators (==, >=, <=)
  4. Single-character operators and delimiters
  5. Invalid identifiers (for error reporting)
  6. Numbers and literals
  7. Valid identifiers

Special Features:
• Tracks position of each token for error reporting
• Manages indentation with INDENT/DEDENT tokens
• Handles comments and whitespace
• Validates identifier names
• Supports multi-line strings
"""

from typing import List
import re
from culebra.token import Token, TokenType

class Lexer:
    def tokenize(self, text: str) -> List[Token]:
        text = text.strip()
        indent_stack = [0]  # Keep track of indent levels
        tokens = []
        i = 0
        while i < len(text):
            chunk = text[i:]
            is_legal = False

            if text[i] == '\n':
                tokens.append(Token(TokenType.NEWLINE, '\n', i))
                indent = 0
                i += 1
                while i < len(text):
                    match = IndentRegex.match(text[i:])
                    if not match: break
                    indent += 1
                    i += match.end()

                current_indent = indent_stack[-1]
                if indent > current_indent:
                    # Increasing indent
                    tokens.append(Token(TokenType.INDENT, indent, i))
                    indent_stack.append(indent)
                elif indent < current_indent:
                    # Decreasing indent - may need multiple DEDENT tokens
                    while indent < indent_stack[-1]:
                        indent_stack.pop()
                        tokens.append(Token(TokenType.DEDENT, None, i))
                    ## TODO: esto esta mal
                    if indent != indent_stack[-1]:
                        raise IndentationError(f"Unindent does not match any outer indentation level")

                continue

            for token_type, regex in TokenRegex.items():
                match = regex.match(chunk)
                if match:
                    value = match.group(0)
                    if token_type not in [TokenType.WHITESPACE, TokenType.LINE_COMMENT]:
                        token = Token(token_type, value, i)
                        tokens.append(token)
                    i += len(value)
                    is_legal = True
                    break

            if not is_legal:
                char = chunk[0]
                token = Token(TokenType.ILLEGAL_CHARACTER, char, i)
                tokens.append(token)
                i += 1

        if not tokens or tokens[-1].type != TokenType.NEWLINE:
            tokens.append(Token(TokenType.NEWLINE, '\n', i))

        # Handle any remaining dedents at the end of file
        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, None, i))

        tokens.append(Token(TokenType.EOF, "", i))
        return tokens

IndentRegex = re.compile(r"^(\t| {4})")

TokenRegex = {
    TokenType.WHITESPACE: re.compile(r"^[\s]+"),
    # Matches line comments, everything except newlines
    TokenType.LINE_COMMENT: re.compile(r"^#[^\n]*"),

    # Keywords
    TokenType.IF: re.compile(r"^if(?=\s|$)"),
    TokenType.ELSE: re.compile(r"^else(?=[\s:]|$)"),
    TokenType.ELIF: re.compile(r"^elif(?=\s|$)"),
    TokenType.WHILE: re.compile(r"^while(?=\s|$)"),
    TokenType.FOR: re.compile(r"^for(?=\s|$)"),
    TokenType.BREAK: re.compile(r"^break(?=\s|$)"),
    TokenType.CONTINUE: re.compile(r"^continue(?=\s|$)"),
    TokenType.RETURN: re.compile(r"^return(?=\s|$)"),
    TokenType.NOT: re.compile(r"^not(?=\s|$)"),
    TokenType.FUNCTION_DEFINITION: re.compile(r"^def(?=[\s\(]|$)"),
    TokenType.BOOLEAN: re.compile(r"^(true|false)(?=[\s,:]|$)"),
    TokenType.AND: re.compile(r"^and(?=\s|$)"),
    TokenType.OR: re.compile(r"^or(?=\s|$)"),

    
    # Single-character tokens
    TokenType.LPAREN: re.compile(r"^\("),
    TokenType.RPAREN: re.compile(r"^\)"), 
    TokenType.LBRACE: re.compile(r"^{"),
    TokenType.RBRACE: re.compile(r"^}"),
    TokenType.LBRACKET: re.compile(r"^\["),
    TokenType.RBRACKET: re.compile(r"^\]"),
    TokenType.COMMA: re.compile(r"^,"),
    TokenType.SEMICOLON: re.compile(r"^;"),
    TokenType.COLON: re.compile(r"^:"),
    TokenType.DOT: re.compile(r"^\."),

    # Assignment after equals
    TokenType.EQUAL: re.compile(r"^=="),
    TokenType.ASSIGN: re.compile(r"^="),

    # Operators
    TokenType.PLUS: re.compile(r"^\+"),
    TokenType.MINUS: re.compile(r"^-"),
    TokenType.MUL: re.compile(r"^\*"),
    TokenType.DIV: re.compile(r"^/"),

    # Comparison operators
    TokenType.NOT_EQUAL: re.compile(r"^!="),
    TokenType.LESS_EQ: re.compile(r"^<="),
    TokenType.LESS: re.compile(r"^<"),
    TokenType.GREATER_EQ: re.compile(r"^>="),
    TokenType.GREATER: re.compile(r"^>"),

    # Literals
    TokenType.INVALID_IDENTIFIER: re.compile(r"^[0-9]+[a-zA-Z_][a-zA-Z0-9_]*"),
    TokenType.FLOAT: re.compile(r"^[0-9]+\.[0-9]+"),
    TokenType.NUMBER: re.compile(r"^([0-9]+)"),
    TokenType.IDENTIFIER: re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*"),
    TokenType.STRING: re.compile(r'^"""[\s\S]*?"""|"(?:[^"\\]|\\.)*"'),
}
