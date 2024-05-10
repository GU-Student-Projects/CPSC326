"""MyPL simple syntax checker (parser) implementation.

NAME: <your-name-here>
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *


class SimpleParser:

    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None

    def parse(self):
        """Start the parser."""
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def()
            else:
                self.fun_def()
        self.eat(TokenType.EOS, 'expecting EOF')

    # ----------------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------------

    def error(self, message):
        """Raises a formatted parser error.

        Args:
            message -- The basic message (expectation)

        """
        lexeme = self.curr_token.lexeme
        line = self.curr_token.line
        column = self.curr_token.column
        err_msg = f'{message} found "{lexeme}" at line {line}, column {column}'
        raise ParserError(err_msg)

    def advance(self):
        """Moves to the next token of the lexer."""
        self.curr_token = self.lexer.next_token()
        # skip comments
        while self.match(TokenType.COMMENT):
            self.curr_token = self.lexer.next_token()

    def match(self, token_type):
        """True if the current token type matches the given one.

        Args:
            token_type -- The token type to match on.

        """
        return self.curr_token.token_type == token_type

    def match_any(self, token_types):
        """True if current token type matches on of the given ones.

        Args:
            token_types -- Collection of token types to check against.

        """
        for token_type in token_types:
            if self.match(token_type):
                return True
        return False

    def eat(self, token_type, message):
        """Advances to next token if current tokey type matches given one,
        otherwise produces and error with the given message.

        Args: 
            token_type -- The totken type to match on.
            message -- Error message if types don't match.

        """
        if not self.match(token_type):
            self.error(message)
        self.advance()

    def is_bin_op(self):
        """Returns true if the current token is a binary operation token."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)

    def is_base_type(self):
        ts = [TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE,
              TokenType.STRING_TYPE]
        return self.match_any(ts)

    def is_base_rvalue(self):
        ts = [TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL,
              TokenType.STRING_VAL]
        return self.match_any(ts)

    def is_stmt_type(self):
        ts = [TokenType.WHILE, TokenType.IF, TokenType.FOR,
              TokenType.RETURN, TokenType.ID, TokenType.ARRAY]
        return self.match_any(ts) or self.is_base_type()

    # ----------------------------------------------------------------------
    # Recursive descent functions
    # ----------------------------------------------------------------------

    def struct_def(self):
        """Check for well-formed struct definition."""
        self.eat(TokenType.STRUCT, "Expected STRUCT")
        self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.fields()
        self.eat(TokenType.RBRACE, "Expected RBRACE")

    def fields(self):
        """Check for well-formed struct fields."""
        if (not self.is_base_type() and not self.match(TokenType.ID) and not self.match(TokenType.ARRAY)):
            return
        self.data_type()
        self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
        if (self.match(TokenType.RBRACE)):
            return
        one_iter = False
        while ((self.is_base_type() or self.match(TokenType.ID) or self.match(TokenType.ARRAY)) or not one_iter):
            if (not self.is_base_type() and not self.match(TokenType.ID) and not self.match(TokenType.ARRAY)):
                self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                break
            self.data_type()
            self.eat(TokenType.ID, "Expected ID")
            self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
            one_iter = True

    def fun_def(self):
        """Check for well-formed function definition."""
        if (not self.match(TokenType.VOID_TYPE)):
            self.data_type()
        else:
            self.eat(TokenType.VOID_TYPE, "Expected VOID_TYPE")
        self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.LPAREN, "Expected LPAREN")
        self.params()
        self.eat(TokenType.RPAREN, "Expected RPAREN")
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.stmt_def()
        self.eat(TokenType.RBRACE, "Expected RBRACE")

    def stmt_def(self):
        while (True):
            if (not self.is_stmt_type()):
                break
            match (self.curr_token.token_type):
                case TokenType.WHILE:
                    self.while_stmt()
                case TokenType.IF:
                    self.if_stmt()
                case TokenType.FOR:
                    self.for_stmt()
                case TokenType.RETURN:
                    self.return_stmt()
                    self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                case TokenType.ID:
                    self.advance()
                    if (self.match(TokenType.LBRACKET)):
                        self.assign_stmt(True)
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                    elif (self.match(TokenType.LPAREN)):
                        self.call_expr(True)
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                    else:
                        if (self.match(TokenType.DOT) or self.match(TokenType.ASSIGN)):
                            self.assign_stmt(True)
                        else:
                            self.vdecl_stmt(True)
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                case _:
                    if (self.is_stmt_type()):
                        self.vdecl_stmt(False)
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                    else:
                        break

    def params(self):
        """Check for well-formed function formal parameters."""
        if (self.is_base_type() or self.match(TokenType.ID) or self.match(TokenType.ARRAY)):
            self.data_type()
            self.eat(TokenType.ID, "Expected ID")
            while (True):
                if (not self.match(TokenType.COMMA)):
                    break
                self.eat(TokenType.COMMA, "Expected comma")
                self.data_type()
                self.eat(TokenType.ID, "Expected ID")

    def data_type(self):
        """Check for well-formed function data types."""
        if (self.is_base_type()):
            self.advance()
        elif (self.match(TokenType.ID)):
            self.advance()
        else:
            self.eat(TokenType.ARRAY, "Expected Data Type")
            if (self.is_base_type()):
                self.advance()
            elif (self.match(TokenType.ID)):
                self.advance()
            else:
                self.error("Expected ID or base type")

    def expr(self):
        """Check for well-formed expression."""
        match self.curr_token.token_type:
            case TokenType.NOT:
                self.eat(TokenType.NOT, "Expected NOT")
                self.expr()
            case TokenType.LPAREN:
                self.eat(TokenType.LPAREN, "Expected LPAREN")
                if (self.match(TokenType.RPAREN)):
                    self.error("Expected expression")
                self.expr()
                self.eat(TokenType.RPAREN, "Expected RPAREN")
            case _:
                if (self.is_bin_op()):
                    self.error("Expected expression")
                self.rvalue()
        if (self.is_bin_op()):
            self.advance()
            if (self.match(TokenType.SEMICOLON)):
                self.error("Expected expression")
            self.expr()

    def lvalue(self, skipID):
        """Check for well-formed left side value."""
        if (not skipID):
            self.eat(TokenType.ID, "Expected ID")
        while (self.match_any([TokenType.LBRACKET, TokenType.DOT])):
            if (self.match(TokenType.LBRACKET)):
                self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                self.expr()
                self.eat(TokenType.RBRACKET, "Expected RBRACKET")
            elif (self.match(TokenType.DOT)):
                self.eat(TokenType.DOT, "Expected DOT")
                self.eat(TokenType.ID, "Expected ID")
                if (self.match(TokenType.LBRACKET)):
                    self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                    self.expr()
                    self.eat(TokenType.RBRACKET, "Expected RBRACKET")

    def rvalue(self):
        if (self.is_base_rvalue()):
            self.advance()
        elif (self.match(TokenType.NULL_VAL)):
            self.advance()
        elif (self.match(TokenType.NEW)):
            self.new_rvalue()
        elif (self.match(TokenType.ID)):
            if (self.lexer.peek() == '('):
                self.call_expr()
            else:
                self.var_rvalue()

    def new_rvalue(self):
        self.eat(TokenType.NEW, "Expected NEW")
        if (self.match(TokenType.ID)):
            self.eat(TokenType.ID, "Expected ID")
            if (self.match(TokenType.LPAREN)):
                self.eat(TokenType.LPAREN, "Expected LPAREN")
                while (not self.match(TokenType.RPAREN)):
                    self.expr()
                    if (not self.match(TokenType.RPAREN)):
                        self.eat(TokenType.COMMA, " Expected COMMA")
                self.eat(TokenType.RPAREN, "Expected RPAREN")
                return
        elif (self.is_base_type()):
            self.advance()
        else:
            self.error("Expected Base Type or ID")
        self.eat(TokenType.LBRACKET, "Expected LBRACKET")
        self.expr()
        self.eat(TokenType.RBRACKET, "Expected RBRACKET")

    def var_rvalue(self):
        self.eat(TokenType.ID, "Expected ID")
        while (self.match_any([TokenType.LBRACKET, TokenType.DOT])):
            if (self.match(TokenType.LBRACKET)):
                self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                self.expr()
                self.eat(TokenType.RBRACKET, "Expected RBRACKET")
            elif (self.match(TokenType.DOT)):
                self.eat(TokenType.DOT, "Expected DOT")
                self.eat(TokenType.ID, "Expected ID")
                if (self.match(TokenType.LBRACKET)):
                    self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                    self.expr()
                    self.eat(TokenType.RBRACKET, "Expected RBRACKET")

    # ----------------------------------------------------------------------
    # Statement Functions
    # ----------------------------------------------------------------------
    def while_stmt(self):
        """Check for well-formed while statements."""
        self.eat(TokenType.WHILE, "Expected while")
        if (not self.match(TokenType.LPAREN)):
            self.error("Expected LPAREN")
        self.expr()
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.stmt_def()
        self.eat(TokenType.RBRACE, "Expected RBRACE")

    def if_stmt(self):
        """Check for well-formed if statements."""
        self.eat(TokenType.IF, "Expected if")
        if (not self.match(TokenType.LPAREN)):
            self.error(" Expected LPAREN")
        self.expr()
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.stmt_def()
        self.eat(TokenType.RBRACE, "Expected RBRACE")
        self.if_stmt_t()

    def if_stmt_t(self):
        match (self.curr_token.token_type):
            case TokenType.ELSEIF:
                self.advance()
                if (not self.match(TokenType.LPAREN)):
                    self.error(" Expected LPAREN")
                self.expr()
                self.eat(TokenType.LBRACE, "Expected LBRACE")
                self.stmt_def()
                self.eat(TokenType.RBRACE, "Expected RBRACE")
                self.if_stmt_t()
            case TokenType.ELSE:
                self.advance()
                self.eat(TokenType.LBRACE, "Expected LBRACE")
                self.stmt_def()
                self.eat(TokenType.RBRACE, "Expected RBRACE")
            case _:
                return

    def for_stmt(self):
        self.eat(TokenType.FOR, " Expected FOR")
        self.eat(TokenType.LPAREN, " Expected LPAREN")
        self.vdecl_stmt(False)
        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
        self.expr()
        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
        self.assign_stmt(False)
        self.eat(TokenType.RPAREN, " Expected RPAREN")
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.stmt_def()
        self.eat(TokenType.RBRACE, "Expected RBRACE")

    def return_stmt(self):
        self.eat(TokenType.RETURN, " Expected RETURN")
        if (self.match(TokenType.SEMICOLON)):
            self.error("Expected Non-Empty Expression")
        self.expr()

    def assign_stmt(self, skip_id):
        self.lvalue(skip_id)
        self.eat(TokenType.ASSIGN, " Expected ASSIGN")
        if (self.match(TokenType.SEMICOLON)):
            self.error("Expected Non-Empty Expression")
        self.expr()

    def call_expr(self, skip_id):
        if (not skip_id):
            self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.LPAREN, " Expected LPAREN")
        while (not self.match(TokenType.RPAREN)):
            self.expr()
            if (not self.match(TokenType.RPAREN)):
                self.eat(TokenType.COMMA, " Expected COMMA")
        self.eat(TokenType.RPAREN, " Expected RPAREN")

    def vdecl_stmt(self, skipID):
        if (not skipID):
            self.data_type()
        self.eat(TokenType.ID, "Expected ID")
        if (self.match(TokenType.ASSIGN)):
            self.eat(TokenType.ASSIGN, " Expected ASSIGN")
            if (self.match(TokenType.SEMICOLON)):
                self.error("Expected Non-Empty Expression")
            self.expr()
