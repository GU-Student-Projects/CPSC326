"""IR code generator for converting MyPL to VM Instructions. 

NAME: Jake VanZyverden
DATE: Spring 2024
CLASS: CPSC 326

"""

from mypl_token import *
from mypl_ast import *
from mypl_var_table import *
from mypl_frame import *
from mypl_opcode import *
from mypl_vm import *


class CodeGenerator(Visitor):

    def __init__(self, vm):
        """Creates a new Code Generator given a VM. 
        
        Args:
            vm -- The target vm.
        """
        # the vm to add frames to
        self.vm = vm
        # the current frame template being generated
        self.curr_template = None
        # for var -> index mappings wrt to environments
        self.var_table = VarTable()
        # struct name -> StructDef for struct field info
        self.struct_defs = {}

    def add_instr(self, instr):
        """Helper function to add an instruction to the current template."""
        self.curr_template.instructions.append(instr)

    def visit_program(self, program):
        for struct_def in program.struct_defs:
            struct_def.accept(self)
        for fun_def in program.fun_defs:
            fun_def.accept(self)

    def visit_struct_def(self, struct_def):
        # remember the struct def for later
        self.struct_defs[struct_def.struct_name.lexeme] = struct_def

    def visit_fun_def(self, fun_def):
        self.curr_template = VMFrameTemplate(fun_def.fun_name.lexeme, len(fun_def.params), [])
        return_stmts = []
        self.var_table.push_environment()
        for param in fun_def.params:
            self.curr_template.function_name += ("_" + param.data_type.type_name.lexeme)
            self.var_table.add(param.var_name.lexeme)
            self.add_instr(STORE(self.var_table.get(param.var_name.lexeme)))
        last_stmt = None
        if (fun_def.stmts):
            for stmt in fun_def.stmts:
                stmt.accept(self)
                last_stmt = stmt
        if (not(last_stmt and isinstance(last_stmt, ReturnStmt))):
            self.add_instr(PUSH(None))
            self.add_instr(RET())
        self.var_table.pop_environment()
        for stmt in return_stmts:
            self.curr_template.instructions[stmt] = JMP(len(self.curr_template.instructions))
        self.add_instr(NOP())
        self.vm.add_frame_template(self.curr_template)

    def visit_return_stmt(self, return_stmt):
        return_stmt.expr.accept(self)
        self.add_instr(RET())

    def visit_var_decl(self, var_decl):
        self.var_table.add(var_decl.var_def.var_name.lexeme)
        if (var_decl.expr):
            var_decl.expr.accept(self)
        else:
            self.instr = self.add_instr(PUSH(None))
        self.add_instr(STORE(self.var_table.get(var_decl.var_def.var_name.lexeme)))

    def visit_assign_stmt(self, assign_stmt):
        if (len(assign_stmt.lvalue) < 2):
            if (assign_stmt.lvalue[0].array_expr):
                self.add_instr(LOAD(self.var_table.get(assign_stmt.lvalue[0].var_name.lexeme)))
                assign_stmt.lvalue[0].array_expr.accept(self)
                assign_stmt.expr.accept(self)
                self.add_instr(SETI())
            else:
                assign_stmt.expr.accept(self)
                self.add_instr(STORE(self.var_table.get(assign_stmt.lvalue[0].var_name.lexeme)))
        else:
            self.add_instr(LOAD(self.var_table.get(assign_stmt.lvalue[0].var_name.lexeme)))
            if (self.var_table.get(assign_stmt.lvalue[0].array_expr)):
                assign_stmt.lvalue[0].array_expr.accept(self)
            if (len(assign_stmt.lvalue) > 2):
                for value in assign_stmt.lvalue[1:-1]:
                    self.add_instr(GETF(value.var_name.lexeme))
                    if (value.array_expr):
                        value.array_expr.accept(self)
                        self.add_instr(GETI())
            last_value = assign_stmt.lvalue[len(assign_stmt.lvalue) - 1]
            if (last_value.array_expr):
                if (self.var_table.get(last_value.var_name.lexeme)):
                    self.add_instr(LOAD(self.var_table.get(last_value.var_name.lexeme)))
                else:
                    self.add_instr(GETF(last_value.var_name.lexeme))
                last_value.array_expr.accept(self)
                assign_stmt.expr.accept(self)
                self.add_instr(SETI())
            else:
                assign_stmt.expr.accept(self)
                self.add_instr(SETF(last_value.var_name.lexeme))

    def visit_while_stmt(self, while_stmt):
        jmp_index = len(self.curr_template.instructions)
        while_stmt.condition.accept(self)
        temp_index = len(self.curr_template.instructions)
        self.add_instr(JMPF(-1))
        self.var_table.push_environment()
        for stmt in while_stmt.stmts:
            stmt.accept(self)
        self.var_table.pop_environment()
        self.add_instr(JMP(jmp_index))
        self.add_instr(NOP())
        self.curr_template.instructions[temp_index] = JMPF(len(self.curr_template.instructions) - 1)

    def visit_for_stmt(self, for_stmt):
        self.var_table.push_environment()
        for_stmt.var_decl.accept(self)
        jmp_index = len(self.curr_template.instructions)
        for_stmt.condition.accept(self)
        temp_index = len(self.curr_template.instructions)
        self.add_instr(JMPF(-1))
        self.var_table.push_environment()
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        self.var_table.pop_environment()
        for_stmt.assign_stmt.accept(self)
        self.var_table.pop_environment()
        self.add_instr(JMP(jmp_index))
        self.add_instr(NOP())
        self.curr_template.instructions[temp_index] = JMPF(len(self.curr_template.instructions) - 1)

    def visit_if_stmt(self, if_stmt):
        if_stmt.if_part.condition.accept(self)
        if_jmp_index = len(self.curr_template.instructions)
        self.add_instr(JMPF(-1))
        self.var_table.push_environment()
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        self.var_table.pop_environment()
        jump_end_indexes = []
        jump_end_indexes.append(len(self.curr_template.instructions))
        self.add_instr(JMP(-1))
        if (if_stmt.else_ifs):
            self.add_instr(NOP())
            self.curr_template.instructions[if_jmp_index] = JMPF(len(self.curr_template.instructions) - 1)
            for basic_if in if_stmt.else_ifs:
                basic_if.condition.accept(self)
                if_jmp_index = len(self.curr_template.instructions)
                self.add_instr(JMPF(-1))
                self.var_table.push_environment()
                for stmt in basic_if.stmts:
                    stmt.accept(self)
                self.var_table.pop_environment()
                jump_end_indexes.append(len(self.curr_template.instructions))
                self.add_instr(JMP(-1))
                self.add_instr(NOP())
                self.curr_template.instructions[if_jmp_index] = JMPF(len(self.curr_template.instructions) - 1)
        if (if_stmt.else_stmts):
            self.curr_template.instructions[if_jmp_index] = JMPF(len(self.curr_template.instructions) - 1)
            self.var_table.push_environment()
            for stmt in if_stmt.else_stmts:
                stmt.accept(self)
            self.var_table.pop_environment()
            self.add_instr(NOP())
        else:
            self.add_instr(NOP())
            self.curr_template.instructions[if_jmp_index] = JMPF(len(self.curr_template.instructions) - 1)
        for index in jump_end_indexes:
            self.curr_template.instructions[index] = JMP(len(self.curr_template.instructions) - 1)

    def visit_call_expr(self, call_expr):
        for arg in call_expr.args:
            arg.accept(self)
        if (not call_expr.args):
            self.add_instr(PUSH(None))
        match (call_expr.fun_name.lexeme):
            case "print":
                self.add_instr(WRITE())
                return
            case "input":
                self.add_instr(READ())
            case "itos":
                self.add_instr(TOSTR())
            case "itod":
                self.add_instr(TODBL())
            case "dtos":
                self.add_instr(TOSTR())
            case "dtoi":
                self.add_instr(TOINT())
            case "stoi":
                self.add_instr(TOINT())
            case "stod":
                self.add_instr(TODBL())
            case "length":
                self.add_instr(LEN())
            case "get":
                self.add_instr(GETC())
            case _:
                call_arg_types = ""
                for type in call_expr.arg_types:
                    call_arg_types += ("_" + type)
                call_name = call_expr.fun_name.lexeme + call_arg_types
                self.add_instr(CALL(call_name))


    def visit_expr(self, expr):
        if (expr.op and (expr.op.token_type == TokenType.GREATER or expr.op.token_type == TokenType.GREATER_EQ)):
            expr.rest.accept(self)
            expr.first.accept(self)
        else:
            expr.first.accept(self)
            if (expr.rest):
                expr.rest.accept(self)
        if (expr.op):
            match (expr.op.token_type):
                case TokenType.PLUS:
                    self.add_instr(ADD())
                case TokenType.MINUS:
                    self.add_instr(SUB())
                case TokenType.TIMES:
                    self.add_instr(MUL())
                case TokenType.DIVIDE:
                    self.add_instr(DIV())
                case TokenType.AND:
                    self.add_instr(AND())
                case TokenType.OR:
                    self.add_instr(OR())
                case TokenType.EQUAL:
                    self.add_instr(CMPEQ())
                case TokenType.LESS:
                    self.add_instr(CMPLT())
                case TokenType.LESS_EQ:
                    self.add_instr(CMPLE())
                case TokenType.GREATER:
                    self.add_instr(CMPLT())
                case TokenType.GREATER_EQ:
                    self.add_instr(CMPLE())
                case TokenType.NOT_EQUAL:
                    self.add_instr(CMPNE())
        if (expr.not_op):
            self.add_instr(NOT())

    def visit_data_type(self, data_type):
        # nothing to do here
        pass

    def visit_var_def(self, var_def):
        # nothing to do here
        pass

    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)

    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)

    def visit_simple_rvalue(self, simple_rvalue):
        val = simple_rvalue.value.lexeme
        if simple_rvalue.value.token_type == TokenType.INT_VAL:
            self.add_instr(PUSH(int(val)))
        elif simple_rvalue.value.token_type == TokenType.DOUBLE_VAL:
            self.add_instr(PUSH(float(val)))
        elif simple_rvalue.value.token_type == TokenType.STRING_VAL:
            val = val.replace('\\n', '\n')
            val = val.replace('\\t', '\t')
            self.add_instr(PUSH(val))
        elif val == 'true':
            self.add_instr(PUSH(True))
        elif val == 'false':
            self.add_instr(PUSH(False))
        elif val == 'null':
            self.add_instr(PUSH(None))

    def visit_new_rvalue(self, new_rvalue):
        if (new_rvalue.array_expr):
            new_rvalue.array_expr.accept(self)
            self.add_instr(ALLOCA())
        if (new_rvalue.struct_params or self.struct_defs.get(new_rvalue.type_name.lexeme)):
            if (not new_rvalue.array_expr):
                self.add_instr(ALLOCS())
                struct = self.struct_defs.get(new_rvalue.type_name.lexeme)
                i = 0
                for str_field in struct.fields:
                    self.add_instr(DUP())
                    new_rvalue.struct_params[i].accept(self)
                    self.add_instr(SETF(str_field.var_name.lexeme))
                    i = i + 1
        pass

    def visit_var_rvalue(self, var_rvalue):
        index = self.var_table.get(var_rvalue.path[0].var_name.lexeme)
        self.add_instr(LOAD(index))
        if (var_rvalue.path[0].array_expr):
            var_rvalue.path[0].array_expr.accept(self)
            self.add_instr(GETI())
        for path in var_rvalue.path[1:]:
            self.add_instr(DUP())
            self.add_instr(GETF(path.var_name.lexeme))
            if (path.array_expr):
                path.array_expr.accept(self)
                self.add_instr(GETI())
