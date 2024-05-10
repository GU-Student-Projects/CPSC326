"""Implementation of the MyPL Virtual Machine (VM).

NAME: Jake VanZyverden
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_error import *
from mypl_opcode import *
from mypl_frame import *


class VM:

    def __init__(self):
        """Creates a VM."""
        self.struct_heap = {}        # id -> dict
        self.array_heap = {}         # id -> list
        self.next_obj_id = 2024      # next available object id (int)
        self.frame_templates = {}    # function name -> VMFrameTemplate
        self.call_stack = []         # function call stack

    
    def __repr__(self):
        """Returns a string representation of frame templates."""
        s = ''
        for name, template in self.frame_templates.items():
            s += f'\nFrame {name}\n'
            for i in range(len(template.instructions)):
                s += f'  {i}: {template.instructions[i]}\n'
        return s

    
    def add_frame_template(self, template):
        """Add the new frame info to the VM. 

        Args: 
            frame -- The frame info to add.

        """
        self.frame_templates[template.function_name] = template

    
    def error(self, msg, frame=None):
        """Report a VM error."""
        if not frame:
            raise VMError(msg)
        pc = frame.pc - 1
        instr = frame.template.instructions[pc]
        name = frame.template.function_name
        msg += f' (in {name} at {pc}: {instr})'
        raise VMError(msg)

    
    #----------------------------------------------------------------------
    # RUN FUNCTION
    #----------------------------------------------------------------------
    
    def run(self, debug=False):
        """Run the virtual machine."""

        # grab the "main" function frame and instantiate it
        if not 'main' in self.frame_templates:
            self.error('No "main" functrion')
        frame = VMFrame(self.frame_templates['main'])
        self.call_stack.append(frame)

        # run loop (continue until run out of call frames or instructions)
        while self.call_stack and frame.pc < len(frame.template.instructions):
            # get the next instruction
            instr = frame.template.instructions[frame.pc]
            # increment the program count (pc)
            frame.pc += 1
            # for debugging:
            if debug:
                print('\n')
                print('\t FRAME.........:', frame.template.function_name)
                print('\t PC............:', frame.pc)
                print('\t INSTRUCTION...:', instr)
                val = None if not frame.operand_stack else frame.operand_stack[-1]
                print('\t NEXT OPERAND..:', val)
                cs = self.call_stack
                fun = cs[-1].template.function_name if cs else None
                print('\t NEXT FUNCTION..:', fun)

            #------------------------------------------------------------
            # Literals and Variables
            #------------------------------------------------------------

            if instr.opcode == OpCode.PUSH:
                frame.operand_stack.append(instr.operand)

            elif instr.opcode == OpCode.POP:
                frame.operand_stack.pop()

            elif instr.opcode == OpCode.LOAD:
                index = instr.operand
                frame.operand_stack.append(frame.variables[index])
            elif instr.opcode == OpCode.STORE:
                data = frame.operand_stack.pop()
                index = instr.operand
                if (len(frame.variables) == index):
                    frame.variables.append(data)
                else:
                    frame.variables[index] = data


            
            #------------------------------------------------------------
            # Operations
            #------------------------------------------------------------
            elif (instr.opcode == OpCode.ADD
            or instr.opcode == OpCode.SUB
            or instr.opcode == OpCode.MUL
            or instr.opcode == OpCode.DIV
            or instr.opcode == OpCode.CMPLT
            or instr.opcode == OpCode.CMPLE
            or instr.opcode == OpCode.CMPEQ
            or instr.opcode == OpCode.CMPNE
            or instr.opcode == OpCode.AND
            or instr.opcode == OpCode.OR
            ):
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                result = self.do_operation(x, y, instr.opcode.name)
                if (result is True or result is False):
                    result = "true" if (result) else "false"
                frame.operand_stack.append(result)
            elif instr.opcode == OpCode.NOT:
                x = frame.operand_stack.pop()
                if (x is None):
                    self.error("Invalid value for not operation")
                result = "true" if (not x) else "false"
                frame.operand_stack.append(result)
            

            #------------------------------------------------------------
            # Branching
            #------------------------------------------------------------


            elif instr.opcode == OpCode.JMP:
                offset = instr.operand
                frame.pc = offset
            elif instr.opcode == OpCode.JMPF:
                offset = instr.operand
                x = frame.operand_stack.pop()
                if (x == 'true' or x == 'false'):
                    x = True if (x == 'true') else False
                if (not x):
                    frame.pc = offset
                    
            #------------------------------------------------------------
            # Functions
            #------------------------------------------------------------


            elif instr.opcode == OpCode.CALL:
                fun_name = instr.operand
                new_frame_template = self.frame_templates[fun_name]
                new_frame = VMFrame(new_frame_template)
                self.call_stack.append(new_frame)
                for i in range(new_frame.template.arg_count):
                    arg = frame.operand_stack.pop()
                    new_frame.operand_stack.append(arg)
                frame = new_frame
            elif instr.opcode == OpCode.RET:
                ret_val = frame.operand_stack.pop()
                self.call_stack.pop()
                if (self.call_stack):
                    frame = self.call_stack[-1]
                    frame.operand_stack.append(ret_val)

            
            #------------------------------------------------------------
            # Built-In Functions
            #------------------------------------------------------------

            elif instr.opcode == OpCode.WRITE:
                val = frame.operand_stack.pop()
                if (val is True or val is False):
                    val = str.lower(str(val))
                if (val is None):
                    print("null", end="")
                    continue
                val = str(val).replace('\\n', '\n')
                val = val.replace('\\t', '\t')
                print(val, end="")
            elif instr.opcode == OpCode.READ:
                val = input()
                frame.operand_stack.append(val)
            elif instr.opcode == OpCode.LEN:
                val = frame.operand_stack.pop()
                if (val is None):
                    self.error("Cannot execute len operation on null value")
                if (type(val) == str):
                    frame.operand_stack.append(len(val))
                else:
                    frame.operand_stack.append(len(self.array_heap[val]))
            elif instr.opcode == OpCode.GETC:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if (y is None or x is None):
                    self.error("Cannot execute getc operation on null value")
                if (len(x) - 1 < y or y < 0):
                    self.error("Invalid index for getc operation")
                frame.operand_stack.append(x[y])
            elif instr.opcode == OpCode.TOINT:
                x = frame.operand_stack.pop()
                try:
                    y = int(x)
                    frame.operand_stack.append(y)
                except:
                    self.error("Cannot convert value to int")
            elif instr.opcode == OpCode.TODBL:
                x = frame.operand_stack.pop()
                try:
                    y = float(x)
                    frame.operand_stack.append(y)
                except:
                    self.error("Cannot convert value to double")
            elif instr.opcode == OpCode.TOSTR:
                x = frame.operand_stack.pop()
                if (x is None):
                    self.error("Cannot convert null value to string")
                frame.operand_stack.append(str(x))

            
            
            #------------------------------------------------------------
            # Heap
            #------------------------------------------------------------


            elif instr.opcode == OpCode.ALLOCS:
                oid = self.next_obj_id
                self.next_obj_id += 1
                self.struct_heap[oid] = {}
                frame.operand_stack.append(oid)
            elif instr.opcode == OpCode.SETF:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if (y is None):
                    self.error("Invalid value for OID or field value for struct")
                self.struct_heap[y][instr.operand] = x
            elif instr.opcode == OpCode.GETF:
                x = frame.operand_stack.pop()
                if (x is None):
                    self.error("Invalid value for OID for struct")
                frame.operand_stack.append(self.struct_heap[x][instr.operand])
            elif instr.opcode == OpCode.ALLOCA:
                oid = self.next_obj_id
                self.next_obj_id += 1
                array_length = frame.operand_stack.pop()
                if (array_length is None or array_length < 0):
                    self.error("Invalid value for array length")
                self.array_heap[oid] = [None for _ in range(array_length)]
                frame.operand_stack.append(oid)
            elif instr.opcode == OpCode.SETI:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                oid = frame.operand_stack.pop()
                if (x is None or y is None or oid is None):
                    self.error("Invalid value for insert into array")
                if (len(self.array_heap[oid]) - 1 < y or y < 0):
                    self.error("Invalid index for array lookup")
                self.array_heap[oid][y] = x
            elif instr.opcode == OpCode.GETI:
                x = frame.operand_stack.pop()
                y = frame.operand_stack.pop()
                if (x is None or y is None):
                    self.error("Invalid value for array lookup")
                if (len(self.array_heap[y]) - 1 < x or x < 0):
                    self.error("Invalid index for array lookup")
                frame.operand_stack.append(self.array_heap[y][x])
            
            
            #------------------------------------------------------------
            # Special 
            #------------------------------------------------------------

            elif instr.opcode == OpCode.DUP:
                x = frame.operand_stack.pop()
                frame.operand_stack.append(x)
                frame.operand_stack.append(x)

            elif instr.opcode == OpCode.NOP:
                # do nothing
                pass

            else:
                self.error(f'unsupported operation {instr}')

    def do_operation(self, x, y, op_name):
        if (x is None or y is None):
            if (op_name != "CMPEQ" and op_name != "CMPNE"):
                self.error('Invalid value in operation')
        match(op_name):
            case "ADD":
                return y + x
            case "SUB":
                return y - x
            case "MUL":
                return y * x
            case "DIV":
                if (int(x) == 0):
                    self.error("Invalid value for operation")
                if (type(y) is float or type(x) is float):
                    return y / x
                else:
                    return y // x
            case "CMPLT":
                return y < x
            case "CMPLE":
                return y <= x
            case "CMPEQ":
                return y == x
            case "CMPNE":
                return y != x
            case "AND":
                return y and x
            case "OR":
                return y or x
            case _:
                self.error("Unknown operation!")