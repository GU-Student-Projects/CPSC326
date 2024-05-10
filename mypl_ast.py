"""MyPL AST classes.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""

from dataclasses import dataclass
from mypl_token import Token
from typing import List

#----------------------------------------------------------------------
# Visitor class definition
#----------------------------------------------------------------------

class Visitor:
    """Visitor interface for navigating and processing AST."""

    def visit_program(self, program):
        pass

    def visit_struct_def(self, struct_def):
        pass

    def visit_fun_def(self, fun_def):
        pass

    def visit_return_stmt(self, return_stmt):
        pass

    def visit_var_decl(self, var_decl):
        pass

    def visit_assign_stmt(self, assign_stmt):
        pass

    def visit_while_stmt(self, while_stmt):
        pass

    def visit_for_stmt(self, for_stmt):
        pass

    def visit_if_stmt(self, if_stmt):
        pass
    
    def visit_call_expr(self, call_expr):
        pass
    
    def visit_expr(self, expr):
        pass
    
    def visit_data_type(self, data_type):
        pass

    def visit_var_def(self, var_def):
        pass

    def visit_simple_term(self, simple_term):
        pass

    def visit_complex_term(self, complex_term):
        pass

    def visit_simple_rvalue(self, simple_rvalue):
        pass
    
    def visit_new_rvalue(self, new_rvalue):
        pass

    def visit_var_rvalue(self, var_rvalue):
        pass
    

    
#----------------------------------------------------------------------
# AST Classes
#----------------------------------------------------------------------

# General Program-Related Basic AST Classes

@dataclass
class DataType:
    is_array: bool
    type_name: Token
    def accept(self, visitor):
        visitor.visit_data_type(self)

@dataclass
class VarDef:
    data_type: DataType
    var_name: Token
    def accept(self, visitor):
        visitor.visit_var_def(self)

@dataclass
class Stmt:
    pass

@dataclass
class StructDef:
    struct_name: Token
    fields: List[VarDef]
    def accept(self, visitor):
        visitor.visit_struct_def(self)

@dataclass
class FunDef:
    return_type: DataType
    fun_name: Token
    params: List[VarDef]
    stmts: List[Stmt]
    def accept(self, visitor):
        visitor.visit_fun_def(self)

@dataclass
class Program: 
    struct_defs: List[StructDef]
    fun_defs: List[FunDef]
    def accept(self, visitor):
        visitor.visit_program(self)


# Expression Related Classes

@dataclass
class RValue:
    pass                        

@dataclass
class ExprTerm:
    pass                        

@dataclass
class Expr:
    not_op: bool
    first: ExprTerm
    op: Token
    rest: 'Expr'
    def accept(self, visitor):
        visitor.visit_expr(self)

@dataclass
class CallExpr(Stmt, RValue):
    fun_name: Token
    args: List[Expr]
    def accept(self, visitor):
        visitor.visit_call_expr(self)
        
@dataclass
class SimpleTerm(ExprTerm):
    rvalue: RValue
    def accept(self, visitor):
        visitor.visit_simple_term(self)
        
@dataclass
class ComplexTerm(ExprTerm):
    expr: Expr
    def accept(self, visitor):
        visitor.visit_complex_term(self)

@dataclass
class SimpleRValue(RValue):
    value: Token
    def accept(self, visitor):
        visitor.visit_simple_rvalue(self)

@dataclass
class NewRValue(RValue):
    type_name: Token
    array_expr: Expr
    struct_params: List[Expr]
    def accept(self, visitor):
        visitor.visit_new_rvalue(self)
    
@dataclass
class VarRef:
    var_name: Token
    array_expr: Expr
        
@dataclass
class VarRValue(RValue):
    path: List[VarRef]
    def accept(self, visitor):
        visitor.visit_var_rvalue(self)

        
# Statement Related Classes

@dataclass
class ReturnStmt(Stmt):
    expr: Expr
    def accept(self, visitor):
        visitor.visit_return_stmt(self)

@dataclass
class VarDecl(Stmt):
    var_def: VarDef
    expr: Expr
    def accept(self, visitor):
        visitor.visit_var_decl(self)

@dataclass
class AssignStmt(Stmt):
    lvalue: List[VarRef]
    expr: Expr
    def accept(self, visitor):
        visitor.visit_assign_stmt(self)

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    stmts: List[Stmt]
    def accept(self, visitor):
        visitor.visit_while_stmt(self)
        
@dataclass
class ForStmt(Stmt):
    var_decl: VarDecl
    condition: Expr
    assign_stmt: AssignStmt
    stmts: List[Stmt]
    def accept(self, visitor):
        visitor.visit_for_stmt(self)

@dataclass
class BasicIf:
    condition: Expr
    stmts: List[Stmt]

@dataclass
class IfStmt(Stmt):
    if_part: BasicIf
    else_ifs: List[BasicIf]
    else_stmts: List[Stmt]
    def accept(self, visitor):
        visitor.visit_if_stmt(self)

