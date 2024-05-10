"""MyPL AST parser implementation.

NAME: Jake VanZyverden
DATE: Spring 2024
CLASS: CPSC 326
"""

from mypl_error import *
from mypl_token import *
from mypl_lexer import *
from mypl_ast import *


class ASTParser:

    def __init__(self, lexer):
        """Create a MyPL syntax checker (parser). 
        
        Args:
            lexer -- The lexer to use in the parser.

        """
        self.lexer = lexer
        self.curr_token = None
        self.struct_defs = {}
        self.var_bindings = {}

    def parse(self):
        """Start the parser, returning a Program AST node."""
        program_node = Program([], [])
        self.advance()
        while not self.match(TokenType.EOS):
            if self.match(TokenType.STRUCT):
                self.struct_def(program_node)
            else:
                self.fun_def(program_node)
        self.eat(TokenType.EOS, 'expecting EOF')
        return program_node

    # ----------------------------------------------------------------------
    # Helper functions
    # ----------------------------------------------------------------------

    def error(self, message):
        """Raises a formatted parser error.

        Args:
            message -- The basic message (expectation)

        """
        lexeme = self.curr_token.lexeme
        line = self.curr_token.line
        column = self.curr_token.column
        err_msg = f'{message} found "{lexeme}" at line {line}, column {column}'
        raise ParserError(err_msg)

    def advance(self):
        """Moves to the next token of the lexer."""
        self.curr_token = self.lexer.next_token()
        # skip comments
        while self.match(TokenType.COMMENT):
            self.curr_token = self.lexer.next_token()

    def match(self, token_type):
        """True if the current token type matches the given one.

        Args:
            token_type -- The token type to match on.

        """
        return self.curr_token.token_type == token_type

    def match_any(self, token_types):
        """True if current token type matches on of the given ones.

        Args:
            token_types -- Collection of token types to check against.

        """
        for token_type in token_types:
            if self.match(token_type):
                return True
        return False

    def eat(self, token_type, message):
        """Advances to next token if current tokey type matches given one,
        otherwise produces and error with the given message.

        Args: 
            token_type -- The totken type to match on.
            message -- Error message if types don't match.

        """
        if not self.match(token_type):
            self.error(message)
        self.advance()

    def is_bin_op(self):
        """Returns true if the current token is a binary operator."""
        ts = [TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE,
              TokenType.AND, TokenType.OR, TokenType.EQUAL, TokenType.LESS,
              TokenType.GREATER, TokenType.LESS_EQ, TokenType.GREATER_EQ,
              TokenType.NOT_EQUAL]
        return self.match_any(ts)

    def is_base_type(self):
        ts = [TokenType.INT_TYPE, TokenType.DOUBLE_TYPE, TokenType.BOOL_TYPE,
              TokenType.STRING_TYPE]
        return self.match_any(ts)

    def is_base_rvalue(self):
        ts = [TokenType.INT_VAL, TokenType.DOUBLE_VAL, TokenType.BOOL_VAL,
              TokenType.STRING_VAL]
        return self.match_any(ts)

    def is_stmt_type(self):
        ts = [TokenType.WHILE, TokenType.IF, TokenType.FOR,
              TokenType.RETURN, TokenType.ID, TokenType.ARRAY]
        return self.match_any(ts) or self.is_base_type()

    # ----------------------------------------------------------------------
    # Recursive descent functions
    # ----------------------------------------------------------------------

    def struct_def(self, program_node):
        """Check for well-formed struct definition."""
        self.eat(TokenType.STRUCT, "Expected STRUCT")
        name = self.curr_token
        self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        fields_node = []
        self.fields(fields_node)
        self.eat(TokenType.RBRACE, "Expected RBRACE")
        self.struct_defs[name.lexeme] = []
        program_node.struct_defs.append(StructDef(name, fields_node))

    def fields(self, fields_node):
        tmpType = None
        tmpName = None
        """Check for well-formed struct fields."""
        if (not self.is_base_type() and not self.match(TokenType.ID) and not self.match(TokenType.ARRAY)):
            return

        tmpType = self.data_type()
        tmpName = self.curr_token
        self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
        fields_node.append(VarDef(tmpType, tmpName))
        if (self.match(TokenType.RBRACE)):
            return
        one_iter = False
        while ((self.is_base_type() or self.match(TokenType.ID) or self.match(TokenType.ARRAY)) or not one_iter):
            if (not self.is_base_type() and not self.match(TokenType.ID) and not self.match(TokenType.ARRAY)):
                self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                break
            tmpType = self.data_type()
            tmpName = self.curr_token
            self.eat(TokenType.ID, "Expected ID")
            self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
            fields_node.append(VarDef(tmpType, tmpName))
            one_iter = True
        return

    def fun_def(self, program_node):
        """Check for well-formed function definition."""
        return_type = None
        func_name = None
        params = []
        stmts = []
        if (not self.match(TokenType.VOID_TYPE)):
            return_type = self.data_type()
        else:
            return_type = DataType(False, self.curr_token)
            self.eat(TokenType.VOID_TYPE, "Expected VOID_TYPE")
        func_name = self.curr_token
        self.eat(TokenType.ID, "Expected ID")
        self.eat(TokenType.LPAREN, "Expected LPAREN")
        self.params(params)
        self.eat(TokenType.RPAREN, "Expected RPAREN")
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.stmt_def(stmts)
        self.eat(TokenType.RBRACE, "Expected RBRACE")
        program_node.fun_defs.append(FunDef(return_type, func_name, params, stmts))

    def stmt_def(self, stmt_node):
        while (True):
            if (not self.is_stmt_type()):
                break
            match (self.curr_token.token_type):
                case TokenType.WHILE:
                    stmt_node.append(self.while_stmt())
                case TokenType.IF:
                    stmt_node.append(self.if_stmt())
                case TokenType.FOR:
                    stmt_node.append(self.for_stmt())
                case TokenType.RETURN:
                    stmt_node.append(self.return_stmt())
                    self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                case TokenType.ID:
                    data_type = DataType(False, self.curr_token)
                    tmp = self.curr_token
                    self.advance()
                    if (self.match(TokenType.LBRACKET)):
                        self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                        array_expr = self.expr()
                        self.eat(TokenType.RBRACKET, "Expected RBRACKET")
                        stmt_node.append(self.assign_stmt(True, VarRef(tmp, array_expr)))
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                    elif (self.match(TokenType.LPAREN)):
                        stmt_node.append(self.call_expr(True, tmp))
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                    else:
                        if (self.match(TokenType.DOT) or self.match(TokenType.ASSIGN)):
                            stmt_node.append(self.assign_stmt(True, VarRef(tmp, None)))
                        else:
                            stmt_node.append(self.vdecl_stmt(True, VarDef(data_type, None)))
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                case _:
                    if (self.is_stmt_type()):
                        stmt_node.append(self.vdecl_stmt(False, VarDef(None, None)))
                        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
                    else:
                        break

    def params(self, var_def_node):
        """Check for well-formed function formal parameters."""
        if (self.is_base_type() or self.match(TokenType.ID) or self.match(TokenType.ARRAY)):
            data_type = self.data_type()
            var_name = self.curr_token
            self.eat(TokenType.ID, "Expected ID")
            var_def_node.append(VarDef(data_type, var_name))
            while (True):
                if (not self.match(TokenType.COMMA)):
                    break
                self.eat(TokenType.COMMA, "Expected comma")
                data_type = self.data_type()
                var_name = self.curr_token
                self.eat(TokenType.ID, "Expected ID")
                var_def_node.append(VarDef(data_type, var_name))

    def data_type(self):
        """Check for well-formed function data types."""
        is_array = False
        type_name = None
        if (self.is_base_type()):
            type_name = self.curr_token
            self.advance()
        elif (self.match(TokenType.ID)):
            type_name = self.curr_token
            self.advance()
        else:
            is_array = True
            self.eat(TokenType.ARRAY, "Expected Data Type")
            if (self.is_base_type()):
                type_name = self.curr_token
                self.advance()
            elif (self.match(TokenType.ID)):
                type_name = self.curr_token
                self.advance()
            else:
                self.error("Expected ID or base type")
        return DataType(is_array, type_name)

    def expr(self):
        """Check for well-formed expression."""
        not_op = False
        first = None
        op = None
        rest = None
        match self.curr_token.token_type:
            case TokenType.NOT:
                not_op = True
                self.eat(TokenType.NOT, "Expected NOT")
                first = ComplexTerm(self.expr())
                op = first.expr.op
                rest = first.expr.rest
                first = first.expr.first
            case TokenType.LPAREN:
                self.eat(TokenType.LPAREN, "Expected LPAREN")
                if (self.match(TokenType.RPAREN)):
                    self.error("Expected expression")
                first = ComplexTerm(self.expr())
                if (isinstance(first.expr.first, SimpleTerm) and first.expr.rest is None):
                    first = first.expr.first
                self.eat(TokenType.RPAREN, "Expected RPAREN")
            case _:
                if (self.is_bin_op()):
                    self.error("Expected expression")
                first = SimpleTerm(self.rvalue())
        if (self.is_bin_op()):
            op = self.curr_token
            self.advance()
            if (self.match(TokenType.SEMICOLON)):
                self.error("Expected expression")
            rest = self.expr()
        return Expr(not_op, first, op, rest)

    def lvalue(self, skipID, var_ref_node):
        """Check for well-formed left side value."""
        if (not skipID):
            tmp_name = self.curr_token
            self.eat(TokenType.ID, "Expected ID")
        else:
            tmp_name = var_ref_node[0].var_name
        while (self.match_any([TokenType.LBRACKET, TokenType.DOT])):
            if (self.match(TokenType.LBRACKET)):
                self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                array_expr = self.expr()
                self.eat(TokenType.RBRACKET, "Expected RBRACKET")
                var_ref_node.append(VarRef(tmp_name, array_expr))
            elif (self.match(TokenType.DOT)):
                self.eat(TokenType.DOT, "Expected DOT")
                tmp_name = self.curr_token
                self.eat(TokenType.ID, "Expected ID")
                if (self.match(TokenType.LBRACKET)):
                    self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                    array_expr = self.expr()
                    self.eat(TokenType.RBRACKET, "Expected RBRACKET")
                    var_ref_node.append(VarRef(tmp_name, array_expr))
                else:
                    var_ref_node.append(VarRef(tmp_name, None))
        if (var_ref_node == []):
            var_ref_node.append(VarRef(tmp_name, None))

    def rvalue(self):
        if (self.is_base_rvalue()):
            simple_val = SimpleRValue(self.curr_token)
            self.advance()
            return simple_val
        elif (self.match(TokenType.NULL_VAL)):
            simple_val = SimpleRValue(self.curr_token)
            self.advance()
            return simple_val
        elif (self.match(TokenType.NEW)):
            return self.new_rvalue()
        elif (self.match(TokenType.ID)):
            tmp = self.curr_token
            self.advance()
            if (self.match(TokenType.LPAREN)):
                return self.call_expr(True, tmp)
            else:
                return self.var_rvalue(True, tmp)

    def new_rvalue(self):
        type_name = None
        array_expr = None
        struct_params = None
        self.eat(TokenType.NEW, "Expected NEW")
        if (self.match(TokenType.ID)):
            type_name = self.curr_token
            self.eat(TokenType.ID, "Expected ID")
            if (self.match(TokenType.LPAREN)):
                self.eat(TokenType.LPAREN, "Expected LPAREN")
                struct_params = []
                while (not self.match(TokenType.RPAREN)):
                    struct_params.append(self.expr())
                    if (not self.match(TokenType.RPAREN)):
                        self.eat(TokenType.COMMA, " Expected COMMA")
                self.eat(TokenType.RPAREN, "Expected RPAREN")
                return NewRValue(type_name, array_expr, struct_params)
        elif (self.is_base_type()):
            type_name = self.curr_token
            self.advance()
        else:
            self.error("Expected Base Type or ID")
        self.eat(TokenType.LBRACKET, "Expected LBRACKET")
        array_expr = self.expr()
        self.eat(TokenType.RBRACKET, "Expected RBRACKET")
        return NewRValue(type_name, array_expr, struct_params)

    def var_rvalue(self, skip_id, skipped_id):
        path = []
        if (not skip_id):
            var_name = self.curr_token
            self.eat(TokenType.ID, "Expected ID")
        else:
            var_name = skipped_id
        while (self.match_any([TokenType.LBRACKET, TokenType.DOT])):
            if (self.match(TokenType.LBRACKET)):
                self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                array_expr = self.expr()
                self.eat(TokenType.RBRACKET, "Expected RBRACKET")
                path.append(VarRef(var_name, array_expr))
            elif (self.match(TokenType.DOT)):
                if (path == []):
                    path.append(VarRef(var_name, None))
                self.eat(TokenType.DOT, "Expected DOT")
                var_name = self.curr_token
                self.eat(TokenType.ID, "Expected ID")
                if (self.match(TokenType.LBRACKET)):
                    self.eat(TokenType.LBRACKET, "Expected LBRACKET")
                    array_expr = self.expr()
                    self.eat(TokenType.RBRACKET, "Expected RBRACKET")
                    path.append(VarRef(var_name, array_expr))
                else:
                    path.append(VarRef(var_name, None))
        if (path == []):
            path.append(VarRef(var_name, None))
        return VarRValue(path)

    # ----------------------------------------------------------------------
    # Statement Functions
    # ----------------------------------------------------------------------
    def while_stmt(self):
        """Check for well-formed while statements."""
        self.eat(TokenType.WHILE, "Expected while")
        if (not self.match(TokenType.LPAREN)):
            self.error("Expected LPAREN")
        condition = self.expr()
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        stmt_node = []
        self.stmt_def(stmt_node)
        self.eat(TokenType.RBRACE, "Expected RBRACE")
        return WhileStmt(condition, stmt_node)

    def if_stmt(self):
        """Check for well-formed if statements."""
        self.eat(TokenType.IF, "Expected if")
        if (not self.match(TokenType.LPAREN)):
            self.error(" Expected LPAREN")
        basic_if = BasicIf(self.expr(), None)
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        stmt_node = []
        self.stmt_def(stmt_node)
        basic_if.stmts = stmt_node
        self.eat(TokenType.RBRACE, "Expected RBRACE")
        elif_node = []
        else_node = []
        self.if_stmt_t(elif_node, else_node)
        return IfStmt(basic_if,  elif_node, else_node)

    def if_stmt_t(self, elif_node, else_node):
        match (self.curr_token.token_type):
            case TokenType.ELSEIF:
                self.advance()
                if (not self.match(TokenType.LPAREN)):
                    self.error(" Expected LPAREN")
                tmp = BasicIf(self.expr(), None)
                tmp_stmts = []
                self.eat(TokenType.LBRACE, "Expected LBRACE")
                self.stmt_def(tmp_stmts)
                tmp.stmts = tmp_stmts
                self.eat(TokenType.RBRACE, "Expected RBRACE")
                elif_node.append(tmp)
                self.if_stmt_t(elif_node, else_node)
            case TokenType.ELSE:
                self.advance()
                self.eat(TokenType.LBRACE, "Expected LBRACE")
                self.stmt_def(else_node)
                self.eat(TokenType.RBRACE, "Expected RBRACE")
            case _:
                return

    def for_stmt(self):
        v_decl = None
        condition = None
        assign_stmt = None
        stmt_node = []
        self.eat(TokenType.FOR, " Expected FOR")
        self.eat(TokenType.LPAREN, " Expected LPAREN")
        v_decl = self.vdecl_stmt(False, VarDef(None, None))
        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
        condition = self.expr()
        self.eat(TokenType.SEMICOLON, "Expected SEMICOLON")
        assign_stmt = self.assign_stmt(False, None)
        self.eat(TokenType.RPAREN, " Expected RPAREN")
        self.eat(TokenType.LBRACE, "Expected LBRACE")
        self.stmt_def(stmt_node)
        self.eat(TokenType.RBRACE, "Expected RBRACE")
        return ForStmt(v_decl, condition, assign_stmt, stmt_node)

    def return_stmt(self):
        self.eat(TokenType.RETURN, " Expected RETURN")
        if (self.match(TokenType.SEMICOLON)):
            self.error("Expected Non-Empty Expression")
        expr = self.expr()
        return ReturnStmt(expr)

    def assign_stmt(self, skip_id, skip_ref):
        var_ref_node = []
        if (skip_id):
            var_ref_node.append(skip_ref)
        self.lvalue(skip_id, var_ref_node)
        self.eat(TokenType.ASSIGN, " Expected ASSIGN")
        if (self.match(TokenType.SEMICOLON)):
            self.error("Expected Non-Empty Expression")
        expr = self.expr()
        return AssignStmt(var_ref_node, expr)

    def call_expr(self, skip_id, skipped_id):
        args = []
        arg_types = []
        if (not skip_id):
            fun_name = self.curr_token
            self.eat(TokenType.ID, "Expected ID")
        else:
            fun_name = skipped_id
        self.eat(TokenType.LPAREN, " Expected LPAREN")
        while (not self.match(TokenType.RPAREN)):
            match self.curr_token.token_type:
                case TokenType.ID:
                    added = False
                    for _def in self.struct_defs:
                        for val in self.struct_defs[_def]:
                            if (val == self.curr_token.lexeme):
                                arg_types.append(_def)
                    if (not added):
                        if (self.var_bindings.__contains__(self.curr_token.lexeme)):
                            arg_types.append(self.var_bindings[self.curr_token.lexeme])
                case TokenType.INT_VAL:
                    arg_types.append("int")
                case TokenType.STRING_VAL:
                    arg_types.append("string")
                case TokenType.DOUBLE_VAL:
                    arg_types.append("double")
                case TokenType.BOOL_VAL:
                    arg_types.append("bool")
                case TokenType.NOT:
                    arg_types.append("bool")
                case _:
                    arg_types.append("expr")
            args.append(self.expr())
            if (not self.match(TokenType.RPAREN)):
                self.eat(TokenType.COMMA, " Expected COMMA")
        self.eat(TokenType.RPAREN, " Expected RPAREN")
        return CallExpr(fun_name, args, arg_types)

    def vdecl_stmt(self, skipID, var_def):
        expr = None
        if (not skipID):
            var_def.data_type = self.data_type()
            var_def.var_name = self.curr_token
            if (self.struct_defs.__contains__(var_def.data_type.type_name.lexeme)):
                self.struct_defs[var_def.data_type.type_name.lexeme].append(var_def.var_name.lexeme)
            else:
                self.var_bindings[var_def.var_name.lexeme] = var_def.data_type.type_name.lexeme
        else:
            var_def.var_name = self.curr_token
            if (self.struct_defs.__contains__(var_def.data_type.type_name.lexeme)):
                self.struct_defs[var_def.data_type.type_name.lexeme].append(var_def.var_name.lexeme)
            else:
                self.var_bindings[var_def.var_name.lexeme] = var_def.data_type.type_name.lexeme
        self.eat(TokenType.ID, "Expected ID")
        if (self.match(TokenType.ASSIGN)):
            self.eat(TokenType.ASSIGN, " Expected ASSIGN")
            if (self.match(TokenType.SEMICOLON)):
                self.error("Expected Non-Empty Expression")
            expr = self.expr()
        return VarDecl(var_def, expr)
