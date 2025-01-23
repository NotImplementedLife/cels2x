from lexer import LexicalToken
from grammar import NonTerminal, Terminal, Epsilon, Grammar, RuleComponent, RuleComponentFactory, rule_callbacks as rc
from lr1 import LR1Parser

from cels_scope import Scope, Symbol, ScopeStack, ScopeNameProvider, ScopeResolveStrategy
from cels_symbols import DataType, PrimitiveType, Variable, FormalParameter, Function, FunctionOverload, BinaryOperator, OperatorSolver, TaskType
from cels_symbols import StructType, Field
from cels2tokens import CelsTokenTypes
from cels_ast_nodes import ASTNodes, ASTBlock, ASTException
from cels_env import CelsEnvironment
from utils import ensure_type

from cels2tokens import CelsLexer

class Cels2AST:
    def __init__(self, cels_env:CelsEnvironment|None = None, lr1_path=None,
        lexer:CelsLexer|None=None):
        self.env = cels_env or CelsEnvironment.create_default()
            
        self.scope_stack = ScopeStack(self.env.global_scope)        
                
        grammar = self.__create_grammar()
        self.named_scope_stack = []        
        
        print("H=",grammar.checksum())
        
        self.parser = LR1Parser(grammar, lr1_path)
        if lr1_path is None:
            self.parser.analysis_table.save("cels_lr1_at.txt")
        
        def default_import_solver(path):
            raise NotImplementedError("Imports are not implemented")
        
        self.import_solver:callable[[str], ASTNode] = default_import_solver
        self.lexer = lexer or CelsLexer()
        
    def parse_tokens(self, tokens, verbose=False, debug=True):
        print(tokens)
        parse_result = self.parser.parse_tokens(tokens, lambda tk: self.rcf.terminal(tk.token_type), verbose=verbose)                
        if debug:
            print(self.env.global_scope.to_str_recursive())
            if 'error' in parse_result:
                print("\n", parse_result['message'], "\n")
                raise parse_result['error']            
        if not parse_result['success']:
            raise RuntimeError(parse_result['message'])
        ast = parse_result['value']
        ast = self.post_process(ast)
        return ast
        #return self.post_process(ast)
        
    def build_ast(self, code:str):        
        tokens = self.lexer.parse(code)['tokens']
        return self.parse_tokens(tokens)
    
    def __create_grammar(self):
        self.rcf = rcf = RuleComponentFactory(on_match=lambda val, token: val == token.token_type)
        
        # TERMINALS
        
        literal_bool   = rcf.terminal(CelsTokenTypes.LITERAL_BOOL.name)
        literal_dec    = rcf.terminal(CelsTokenTypes.LITERAL_DEC.name)
        literal_int    = rcf.terminal(CelsTokenTypes.LITERAL_INT.name)
        literal_str    = rcf.terminal(CelsTokenTypes.LITERAL_STR.name)
        
        kw_begin       = rcf.terminal(CelsTokenTypes.KW_BEGIN.name)
        kw_bool        = rcf.terminal(CelsTokenTypes.KW_BOOL.name)
        kw_break       = rcf.terminal(CelsTokenTypes.KW_BREAK.name)
        kw_const       = rcf.terminal(CelsTokenTypes.KW_CONST.name)
        kw_continue    = rcf.terminal(CelsTokenTypes.KW_CONTINUE.name)
        kw_cpp_include = rcf.terminal(CelsTokenTypes.KW_CPP_INCLUDE.name)
        kw_do          = rcf.terminal(CelsTokenTypes.KW_DO.name)
        kw_end         = rcf.terminal(CelsTokenTypes.KW_END.name)
        kw_else        = rcf.terminal(CelsTokenTypes.KW_ELSE.name)
        kw_extern      = rcf.terminal(CelsTokenTypes.KW_EXTERN.name)        
        kw_fi          = rcf.terminal(CelsTokenTypes.KW_FI.name)        
        kw_function    = rcf.terminal(CelsTokenTypes.KW_FUNCTION.name)
        kw_if          = rcf.terminal(CelsTokenTypes.KW_IF.name)
        kw_import      = rcf.terminal(CelsTokenTypes.KW_IMPORT.name)
        kw_int         = rcf.terminal(CelsTokenTypes.KW_INT.name)
        kw_lambda      = rcf.terminal(CelsTokenTypes.KW_LAMBDA.name)
        kw_multiframe  = rcf.terminal(CelsTokenTypes.KW_MULTIFRAME.name)
        kw_not         = rcf.terminal(CelsTokenTypes.KW_NOT.name)
        kw_package     = rcf.terminal(CelsTokenTypes.KW_PACKAGE.name)
        kw_return      = rcf.terminal(CelsTokenTypes.KW_RETURN.name)
        kw_scope       = rcf.terminal(CelsTokenTypes.KW_SCOPE.name)
        kw_short       = rcf.terminal(CelsTokenTypes.KW_SHORT.name)
        kw_string      = rcf.terminal(CelsTokenTypes.KW_STRING.name)
        kw_struct      = rcf.terminal(CelsTokenTypes.KW_STRUCT.name)
        kw_suspend     = rcf.terminal(CelsTokenTypes.KW_SUSPEND.name)
        kw_taskstart   = rcf.terminal(CelsTokenTypes.KW_TASKSTART.name)
        kw_taskready   = rcf.terminal(CelsTokenTypes.KW_TASKREADY.name)
        kw_taskresult   = rcf.terminal(CelsTokenTypes.KW_TASKRESULT.name)        
        kw_then        = rcf.terminal(CelsTokenTypes.KW_THEN.name)        
        kw_uint        = rcf.terminal(CelsTokenTypes.KW_UINT.name)        
        kw_ushort        = rcf.terminal(CelsTokenTypes.KW_USHORT.name)        
        kw_var         = rcf.terminal(CelsTokenTypes.KW_VAR.name)
        kw_void        = rcf.terminal(CelsTokenTypes.KW_VOID.name)
        kw_while       = rcf.terminal(CelsTokenTypes.KW_WHILE.name)
           

        s_ampersand    = rcf.terminal(CelsTokenTypes.S_AMPERSAND.name)        
        s_colon        = rcf.terminal(CelsTokenTypes.S_COLON.name)
        s_comma        = rcf.terminal(CelsTokenTypes.S_COMMA.name)
        s_dot          = rcf.terminal(CelsTokenTypes.S_DOT.name)
        s_doublecolon  = rcf.terminal(CelsTokenTypes.S_DOUBLECOLON.name)
        s_gt           = rcf.terminal(CelsTokenTypes.S_GT.name)
        s_gte          = rcf.terminal(CelsTokenTypes.S_GTE.name)
        s_eqeq         = rcf.terminal(CelsTokenTypes.S_EQEQ.name)
        s_equal        = rcf.terminal(CelsTokenTypes.S_EQUAL.name)
        s_lbrack       = rcf.terminal(CelsTokenTypes.S_LBRACK.name)
        s_lparen       = rcf.terminal(CelsTokenTypes.S_LPAREN.name)
        s_lrarrow       = rcf.terminal(CelsTokenTypes.S_LRARROW.name)
        s_rrarrow       = rcf.terminal(CelsTokenTypes.S_RRARROW.name)
        s_lt           = rcf.terminal(CelsTokenTypes.S_LT.name)
        s_lte          = rcf.terminal(CelsTokenTypes.S_LTE.name)
        s_minus        = rcf.terminal(CelsTokenTypes.S_MINUS.name)
        s_neq          = rcf.terminal(CelsTokenTypes.S_NEQ.name)
        s_percent      = rcf.terminal(CelsTokenTypes.S_PERCENT.name)
        s_plus         = rcf.terminal(CelsTokenTypes.S_PLUS.name)
        s_rbrack       = rcf.terminal(CelsTokenTypes.S_RBRACK.name)
        s_rparen       = rcf.terminal(CelsTokenTypes.S_RPAREN.name)
        s_semicolon    = rcf.terminal(CelsTokenTypes.S_SEMICOLON.name)
        s_slash        = rcf.terminal(CelsTokenTypes.S_SLASH.name)
        s_star         = rcf.terminal(CelsTokenTypes.S_STAR.name)
        
        t_id           = rcf.terminal(CelsTokenTypes.ID.name)
        eps            = rcf.epsilon()
        
        # NON_TERMINALS
        
        P              = rcf.non_terminal("P")
        E              = rcf.non_terminal("E")
                
        E_EQ           = rcf.non_terminal("E_EQ")
        E_REL           = rcf.non_terminal("E_REL")
        E_A           = rcf.non_terminal("E_A")
        E_M           = rcf.non_terminal("E_M")
        E_P           = rcf.non_terminal("E_P")
        E_F           = rcf.non_terminal("E_F")
        E_CALL        = rcf.non_terminal("E_CALL")
        E_RTL         = rcf.non_terminal("E_RTL")
        E_TERM        = rcf.non_terminal("E_TERM")
        E_LIST        = rcf.non_terminal("E_LIST")
        SYMBOL_TERM   = rcf.non_terminal("SYMBOL_TERM")
        
        
        STMT_BLOCK    = rcf.non_terminal("STMT_BLOCK")
        STMTS         = rcf.non_terminal("STMTS")
        STMT          = rcf.non_terminal("STMT")
                
        ANON_SCOPED_BLOCK  = rcf.non_terminal("ANON_SCOPED_BLOCK")
        ANON_SCOPED_BLOCK_ENCAPSULED = rcf.non_terminal("ANON_SCOPED_BLOCK_ENCAPSULED")
        
        DATA_TYPE = rcf.non_terminal("DATA_TYPE")
        
        STRUCT_BLOCK = rcf.non_terminal("STRUCT_BLOCK")                
        STRUCT_MEMBERS = rcf.non_terminal("STRUCT_MEMBERS")
        STRUCT_MEMBER = rcf.non_terminal("STRUCT_MEMBER")
        STRUCT_METHOD_HEADER = rcf.non_terminal("STRUCT_METHOD_HEADER")
        
        LITERAL       = rcf.non_terminal("LITERAL")
        
        LAMBDA_DECL   = rcf.non_terminal("LAMBDA_DECL")
        LAMBDA_HEADER   = rcf.non_terminal("LAMBDA_HEADER")
        
        SYMBOL        = rcf.non_terminal("SYMBOL")
        SYM_CHAIN     = rcf.non_terminal("SYM_CHAIN")
        
        FUNC_HEADER   = rcf.non_terminal("FUNC_HEADER")
        FUNC_DECL   = rcf.non_terminal("FUNC_DECL")
        FUNC_SPEC    = rcf.non_terminal("FUNC_SPEC")
        FUNC_SPECS    = rcf.non_terminal("FUNC_SPECS")
        
        FPARAMS      = rcf.non_terminal("FPARAMS")
        FPARAM      = rcf.non_terminal("FPARAM")
        
        SCOPE_PUSH       = rcf.non_terminal("SCOPE_PUSH")
        NAMED_SCOPE_PUSH = rcf.non_terminal("NAMED_SCOPE_PUSH")
        SCOPE_POP        = rcf.non_terminal("SCOPE_POP")
        ID_DEFINES_SCOPE = rcf.non_terminal("ID_DEFINES_SCOPE")
        ID_DEFINES_SCOPED_STRUCT = rcf.non_terminal("ID_DEFINES_SCOPED_STRUCT")
        
        
        def dbg_call(*pms):
            ex = rc.call(*pms)
            def f(*args): 
                print("DBG INIT")
                print(args)
                res = ex(*args)
                print("DBG:", res)
                return res
            return f            
        
        def binary_operator_rules(E_CRT, E_H, ops, reduce, precedence='left'):
            rules = []
            for op in ops:
                if precedence=='left':
                    rules.append((E_CRT << E_CRT * op * E_H).on_build(rc.call(reduce, rc.arg(0), rc.arg(1), rc.arg(2))))
                elif precedence=='right':
                    rules.append((E_CRT << E_H * op * E_CRT).on_build(rc.call(reduce, rc.arg(0), rc.arg(1), rc.arg(2))))
                else:
                    raise RuntimeError(f"Invalid argument for precedence: `{precedence}`")
                rules.append((E_CRT << E_H).on_build(rc.arg(0)))
            return rules
        
        G = Grammar([
            ( P << STMT_BLOCK                       ).on_build(rc.arg(0)),
            
            ( STMT_BLOCK << STMTS                   ).on_build(rc.call(self.reduce_block, rc.arg(0))),            
            ( STMTS << STMT * s_semicolon * STMTS  ).on_build(rc.call(self.reduce_list, rc.arg(0), rc.arg(2))),            
            ( STMTS << eps  ).on_build(rc.call(self.empty_list)),
            
            
            ( ANON_SCOPED_BLOCK_ENCAPSULED << SCOPE_PUSH * kw_begin * STMT_BLOCK * kw_end * SCOPE_POP ).on_build(rc.arg(2)),            
            
            ( ANON_SCOPED_BLOCK << ANON_SCOPED_BLOCK_ENCAPSULED ).on_build(rc.arg(0)),
            ( ANON_SCOPED_BLOCK << SCOPE_PUSH * STMT * SCOPE_POP ).on_build(rc.call(ASTBlock, rc.arg(1))),
            
            # Var decl
            ( STMT << kw_var * t_id * s_colon * DATA_TYPE).on_build(rc.call(self.reduce_vdecl, rc.arg(1), rc.arg(3))),
            ( STMT << kw_var * t_id * s_colon * DATA_TYPE * s_equal * E).on_build(rc.call(self.reduce_vdecl_with_expr, rc.arg(1), rc.arg(3), rc.arg(5))),
            ( STMT << kw_var * t_id * s_equal * E).on_build(rc.call(self.reduce_vdecl_with_expr, rc.arg(1), None, rc.arg(3))),
            
            # Package decl
            ( STMT << kw_package * ID_DEFINES_SCOPE * NAMED_SCOPE_PUSH * kw_begin * STMT_BLOCK * kw_end * SCOPE_POP)
                .on_build(rc.call(self.reduce_package, rc.arg(1), rc.arg(4), rc.arg(6))),            
                
            ( STMT << kw_import * literal_str).on_build(rc.call(self.reduce_import, rc.arg(1))),
                
            # Function decl
            ( STMT << FUNC_HEADER * kw_begin * STMT_BLOCK * kw_end * SCOPE_POP).on_build(rc.call(self.reduce_func_decl, rc.arg(0), rc.arg(2))),
            ( STMT << FUNC_HEADER * SCOPE_POP).on_build(rc.call(self.reduce_func_decl, rc.arg(0))),
            
            ( STMT << kw_return * E ).on_build(rc.call(self.reduce_return, rc.arg(1))),
            ( STMT << kw_return ).on_build(rc.call(self.reduce_return)),
            # Assign
            ( STMT << E_RTL * s_equal * E ).on_build(rc.call(self.reduce_assign, rc.arg(0), rc.arg(2))),
            
            # Struct decl
            
            ( STMT << kw_struct * ID_DEFINES_SCOPED_STRUCT * STRUCT_BLOCK * SCOPE_POP).on_build(rc.call(self.reduce_struct_decl, rc.arg(1), rc.arg(2))),
            
            ( STRUCT_BLOCK << eps).on_build(rc.call(self.empty_list)),
            ( STRUCT_BLOCK << kw_begin * STRUCT_MEMBERS * kw_end).on_build(rc.arg(1)),
            
            ( STRUCT_MEMBERS << STRUCT_MEMBER * s_semicolon * STRUCT_MEMBERS).on_build(rc.call(self.reduce_list, rc.arg(0), rc.arg(2))),
            ( STRUCT_MEMBERS << eps).on_build(rc.call(self.empty_list)),
            
            ( STRUCT_MEMBER << STRUCT_METHOD_HEADER * kw_begin * STMT_BLOCK * kw_end * SCOPE_POP).on_build(rc.call(self.reduce_func_decl, rc.arg(0), rc.arg(2))),
            ( STRUCT_MEMBER << STRUCT_METHOD_HEADER * SCOPE_POP).on_build(rc.call(self.reduce_func_decl, rc.arg(0))),
            
            ( STRUCT_MEMBER << kw_var * t_id * s_colon * DATA_TYPE).on_build(rc.call(self.reduce_field_decl, rc.arg(1), rc.arg(3))),
            
            ( STRUCT_METHOD_HEADER << FUNC_SPECS * kw_function * t_id * s_lparen * FPARAMS * s_rparen * s_colon * DATA_TYPE)
                .on_build(rc.call(self.reduce_struct_method_header, rc.arg(2), rc.arg(4), rc.arg(7), rc.arg(0))),
            
            
            ( FUNC_HEADER << FUNC_SPECS * kw_function * t_id * s_lparen * FPARAMS * s_rparen * s_colon * DATA_TYPE)
                .on_build(rc.call(self.reduce_func_header, rc.arg(2), rc.arg(4), rc.arg(7), rc.arg(0))),
            
            ( FUNC_SPECS << FUNC_SPEC * FUNC_SPECS).on_build(rc.call(self.reduce_list, rc.arg(0), rc.arg(1))),
            ( FUNC_SPECS << eps).on_build(rc.call(self.empty_list)),            
            ( FUNC_SPEC << kw_cpp_include * s_lparen * literal_str * s_rparen).on_build(rc.call(self.reduce_cpp_include, rc.arg(2))),
            ( FUNC_SPEC << kw_multiframe).on_build(rc.call(self.reduce_simple_func_spec, rc.arg(0))),
            ( FUNC_SPEC << kw_extern).on_build(rc.call(self.reduce_simple_func_spec, rc.arg(0))),
            
            ( FPARAMS << FPARAM * s_comma * FPARAMS ).on_build(rc.call(self.reduce_list, rc.arg(0), rc.arg(2))),
            ( FPARAMS << FPARAM).on_build(rc.call(self.reduce_list, rc.arg(0), None)),
            ( FPARAMS << eps ).on_build(rc.call(self.empty_list)),
            
            ( FPARAM << t_id * s_colon * DATA_TYPE ).on_build(rc.call(self.reduce_formal_parameter_data, rc.arg(0), rc.arg(2))),
            
            # While
            ( STMT << kw_while * E * kw_do * ANON_SCOPED_BLOCK).on_build(rc.call(ASTNodes.While, rc.arg(1), rc.arg(3))),
            
            ( STMT << kw_suspend ).on_build(rc.call(ASTNodes.Suspend)),
            
            # If
            ( STMT << kw_if * E * kw_then * ANON_SCOPED_BLOCK * s_semicolon * kw_else * ANON_SCOPED_BLOCK * s_semicolon * kw_fi).on_build(rc.call(ASTNodes.If, rc.arg(1), rc.arg(3), rc.arg(6))),
            ( STMT << kw_if * E * kw_then * ANON_SCOPED_BLOCK * s_semicolon * kw_fi).on_build(rc.call(ASTNodes.If, rc.arg(1), rc.arg(3), None)),
            
            ( STMT << E).on_build(rc.arg(0)),
            
            (E << E_EQ).on_build(rc.arg(0)),
            
            *binary_operator_rules(E_EQ, E_REL, [s_eqeq, s_neq], self.reduce_binary_operator),
            *binary_operator_rules(E_REL, E_A, [s_lt, s_lte, s_gt, s_gte], self.reduce_binary_operator),
            *binary_operator_rules(E_A, E_M, [s_plus, s_minus], self.reduce_binary_operator),
            *binary_operator_rules(E_M, E_RTL, [s_star, s_slash, s_percent], self.reduce_binary_operator),
            
            ( E_RTL << s_ampersand * E_RTL).on_build(rc.call(self.reduce_addressof, rc.arg(1))),
            ( E_RTL << s_star * E_RTL     ).on_build(rc.call(self.reduce_dereference, rc.arg(1))),            
            ( E_RTL << E_CALL).on_build(rc.arg(0)),
            
            ( E_CALL << E_CALL * s_lparen * E_LIST * s_rparen    ).on_build(rc.call(self.reduce_call, rc.arg(0), rc.arg(2))),
            ( E_CALL << E_CALL * s_lbrack * E * s_rbrack ).on_build(rc.call(self.reduce_index_access, rc.arg(0), rc.arg(2))),
            ( E_CALL << E_CALL * s_lrarrow * t_id ).on_build(rc.call(self.reduce_pointer_member_access, rc.arg(0), rc.arg(2))),
            ( E_CALL << E_CALL * s_dot * t_id ).on_build(rc.call(self.reduce_member_access, rc.arg(0), rc.arg(2))),
            
            ( E_CALL << E_TERM).on_build(rc.arg(0)),
            
            ( E_TERM << SYMBOL_TERM                     ).on_build(rc.arg(0)),
            ( E_TERM << LITERAL                         ).on_build(rc.arg(0)),
            ( E_TERM << s_lparen * E * s_rparen         ).on_build(rc.arg(1)),                        
            ( E_TERM << kw_taskstart * LAMBDA_DECL    ).on_build(rc.call(self.reduce_taskstart, rc.arg(1))),
            ( E_TERM << LAMBDA_DECL    ).on_build(rc.arg(0)),
            ( E_TERM << kw_taskready * s_lparen * E *  s_rparen).on_build(rc.call(self.reduce_taskready, rc.arg(2))),
            ( E_TERM << kw_taskresult * s_lparen * E *  s_rparen).on_build(rc.arg(2)),
            
            ( E_LIST << E * s_comma * E_LIST).on_build(rc.call(self.reduce_list, rc.arg(0), rc.arg(2))),
            ( E_LIST << E).on_build(rc.call(self.reduce_list, rc.arg(0), None)),            
            ( E_LIST << eps).on_build(rc.call(self.empty_list)),
            
            ( LAMBDA_DECL << LAMBDA_HEADER * s_colon * DATA_TYPE * s_rrarrow * ANON_SCOPED_BLOCK_ENCAPSULED * SCOPE_POP)
                .on_build(rc.call(self.reduce_lambda, rc.arg(0), rc.arg(4), rc.arg(2))),
            ( LAMBDA_DECL << LAMBDA_HEADER * s_rrarrow * ANON_SCOPED_BLOCK_ENCAPSULED * SCOPE_POP)
                .on_build(rc.call(self.reduce_lambda, rc.arg(0), rc.arg(2))), 
                
            ( LAMBDA_DECL << LAMBDA_HEADER * s_rrarrow * s_lparen * E * s_rparen * SCOPE_POP)
                .on_build(rc.call(self.reduce_lambda, rc.arg(0), rc.arg(3))),
            
            ( LAMBDA_HEADER << kw_lambda * s_lparen * SCOPE_PUSH * FPARAMS * s_rparen)
                .on_build(rc.call(self.reduce_lambda_header, rc.arg(2), rc.arg(3))),
            
            ( SYMBOL_TERM << SYMBOL                     ).on_build(rc.call(self.reduce_symbol_term, rc.arg(0))),
            
            ( SYMBOL << SYM_CHAIN         ).on_build(rc.call(self.reduce_symbol, rc.arg(0))),
            ( SYM_CHAIN << t_id * s_doublecolon * SYM_CHAIN).on_build(rc.call(self.reduce_list, rc.arg(0), rc.arg(2))),
            ( SYM_CHAIN << t_id).on_build(rc.call(self.reduce_list, rc.arg(0), None)),
            
            
            ( LITERAL << literal_int               ).on_build(rc.call(self.reduce_int_literal, rc.arg(0))),
            ( LITERAL << literal_dec               ).on_build(rc.call(self.reduce_dec_literal, rc.arg(0))),
            ( LITERAL << literal_str               ).on_build(rc.call(self.reduce_string_literal, rc.arg(0))),
            ( LITERAL << literal_bool              ).on_build(rc.call(self.reduce_bool_literal, rc.arg(0))),
            
            ( DATA_TYPE << kw_int                  ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            #( DATA_TYPE << kw_float                ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << kw_bool                 ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << kw_short                ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << kw_string               ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << kw_uint                 ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << kw_ushort               ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << kw_void                 ).on_build(rc.call(self.reduce_data_type_from_token, rc.arg(0))),
            ( DATA_TYPE << SYMBOL                  ).on_build(rc.call(self.reduce_data_type_from_symbol, rc.arg(0))),
            ( DATA_TYPE << DATA_TYPE * s_star      ).on_build(rc.call(self.reduce_data_type_pointer, rc.arg(0))),
            ( DATA_TYPE << DATA_TYPE * s_lbrack * literal_int * s_rbrack).on_build(rc.call(self.reduce_data_type_array, rc.arg(0), rc.arg(2))),
            
            
            ( NAMED_SCOPE_PUSH << eps                ).on_build(rc.call(self.reduce_named_scope_push)),
            ( SCOPE_PUSH << eps                      ).on_build(rc.call(self.reduce_push_scope)),
            ( SCOPE_POP << eps                       ).on_build(rc.call(self.reduce_pop_scope)),            
            ( ID_DEFINES_SCOPE << t_id               ).on_build(rc.call(self.reduce_id_defines_scope, rc.arg(0))),
            ( ID_DEFINES_SCOPED_STRUCT << t_id       ).on_build(rc.call(self.reduce_id_defines_scoped_struct, rc.arg(0))),
        ])
        return G
        
    def empty_list(self): return []
        
    def current_scope(self): return self.scope_stack.peek()
    
    def current_struct_context(self)->tuple[Scope, StructType]:
        scope = self.current_scope()
        struct_type = ensure_type(scope.associated_symbol, StructType)        
        return scope, struct_type
    
    def reduce_lambda_header(self, scope:Scope, params:list[tuple[str, DataType]])->tuple[Scope, list[FormalParameter]]:
        params = [self.env.add_symbol(scope, lambda scope: FormalParameter(pname, scope, pdata_type)) for pname, pdata_type in params]
        return scope, params
        
    def reduce_taskstart(self, task)->ASTNodes.TaskStart:
        if isinstance(task, ASTNodes.FunctionClosure):
            overload = task.function_overload
            return ASTNodes.TaskStart(task, TaskType(overload.return_type))
        return NotImplementedError()
    
    def reduce_taskready(self, task)->ASTNodes.TaskReady:
        return ASTNodes.TaskReady(task, self.env.dtype_bool)
    
    def reduce_lambda(self, header: tuple[Scope, list[FormalParameter]], implementation:ASTNodes.Block|ASTNodes.ExpressionNode, return_type:DataType|None=None)->ASTNodes.FunctionClosure:
        ensure_type(implementation, ASTNodes.Block, ASTNodes.ExpressionNode)
        ensure_type(return_type, DataType, None)
    
        scope, params = header
        print("?????????????????????????????????????")
        print(params)
        print(implementation)
        print(self.current_scope(), scope)
        print("?????????????????????????????????????")
        
        if return_type is None:
            if isinstance(implementation, ASTNodes.ExpressionNode):
                return_type = implementation.data_type
            else:
                return_type = self.env.dtype_void
        
        captured_nodes = []
        lambda_arg_nodes = []
        specs_dict = {}
        
        def find_captures(node):
            if isinstance(node, ASTNodes.SymbolTerm):
                symbol = node.symbol
                if symbol.is_in_scope(scope): 
                    if not(isinstance(symbol, FormalParameter) and symbol.scope==scope):
                        return False
                    lambda_arg_nodes.append(node)
                    pass
                else:
                    # ignore global symbols (that not have @ in name): 
                    if not '@' in symbol.get_full_name(): return False
                    captured_nodes.append(node)      
            if isinstance(node, ASTNodes.FunOverloadCall):
                if node.function_overload.is_multiframe:
                    specs_dict['is_multiframe']=True
            return False
        implementation.parse(find_captures)
                
        captured_symbols:dict[Symbol, tuple[str, DataType]] = {}
        for node in captured_nodes:
            if not node.symbol in captured_symbols:
                captured_symbols[node.symbol] = (node.symbol.name, node.data_type.make_pointer())
        
        lambda_sym, lambda_scope = self.env.generate_lambda_function()
        
        captures = []
        lambda_params = []
        for symbol in captured_symbols.keys():
            captures.append(symbol)
            name, data_type = captured_symbols[symbol]
            param = self.env.add_symbol(lambda_scope, FormalParameter.scoped_creator(name, data_type))
            lambda_params.append(param)
            captured_symbols[symbol] = param
        
        l_arg_symbols = {}
        for param in params:
            name, data_type = param.name, param.data_type
            lparam = self.env.add_symbol(lambda_scope, FormalParameter.scoped_creator(name, data_type))
            l_arg_symbols[param] = lparam
            lambda_params.append(lparam)
        
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        print(lambda_params)
            
        overload = lambda_sym.add_overload(FunctionOverload(lambda_sym, lambda_params, return_type, **specs_dict))
        captured_args = [self.reduce_addressof(self.reduce_symbol_term(symbol)) for symbol in captures]
        
        print(overload)
        print(overload.params)
        print(overload.func_symbol.declaring_type)
        
        for cnode in captured_nodes:
            sym = captured_symbols[node.symbol]
            cnode.replace_with(self.reduce_dereference(self.reduce_symbol_term(sym)))
        
        for anode in lambda_arg_nodes:
            lambda_sym = l_arg_symbols[anode.symbol]
            anode.replace_with(self.reduce_symbol_term(lambda_sym))

        if isinstance(implementation, ASTNodes.ExpressionNode):
            implementation = self.reduce_block([self.reduce_return(implementation)])
        
        overload.implementation = implementation
        
        print("!!! IMPLEMENTATION")
        print(overload.implementation)
        print("!!! IMPLEMENTATION")
        
        return ASTNodes.FunctionClosure(overload, self.env.dtype_closure_function, captured_args)

        
    def reduce_vdecl_with_expr(self, var_token:LexicalToken, data_type:DataType, expr: ASTNodes.ExpressionNode):        
        ensure_type(expr, ASTNodes.ExpressionNode)
        data_type = ensure_type(data_type, DataType, None) or expr.data_type
        vdecl = self.reduce_vdecl(var_token, data_type)
        assign = self.reduce_assign(self.reduce_symbol_term(vdecl.variable), expr)
        return self.reduce_block([vdecl, assign])
    
    def reduce_block(self, nodes:list):
        block = ASTNodes.Block(*nodes)
        block.properties['scope'] = self.current_scope()
        return block
        
    def reduce_return(self, value:ASTNodes.ExpressionNode|None=None):
        return ASTNodes.Return(value)
        
    def reduce_call(self, callable_item:ASTNodes.ExpressionNode, args:list[ASTNodes.ExpressionNode])->ASTNodes.ExpressionNode:
        if callable_item.data_type==self.env.dtype_function:
            if not isinstance(callable_item, ASTNodes.SymbolTerm):
                raise ASTException("Expression of type function must be a symbol")
            function = callable_item.symbol
            arg_types = list(map(lambda a:a.data_type, args))
            overload = self.match_function_calling_args(function, arg_types)
            
            for i in range(len(args)):
                if overload.params[i].data_type!=arg_types[i]:
                    conv = self.env.op_solver.resolve_converter(arg_types[i], overload.params[i].data_type)
                    args[i] = ASTNodes.TypeConvert(args[i], conv)
            
            return ASTNodes.FunOverloadCall(overload, args)
    
        if callable_item.data_type==self.env.dtype_closure_function:
            if not isinstance(callable_item, ASTNodes.FunctionClosure):
                raise ASTException("Expression of type closure must be explicit: (lambda (params)=>(...))(args)")
            overload = callable_item.function_overload
            c_args = callable_item.captured_args + args
            arg_types = list(map(lambda a:a.data_type, c_args))
            for i in range(len(c_args)):
                if overload.params[i].data_type!=arg_types[i]:
                    conv = self.env.op_solver.resolve_converter(arg_types[i], overload.params[i].data_type)
                    c_args[i] = ASTNodes.TypeConvert(c_args[i], conv)
            # include lambda implementation so that it will be reachable in AST parse
            return ASTNodes.FunOverloadCall(overload, c_args, include_impl_node=True)
        
        if callable_item.data_type==self.env.dtype_instance_method:
            if not isinstance(callable_item, ASTNodes.MethodAccessor):
                raise ASTException(f"Expected method accessor, got {type(callable_item)}")
            args = [self.reduce_addressof(callable_item.element)] + args
            arg_types = list(map(lambda a:a.data_type, args))
            overload = self.match_function_calling_args(callable_item.method, arg_types)
            return ASTNodes.FunOverloadCall(overload, args)
        
        raise ASTException(f"Object of type {callable_item.data_type} is not callable.")        
        
    def match_function_calling_args(self, func:Function, arg_types:list[DataType])->FunctionOverload:
        ov_candidates:list[tuple[FunctionOverload, int]] = []
        for overload in func.overloads:
            no_convs = self.is_overload_compatible_with_args(overload, arg_types)
            if no_convs>=0:
                ov_candidates.append((overload, no_convs))
        ov_candidates.sort(key=lambda t:t[1])        
        if len(ov_candidates)>1:
            str_types = ', '.join(map(str, arg_types))
            str_ovs = '; '.join([str(ov) for ov,_ in ov_candidates])
            raise ASTException(f"Ambiguous call for {func} with types ({str_types}). Possible matches: {str_ovs}")
        
        if len(ov_candidates)==0:
            str_types = ', '.join(map(str, arg_types))
            raise ASTException(f"No match for calling {func} with argument types {str_types}")
        
        return ov_candidates[0][0]
    
    def is_overload_compatible_with_args(self, overload:FunctionOverload, arg_types:list[DataType])->int:
        # checks if an overload can be called with certain arg types
        # returns -1 if not possible
        # if possible, return number of casts required to match the formal param types
        params = overload.params        
        if len(params)!=len(arg_types): return -1
        
        no_convs = 0
        for i in range(len(params)):
            in_type = arg_types[i]
            out_type = params[i].data_type
            if in_type==out_type: continue
            if not self.env.op_solver.can_convert(in_type, out_type):
                return -1
            no_convs +=1
        return no_convs
        
    
    def reduce_field_decl(self, name_tk:LexicalToken, data_type:DataType) -> ASTNodes.FieldDecl:
        ensure_type(name_tk, LexicalToken)
        ensure_type(data_type, DataType)
        struct_scope, struct_type = self.current_struct_context()
        field = self.env.add_symbol(struct_scope, lambda scope: Field(name_tk.value, scope, data_type))
        struct_type.add_member(field)
        return ASTNodes.FieldDecl(field)
    
    def reduce_struct_decl(self, struct_type:StructType, members:list):
        return ASTNodes.StructDecl(ensure_type(struct_type, StructType), members)
    
    def reduce_formal_parameter_data(self, name_tk:LexicalToken, data_type:DataType)->tuple:
        return (name_tk.value, data_type)
    
    def reduce_func_decl(self, func_overload:FunctionOverload, impl:ASTBlock|None=None):
        if impl is not None:
            func_overload.implementation = impl
        return ASTNodes.FuncDecl(func_overload)
    
    def reduce_struct_method_header(self, name_tk:LexicalToken, params:list[tuple[str, DataType]], ret_type:DataType, specs=None)-> FunctionOverload:
        _, struct_type = self.current_struct_context()
        params = [("this", struct_type.make_pointer())] + params
        print(params)
        overload = self.reduce_func_header(name_tk, params, ret_type, specs, struct_type)
        
        struct_type.add_member(overload.func_symbol)
        
        return overload
    
    def reduce_func_header(self, name_tk:LexicalToken, params:list[tuple[str, DataType]], ret_type:DataType, specs=None, declaring_type=None)-> FunctionOverload:              
        ensure_type(name_tk, LexicalToken)
        ensure_type(params, list)
        ensure_type(ret_type, DataType)        
        
        name = name_tk.value
        func_sym = self.current_scope().try_resolve_immediate_symbol(name)
        
        specs_dict = {}
        if specs is not None:
            for spec in specs:
                if spec[0]=="multiframe": specs_dict["is_multiframe"]=True
                elif spec[0]=="extern": specs_dict["is_extern"]=True
                elif spec[0]=="cpp_include": specs_dict["cpp_include"]=spec[1]['header']
        
        if func_sym is None:
            func_sym = self.env.add_symbol(self.current_scope(), Function.scoped_creator(name, declaring_type))
        
        overload_scope = self.scope_stack.push(f"@{name}_ov{func_sym.get_overloads_count()+1}")
        overload_scope.associated_symbol = func_sym
        
        params = [self.env.add_symbol(overload_scope, lambda scope: FormalParameter(pname, scope, pdata_type)) for pname, pdata_type in params]
        
        func_overload = func_sym.add_overload(FunctionOverload(func_sym, params, ret_type, **specs_dict))

        
        return func_overload
        
    def reduce_index_access(self, expr:ASTNodes.ExpressionNode, key:ASTNodes.ExpressionNode):
        indexer = self.env.op_solver.resolve_indexer(expr.data_type, key.data_type)
        return ASTNodes.IndexAccess(expr, key, indexer)
        
    def reduce_pointer_member_access(self, elem:ASTNodes.ExpressionNode, field_tk:LexicalToken|str)->ASTNodes.ExpressionNode:
        deref = self.reduce_dereference(elem)
        return self.reduce_member_access(deref, field_tk)
        
    def reduce_member_access(self, elem:ASTNodes.ExpressionNode, field_tk:LexicalToken|str)->ASTNodes.ExpressionNode:
        if isinstance(field_tk, LexicalToken):
            field_tk = field_tk.value
        if elem.data_type.is_struct:
            struct_type = ensure_type(elem.data_type, StructType)
            
            member = struct_type.inner_scope.resolve_symbol(field_tk)
            
            if isinstance(member, Field):
                return ASTNodes.FieldAccessor(elem, member)
                
            if isinstance(member, Function):
                if member.declaring_type is None:
                    raise ASTException("Non-member function called on object")
                return ASTNodes.MethodAccessor(elem, member, self.env.dtype_instance_method)
                
            raise ASTException(f"Not implemented: member accessor of type {type(member)}")

        raise ASTException(f"Invalid accessor: {field_tk} for type {elem.data_type}")
        
    
    def reduce_cpp_include(self, lit_string:LexicalToken)->tuple:
        return ("cpp_include", {'header': eval(lit_string.value)})
        
    def reduce_simple_func_spec(self, spec:LexicalToken)->tuple:
        return (spec.value, )
    
    def reduce_symbol(self, sym_chain:list)->ASTNodes.SymbolTerm:
        path = [tk.value for tk in sym_chain]
        symbol = self.current_scope().resolve_symbol(path)
        return symbol        
    
    def reduce_symbol_term(self, symbol:Symbol)->ASTNodes.SymbolTerm:
        custom_data_type:DataType|None = None
        
        if isinstance(symbol, Function):
            custom_data_type = self.env.dtype_function
        
        if isinstance(symbol, Field):
            this = self.reduce_symbol_term(self.current_scope().try_resolve_immediate_symbol("this"))
            return self.reduce_pointer_member_access(this, symbol.name)
        
        return ASTNodes.SymbolTerm(symbol, custom_data_type)
    
    def reduce_assign(self, left:ASTNodes.ExpressionNode, right:ASTNodes.ExpressionNode)->ASTNodes.Assign:
        ensure_type(left, ASTNodes.ExpressionNode)
        ensure_type(right, ASTNodes.ExpressionNode)        
        if left.data_type != right.data_type:
            converter = self.env.op_solver.resolve_converter(right.data_type, left.data_type)
            right = ASTNodes.TypeConvert(right, converter)
        return ASTNodes.Assign(left, right)
    
    def reduce_binary_operator(self, arg1:ASTNodes.ExpressionNode, op_token:LexicalToken, arg2:ASTNodes.ExpressionNode)->ASTNodes.BinaryOperator:
        ensure_type(arg1, ASTNodes.ExpressionNode)
        ensure_type(arg2, ASTNodes.ExpressionNode)
        ensure_type(op_token, LexicalToken)
        operator = self.env.op_solver.resolve_binary_operator(op_token.value, arg1.data_type, arg2.data_type)
        return ASTNodes.BinaryOperator(operator, arg1, arg2)
        
    def reduce_import(self, path_tk: LexicalToken):
        path = self.reduce_string_literal(path_tk).value
        return self.import_solver(path) or self.reduce_block([])
    
    def reduce_package(self, name_token:LexicalToken, block:ASTNodes.Block, scope:Scope):
        scope.metadata['type']='package'
        return ASTNodes.Package(name_token.value, block, scope)
        
    def reduce_id_defines_scope(self, token):
        self.named_scope_stack.append(token.value)
        return token
        
    def reduce_id_defines_scoped_struct(self, token:LexicalToken):
        type_name = token.value
        type_symbol = self.env.add_symbol(self.current_scope(), lambda scope: StructType(type_name, scope))
        type_scope = self.scope_stack.push(type_name, strategy=ScopeResolveStrategy.CREATE)
        
        type_scope.associated_symbol = type_symbol
        type_symbol.inner_scope = type_scope
        return type_symbol
    
    def reduce_data_type_array(self, data_type:DataType, length:LexicalToken):
        return data_type.make_array(self.reduce_int_literal(length).value)
    
    def reduce_data_type_pointer(self, data_type:DataType)->DataType:
        return data_type.make_pointer()
    
    def reduce_data_type_from_symbol(self, symbol:Symbol)->DataType:
        if not isinstance(symbol, DataType):
            raise ASTException(f"Symbol is not a datatype: {symbol} {type(symbol).__name__ if symbol is not None else None}")
        return symbol
        
    def reduce_data_type_from_token(self, token:LexicalToken)->DataType:        
        symbol = self.current_scope().resolve_symbol(token.value)        
        if not isinstance(symbol, DataType):
            raise ASTException(f"Invalid symbol: expected data type, got {symbol} ({type(symbol).__name__})")
        return symbol
        
    def reduce_vdecl(self, var_token:LexicalToken, data_type:DataType):
        ensure_type(data_type, DataType)
        variable = self.env.add_symbol(self.current_scope(), lambda scope: Variable(var_token.value, scope, data_type))
        return ASTNodes.VDecl(variable)        
        
    def reduce_addressof(self, term:ASTNodes.ExpressionNode)->ASTNodes.AddressOf:
        return ASTNodes.AddressOf(term)
    
    def reduce_dereference(self, term:ASTNodes.ExpressionNode)->ASTNodes.Dereference:
        return ASTNodes.Dereference(term)
    
    def reduce_int_literal(self, token):
        return ASTNodes.Literal(int(token.value), self.env.dtype_int)
        
    def reduce_dec_literal(self, token):
        return ASTNodes.Literal(float(token.value), self.env.dtype_float)
        
    def reduce_string_literal(self, token):        
        return ASTNodes.Literal(eval(token.value), self.env.dtype_string)
    
    def reduce_bool_literal(self, token):
        return ASTNodes.Literal(token.value=="true", self.env.dtype_bool)

    def reduce_push_scope(self, scope_name=None, strategy:list[str]=ScopeResolveStrategy.CREATE):
        scope_name = scope_name or self.env.scope_name_provider.new_name()
        scope = self.scope_stack.push(scope_name, strategy=strategy)
        return scope
    
    def reduce_named_scope_push(self, strategy:list[str]=ScopeResolveStrategy.CREATE):
        scope_name = self.named_scope_stack.pop()
        self.scope_stack.push(scope_name, strategy=strategy)
        return None
        
    def reduce_pop_scope(self):
        scope = self.scope_stack.peek()
        self.scope_stack.pop()
        return scope
    
    def reduce_list(self, head:any, tail:None|list[any]):        
        if tail is None: return [head]
        return [head] + ensure_type(tail, list)
        
    def post_process(self, ast):
        ast = self.__ast_extract_multiframe_calls_in_block(ast)        
        return ast        
        
    def gen_internal_var_name(self):
        return f"cels_s{self.env.internal_sym_id_provider.create_id()}"
     
    def __ast_extract_multiframe_calls_in_block(self, ast):
        stack = [ast]
        
        mf_calls = []        
        def identify_multiframe_calls(node):
            print("IMC", type(node).__name__, str(node).replace("\n", " "))
            if isinstance(node, ASTNodes.FunOverloadCall) and node.function_overload.is_multiframe:
                mf_calls.append(node)
                return True
            return False
            
        def extract_mf_call(mf_call):
            # Converts Expr(mfcall(x)) to internal_var = mf_call(x); Expr(internal_var)
            # In case of nested multiframe calls, they are extracted recursively        
            
            block = mf_call
            instr = None
            parent_iterative = None            
            while block is not None and not isinstance(block, ASTNodes.Block):                                
                instr = block
                block = block.parent                
                if isinstance(block, ASTNodes.While) and instr is block.condition:
                    parent_iterative = block
                    
            if block is None:
                raise RuntimeError("Invalid AST: multiframe function call does not have a block among its parents")
            
            result = []
                      
            if instr is not mf_call:  
                block_scope = block.properties['scope']
                
                sym_name = self.gen_internal_var_name()
                symbol = self.env.add_symbol(block_scope, lambda scope: Variable(sym_name, block_scope, mf_call.function_overload.return_type))

                vdecl = ASTNodes.VDecl(symbol)

                sterm_l = ASTNodes.SymbolTerm(symbol)
                sterm_r = ASTNodes.SymbolTerm(symbol)            
                
                mf_call.replace_with(sterm_r)
                attr = self.reduce_assign(sterm_l, mf_call)
                    
                instr.insert_before_it(vdecl)
                instr.insert_before_it(attr)
                
                result.append(mf_call)
            else:
                result.append(mf_call)
                
            # while(MF) { BLOCK; } ==> var cond = MF; while(cond) { BLOCK; cond = MF; }
            if parent_iterative is not None:
                l_clone = sterm_l.clone()
                r_clone = mf_call.clone()
                assign = self.reduce_assign(l_clone, r_clone)
                parent_iterative.block.insert_at_end(assign)
                result.append(r_clone)
            
            return result
        
        while len(stack)>0:
            mf_calls.clear()
            node = stack[-1]
            stack.pop()
            node.parse(identify_multiframe_calls)            
            
            for mf_call in mf_calls:
                extracts = extract_mf_call(mf_call)
                for extract in extracts:
                    for child in extract.enumerate_children():
                        stack.append(child)            
        
        """
        def check_import_statements()-> list[str]:            
            imports = []
            for node in ast.enumerate_children_deep():                
                if not isinstance(node, ASTNodes.Import): continue                
                if not (isinstance(node.parent, ASTNodes.Block) and node.parent.parent is None):
                    raise ASTException("Import statement must be declared in global scope")                                
                imports.append(node.path)
            return imports
                
        imports = check_import_statements()
        print(imports)
        """
        
        
        return ast