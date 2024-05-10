"""Implementation of Frame Templates, Frames, and Instructions for the
MyPL VM.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""


from dataclasses import dataclass, field
from typing import Any
from mypl_opcode import OpCode


@dataclass
class VMFrameTemplate:

    """A VM function-call frame template (type)."""
    function_name: str
    arg_count: int
    instructions: list['VMInstr'] = field(default_factory=list) 

    
@dataclass
class VMFrame:
    """A VM function-call frame."""
    template: VMFrameTemplate
    pc: int = 0
    variables: list[Any] = field(default_factory=list) 
    operand_stack: list[Any] = field(default_factory=list) 


@dataclass
class VMInstr:
    """A VM instruction."""
    opcode: OpCode
    operand: Any = None
    comment: str = ''

    def __repr__(self):
        s = f'{self.opcode}('
        s += f'{str(self.operand)}' if self.operand != None else ''
        s += ')'
        s += f'  // {self.comment}' if self.comment else ''
        return s

# Helper functions for creating specific instruction types

def PUSH(value):
    return VMInstr(OpCode.PUSH, value)

def POP():
    return VMInstr(OpCode.POP)

def LOAD(mem_addr):
    return VMInstr(OpCode.LOAD, mem_addr)
    
def STORE(mem_addr):
    return VMInstr(OpCode.STORE, mem_addr)

def ADD():
    return VMInstr(OpCode.ADD)

def SUB():
    return VMInstr(OpCode.SUB)

def MUL():
    return VMInstr(OpCode.MUL)

def DIV():
    return VMInstr(OpCode.DIV)

def CMPLT():
    return VMInstr(OpCode.CMPLT)

def CMPLE():
    return VMInstr(OpCode.CMPLE)

def CMPEQ():
    return VMInstr(OpCode.CMPEQ)

def CMPNE():
    return VMInstr(OpCode.CMPNE)

def AND():
    return VMInstr(OpCode.AND)

def OR():
    return VMInstr(OpCode.OR)

def NOT():
    return VMInstr(OpCode.NOT)

def JMP(offset):
    return VMInstr(OpCode.JMP, offset)

def JMPF(offset):
    return VMInstr(OpCode.JMPF, offset)

def CALL(fun_name):
    return VMInstr(OpCode.CALL, fun_name)

def RET():
    return VMInstr(OpCode.RET)    

def WRITE():
    return VMInstr(OpCode.WRITE)

def READ():
    return VMInstr(OpCode.READ)

def LEN():
    return VMInstr(OpCode.LEN)

def GETC():
    return VMInstr(OpCode.GETC)

def TOINT():
    return VMInstr(OpCode.TOINT)

def TODBL():
    return VMInstr(OpCode.TODBL)

def TOSTR():
    return VMInstr(OpCode.TOSTR)

def ALLOCS():
    return VMInstr(OpCode.ALLOCS)

def SETF(field_name):
    return VMInstr(OpCode.SETF, field_name)

def GETF(field_name):
    return VMInstr(OpCode.GETF, field_name)

def ALLOCA():
    return VMInstr(OpCode.ALLOCA)

def SETI():
    return VMInstr(OpCode.SETI)

def GETI():
    return VMInstr(OpCode.GETI)

def DUP():
    return VMInstr(OpCode.DUP)

def NOP():
    return VMInstr(OpCode.NOP)



    
