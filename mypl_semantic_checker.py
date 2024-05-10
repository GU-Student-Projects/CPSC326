"""Semantic Checker Visitor for semantically analyzing a MyPL program.

NAME: Jake VanZyverden
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_error import *
from mypl_token import Token, TokenType
from mypl_ast import *
from mypl_symbol_table import SymbolTable

BASE_TYPES = ['int', 'double', 'bool', 'string']
BUILT_INS = ['print', 'input', 'itos', 'itod', 'dtos', 'dtoi', 'stoi', 'stod',
             'length', 'get']
COMPARE_OPS = ['<', '<=', '>', '>=', '!=', '==', 'and', 'or']


class SemanticChecker(Visitor):
    """Visitor implementation to semantically check MyPL programs."""

    def __init__(self):
        self.structs = {}
        self.functions = {}
        self.symbol_table = SymbolTable()
        self.curr_type = None

    # Helper Functions

    def error(self, msg, token):
        """Create and raise a Static Error."""
        if token is None:
            raise StaticError(msg)
        else:
            m = f'{msg} near line {token.line}, column {token.column}'
            raise StaticError(m)

    def get_field_type(self, struct_def, field_name):
        """Returns the DataType for the given field name of the struct
        definition.

        Args:
            struct_def: The StructDef object 
            field_name: The name of the field

        Returns: The corresponding DataType or None if the field name
        is not in the struct_def.

        """
        for var_def in struct_def.fields:
            if var_def.var_name.lexeme == field_name:
                return var_def.data_type
        return None

    # Visitor Functions

    def visit_program(self, program):
        # check and record struct defs
        for struct in program.struct_defs:
            struct_name = struct.struct_name.lexeme
            if struct_name in self.structs:
                self.error(f'duplicate {struct_name} definition', struct.struct_name)
            self.structs[struct_name] = struct
        # check and record function defs
        for fun in program.fun_defs:
            fun_name = fun.fun_name.lexeme
            if fun_name in self.functions:
                self.error(f'duplicate {fun_name} definition', fun.fun_name)
            if fun_name in BUILT_INS:
                self.error(f'redefining built-in function', fun.fun_name)
            if fun_name == 'main' and fun.return_type.type_name.lexeme != 'void':
                self.error('main without void type', fun.return_type.type_name)
            if fun_name == 'main' and fun.params:
                self.error('main function with parameters', fun.fun_name)
            self.functions[fun_name] = fun
        # check main function
        if 'main' not in self.functions:
            self.error('missing main function', None)
        # check each struct
        for struct in self.structs.values():
            struct.accept(self)
        # check each function
        for fun in self.functions.values():
            fun.accept(self)

    def visit_struct_def(self, struct_def):
        self.symbol_table.push_environment()
        for field in struct_def.fields:
            if (self.symbol_table.exists_in_curr_env(field.var_name.lexeme)):
                self.error("Duplicate parameter names in function definition", field.var_name)
            else:
                if (field.data_type.type_name.lexeme not in self.structs.keys() and
                        field.data_type.type_name.lexeme not in BASE_TYPES):
                    self.error("Param type not defined", field.data_type.type_name)
                self.symbol_table.add(field.var_name.lexeme, field.data_type)
        self.symbol_table.pop_environment()

        return

    def visit_fun_def(self, fun_def):
        self.symbol_table.push_environment()
        for param in fun_def.params:
            if (self.symbol_table.exists_in_curr_env(param.var_name.lexeme)):
                self.error("Duplicate parameter names in function definition", param.var_name)
            else:
                if (param.data_type.type_name.lexeme not in self.structs.keys() and
                        param.data_type.type_name.lexeme not in BASE_TYPES):
                    self.error("Param type not defined", param.data_type.type_name)
                self.symbol_table.add(param.var_name.lexeme, param.data_type)
        if (self.symbol_table.exists_in_curr_env(fun_def.return_type.type_name.lexeme)):
            self.error("return binding already exists for environment", fun_def.return_type.type_name)
        else:
            if (not self.symbol_table.exists(fun_def.return_type.type_name.lexeme) and
                    fun_def.return_type.type_name.lexeme not in BASE_TYPES
                    and fun_def.return_type.type_name.lexeme != 'void'):
                self.error('return type does not exist', fun_def.return_type.type_name)
            self.symbol_table.add('return', fun_def.return_type.type_name.lexeme)
        for stmt in fun_def.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()

        return

    def visit_return_stmt(self, return_stmt):
        return_binding = self.symbol_table.get('return')
        if (not return_binding):
            self.error("no return binding found", return_stmt)
        else:
            return_stmt.expr.accept(self)
            if (self.curr_type.type_name.lexeme != return_binding and self.curr_type.type_name.lexeme != 'void'):
                self.error("return type does not match binding", self.curr_type.type_name)

    def visit_var_decl(self, var_decl):
        if (self.symbol_table.exists_in_curr_env(var_decl.var_def.var_name.lexeme)):
            self.error("Shadowed variable within current environment", var_decl.var_def.var_name)
        self.symbol_table.add(var_decl.var_def.var_name.lexeme, var_decl.var_def.data_type)
        var_binding = var_decl.var_def.data_type
        if (var_decl.expr):
            var_decl.expr.accept(self)
        else:
            return
        if (self.curr_type.is_array and not var_decl.var_def.data_type.is_array):
            self.error('Expression cannot have array on right side but not left', self.curr_type.type_name)
        if (self.curr_type.type_name.lexeme != var_binding.type_name.lexeme):
            if (not self.curr_type.type_name.lexeme == 'void'):
                self.error("Mismatched binding in variable declaration.", var_decl.var_def.data_type.type_name)
        if (var_decl.var_def.data_type.is_array and not self.curr_type.is_array):
            if (self.curr_type.type_name.lexeme != 'void'):
                self.error("Mismatched array types.", self.curr_type.type_name)
        return

    def visit_assign_stmt(self, assign_stmt):
        lvalue_type = None
        depth = 0
        for lvalue in assign_stmt.lvalue:
            if (not self.symbol_table.exists_in_curr_env(lvalue.var_name.lexeme)):
                lvalue_type = self.symbol_table.get(assign_stmt.lvalue[depth - 1].var_name.lexeme)
                if (lvalue_type is not None and lvalue_type.type_name.lexeme in self.structs):
                    if (lvalue_type.is_array and lvalue.array_expr is None):
                        self.error("Array type must have an array expression", lvalue.var_name.lexeme)
                    struct = self.structs[lvalue_type.type_name.lexeme]
                    for field in struct.fields:
                        if (field.var_name.lexeme == lvalue.var_name.lexeme):
                            self.curr_type = field.data_type
                            return
                    self.error('Undefined variable type', lvalue.var_name)
                else:
                    self.error('Undefined variable type', lvalue.var_name)
            depth = depth + 1
            self.curr_type = self.symbol_table.get(lvalue.var_name.lexeme)
        lvalue_final_type = self.curr_type
        assign_stmt.expr.accept(self)
        if (self.curr_type.type_name.lexeme != lvalue_final_type.type_name.lexeme):
            if (not self.curr_type.type_name.lexeme == 'void'):
                self.error("Mismatched types on assignment", lvalue_final_type.type_name)
        return

    def visit_while_stmt(self, while_stmt):
        while_stmt.condition.accept(self)
        if (self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array):
            self.error("If statement condition must be a bool", self.curr_type.type_name)
        self.symbol_table.push_environment()
        for stmt in while_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        return

    def visit_for_stmt(self, for_stmt):
        self.symbol_table.push_environment()
        for_stmt.var_decl.accept(self)
        for_stmt.condition.accept(self)
        if (self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array):
            self.error("If statement condition must be a bool", self.curr_type.type_name)
        for_stmt.assign_stmt.accept(self)
        for stmt in for_stmt.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        return

    def visit_if_stmt(self, if_stmt):
        if_stmt.if_part.condition.accept(self)
        if (self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array):
            self.error("If statement condition must be a bool", self.curr_type.type_name)
        self.symbol_table.push_environment()
        for stmt in if_stmt.if_part.stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        for else_if in if_stmt.else_ifs:
            else_if.condition.accept(self)
            if (self.curr_type.type_name.lexeme != 'bool' or self.curr_type.is_array):
                self.error("If statement condition must be a bool", self.curr_type.type_name)
            self.symbol_table.push_environment()
            for stmt in else_if.stmts:
                stmt.accept(self)
            self.symbol_table.pop_environment()
        self.symbol_table.push_environment()
        for stmt in if_stmt.else_stmts:
            stmt.accept(self)
        self.symbol_table.pop_environment()
        return

    def visit_call_expr(self, call_expr):
        if (call_expr.fun_name.lexeme not in self.functions.keys()):
            if (call_expr.fun_name.lexeme not in BUILT_INS):
                self.error("Function not defined", call_expr.fun_name)
        i = 0
        if (call_expr.fun_name.lexeme in BUILT_INS):
            args = call_expr.args
            match call_expr.fun_name.lexeme:
                case 'itos':
                    self.check_built_ins(args, 'int', call_expr.fun_name)
                    curr_token = Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'itod':
                    self.check_built_ins(args, 'int', call_expr.fun_name)
                    curr_token = Token(TokenType.DOUBLE_TYPE, 'double', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'dtos':
                    self.check_built_ins(args, 'double', call_expr.fun_name)
                    curr_token = Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'dtoi':
                    self.check_built_ins(args, 'double', call_expr.fun_name)
                    curr_token = Token(TokenType.INT_TYPE, 'int', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'stoi':
                    self.check_built_ins(args, 'string', call_expr.fun_name)
                    curr_token = Token(TokenType.INT_TYPE, 'int', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'stod':
                    self.check_built_ins(args, 'string', call_expr.fun_name)
                    curr_token = Token(TokenType.DOUBLE_TYPE, 'double', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'get':
                    if (len(args) != 2):
                        self.error('Invalid number of args for built-in function', call_expr.fun_name)
                    args[0].accept(self)
                    arg1 = self.curr_type
                    args[1].accept(self)
                    arg2 = self.curr_type
                    if (arg1.type_name.lexeme != 'int' or arg2.type_name.lexeme != 'string' or arg2.is_array):
                        self.error('Invalid arguments for built-in function', call_expr.fun_name)
                    curr_token = Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'length':
                    if (len(args) != 1):
                        self.error('Invalid number of args for built-in function', call_expr.fun_name)
                    args[0].accept(self)
                    if (self.curr_type.type_name.lexeme != 'string' and not self.curr_type.is_array):
                        self.error('invalid argument for built-in function', call_expr.fun_name)
                    curr_token = Token(TokenType.INT_TYPE, 'int', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'print':
                    if (len(call_expr.args) > 1):
                        self.error('Only one argument allowed for print functions', call_expr.fun_name)
                    for arg in call_expr.args:
                        arg.accept(self)
                        arg_type = self.curr_type.type_name.token_type
                        if (arg_type == TokenType.ID or self.curr_type.is_array):
                            self.error('Invalid print object', self.curr_type.type_name)
                    curr_token = Token(TokenType.VOID_TYPE, 'void', call_expr.fun_name.line,
                                       call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                case 'input':
                    curr_token = Token(TokenType.STRING_TYPE, 'string', call_expr.fun_name.line, call_expr.fun_name.column)
                    self.curr_type = DataType(False, curr_token)
                    return
            return
        fun = self.functions[call_expr.fun_name.lexeme]
        for arg in call_expr.args:
            arg.accept(self)
            if (i > len(fun.params) - 1):
                self.error("Too many args for function definition", call_expr.fun_name)
            if (fun.params[i].data_type.type_name.lexeme != self.curr_type.type_name.lexeme):
                if (self.curr_type.type_name.lexeme != 'void'):
                    self.error("Parameter type mismatch", self.curr_type.type_name)
            i = i + 1
        if (i != len(fun.params)):
            self.error("Number of args does not match number of parameters", call_expr.fun_name)
        self.curr_type = fun.return_type
        return

    def visit_expr(self, expr):
        expr.first.accept(self)

        lhs_type = self.curr_type

        if (expr.op):
            expr.rest.accept(self)
            rhs_type = self.curr_type

            if (rhs_type.type_name.lexeme != lhs_type.type_name.lexeme):
                if (not rhs_type.type_name.lexeme == 'void'):
                    self.error('left and ride side of expression do not match', rhs_type.type_name)
            if (expr.op.lexeme in COMPARE_OPS):
                if (
                        expr.op.lexeme != '==' and expr.op.lexeme != '!=' and expr.op.lexeme != 'or' and expr.op.lexeme != 'and'):
                    if (lhs_type.type_name.lexeme == 'bool'):
                        self.error('Cannot compare string/bool to each other', rhs_type.type_name)
                self.curr_type = DataType(False, Token(TokenType.BOOL_VAL, 'bool', self.curr_type.type_name.line,
                                                       self.curr_type.type_name.column))

    def visit_data_type(self, data_type):
        # note: allowing void (bad cases of void caught by parser)
        name = data_type.type_name.lexeme
        if name == 'void' or name in BASE_TYPES or name in self.structs:
            self.curr_type = data_type
        else:
            self.error(f'invalid type "{name}"', data_type.type_name)

    def visit_var_def(self, var_def):
        var_def.data_type.accept()
        return

    def visit_simple_term(self, simple_term):
        simple_term.rvalue.accept(self)
        return

    def visit_complex_term(self, complex_term):
        complex_term.expr.accept(self)
        return

    def visit_simple_rvalue(self, simple_rvalue):
        value = simple_rvalue.value
        line = simple_rvalue.value.line
        column = simple_rvalue.value.column
        type_token = None
        if value.token_type == TokenType.INT_VAL:
            type_token = Token(TokenType.INT_TYPE, 'int', line, column)
        elif value.token_type == TokenType.DOUBLE_VAL:
            type_token = Token(TokenType.DOUBLE_TYPE, 'double', line, column)
        elif value.token_type == TokenType.STRING_VAL:
            type_token = Token(TokenType.STRING_TYPE, 'string', line, column)
        elif value.token_type == TokenType.BOOL_VAL:
            type_token = Token(TokenType.BOOL_TYPE, 'bool', line, column)
        elif value.token_type == TokenType.NULL_VAL:
            type_token = Token(TokenType.VOID_TYPE, 'void', line, column)
        self.curr_type = DataType(False, type_token)

    def visit_new_rvalue(self, new_rvalue):
        if (new_rvalue.array_expr):
            new_rvalue.array_expr.accept(self)
        self.curr_type = DataType(new_rvalue.array_expr, new_rvalue.type_name)
        if (new_rvalue.type_name.lexeme in self.structs and not self.curr_type.is_array):
            i = 0
            struct = self.structs[new_rvalue.type_name.lexeme]
            if (new_rvalue.struct_params is None and len(struct.fields) == 0):
                return
            if (len(struct.fields) != len(new_rvalue.struct_params)):
                self.error("Number of args does not match number of parameters", new_rvalue.type_name)
            for field in new_rvalue.struct_params:
                field.accept(self)
                if (i > len(struct.fields) - 1):
                    self.error("Too many args for function definition", new_rvalue.type_name)
                if (struct.fields[i].data_type.type_name.lexeme != self.curr_type.type_name.lexeme):
                    if (self.curr_type.type_name.lexeme != 'void'):
                        self.error("Parameter type mismatch", self.curr_type.type_name)
                i = i + 1
        self.curr_type = DataType(new_rvalue.array_expr, new_rvalue.type_name)
        return

    def visit_var_rvalue(self, var_rvalue):
        depth = 0
        for var_ref in var_rvalue.path:
            if (not self.symbol_table.exists_in_curr_env(var_ref.var_name.lexeme)):
                parent = self.symbol_table.get(var_rvalue.path[depth - 1].var_name.lexeme)
                if (parent is not None and parent.type_name.lexeme in self.structs):
                    struct = self.structs[parent.type_name.lexeme]
                    for field in struct.fields:
                        if (field.var_name.lexeme == var_ref.var_name.lexeme):
                            self.curr_type = field.data_type
                            return
                    self.error("Undefined variable referenced in expression", var_ref.var_name)
                else:
                    self.error("Undefined variable referenced in expression", var_ref.var_name)
            depth = depth + 1
            self.curr_type = self.symbol_table.get(var_ref.var_name.lexeme)
        return


    def check_built_ins(self, args, type1, function):
        if (len(args) != 1):
            self.error("Invalid number of args for built-in function", function)
        args[0].accept(self)
        arg1 = self.curr_type
        if (arg1.type_name.lexeme != type1):
            self.error('invalid argument for built-in function', function)
