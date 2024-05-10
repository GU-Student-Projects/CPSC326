"""Print Visitor for pretty printing a MyPL program.

NAME: Jake VanZyverden
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_token import Token, TokenType
from mypl_ast import *


class PrintVisitor(Visitor):
    """Visitor implementation to pretty print MyPL program."""

    def __init__(self):
        self.indent = 0
        self.is_complex = False

    # Helper Functions

    def output(self, msg):
        """Prints message without ending newline.

        Args:
           msg -- The string to print.

        """
        print(msg, end='')

    def output_indent(self):
        """Prints an initial indent string."""
        self.output('  ' * self.indent)

    def output_semicolon(self, stmt):
        """Prints a semicolon if the type of statment should end in a
        semicolon.
        
        Args:
            stmt -- The statement to print a semicolon after.

        """
        if type(stmt) in [VarDecl, AssignStmt, ReturnStmt, CallExpr]:
            self.output(';')

    def print_var_ref(self, var_ref):
        if (self.is_complex):
            self.output(var_ref.var_name.lexeme)
            self.is_complex = False
        else:
            self.output(' ' + var_ref.var_name.lexeme)
        if (var_ref.array_expr is not None):
            var_ref.array_expr.accept(self)

    def print_basic_if(self, basic_if):
        self.output(' if (')
        self.is_complex = True
        basic_if.condition.accept(self)
        self.is_complex = False
        self.output(') {\n')
        self.indent += 1
        for stmt in basic_if.stmts:
            self.output_indent()
            stmt.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output_indent()
        self.output(' }')

    # Visitor Functions

    def visit_program(self, program):
        for struct in program.struct_defs:
            struct.accept(self)
            self.output('\n')
        for fun in program.fun_defs:
            fun.accept(self)
            self.output('\n')

    def visit_struct_def(self, struct_def):
        self.output('struct ' + struct_def.struct_name.lexeme + ' {\n')
        self.indent += 1
        for var_def in struct_def.fields:
            self.output_indent()
            var_def.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output('}\n')

    def visit_fun_def(self, fun_def):
        fun_def.return_type.accept(self)
        self.output(' ' + fun_def.fun_name.lexeme + '(')
        for i in range(len(fun_def.params)):
            fun_def.params[i].accept(self)
            if i < len(fun_def.params) - 1:
                self.output(', ')
        self.output(') {\n')
        self.indent += 1
        for stmt in fun_def.stmts:
            self.is_complex = False
            self.output_indent()
            stmt.accept(self)
            self.output_semicolon(stmt)
            self.output('\n')
        self.indent -= 1
        self.output('}\n')

    def visit_expr(self, expr):
        if (expr.not_op):
            if (self.is_complex):
                self.output('not (')
                self.is_complex = False
            else:
                self.output(' not (')
            expr.first.accept(self)
            self.output(')')
        else:
            expr.first.accept(self)
        if (expr.op is not None):
            self.output(' ' + expr.op.lexeme)
        if (expr.rest is not None):
            self.visit_expr(expr.rest)

    def visit_call_expr(self, call_expr):
        self.output(' ' + call_expr.fun_name.lexeme + '(')
        self.is_complex = True
        for arg in call_expr.args[:-1]:
            arg.accept(self)
            self.output(', ')
        call_expr.args[len(call_expr.args) - 1].accept(self)
        self.is_complex = False
        self.output(')')

    def visit_simple_term(self, simple_expr):
        simple_expr.rvalue.accept(self)

    def visit_complex_term(self, complex_term):
        self.is_complex = True
        self.output(' (')
        complex_term.expr.accept(self)
        self.output(')')
        self.is_complex = False

    def visit_simple_rvalue(self, simple_rvalue):
        if (simple_rvalue.value.token_type is TokenType.STRING_VAL):
            if (self.is_complex):
                self.output('\"' + simple_rvalue.value.lexeme + '\"')
            else:
                self.output(' \"' + simple_rvalue.value.lexeme + '\"')
        else:
            if (self.is_complex):
                self.output(simple_rvalue.value.lexeme)
                self.is_complex = False
            else:
                self.output(' ' + simple_rvalue.value.lexeme)

    def visit_new_rvalue(self, new_rvalue):
        if self.is_complex:
            self.output('new ')
            self.is_complex = False
        else:
            self.output(' new ')
        self.output(new_rvalue.type_name.lexeme)
        if (new_rvalue.array_expr is not None):
            new_rvalue.array_expr.accept(self)
        self.output('(')
        self.is_complex = True
        for param in new_rvalue.struct_params[:-1]:
            param.accept(self)
            self.output(', ')
        if (len(new_rvalue.struct_params) > 0):
            new_rvalue.struct_params[len(new_rvalue.struct_params) - 1].accept(self)
        self.output(')')

    def visit_var_rvalue(self, var_rvalue):
        first = True
        for path in var_rvalue.path[:-1]:
            if not first:
                self.is_complex = True
            else:
                first = False
            self.print_var_ref(path)
            self.output('.')
        if (len(var_rvalue.path) > 1):
            self.is_complex = True
        self.print_var_ref(var_rvalue.path[len(var_rvalue.path) - 1])

    def visit_return_stmt(self, return_stmt):
        self.output(' return')
        self.is_complex = False
        return_stmt.expr.accept(self)

    def visit_var_decl(self, var_decl):
        var_decl.var_def.accept(self)
        self.output(' =')
        var_decl.expr.accept(self)

    def visit_assign_stmt(self, assign_stmt):
        first = True
        for value in assign_stmt.lvalue[:-1]:
            if first is False:
                self.is_complex = True
            else:
                self.is_complex = False
                first = False
            self.print_var_ref(value)
            self.output('.')
        if len(assign_stmt.lvalue) > 0:
            if len(assign_stmt.lvalue) != 1:
                self.is_complex = True
            self.print_var_ref(assign_stmt.lvalue[len(assign_stmt.lvalue) - 1])
        self.output(' =')
        assign_stmt.expr.accept(self)

    def visit_while_stmt(self, while_stmt):
        self.output('while')
        while_stmt.condition.accept(self)
        self.output(' {\n')
        self.indent += 1
        for stmt in while_stmt.stmts:
            self.output_indent()
            stmt.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output_indent()
        self.output(' }')

    def visit_for_stmt(self, for_stmt):
        self.output('for(')
        self.is_complex = True
        for_stmt.var_decl.accept(self)
        self.output('; ')
        self.is_complex = True
        for_stmt.condition.accept(self)
        self.output('; ')
        self.is_complex = True
        for_stmt.assign_stmt.accept(self)
        self.output(') {\n')
        self.indent += 1
        for stmt in for_stmt.stmts:
            self.output_indent()
            stmt.accept(self)
            self.output(';\n')
        self.indent -= 1
        self.output_indent()
        self.output(' }')

    def visit_if_stmt(self, if_stmt):
        self.print_basic_if(if_stmt.if_part)
        for else_if in if_stmt.else_ifs:
            self.output(' else')
            self.print_basic_if(else_if)
        if (len(if_stmt.else_stmts) > 0):
            self.output(' else {\n')
            self.indent += 1
            for stmt in if_stmt.else_stmts:
                self.output_indent()
                stmt.accept(self)
                self.output(';\n')
            self.indent -= 1
            self.output_indent()
            self.output(' }')

    def visit_data_type(self, data_type):
        if (data_type.is_array):
            self.output('array ')
        if (self.is_complex):
            self.output(data_type.type_name.lexeme)
            self.is_complex = False
        else:
            self.output(' ' + data_type.type_name.lexeme)

    def visit_var_def(self, var_def):
        var_def.data_type.accept(self)
        if (self.is_complex):
            self.output(var_def.var_name.lexeme)
            self.is_complex = False
        else:
            self.output(' ' + var_def.var_name.lexeme)
