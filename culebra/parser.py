from culebra.ast import *
from culebra.token import Token, TokenType

"""
Culebra Language Grammar and Parser Implementation
================================================

The Culebra parser implements a **recursive descent approach** to process the language's 
grammar and generate an Abstract Syntax Tree (AST). It follows a **top-down parsing strategy**, 
where each grammar rule corresponds to a dedicated `_parse_*` method.

Recursive Descent Parser Flow:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Program   │ ──> │ Statements  │ ──> │ Statement   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                    ┌──────────────────┬──────┴───────┬─────────────┐
                    ▼                  ▼              ▼             ▼
            ┌─────────────┐    ┌────────────┐  ┌──────────┐  ┌──────────┐
            │ Assignment  │    │ Expression │  │ Function │  │   Flow   │
            └─────────────┘    └────────────┘  └──────────┘  └──────────┘
                                     │                            │
                                     ▼                      ┌─────┴─────┐
                    Expression Precedence Hierarchy         ▼           ▼
                    ┌──────────────────────────────┐   ┌───────┐   ┌───────┐
                    │   Logical (and/or)           │   │  If   │   │ Loop  │
                    │   Comparison (>,<,>=,<=,==)  │   └───────┘   └───────┘
                    │   Arithmetic (+,-)           │
                    │   Term (*,/)                 │
                    │   Factor                     │
                    │   Unary (-,not)              │
                    │   Elemental                  │
                    └──────────────────────────────┘

The parser starts at the highest level (`Program`), which consists of multiple `Statement` nodes. 
Each `Statement` may be an **assignment, function definition, control structure**, or an **expression**. 
Expressions are parsed with operator precedence in mind, ensuring **correct evaluation order**.

Program
 ├── Statement
 │    ├── Assignment
 │    │    ├── Identifier
 │    │    ├── "="
 │    │    └── Expression
 │    ├── FunctionDef
 │    │    ├── "def"
 │    │    ├── Identifier
 │    │    ├── "(" Parameters? ")"
 │    │    ├── ":"
 │    │    └── Block
 │    ├── ReturnStatement
 │    │    ├── "return"
 │    │    └── Expression
 │    ├── IfStatement
 │    │    ├── "if" Expression ":" Block
 │    │    ├── ("elif" Expression ":" Block)*
 │    │    ├── ("else" ":" Block)?
 │    │    └── Block
 │    ├── WhileStatement
 │    │    ├── "while" Expression ":" Block
 │    │    └── Block
 │    ├── ForStatement
 │    │    ├── "for" Assignment ";" Expression ";" Assignment ":" Block
 │    │    └── Block
 │    ├── Expression
 │    │    ├── LogicalExpr
 │    │    │    ├── ComparisonExpr (("and" | "or") ComparisonExpr)*
 │    │    │    └── ComparisonExpr
 │    │    ├── ArithmeticExpr
 │    │    │    ├── Term (("+" | "-") Term)*
 │    │    │    └── Term
 │    │    ├── Term
 │    │    │    ├── Factor (("*" | "/") Factor)*
 │    │    │    └── Factor
 │    │    ├── Factor
 │    │    │    ├── UnaryExpr | ElementalExpr
 │    │    │    └── UnaryExpr
 │    │    ├── UnaryExpr
 │    │    │    ├── ("-" | "not") ElementalExpr
 │    │    │    └── ElementalExpr
 │    │    ├── ElementalExpr
 │    │    │    ├── Identifier
 │    │    │    ├── Literal
 │    │    │    ├── "(" Expression ")"
 │    │    │    └── FunctionCall
 │    │    └── FunctionCall
 │    │         ├── Identifier "(" (Expression ("," Expression)*)? ")"
 │    │         └── Expression
 │    └── Block
 │         ├── INDENT
 │         ├── Statement+
 │         └── DEDENT

==================================
Expression example
==================================

Expression: `1 + 2 * 3`
-----------------------
    (+)
   /   \
 (1)    (*)
       /   \
     (2)   (3)

Explanation:
------------
- The parser first evaluates `2 * 3` due to operator precedence.
- The result of `2 * 3` is then added to `1`.
- The AST represents this order of operations correctly.
                    
==================================
Complete Grammar Definition
==================================
Program         ::= Statement*

Statement       ::= Assignment
                 | FunctionDef
                 | ReturnStatement
                 | IfStatement
                 | WhileStatement
                 | ForStatement
                 | Expression

Assignment      ::= (Identifier | BracketAccess) "=" Expression

Expression      ::= LogicalExpr
LogicalExpr     ::= ComparisonExpr (("and" | "or") ComparisonExpr)*
ComparisonExpr  ::= ArithmeticExpr ((">" | "<" | ">=" | "<=" | "==" | "!=") ArithmeticExpr)*
ArithmeticExpr  ::= Term (("+" | "-") Term)*
Term            ::= Factor (("*" | "/") Factor)*
Factor          ::= UnaryExpr | ElementalExpr
UnaryExpr       ::= ("-" | "not") ElementalExpr
ElementalExpr   ::= Identifier
                 | Literal
                 | "(" Expression ")"
                 | FunctionCall
                 | BracketAccess
                 | Array Literal
BracketAccess   ::= (Identifier | BracketAccess) "[" Expression "]"
Array Literal   ::= "[" Expression ("," Expression)* "]"

Literal         ::= NUMBER | STRING | BOOLEAN | FLOAT | NULL
FunctionCall    ::= Identifier "(" (Expression ("," Expression)*)? ")"
FunctionDef     ::= "def" Identifier "(" (Identifier ("," Identifier)*)? ")" ":" Block

IfStatement     ::= "if" Expression ":" Block ("elif" Expression ":" Block)* ("else" ":" Block)?
WhileStatement  ::= "while" Expression ":" Block
ForStatement    ::= "for" Assignment ";" Expression ";" Assignment ":" Block

Block           ::= INDENT Statement+ DEDENT
ReturnStatement ::= "return" Expression

Notes:
- Each rule maps directly to a _parse_* method in the Parser class
- The parser uses recursive descent with operator precedence for expressions
- INDENT/DEDENT tokens are generated by the lexer for block structure
- Error handling includes synchronization and detailed error messages
"""

