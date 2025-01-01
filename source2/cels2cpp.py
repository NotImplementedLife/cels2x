from __future__ import annotations
from ast_base import ASTNode, ASTBlock
from cels_ast_nodes import ASTNodes
from cels2ast import Cels2AST
from cels_env import CelsEnvironment
from cels_scope import Symbol
from cels_symbols import DataType, PrimitiveType, StructType, Field, FunctionOverload, Function, FormalParameter
from cels_multiframe import MultiFrameCFGNode, PseudoAST_PreMultiframeFunCall, PseudoAST_PostMultiframeFunCall, MultiframeCFG
from utils import ensure_type, indent

class CppSnippet:    
    def __init__(self, components:list[CppSnippet|str], headers:list[str]|None=None):
        self._headers = headers or []
        self._code = ""
        for comp in components:
            if isinstance(comp, str):
                self._code += comp
            elif isinstance(comp, CppSnippet):
                self._code += comp.code
                self._headers += comp.headers
            #elif isinstance(comp, CppIdentifier):
                #self._code += comp.full_name            
            else:
                raise RuntimeError(f"Invalid CppSnippet component: type {type(comp)}")
    @property
    def code(self): return self._code
    
    @property
    def headers(self): return self._headers
        
    def __add__(self, other:CppSnippet|str|list):        
        if not isinstance(other, list):
            other = [other]
        return CppSnippet([self, *other])    
    
    def __iadd__(self, other:CppSnippet|str|list):        
        if not isinstance(other, list):
            other = [other]
        other = CppSnippet(other)
        self._code += other.code
        self._headers += other.headers
        return self
    
    def indent(self):
        return CppSnippet([indent(self.code)], self.headers)
        

class CppIdentifier:
    def __init__(self, symbol:Symbol, name:str, full_name:str=None, headers:list[str]|None=None):
        self._symbol = symbol
        self._name_snippet = CppSnippet([name], headers)
        full_name = name if full_name is None else full_name
        self._full_name_snippet = CppSnippet([full_name], headers)
    
    @property
    def name(self)->CppSnippet: return self._name_snippet
    
    @property
    def full_name(self)->CppSnippet: return self._full_name_snippet

