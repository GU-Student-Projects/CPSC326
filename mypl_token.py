"""MyPL token and token type representations. 

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from enum import Enum


TokenType = Enum('TokenType', [
    # end-of-stream, identifiers, comments
    'EOS', 'ID', 'COMMENT',
    # punctuation
    'DOT', 'COMMA', 'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'SEMICOLON',
    'LBRACE', 'RBRACE',
    # operators
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'ASSIGN', 'AND', 'OR', 'NOT', 
    # relational comparators
    'EQUAL', 'NOT_EQUAL', 'LESS', 'LESS_EQ', 'GREATER', 'GREATER_EQ', 
    # values
    'INT_VAL', 'DOUBLE_VAL', 'STRING_VAL', 'BOOL_VAL', 'NULL_VAL',
    # primitive data types
    'INT_TYPE', 'DOUBLE_TYPE', 'STRING_TYPE', 'BOOL_TYPE', 'VOID_TYPE', 
    # reserved words
    'STRUCT', 'ARRAY', 'FOR', 'WHILE', 'IF', 'ELSEIF', 'ELSE', 'NEW', 'RETURN'
])
    

@dataclass
class Token:
    token_type: TokenType
    lexeme: str
    line: int
    column: int

    def __repr__(self):
        """Returns a string representation of the token."""
        return f'{self.line}, {self.column}: {self.token_type.name} "{self.lexeme}"'