ComparisonOperators = {
    TokenType.LESS: LessOperation,
    TokenType.LESS_EQ: LessOrEqualOperation,
    TokenType.EQUAL: EqualOperation,
    TokenType.GREATER: GreaterOperation,
    TokenType.GREATER_EQ: GreaterOrEqualOperation,
    TokenType.NOT_EQUAL: NotEqualOperation,
}

PrefixOperators = {
    TokenType.MINUS: NegativeOperation,
    TokenType.NOT: NotOperation,
}

TermOperators = {
    TokenType.MUL: MultiplicationOperation,
    TokenType.DIV: DivisionOperation,
}

ArithmeticOperators = {
    TokenType.PLUS: PlusOperation,
    TokenType.MINUS: MinusOperation,
}

LogicalOperators = {
    TokenType.AND: AndOperation,
    TokenType.OR: OrOperation,
}

class Parser:
    def __init__(self, sequence: list[Token]):
        self.sequence = sequence
        self.index = 0
        self.last_error = None
        self.last_token = None

    def parse(self) -> Program:
        try:
            statements = []
            while self._ignore_newlines() and self._has_token() and self._current_token.type != TokenType.EOF:
                statement = self._parse_statement()
                if statement is None:
                    self._advance_token()
                else:
                    statements.append(statement)

            return Program(statements)
        except Exception as e:
            if not self.has_error:
                self.last_error = e
                self.last_token = self._current_token
            raise e

    @property
    def has_error(self):
        return self.last_error is not None

    def _parse_statement(self) -> Optional[Statement]:
        assert self._current_token is not None
        if self._current_token.type in [TokenType.NEWLINE, TokenType.EOF]:
            return None

        if self._current_token.type == TokenType.IDENTIFIER:
            start_index = self.index
            target = self._parse_assignment_target()
            if self._current_token is not None and self._current_token.type == TokenType.ASSIGN:
                return self._parse_assignment_statement(target)
            else:
                # Not an assignment, so revert to the saved index.
                self.index = start_index

        if self._current_token.type == TokenType.FUNCTION_DEFINITION:
            return self._parse_function_definition()

        if self._current_token.type == TokenType.RETURN:
            return self._parse_return_statement()

        if self._current_token.type == TokenType.IF:
            return self._parse_if_statement()

        if self._current_token.type == TokenType.WHILE:
            return self._parse_while()

        if self._current_token.type == TokenType.FOR:
            return self._parse_for()

        expr = self._parse_expression()
        if expr is not None:
            return expr

        self._expect_one_of([TokenType.IDENTIFIER, TokenType.FUNCTION_DEFINITION])
        
    def _parse_assignment_statement(self, target: Expression) -> Optional[Assignment]:
        assert self._current_token.type == TokenType.ASSIGN
        assignment_token = self._current_token
        self._advance_token()

        # Parse expression to assign
        value = self._parse_expression()
        if value is None:
            return None

        return Assignment(assignment_token, target, value)

    def _parse_expression(self) -> Optional[Expression]:
        expr = self._parse_logical_expression()
        return expr
    
    def _parse_logical_expression(self) -> Optional[Expression]:
        first_expr = self._parse_comparison_expression()
        if first_expr is None:
            return None

        while first_expr is not None and self._current_token.type in LogicalOperators.keys():
            token = self._current_token
            self._advance_token()
            second_expr = self._parse_comparison_expression()
            if second_expr is None:
                return None
            first_expr = LogicalOperators[token.type](token, first_expr, second_expr)

        return first_expr

    def _expect_one_of(self, token_types: list[TokenType]) -> bool:
        if self._current_token.type not in token_types:
            if not self.has_error:
                ls = ', '.join([t.name for t in token_types])
                error = f"Expected {ls}, got {self._current_token.type.name} instead in position {self._current_token.pos}"
                self.last_error = SyntaxError(error)
                self.last_token = self._current_token
            return False

        return True

    @property
    def _current_token(self) -> Optional[Token]:
        if self.index < len(self.sequence):
            return self.sequence[self.index]
        return None

    @property
    def _next_token(self) -> Optional[Token]:
        if self.index + 1 < len(self.sequence):
            return self.sequence[self.index + 1]
        return None

    def _advance_token(self) -> None:
        self.index += 1

    def _parse_comparison_expression(self) -> Optional[Expression]:
        first = self._parse_arithmetic_expression()
        if first is None:
            return None

        while first is not None and self._current_token.type in ComparisonOperators.keys():
            token = self._current_token
            comparison_operator = ComparisonOperators[token.type]
            self._advance_token()
            second_expr = self._parse_arithmetic_expression()
            if second_expr is None:
                return None
            first = comparison_operator(token, first, second_expr)

        return first

    def _parse_arithmetic_expression(self) -> Optional[Expression]:
        term = self._parse_term()
        if term is None:
            return None

        while term is not None and self._current_token.type in ArithmeticOperators.keys():
            token = self._current_token
            self._advance_token()
            second_term = self._parse_term()
            if second_term is None:
                return None
            term = ArithmeticOperators[token.type](token, term, second_term)

        return term

    def _parse_term(self) -> Optional[Expression]:
        factor = self._parse_unary_expression()
        if factor is None:
            return None

        while factor is not None and self._current_token.type in TermOperators.keys():
            token = self._current_token
            self._advance_token()
            second_factor = self._parse_unary_expression()
            if second_factor is None:
                return None
            factor = TermOperators[token.type](token, factor, second_factor)

        return factor

    def _parse_unary_expression(self) -> Optional[Expression]:
        if self._current_token.type not in PrefixOperators.keys():
            return self._parse_elemental_expression()

        tokens = [self._current_token]
        self._advance_token()

        while self._current_token.type in PrefixOperators.keys():
            tokens.append(self._current_token)
            self._advance_token()

        expr = self._parse_expression()
        if expr is None:
            return None

        while tokens:
            token = tokens.pop()
            expr = PrefixOperators[token.type](token, expr)

        return expr

    def _parse_elemental_expression(self) -> Optional[Expression]:
        if self._current_token.type == TokenType.LBRACKET:
            return self._parse_array_literal()

        if self._current_token.type == TokenType.LBRACE:
            return self._parse_brace_expression()

        if self._current_token.type == TokenType.LPAREN:
            return self._parse_parentheses_group_expression()

        if self._current_token.type == TokenType.IDENTIFIER and self._next_token.type == TokenType.LPAREN:
            return self._parse_function_call()

        if self._current_token.type == TokenType.IDENTIFIER:
            factor = Identifier(self._current_token, self._current_token.literal)
            self._advance_token()
            # Check for bracket access or dot access
            factor = self._parse_postfix_operations(factor)
            return factor

        if self._current_token.type == TokenType.NUMBER:
            number = Integer(self._current_token, int(self._current_token.literal))
            self._advance_token()
            return number

        if self._current_token.type == TokenType.STRING:
            literal = self._current_token.literal
            # Handle triple quotes
            if literal.startswith('"""') and literal.endswith('"""'):
                string_content = literal[3:-3]
            # Handle single quotes
            elif literal.startswith('"') and literal.endswith('"'):
                string_content = literal[1:-1]
            else:
                self.errors.append(f"Invalid string format at position {self._current_token.pos}")
                return None

            # Process escape sequences
            string_content = self._process_escape_sequences(string_content)
            string = String(self._current_token, string_content)
            self._advance_token()
            # Check for bracket access or dot access
            string = self._parse_postfix_operations(string)
            return string

        if self._current_token.type == TokenType.BOOLEAN:
            val = True if self._current_token.literal == 'true' else False
            b = Bool(self._current_token, val)
            self._advance_token()
            return b

        if self._current_token.type == TokenType.FLOAT:
            val = Float(self._current_token, float(self._current_token.literal))
            self._advance_token()
            return val
        
        self._expect_one_of([TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.FLOAT])
        return None

    def _process_escape_sequences(self, s: str) -> str:
        """Process common escape sequences in strings."""
        escape_sequences = {
            r'\n': '\n',    # newline
            r'\t': '\t',    # tab
            r'\r': '\r',    # carriage return
            r'\"': '"',     # quote
            r'\\': '\\',    # backslash
            r'\b': '\b',    # backspace
            r'\f': '\f',    # form feed
        }
        result = ''
        i = 0
        while i < len(s):
            if s[i] == '\\' and i + 1 < len(s):
                escape_seq = s[i:i+2]
                if escape_seq in escape_sequences:
                    result += escape_sequences[escape_seq]
                    i += 2
                else:
                    # Invalid escape sequence - keep it as is
                    result += escape_seq
                    i += 2
            else:
                result += s[i]
                i += 1
        return result

    def _parse_function_call(self) -> Optional[Expression]:
        token = self._current_token
        identifier = Identifier(self._current_token, self._current_token.literal)
        self._advance_token()
        assert self._current_token.type == TokenType.LPAREN
        self._advance_token()
        arguments = []
        while self._current_token.type != TokenType.RPAREN:
            expr = self._parse_expression()
            if expr is None:
                return None
            arguments.append(expr)

            if self._current_token.type in [TokenType.COMMA]:
                self._advance_token()
                continue

            if not self._expect_one_of([TokenType.COMMA, TokenType.RPAREN]):
                return None

        self._advance_token()
        func_call = FunctionCall(token, identifier, arguments)
        # Check for chained bracket access or dot access
        func_call = self._parse_postfix_operations(func_call)
        return func_call

    def _parse_parentheses_group_expression(self) -> Optional[Expression]:
        assert self._current_token.type == TokenType.LPAREN
        token = self._current_token
        self._advance_token()

        # Check for empty parentheses - just return it as a syntax error
        if self._current_token.type == TokenType.RPAREN:
            self._expect_one_of([TokenType.IDENTIFIER, TokenType.NUMBER])
            return None

        expr = self._parse_expression()
        if expr is None:
            return None

        # Check if it's a tuple (has comma) or just a grouped expression
        if self._current_token.type == TokenType.COMMA:
            # It's a tuple with 2+ elements
            elements = [expr]
            while self._current_token.type == TokenType.COMMA:
                self._advance_token()
                
                # Allow trailing comma
                if self._current_token.type == TokenType.RPAREN:
                    break
                    
                element = self._parse_expression()
                if element is None:
                    return None
                elements.append(element)

            if not self._expect_one_of([TokenType.RPAREN]):
                return None
            self._advance_token()
            
            result = Tuple(token, elements)
            # Check for postfix operations on tuples
            result = self._parse_postfix_operations(result)
            return result
        else:
            # Just a grouped expression
            if self._current_token.type != TokenType.RPAREN:
                self._expect_one_of([TokenType.RPAREN])
                return None

            self._advance_token()
            # Check for postfix operations on grouped expressions
            expr = self._parse_postfix_operations(expr)
            return expr

    def _parse_function_definition(self):
        assert self._current_token.type == TokenType.FUNCTION_DEFINITION
        token = self._current_token
        self._advance_token()

        identifier = self._parse_identifier()
        if identifier is None:
            return None

        arguments = self._parse_argument_list()
        if arguments is None:
            return None

        block = self._parse_block()

        return FunctionDefinition(token, identifier, arguments, block)

    def _parse_identifier(self) -> Optional[Identifier]:
        if not self._expect_one_of([TokenType.IDENTIFIER]):
            return None
        identifier = Identifier(self._current_token, self._current_token.literal)
        self._advance_token()
        return identifier

    def _parse_argument_list(self) -> Optional[List[Identifier]]:
        if not self._expect_one_of([TokenType.LPAREN]):
            return None
        self._advance_token()

        arguments = []
        while self._current_token.type != TokenType.RPAREN:
            arg = self._parse_identifier()
            if arg is None:
                return None
            arguments.append(arg)

            if self._current_token.type in [TokenType.COMMA]:
                self._advance_token()
                continue

            if not self._expect_one_of([TokenType.COMMA, TokenType.RPAREN]):
                return None
        self._advance_token()
        return arguments

    def _parse_block_statements(self) -> Optional[Block]:
        if not self._expect_one_of([TokenType.INDENT]):
            return None
        self._advance_token()

        statements = []
        while self._ignore_newlines() and self._has_token() and self._current_token.type != TokenType.DEDENT:
            statement = self._parse_statement()
            if statement is None:
                self._advance_token()
            else:
                statements.append(statement)
        self._advance_token()
        return Block(statements)

    def _parse_return_statement(self):
        assert self._current_token.type == TokenType.RETURN
        token = self._current_token
        self._advance_token()
        value = self._parse_expression()
        if value is None:
            return None
        return ReturnStatement(token, value)


    def _ignore_newlines(self):
        while self._has_token() and self._current_token.type == TokenType.NEWLINE:
            self._advance_token()
        return True

    def _has_token(self):
        return self._current_token is not None

    def _parse_while(self):
        assert self._current_token.type == TokenType.WHILE
        token = self._current_token
        self._advance_token()

        expr = self._parse_expression()
        if expr is None:
            return None
        block = self._parse_block()
        self._ignore_newlines()

        return While(token, expr, block)

    def _parse_for(self):
        assert self._current_token.type == TokenType.FOR
        token = self._current_token
        self._advance_token()

        pre = self._parse_statement()
        if pre is None:
            return None

        if not self._expect_one_of([TokenType.SEMICOLON]):
            return None
        self._advance_token()

        condition = self._parse_expression()
        if condition is None:
            return None
        if not self._expect_one_of([TokenType.SEMICOLON]):
            return None
        self._advance_token()

        post = self._parse_statement()
        if post is None:
            return None

        block = self._parse_block()
        self._ignore_newlines()
        if block is None:
            return None

        return For(token, condition, block, post, pre)



    def _parse_if_statement(self):
        assert self._current_token.type in [TokenType.IF]
        token = self._current_token
        self._advance_token()

        expr = self._parse_expression()
        if expr is None:
            return None

        block = self._parse_block()
        self._ignore_newlines()

        if self._has_token() and self._current_token.type in [TokenType.ELSE, TokenType.ELIF]:
            otherwise = self._parse_otherwise()
            return Conditional(token, expr, block, otherwise)

        return Conditional(token, expr, block, None)

    def _parse_otherwise(self):
        assert self._current_token.type in [TokenType.ELSE, TokenType.ELIF]
        token = self._current_token
        self._advance_token()

        expr = Bool(token, True) if token.type == TokenType.ELSE else self._parse_expression()
        if expr is None:
            return None

        block = self._parse_block()
        self._ignore_newlines()

        if token.type == TokenType.ELSE:
            return Conditional(token, expr, block, None)

        if self._has_token() and self._current_token.type in [TokenType.ELSE, TokenType.ELIF]:
            otherwise = self._parse_otherwise()
            return Conditional(token, expr, block, otherwise)

        return Conditional(token, expr, block, None)

    def _parse_block(self):
        if not self._expect_one_of([TokenType.COLON]):
            return None
        self._advance_token()

        # Expect one new line before parsing the block
        if not self._expect_one_of([TokenType.NEWLINE]):
            return None
        self._advance_token()
        self._ignore_newlines()

        block = self._parse_block_statements()
        return block

    def _parse_postfix_operations(self, target: Expression) -> Optional[Expression]:
        """Parse chained bracket access and dot access operations."""
        while self._current_token and self._current_token.type in [TokenType.LBRACKET, TokenType.DOT]:
            if self._current_token.type == TokenType.LBRACKET:
                target = self._parse_bracket_access(target)
                if target is None:
                    return None
            elif self._current_token.type == TokenType.DOT:
                target = self._parse_dot_access(target)
                if target is None:
                    return None
        return target

    def _parse_bracket_access(self, target: Expression) -> Optional[Expression]:
        """Parse array/string index access with brackets."""
        assert self._current_token.type == TokenType.LBRACKET
        token = self._current_token
        self._advance_token()

        index = self._parse_expression()
        if index is None:
            return None

        if not self._expect_one_of([TokenType.RBRACKET]):
            return None
        self._advance_token()

        return BracketAccess(token, target, index)

    def _parse_dot_access(self, target: Expression) -> Optional[Expression]:
        """Parse method call with dot notation."""
        assert self._current_token.type == TokenType.DOT
        token = self._current_token
        self._advance_token()

        # Expect method name (identifier)
        if not self._expect_one_of([TokenType.IDENTIFIER]):
            return None
        method_name = self._current_token.literal
        self._advance_token()

        # Expect opening parenthesis
        if not self._expect_one_of([TokenType.LPAREN]):
            return None
        self._advance_token()

        # Parse arguments
        arguments = []
        while self._current_token.type != TokenType.RPAREN:
            expr = self._parse_expression()
            if expr is None:
                return None
            arguments.append(expr)

            if self._current_token.type in [TokenType.COMMA]:
                self._advance_token()
                continue

            if not self._expect_one_of([TokenType.COMMA, TokenType.RPAREN]):
                return None

        self._advance_token()
        return DotAccess(token, target, method_name, arguments)

    def _parse_array_literal(self) -> Optional[Expression]:
        """Parse array literals like [1, 2, 3]"""
        assert self._current_token.type == TokenType.LBRACKET
        token = self._current_token
        self._advance_token()

        elements = []
        while self._current_token.type != TokenType.RBRACKET:
            expr = self._parse_expression()
            if expr is None:
                return None
            elements.append(expr)

            if self._current_token.type in [TokenType.COMMA]:
                self._advance_token()
                continue

            if not self._expect_one_of([TokenType.COMMA, TokenType.RBRACKET]):
                return None

        self._advance_token()
        result = Array(token, elements)
        # Check for postfix operations on arrays
        result = self._parse_postfix_operations(result)
        return result

    def _parse_brace_expression(self) -> Optional[Expression]:
        """Parse map literals {key: value} or set literals {value}"""
        assert self._current_token.type == TokenType.LBRACE
        token = self._current_token
        self._advance_token()

        # Check for empty braces - this is an error
        if self._current_token.type == TokenType.RBRACE:
            if not self.has_error:
                error = f"Empty {{}} not allowed. Use Map() or Set() constructors for empty collections at position {token.pos}"
                self.last_error = SyntaxError(error)
                self.last_token = token
            return None

        # Parse the first element/pair to determine if it's a map or set
        first_expr = self._parse_expression()
        if first_expr is None:
            return None

        # Check if it's a map (has colon) or set (no colon)
        if self._current_token.type == TokenType.COLON:
            # It's a map
            return self._parse_map_continuation(token, first_expr)
        else:
            # It's a set
            return self._parse_set_continuation(token, first_expr)

    def _parse_map_continuation(self, token: Token, first_key: Expression) -> Optional[Expression]:
        """Continue parsing a map after the first key"""
        pairs = []
        
        # Parse first pair
        assert self._current_token.type == TokenType.COLON
        self._advance_token()
        first_value = self._parse_expression()
        if first_value is None:
            return None
        pairs.append((first_key, first_value))

        # Parse remaining pairs
        while self._current_token.type == TokenType.COMMA:
            self._advance_token()
            
            # Allow trailing comma
            if self._current_token.type == TokenType.RBRACE:
                break
                
            key = self._parse_expression()
            if key is None:
                return None
            
            if not self._expect_one_of([TokenType.COLON]):
                return None
            self._advance_token()
            
            value = self._parse_expression()
            if value is None:
                return None
            pairs.append((key, value))

        if not self._expect_one_of([TokenType.RBRACE]):
            return None
        self._advance_token()
        
        result = Map(token, pairs)
        # Check for postfix operations on maps
        result = self._parse_postfix_operations(result)
        return result

    def _parse_set_continuation(self, token: Token, first_element: Expression) -> Optional[Expression]:
        """Continue parsing a set after the first element"""
        elements = [first_element]

        # Parse remaining elements
        while self._current_token.type == TokenType.COMMA:
            self._advance_token()
            
            # Allow trailing comma
            if self._current_token.type == TokenType.RBRACE:
                break
                
            expr = self._parse_expression()
            if expr is None:
                return None
            elements.append(expr)

        if not self._expect_one_of([TokenType.RBRACE]):
            return None
        self._advance_token()
        
        result = Set(token, elements)
        # Check for postfix operations on sets
        result = self._parse_postfix_operations(result)
        return result

    def _parse_assignment_target(self) -> Optional[Expression]:
        # Only identifiers are valid as assignment base targets.
        if self._current_token.type != TokenType.IDENTIFIER:
            return None
        target = Identifier(self._current_token, self._current_token.literal)
        self._advance_token()

        # Allow chain bracket access for assignment targets, e.g., mylist[0][1]
        while self._has_token() and self._current_token.type == TokenType.LBRACKET:
            target = self._parse_bracket_access(target)
            if target is None:
                return None
        return target