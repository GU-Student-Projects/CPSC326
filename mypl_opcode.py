"""OpCodes enumerated values for the MyPL VM instructions.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""
from enum import Enum

# instruction opcodes where A is the operand (argument); push and pop
# operations are applied to the operand stack, and x, y, and z are stack
# values
OpCode = Enum('OpCode', [

    # literals and variables
    'PUSH',    # push operand A
    'POP',     # pop x
    'LOAD',    # push value at memory address (operand) A 
    'STORE',   # pop x, store x at memory address (operand) A

    # arithmetic, relational, and logical operators
    'ADD',     # pop x, pop y, push (y + x) 
    'SUB',     # pop x, pop y, push (y - x) 
    'MUL',     # pop x, pop y, push (y * x)
    'DIV',     # pop x, pop y, push (y // x) or (y / x)
    'CMPLT',   # pop x, pop y, push (y < x)
    'CMPLE',   # pop x, pop y, push (y <= x)
    'CMPEQ',   # pop x, pop y, push (y == x)
    'CMPNE',   # pop x, pop y, push (y != x)
    'AND',     # pop x, pop y, push (y and x)
    'OR',      # pop x, pop y, push (y or x)
    'NOT',     # pop x, push (not x)

    # jump and branch
    'JMP',     # jump to given instruction offset A
    'JMPF',    # pop x, if x is False jump to instruction offset A

    # functions
    'CALL',    # call function A (pop and push arguments)
    'RET',     # return from current function

    # built ins
    'WRITE',   # pop x, print x to standard output
    'READ',    # read standard input, push result onto stack
    'LEN',     # pop string x, push len(x) if str, else push len(obj(x))
    'GETC',    # pop string x, pop int y, push x[y]
    'TOINT',   # pop x, push int(x)
    'TODBL',   # pop x, push double(x)
    'TOSTR',   # pop x, push str(x)

    # heap
    'ALLOCS',  # allocate struct object, push oid x
    'SETF',    # pop value x, pop oid y, set obj(y)[A] = x
    'GETF',    # pop oid x, push obj(x)[A] onto stack
    'ALLOCA',  # pop int x, allocate array object with x None values, push oid
    'SETI',    # pop value x, pop index y, pop oid z, set array obj(z)[y] = x
    'GETI',    # pop index x, pop oid y, push obj(y)[x] onto stack

    # special
    'DUP',     # pop x, push x, push x
    'NOP'      # do nothing
])