class CelsEnv2Cpp:
    def __init__(self, env:CelsEnvironment):    
        self._env = env
        
        self.symbol2id:dict[Symbol, CppIdentifier] = {}
        self.binop_translator:dict[BinaryOperator, callable] = {}
        
        pass
        
    def identify_symbol(self, symbol:Symbol, identifier:CppIdentifier):
        self.symbol2id[symbol] = identifier
    
    def resolve_identifier(self, symbol:Symbol)->CppIdentifier:
        print(symbol)
        return self.symbol2id[symbol]
        
    def resolve_data_type(self, data_type:DataType)->CppSnippet:
        if isinstance(data_type, DataType):
            if data_type.is_pointer:
                element_type:CppSnippet = self.resolve_data_type(data_type.element_type)
                return CppSnippet([element_type, "*"])
        return self.resolve_identifier(data_type).full_name
        
    @property
    def env(self): return self._env
        
    def compile_env(self)->CppSnippet:
        def symbol2cpp(symbol:Symbol, headers:list[str]|None=None)->CppIdentifier:                                    
            path = [symbol.name]
            scope = symbol.scope
            while scope is not None and not scope.name.startswith('@'):
                path.append(scope.name)
                scope = scope.parent
            full_name = '::'.join(path[::-1])
            return CppIdentifier(symbol, symbol.name, full_name, headers)
        
        self.identify_symbol(self.env.dtype_int, CppIdentifier(self.env.dtype_int, "int"))
        self.identify_symbol(self.env.dtype_void, CppIdentifier(self.env.dtype_void, "void"))
        
        dtype_int = self.env.dtype_int
        
        rbo = self.env.op_solver.resolve_binary_operator
        self.binop_translator[rbo('+', dtype_int, dtype_int)] = lambda l,r: ["(", l, "+", r, ")"]
        self.binop_translator[rbo('-', dtype_int, dtype_int)] = lambda l,r: ["(", l, "-", r, ")"]
        self.binop_translator[rbo('*', dtype_int, dtype_int)] = lambda l,r: ["(", l, "*", r, ")"]
        self.binop_translator[rbo('/', dtype_int, dtype_int)] = lambda l,r: ["(", l, "/", r, ")"]
        self.binop_translator[rbo('%', dtype_int, dtype_int)] = lambda l,r: ["(", l, "%", r, ")"]
        self.binop_translator[rbo('>', dtype_int, dtype_int)] = lambda l,r: ["(", l, ">", r, ")"]
        self.binop_translator[rbo('>=', dtype_int, dtype_int)] = lambda l,r: ["(", l, ">=", r, ")"]
        self.binop_translator[rbo('<=', dtype_int, dtype_int)] = lambda l,r: ["(", l, "<=", r, ")"]
        self.binop_translator[rbo('<', dtype_int, dtype_int)] = lambda l,r: ["(", l, "<", r, ")"]
        self.binop_translator[rbo('==', dtype_int, dtype_int)] = lambda l,r: ["(", l, "==", r, ")"]
        self.binop_translator[rbo('!=', dtype_int, dtype_int)] = lambda l,r: ["(", l, "!=", r, ")"]
        
        for symbol in self.env.enumerate_symbols():            
            if isinstance(symbol, PrimitiveType): continue
            
            if isinstance(symbol, StructType):
                self.identify_symbol(symbol, symbol2cpp(symbol))
            
            if isinstance(symbol, Field):
                self.identify_symbol(symbol, symbol2cpp(symbol))
                
            if isinstance(symbol, Function):
                self.identify_symbol(symbol, symbol2cpp(symbol))
            
            if isinstance(symbol, FormalParameter):
                self.identify_symbol(symbol, symbol2cpp(symbol))
            
            # TO DO: preregister symbol identifiers
            pass
        
        snippets_stack = [ CppSnippet([]) ]
        
        def is_package_scope(scope:Scope):
            return 'type' in scope.metadata and scope.metadata['type']=='package'
        
        def on_scope_enter(scope:Scope)->bool:     
            if scope==self.env.global_scope: return True
        
            if is_package_scope(scope):
                snippets_stack[-1] += f"namespace {scope.name}\n{{\n"
                snippets_stack.append(CppSnippet([]))
                return True
            
            if isinstance(scope.associated_symbol, StructType):
                return False
            
            if isinstance(scope.associated_symbol, Function):
                return False
            
            
            snippets_stack[-1] += CppSnippet(f"/* Not implemented scope {scope} ({scope.associated_symbol}) */\n")
            
            return True
        
        def on_scope_exit(scope:Scope):
            if is_package_scope(scope):
                inner = snippets_stack.pop()
                snippets_stack[-1] += inner.indent()
                snippets_stack[-1] += "\n}\n"            
        
        def on_symbol_encountered(symbol:Symbol):
            if isinstance(symbol, PrimitiveType): return
            
            if isinstance(symbol, Function):
                for overload in symbol.overloads:
                    snippets_stack[-1] += self.__compile_function_overload(overload)
                    snippets_stack[-1] += "\n"
                            
                return
            
            if isinstance(symbol, StructType):
                cpp_id = self.resolve_identifier(symbol)
                snippets_stack[-1] += ["struct ", cpp_id.name, "\n"]
                snippets_stack[-1] += "{\n"
                
                inner_snippet = CppSnippet([])
                
                for member in sorted(symbol.members, key=lambda m:m.metadata["sid"]):
                    if isinstance(member, Field):
                        t_id = self.resolve_data_type(member.data_type)
                        f_id = self.resolve_identifier(member)
                        inner_snippet += [t_id, " ", f_id.name, ";\n"]
                        continue
                    if isinstance(member, Function):
                        for overload in member.overloads:
                            inner_snippet += self.__compile_function_overload(overload)
                            inner_snippet += "\n"
                            
                        continue
                    
                    inner_snippet += f"/* Not implemented {member} ({type(member)})*/\n"
                    
                snippets_stack[-1] += inner_snippet.indent()
                snippets_stack[-1] += "\n};\n"
                return
        
            snippets_stack[-1] += CppSnippet(f"/* Not implemented {symbol} ({type(symbol)}) */\n")
            
            
        self.parse_scope_tree(on_scope_enter, on_scope_exit, on_symbol_encountered)
        
        return snippets_stack[0]
        
    def __build_multiframe_component(self, component, fname, vdecls)->CppSnippet:            
        
        def prio_build(ast_node)->CppSnippet|None:
            nonlocal vdecls
            if isinstance(ast_node, ASTNodes.VDecl):
                def verbatim_local_symbol_id(param):
                    return CppIdentifier(param, param.name, f"ctx->{param.name}")
                var = ast_node.variable                
                sid = verbatim_local_symbol_id(var)                
                self.identify_symbol(var, sid)
                # print("PRIO_BUILD VAR_DECL ", var, sid)
                vdecls += [self.resolve_identifier(var.data_type).full_name, " ", sid.name, ";\n"]                
                return CppSnippet([""])
            if isinstance(ast_node, ASTNodes.Suspend):
                return CppSnippet(["ctrl->suspend();\n"])
            if isinstance(ast_node, ASTNodes.Return):
                if ast_node.value is None:
                    return CppSnippet(["ctrl->ret(); return;\n"])
                else:
                    return CppSnippet(["ctx->return_value = ", self.__compile_ast_node(ast_node.value, prio_build), ";\n", "ctrl->ret(); return;\n"]) 
            if isinstance(ast_node, PseudoAST_PreMultiframeFunCall):
                func = ast_node.funcall.function_overload
                func_name = self.resolve_identifier(func.func_symbol).full_name
                snippet = CppSnippet([])
                snippet += ["{\n", "\tauto* f = ctrl->push<", func_name, ">();\n"]
                for param, arg in zip(func.params, ast_node.funcall.args):
                    snippet += [f"\tf->params.{param.name} = ", self.__compile_ast_node(arg, prio_build), ";\n"]
                snippet += [f"\tctrl->call(f, ", func_name, f"::f0, ctx, ", fname, f"::f{ast_node.jump_f});\n", "\treturn;\n", "}\n"]
                return snippet
            if isinstance(ast_node, PseudoAST_PostMultiframeFunCall):
                func = ast_node.funcall.function_overload
                func_name = self.resolve_identifier(func.func_symbol).full_name
                snippet = CppSnippet([])
                if ast_node.result_lhs is not None:
                    snippet += [ "{\n", f"\tauto* f = ctrl->peek<",func_name,">();\n", "\t", self.__compile_ast_node(ast_node.result_lhs, prio_build), " = f->return_value;\n", "}\n" ]
                snippet += ["ctrl->pop();\n"]
                return snippet
            return None
        
        snippet = CppSnippet([])
        snippet += [f"inline static void f{component['id']}(void* _ctx, Celesta::ExecutionController* ctrl)\n"]
        snippet += "{\n"
        inner_snippet = CppSnippet([])
        inner_snippet += [f"auto* ctx = (", fname, "*)_ctx;\n"]
        inner_snippet += [f"goto L_{component['head'].node_id};\n"]
        
        for node in MultiframeCFG.enumerate_nodes(component['head']):
            inner_snippet += [f"L_{node.node_id}:\n"]
            
            if node.node_type=='c':
                cond = self.__compile_ast_node(node.ast, prio_build)
                inner_snippet += ["if(",cond,")\n", f"    goto L_{node.next_nodes[1].node_id}; else goto L_{node.next_nodes[0].node_id};\n"]                
            elif node.node_type=='i':
                if node.ast is not None:      
                    inner_snippet += [self.__compile_ast_node(node.ast, prio_build), "\n"]                    
                if len(node.next_nodes)>0:
                    inner_snippet += [f"goto L_{node.next_nodes[0].node_id};\n"]
                else:
                    inner_snippet += "return;\n"                    
            elif node.node_type=='f':
                inner_snippet += [f"ctrl->jump(ctx, ", fname, f"::f{node.data['id']}); return;\n"]               
            elif node.node_type=='e':
                inner_snippet += f"ctrl->ret(); return;\n"                
            else:
                inner_snippet += f"/* Node #{node.node_id} {node.node_type} */"                
                
        
        snippet += [inner_snippet.indent(), "\n"]
        snippet += "}\n\n"
        #wcards += ["{\n", CppSnippet(wcontent).indent(), "}\n\n"]
        
        #print(MultiframeCFG.tree2string(component['head']))
    
        return snippet
        
    def __compile_function_overload(self, overload:FunctionOverload)->CppSnippet:
        snippet = CppSnippet([])
        
        if overload.is_multiframe:
            if overload.is_extern:
                return CppSnippet([f"/* Not Implemented: Extern multiframe functions: {overload} */"])
            
            fun_id = self.resolve_identifier(overload.func_symbol)
            ret_type_id = self.resolve_data_type(overload.return_type)
            
            snippet += ["struct ", fun_id.name, "\n{\n"]
            inner_snippet = CppSnippet([])
            
            
            if len(overload.params)>0:
                def verbatim_local_symbol_id(param):
                    return CppIdentifier(param, param.name, f"ctx->params.{param.name}")
            
                inner_snippet += "struct\n{\n"
                
                for param in overload.params:
                    sid = verbatim_local_symbol_id(param)
                    self.identify_symbol(param, sid)
                    #vdecls.append(f"    {self.symbol_repo.resolve_symbol(param.data_type).full_name} {param.name};\n")
                    
                    d = self.resolve_data_type(param.data_type)
                    p = self.resolve_identifier(param)
                    inner_snippet += [CppSnippet([d, " ", p.name, ";"]).indent(), "\n"]
                inner_snippet+= ["} params;\n"]
                #vdecls.append("} params;\n")
            
            if overload.return_type != self.env.dtype_void:
                inner_snippet+= [ret_type_id, " ", "return_value;\n"]
            
            cfg = MultiframeCFG(overload)
            cfg.graph.ungroup_ast()
            components = cfg.find_functional_components()
            
            vdecls = []
            wcomps = [self.__build_multiframe_component(c, fun_id.name, vdecls) for c in sorted(components.values(), key=lambda _:_['id'])]
            
            inner_snippet += vdecls
            inner_snippet += wcomps
            
            #for k,v in components.items():
            #    print(k, ":")
            #    print(v["id"], ".", v["head"])
            
            snippet += inner_snippet.indent()
            snippet += "\n};\n"
            return snippet            
        else:
            rid = self.resolve_identifier
            rdt = self.resolve_data_type
            
            fun_id = rid(overload.func_symbol)
            ret_type_id = rdt(overload.return_type)
            
            params = [(rdt(p.data_type), rid(p).name) for p in overload.params]
            if overload.func_symbol.is_method:
                params = params[1:]
            
            header_pms = []
            for i,(d,p) in enumerate(params):
                if i>0: header_pms.append(", ")
                header_pms+=[d," ",p]
            
            snippet += [ret_type_id, " ", fun_id.name, "(", *header_pms, ")"]
            
            if overload.implementation is not None:
                snippet += "\n"
                snippet += self.__compile_ast_node(overload.implementation)
                snippet += "\n"
            else:
                snippet += ';\n'
        
        return snippet
        
    def __compile_ast_node(self, node:ASTNode, prio_build=None)->CppSnippet:
        if prio_build is not None:
            b = prio_build(node)
            if b is not None: return b

        snippet = CppSnippet([])
        if isinstance(node, ASTBlock):
            snippet+="{\n"
            for c in node.children:
                snippet += [self.__compile_ast_node(c, prio_build).indent(), ";\n"]
            snippet+="}\n"
            return snippet
        if isinstance(node, ASTNodes.Assign):
            snippet += self.__compile_ast_node(node.left, prio_build)
            snippet += " = "
            snippet += self.__compile_ast_node(node.right, prio_build)
            return snippet
        if isinstance(node, ASTNodes.FieldAccessor):
            snippet += ["(", self.__compile_ast_node(node.element, prio_build), ").", node.field.name]
            return snippet
        if isinstance(node, ASTNodes.Dereference):
            snippet += ["*(", self.__compile_ast_node(node.operand, prio_build) ,")"]
            return snippet
        if isinstance(node, ASTNodes.SymbolTerm):
            sym_cpp = self.resolve_identifier(node.symbol)
            snippet += sym_cpp.full_name
            return snippet
        if isinstance(node, ASTNodes.BinaryOperator):
            left = self.__compile_ast_node(node.left, prio_build)
            right = self.__compile_ast_node(node.right, prio_build)
            snippet += self.binop_translator[node.operator](left, right)
            return snippet
        if isinstance(node, ASTNodes.While):
            cond = self.__compile_ast_node(node.condition, prio_build)
            block = self.__compile_ast_node(node.block, prio_build)
            snippet += ["while(", cond, ")\n", block]
            return snippet
        if isinstance(node, ASTNodes.VDecl):
            variable = node.variable
            self.identify_symbol(variable, CppIdentifier(variable, variable.name))
            dt_cpp = self.resolve_data_type(variable.data_type)
            snippet+=[dt_cpp, " ", self.resolve_identifier(variable).name]
            return snippet
        if isinstance(node, ASTNodes.Literal):
            if node.data_type == self.env.dtype_int:
                snippet+=["(int)", str(node.value)]
                return snippet
        if isinstance(node, ASTNodes.FunOverloadCall):
            s_args = []
            for i, arg in enumerate(node.args):
                if i>0: s_args.append(", ")
                s_args.append(self.__compile_ast_node(arg, prio_build))                
            f_cpp = self.resolve_identifier(node.function_overload.func_symbol)
            snippet += [f_cpp.full_name, "(", *s_args, ")"]
            return snippet
        if isinstance(node, ASTNodes.Return):
            snippet += "return"
            if node.value is not None:
                snippet+=[" ", self.__compile_ast_node(node.value, prio_build)]
                return snippet
        if isinstance(node, ASTNodes.If):
            cond = self.__compile_ast_node(node.condition, prio_build)
            then_branch = self.__compile_ast_node(node.then_branch, prio_build)
            snippet+=["if (", cond, ")\n", then_branch]
            if node.else_branch is not None:
                else_branch = self.__compile_ast_node(node.else_branch, prio_build)
                snippet += ["else\n", else_branch]
            return snippet

        return CppSnippet([f"/* Not implemented node {type(node)} */"])
        
    def _parse_scope_tree_helper(self, scope:Scope, on_scope_enter, on_scope_exit, on_symbol_encountered):        
        if on_scope_enter(scope):            
            #print([(s, s.metadata) for s in scope.enumerate_symbols(recursive=False)])
            
            for symbol in sorted(scope.enumerate_symbols(recursive=False), key=lambda s:s.metadata['sid']):
                on_symbol_encountered(symbol)
            for subscope in scope.enumerate_subscopes():            
                self._parse_scope_tree_helper(subscope, on_scope_enter, on_scope_exit, on_symbol_encountered)
            on_scope_exit(scope)
    
    def parse_scope_tree(self, on_scope_enter, on_scope_exit, on_symbol_encountered):
        self._parse_scope_tree_helper(self.env.global_scope, on_scope_enter, on_scope_exit, on_symbol_encountered)
    
       
    def build_from_ast(self, ast:ASTNode)->CppSnippet:
        pass

class Cels2Cpp:
    def __init__(self, env:CelsEnvironment):
        self._env = env
        
    
    
    
    @property
    def env(self): return self._env