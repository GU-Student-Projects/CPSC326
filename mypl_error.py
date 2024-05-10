"""Simple class for representing MyPL lexer, parser, static checker,
and runtime errors.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""


class MyPLError(BaseException):
    """For MyPL exceptions."""

    def __init__(self, message):
        """Create a MyPLError exception object. 
        
        Args:
            message -- The error message.
        
        """
        super().__init__(message)
        

        
def LexerError(message):
    """Create a MyPLError for a lexer exception.
    
    Args:
        message -- The error message.

    """
    return MyPLError('Lexer Error: ' + message)



def ParserError(message):
    """Create a MyPLError for a parser exception.
    
    Args:
        message -- The error message.

    """
    return MyPLError('Parser Error: ' + message)        



def StaticError(message):
    """Create a MyPLError for a static exception.
    
    Args:
        message -- The error message.

    """
    return MyPLError('Static Error: ' + message)        


def VMError(message):
    """Create a MyPLError for a runtime exception.
    
    Args:
        message -- The error message.

    """
    return MyPLError('VM Error: ' + message)        





