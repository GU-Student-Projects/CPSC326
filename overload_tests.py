import pytest
import io

from mypl_error import *
from mypl_iowrapper import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast_parser import *
from mypl_var_table import *
from mypl_code_gen import *
from mypl_vm import *


def build(program):
    in_stream = FileWrapper(io.StringIO(program))
    vm = VM()
    cg = CodeGenerator(vm)
    ASTParser(Lexer(FileWrapper(io.StringIO(program)))).parse().accept(cg)
    return vm


def test_no_values(capsys):
    program = (
        'void testOverload(int i) {\n'
        '   print("Err"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload(); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'No params'

def test_int_values(capsys):
    program = (
        'void testOverload(int i) {\n'
        '   print("One Param"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload(1); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'One Param'

def test_string_values(capsys):
    program = (
        'void testOverload(string s) {\n'
        '   print(s); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload("Hello"); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'Hello'

def test_double_values(capsys):
    program = (
        'void testOverload(double d) {\n'
        '   print("dbl"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload(1.0); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'dbl'

def test_double_var_values(capsys):
    program = (
        'void testOverload(double d) {\n'
        '   print("dbl"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   double d = 1.2; \n'
        '   testOverload(d); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'dbl'

def test_bool_values(capsys):
    program = (
        'void testOverload(bool b) {\n'
        '   print("bool"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload(false); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'bool'

def test_not_bool_values(capsys):
    program = (
        'void testOverload(bool b) {\n'
        '   print("bool"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload(not false); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'bool'

def test_struct_values(capsys):
    program = (
        'struct T { \n'
        '   int x; \n'
        '} \n'
        'void testOverload(T t) {\n'
        '   print("t struct"); \n'
        '} \n'
        'void testOverload() {\n'
        '   print("No params"); \n'
        '} \n'
        'void main() { \n'
        '   T t = new T(5); \n'
        '   testOverload(t); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 't struct'

def test_multiple_param_values(capsys):
    program = (
        'void testOverload(string s, int i) {\n'
        '   print("string and int"); \n'
        '} \n'
        'void testOverload(string s) {\n'
        '   print("just string"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload("Hello", 5); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'string and int'

def test_multiple_param_values_defined_last(capsys):
    program = (
        'void testOverload(string s) {\n'
        '   print("just string"); \n'
        '} \n'
        'void testOverload(string s, int i) {\n'
        '   print("string and int"); \n'
        '} \n'
        'void main() { \n'
        '   testOverload("Hello", 5); \n'
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'string and int'

def test_return_values(capsys):
    program = (
        'int testOverload(string s) {\n'
        '   print("just string"); \n'
        '} \n'
        'string testOverload(string s, int i) {\n'
        '   return s; \n'
        '} \n'
        'void main() { \n'
        '   string s = testOverload("Hello", 5); \n'
        '   print(s);'  
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'Hello'

def test_return_values_alt(capsys):
    program = (
        'int testOverload(string s) {\n'
        '   return 12; \n'
        '} \n'
        'string testOverload(string s, int i) {\n'
        '   return s; \n'
        '} \n'
        'void main() { \n'
        '   int i = testOverload("Hello"); \n'
        '   print(itos(i));'  
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == '12'

def test_diff_arg_types(capsys):
    program = (
        'void testOverload(string s) {\n'
        '   print(s); \n'
        '} \n'
        'void testOverload(int i) {\n'
        '   print(itos(i)); \n'
        '} \n'
        'void main() { \n'
        '   testOverload("Hello"); \n'
        '   testOverload(6); \n'  
        '} \n'
    )
    build(program).run()
    captured = capsys.readouterr()
    assert captured.out == 'Hello6'
