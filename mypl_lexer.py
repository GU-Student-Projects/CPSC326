"""The MyPL Lexer class.

NAME: <your name here>
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_error import *


class Lexer:
    """For obtaining a token stream from a program."""

    def __init__(self, in_stream):
        """Create a Lexer over the given input stream.

        Args:
            in_stream -- The input stream. 

        """
        self.in_stream = in_stream
        self.line = 1
        self.column = 0


    def read(self):
        """Returns and removes one character from the input stream."""
        ch = self.in_stream.read_char()
        if (ch != '\n'):
            self.column += 1
        else:
            self.line += 1
            self.column = 0
        return ch

    
    def peek(self):
        """Returns but doesn't remove one character from the input stream."""
        return self.in_stream.peek_char()

    
    def eof(self, ch):
        """Return true if end-of-file character"""
        return ch == ''

    
    def error(self, message, line, column):
        raise LexerError(f'{message} at line {line}, column {column}')


    def readComment(self):
        commentLexeme = ''
        while(self.peek() != '\n' and not self.eof(self.peek())):
            commentLexeme += self.read()
        return commentLexeme

    def readString(self):
        string_val = ''
        while(self.peek() != '\"'):
            if (self.peek() == '\n'):
                self.error('Cannot have multi-line string!', self.line, self.column)
            string_val += self.read()
        self.read()
        return string_val

    def readNumber(self, start_int, ret_line, ret_col):
        number_val = str(start_int)
        decimal = False
        while (self.peek().isdigit() or self.peek() == '.'):
            if (self.peek() == '.'):
                if (decimal == True):
                    break
                decimal = True
            number_val += self.read()
        if (len(number_val) > 1 and number_val[0] == '0'):
            leading_zero = False
            for(index,char) in enumerate(number_val):
                if (char != '0' and char != '.'):
                    leading_zero = True
                elif (char == '.'):
                    leading_zero = False
                    break
            if (leading_zero):
                self.error('Number values may not have leading zeroes!', self.line, self.column)
        if (decimal):
            if (number_val[len(number_val) - 1] == '.'):
                self.error('Cannot end decimal value with non-numeric character.', self.line, self.column)
            return Token(TokenType.DOUBLE_VAL, str(number_val), ret_line, ret_col)
        else:
            return Token(TokenType.INT_VAL, str(number_val), ret_line, ret_col)


    
    def next_token(self):
        """Return the next token in the lexer's input stream."""
        # read initial character
        ch = self.read()
        ret_line = self.line
        ret_col = self.column

        if self.eof(ch):
            return Token(TokenType.EOS, '', ret_line, ret_col)
        match ch:
            case '/':
                if (self.peek() == '/'):
                    self.read()
                    return Token(TokenType.COMMENT, str(self.readComment()), ret_line, ret_col)
                else:
                    return Token(TokenType.DIVIDE, '/', ret_line, ret_col)
            # Punctuation
            case '.':
                return Token(TokenType.DOT, '.', ret_line, ret_col)
            case ',':
                return Token(TokenType.COMMA, ',', ret_line, ret_col)
            case '(':
                return Token(TokenType.LPAREN, '(', ret_line, ret_col)
            case ')':
                return Token(TokenType.RPAREN, ')', ret_line, ret_col)
            case '[':
                return Token(TokenType.LBRACKET, '[', ret_line, ret_col)
            case ']':
                return Token(TokenType.RBRACKET, ']', ret_line, ret_col)
            case '{':
                return Token(TokenType.LBRACE, '{', ret_line, ret_col)
            case '}':
                return Token(TokenType.RBRACE, '}', ret_line, ret_col)
            case ';':
                return Token(TokenType.SEMICOLON, ';', ret_line, ret_col)
            # Operators
            case '+':
                return Token(TokenType.PLUS, '+', ret_line, ret_col)
            case '-':
                return Token(TokenType.MINUS, '-', ret_line, ret_col)
            case '*':
                return Token(TokenType.TIMES, '*', ret_line, ret_col)
            case '=':
                if (self.peek() != '='):
                    return Token(TokenType.ASSIGN, '=', ret_line, ret_col)
                else:
                    self.read()
                    return Token(TokenType.EQUAL, '==', ret_line, ret_col)
            # Relational Operators
            case '!':
                if (self.peek() == '='):
                    self.read()
                    return Token(TokenType.NOT_EQUAL, '!=', ret_line, ret_col)
                else:
                    self.error('Unexpected character ! ', ret_line, ret_col)
            case '<':
                if (self.peek() == '='):
                    self.read()
                    return Token(TokenType.LESS_EQ, '<=', ret_line, ret_col)
                return Token(TokenType.LESS, '<', ret_line, ret_col)
            case '>':
                if (self.peek() == '='):
                    self.read()
                    return Token(TokenType.GREATER_EQ, '>=', ret_line, ret_col)
                return Token(TokenType.GREATER, '>', ret_line, ret_col)
            # Values
            case '\"':
                return Token(TokenType.STRING_VAL, self.readString(), ret_line, ret_col)
            case _:
                if (ch.isdigit()):
                    return self.readNumber(ch, ret_line, ret_col)
                if (ch.isalpha()):
                    id = ch
                    while ((not self.peek().isspace()) and (self.peek().isalpha() or self.peek().isdigit() or self.peek() == '_')):
                        id += self.read()
                    match (id):
                        case 'and':
                            return Token(TokenType.AND, 'and', ret_line, ret_col)
                        case 'or':
                            return Token(TokenType.OR, 'or', ret_line, ret_col)
                        case 'not':
                            return Token(TokenType.NOT, 'not', ret_line, ret_col)
                        case 'int':
                            return Token(TokenType.INT_TYPE, 'int', ret_line, ret_col)
                        case 'double':
                            return Token(TokenType.DOUBLE_TYPE, 'double', ret_line, ret_col)
                        case 'string':
                            return Token(TokenType.STRING_TYPE, 'string', ret_line, ret_col)
                        case 'bool':
                            return Token(TokenType.BOOL_TYPE, 'bool', ret_line, ret_col)
                        case 'void':
                            return Token(TokenType.VOID_TYPE, 'void', ret_line, ret_col)
                        case 'struct':
                            return Token(TokenType.STRUCT, 'struct', ret_line, ret_col)
                        case 'array':
                            return Token(TokenType.ARRAY, 'array', ret_line, ret_col)
                        case 'for':
                            return Token(TokenType.FOR, 'for', ret_line, ret_col)
                        case 'while':
                            return Token(TokenType.WHILE, 'while', ret_line, ret_col)
                        case 'if':
                            return Token(TokenType.IF, 'if', ret_line, ret_col)
                        case 'elseif':
                            return Token(TokenType.ELSEIF, 'elseif', ret_line, ret_col)
                        case 'else':
                            return Token(TokenType.ELSE, 'else', ret_line, ret_col)
                        case 'new':
                            return Token(TokenType.NEW, 'new', ret_line, ret_col)
                        case 'return':
                            return Token(TokenType.RETURN, 'return', ret_line, ret_col)
                        case 'true' | 'false':
                            return Token(TokenType.BOOL_VAL, id, ret_line, ret_col)
                        case 'null':
                            return Token(TokenType.NULL_VAL, 'null', ret_line, ret_col)
                        case _:
                            return Token(TokenType.ID, id, ret_line, ret_col)
                if (ch.isspace()):
                    return self.next_token()
                else:
                    self.error("Invalid Character: " + ch, ret_line, ret_col)
        return Token(TokenType.EOS, '', ret_line, ret_col)