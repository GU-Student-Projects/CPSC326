"""Initial main program driver for MyPL.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""

import argparse
import sys
import io

from mypl_iowrapper import FileWrapper, StdInWrapper
from mypl_error import MyPLError
from mypl_lexer import Lexer
from mypl_token import TokenType, Token
from mypl_simple_parser import SimpleParser
from mypl_ast_parser import ASTParser
from mypl_printer import PrintVisitor
from mypl_semantic_checker import SemanticChecker
from mypl_code_gen import CodeGenerator
from mypl_vm import VM


def run_lex_mode(in_stream):
    """Runs the lexer on the given mypl program and prints to standard
    output the resulting tokens.

    Args: 
        in_stream -- A wrapped input stream containing a mypl program.

    """
    try: 
        lexer = Lexer(in_stream)
        t = lexer.next_token()
        while t.token_type != TokenType.EOS:
            print(t)
            t = lexer.next_token()
        print(t)
    except MyPLError as ex:
        print(ex)
        exit(1)
    

    
def run_parse_mode(in_stream):
    """Runs the parser on the given mypl program and prints to standard
    output any parsing errors. If no errors, the mypl program is
    considered syntactically well formed.

    Args: 
        in_stream -- A wrapped input stream containing a mypl program.

    """
    try: 
        lexer = Lexer(in_stream)
        parser = SimpleParser(lexer)
        parser.parse()
    except MyPLError as ex:
        print(ex)
        exit(1)

    
    
def run_print_mode(in_stream):
    """Runs the pretty printer on the given mypl program and prints to
    standard output a formatted version of the program.

    Args: 
        in_stream -- A wrapped input stream containing a mypl program.

    """
    try: 
        lexer = Lexer(in_stream)
        parser = ASTParser(lexer)
        ast = parser.parse()
        visitor = PrintVisitor()
        ast.accept(visitor)
    except MyPLError as ex:
        print(ex)
        exit(1)

        
    
def run_check_mode(in_stream):
    """Runs the semantic checker on the given mypl program any prints any
    semantic errors it finds. If no errors, the mypl program is
    considered semantically well formed.

    Args: 
        in_stream -- A wrapped input stream containing a mypl program.

    """
    try: 
        lexer = Lexer(in_stream)
        parser = ASTParser(lexer)
        ast = parser.parse()
        visitor = SemanticChecker()
        ast.accept(visitor)
    except MyPLError as ex:
        print(ex)
        exit(1)



    
def run_ir_mode(in_stream):
    """Generates the intermediate representation (VM instructions) for the
    given mypl program and prints to standard output the resulting
    instructions.

    Args: 
        in_stream -- A wrapped input stream containing a mypl program.

    """
    try:
        lexer = Lexer(in_stream)
        parser = ASTParser(lexer)
        ast = parser.parse()
        visitor = SemanticChecker()
        ast.accept(visitor)
        vm = VM()
        codegen = CodeGenerator(vm)
        ast.accept(codegen)
        print(vm)
    except MyPLError as ex:
        print(ex)
        exit(1)

    
def run_normal_mode(in_stream):
    """Executes the given mypl program. Any output produced by the program
    is printed to standard output. 

    Args: 
        in_stream -- A wrapped input stream containing a mypl program.

    """
    try:
        lexer = Lexer(in_stream)
        parser = ASTParser(lexer)
        ast = parser.parse()
        visitor = SemanticChecker()
        # ast.accept(visitor)
        vm = VM()
        codegen = CodeGenerator(vm)
        ast.accept(codegen)
        vm.run()
    except MyPLError as ex:
        print(ex)
        exit(1)


    
if __name__ == '__main__':
    # initial help/usage info
    about = ('Run the mypl interpreter.\n'
             'If filename missing, reads from standard input.')
    # set up the argument parser
    argparser = argparse.ArgumentParser(prog='mypl', description=about)
    group = argparser.add_mutually_exclusive_group()
    # add each argument
    help_msg = 'displays token information'
    group.add_argument('--lex', action='store_true', help=help_msg)
    help_msg = 'checks for syntax errors'
    group.add_argument('--parse', action='store_true', help=help_msg)
    help_msg = 'pretty prints program'
    group.add_argument('--print', action='store_true', help=help_msg)
    help_msg = 'checks for static analysis errors'
    group.add_argument('--check', action='store_true', help=help_msg)
    help_msg = 'displays intermediate code'
    group.add_argument('--ir', action='store_true', help=help_msg)
    help_msg = 'mypl program file (optional)'
    argparser.add_argument('filename', nargs='?', help=help_msg)
    args = argparser.parse_args()
    # get the input (file or standard in)
    in_stream = StdInWrapper(sys.stdin)
    if args.filename:
        try: 
            in_stream = FileWrapper(open(args.filename, 'r', encoding='utf-8'))
        except: 
            print(f"ERROR: Could not open file '{args.filename}'")
            exit(1)
    # check args and route to appropriate function
    if args.lex:
        run_lex_mode(in_stream)
    elif args.parse:
        run_parse_mode(in_stream)
    elif args.print:
        run_print_mode(in_stream)
    elif args.check:
        run_check_mode(in_stream)
    elif args.ir:
        run_ir_mode(in_stream)
    else:
        run_normal_mode(in_stream)
    # close the (wrapped) input stream
    in_stream.close()

