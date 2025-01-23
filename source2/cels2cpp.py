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
    def __init__(self, 
        components:list[CppSnippet|str], 
        headers:list[str]|None=None,
    ):
        self._headers = headers or []
        self._code = ""
        self._forward_decls:dict[Symbol, CppSnippet] = {}
        
        for comp in components:
            if isinstance(comp, str):
                self._code += comp
            elif isinstance(comp, CppSnippet):
                self._code += comp.code
                self._headers += comp.headers
                self._forward_decls.update(comp._forward_decls)            
            else:
                raise RuntimeError(f"Invalid CppSnippet component: type {type(comp)}")
        
    @property
    def code(self): return self._code
    
    @property
    def forward_decls(self): return self._forward_decls
    
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
    
    def get_full_code(self):
        from datetime import datetime
        code = ""
        code += f"/* \n"
        code += f" * Code generated by Cels2Cpp\n"
        code += f" * Built at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        code += f" */\n\n"
                
        for header in self.headers:
            code+=f"#include {header}\n"
        code += self.code
        return code
    
class CppFragment:
    def __init__(self, ref_obj, namespace:str):
        self._ref_obj = ref_obj
        self._namespace = namespace
        self._definition = CppSnippet([])
        self._implementation = CppSnippet([])
    
    @property
    def ref_obj(self): return self._ref_obj
    
    @property
    def definition(self): return self._definition
    
    @definition.setter
    def definition(self, val): self._definition = val
    
    @property
    def implementation(self): return self._implementation
    
    @implementation.setter
    def implementation(self, val): self._implementation = val
    
    @property 
    def namespace(self): return self._namespace

    def __str__(self):
        res = ""
        res += f"Fragment ({self.ref_obj}) {{\n"
        res += f"  namespace: {self.namespace},\n"
        res += f"  definition: {indent(self.definition.code)},\n"
        res += f"  implementation: {indent(self.implementation.code)}\n"
        res += f"}}"        
        return res


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
        self.unop_translator:dict[UnaryOperator, callable] = {}
        
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
            if data_type.is_static_array:
                element_type:CppSnippet = self.resolve_data_type(data_type.element_type)
                return CppSnippet(["Celesta::StaticArray<", element_type, ", ", str(data_type.length), ">"])
            if data_type.is_task:
                result_type:CppSnippet = self.resolve_data_type(data_type.result_type)
                return CppSnippet(["Celesta::Task<", result_type, ">"])
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
        self.identify_symbol(self.env.dtype_uint, CppIdentifier(self.env.dtype_uint, "unsigned int"))
        self.identify_symbol(self.env.dtype_short, CppIdentifier(self.env.dtype_short, "short"))
        self.identify_symbol(self.env.dtype_ushort, CppIdentifier(self.env.dtype_ushort, "unsigned short"))
        self.identify_symbol(self.env.dtype_void, CppIdentifier(self.env.dtype_void, "void"))
        
        dtype_int = self.env.dtype_int
        dtype_uint = self.env.dtype_uint
        dtype_bool = self.env.dtype_bool
        
        rbo = self.env.op_solver.resolve_binary_operator
        ruo = self.env.op_solver.resolve_unary_operator
                
        self.binop_translator[rbo('+', dtype_int, dtype_int)] = lambda l,r: ["(", l, '+', r, ")"]
        self.binop_translator[rbo('-', dtype_int, dtype_int)] = lambda l,r: ["(", l, '-', r, ")"]
        self.binop_translator[rbo('*', dtype_int, dtype_int)] = lambda l,r: ["(", l, '*', r, ")"]
        self.binop_translator[rbo('/', dtype_int, dtype_int)] = lambda l,r: ["(", l, '/', r, ")"]
        self.binop_translator[rbo('%', dtype_int, dtype_int)] = lambda l,r: ["(", l, '%', r, ")"]
        self.binop_translator[rbo('>', dtype_int, dtype_int)] = lambda l,r: ["(", l, '>', r, ")"]
        self.binop_translator[rbo('>=', dtype_int, dtype_int)] = lambda l,r: ["(", l, '>=', r, ")"]
        self.binop_translator[rbo('<', dtype_int, dtype_int)] = lambda l,r: ["(", l, '<', r, ")"]
        self.binop_translator[rbo('<=', dtype_int, dtype_int)] = lambda l,r: ["(", l, '<=', r, ")"]
        self.binop_translator[rbo('==', dtype_int, dtype_int)] = lambda l,r: ["(", l, '==', r, ")"]
        self.binop_translator[rbo('!=', dtype_int, dtype_int)] = lambda l,r: ["(", l, '!=', r, ")"]
        
        self.binop_translator[rbo('+', dtype_bool, dtype_bool)] = lambda l,r: ["(", l, '+', r, ")"]        
        
        self.binop_translator[rbo('==', dtype_bool, dtype_bool)] = lambda l,r: ["(", l, '==', r, ")"]
        
        self.unop_translator[ruo('not', dtype_bool)] = lambda x: ["(!",x,")"]
        self.unop_translator[ruo('-', dtype_int)] = lambda x: ["(-",x,")"]
        self.unop_translator[ruo('-', dtype_uint)] = lambda x: ["(-",x,")"]
        self.unop_translator[ruo('+', dtype_int)] = lambda x: ["(+",x,")"]
        self.unop_translator[ruo('+', dtype_uint)] = lambda x: ["(+",x,")"]

        #print([str(key) for key, _ in self.binop_translator.items()])
        
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
        
        ns_stack = []
        fragments:list[CppFragment] = []
        
        def get_namespace(): return ns_stack[-1] if len(ns_stack)>0 else None
        
        def is_package_scope(scope:Scope):
            return 'type' in scope.metadata and scope.metadata['type']=='package'
        
        def on_scope_enter(scope:Scope)->bool:     
            if scope==self.env.global_scope: return True
        
            if is_package_scope(scope):                
                ns_stack.append(scope.name)
                return True
            
            if isinstance(scope.associated_symbol, StructType):
                return False
            
            if isinstance(scope.associated_symbol, Function):
                return False

            raise NotImplementedError(f"Not implemented scope {scope} ({scope.associated_symbol})")
            return True
        
        def on_scope_exit(scope:Scope):
            if is_package_scope(scope):
                ns_stack.pop()
        
        def on_symbol_encountered(symbol:Symbol):
            if isinstance(symbol, PrimitiveType): return
            
            if isinstance(symbol, Function):
                for overload in symbol.overloads:                    
                    fragment = self.__compile_function_overload_frag(overload, get_namespace())
                    fragments.append(fragment)
                return
            
            if isinstance(symbol, StructType):
                fragment = self.__compile_struct_frag(symbol, get_namespace())
                fragments.append(fragment)
                return
            
            raise NotImplementedError(f"Not implemented {symbol} ({type(symbol)})")            
            
            
        self.parse_scope_tree(on_scope_enter, on_scope_exit, on_symbol_encountered)

        """
        print("FRAGS")
        for fragment in fragments:
            print(fragment)
        print("FRAGS")
        """
        
        defi, impl = self.__assemble_fragments(fragments)
        
        
        return CppSnippet([defi, '\n// IMPL\n', impl])
        
    def __sort_fragments(self, fragments):
        frag_dict = { frag.ref_obj:frag for frag in fragments }
        
        root = object()
        dep_graph = {root:set()}
        incoming_edges_count = {root:0}
        
        def add_dependency(x,y):
            if not x in dep_graph: dep_graph[x] = set()
            if not y in incoming_edges_count: incoming_edges_count[y] = 0
            if y in dep_graph[x]: return
            dep_graph[x].add(y)
            incoming_edges_count[y]+=1
        
        def remove_dependency(x,y):            
            dep_graph[x].remove(y)
            incoming_edges_count[y]-=1
            
        def get_next_nodes(x):
            if not x in dep_graph.keys():
                return []
            return list(dep_graph[x])
        
        def remember_dependency(deps, item):
            if item in frag_dict.keys():
                deps.add(item)
            if isinstance(item, DataType):
                if item.is_pointer or item.is_static_array or item.is_task:
                    remember_dependency(deps, item.element_type)           

        for fragment in fragments:
            ref = fragment.ref_obj            
            deps = set()        
            
            if isinstance(ref, FunctionOverload):
                for param in ref.params:                    
                    remember_dependency(deps, param.data_type)
                remember_dependency(deps, ref.return_type)
            
            if len(deps)>0:
                for dep in deps:
                    add_dependency(dep, ref)
            else:
                add_dependency(root, ref)
                    
        for k, v in dep_graph.items():
            for it in v:
                print("D", k, it)
        
        # sort topologically - Kahn's algorithm
        L = []
        S = set([root])
        
        while len(S)>0:
            n = S.pop()
            print('n=', n)
            L.append(n)
            for m in get_next_nodes(n):
                remove_dependency(n, m)
                if incoming_edges_count[m]==0:
                    S.add(m)
        
        if sum(incoming_edges_count.values())>0:
            raise RuntimeError("__sort_fragments: cyclic dependencies")
        
        return [frag_dict[_] for _ in L if _!=root]
        
        
    def __assemble_fragments(self, fragments)->tuple[CppSnippet, CppSnippet]:
        defi, impl = CppSnippet([]), CppSnippet([])
        for fragment in self.__sort_fragments(fragments): 
            impl += [fragment.implementation, "\n"]
            if fragment.namespace is not None:
                defi += [f"namespace {fragment.namespace}\n{{\n",fragment.definition.indent(), "\n}\n"]
            else:
                defi += [fragment.definition, "\n"]
        return defi, impl

    def __compile_struct_frag(self, struct, namespace:str)->CppFragment:
        fragment  = CppFragment(struct, namespace)
        defi, impl = fragment.definition, fragment.implementation
        
        cpp_id = self.resolve_identifier(struct)
        defi += ["struct ", cpp_id.name, "\n{\n"]
        
        inner_defi = CppSnippet([])
                
        
        for member in sorted(struct.members, key=lambda m:m.metadata["sid"]):
            if isinstance(member, Field):
                t_id = self.resolve_data_type(member.data_type)
                f_id = self.resolve_identifier(member)                                
                inner_defi += [t_id, " ", f_id.name, ";\n"]
                continue
            if isinstance(member, Function):
                for overload in member.overloads:
                    member_frag = self.__compile_function_overload_frag(overload, namespace)
                    inner_defi += [member_frag.definition, "\n"]
                    impl += [member_frag.implementation, "\n"]
                continue
            
            inner_defi += f"/* Not implemented {member} ({type(member)})*/\n"
        
        defi += [inner_defi.indent(), "\n};\n"]
        return fragment

    def __build_multiframe_component_frag(self, component, fname, vdecls, namespace, task_refs)->tuple[CppSnippet, CppSnippet]:
        def prio_build(ast_node)->CppSnippet|None:
            print("PRIO_BUILD", type(ast_node))
            nonlocal vdecls
            if isinstance(ast_node, ASTNodes.VDecl):
                def verbatim_local_symbol_id(param):
                    return CppIdentifier(param, param.name, f"ctx->{param.name}")
                var = ast_node.variable                
                sid = verbatim_local_symbol_id(var)                
                self.identify_symbol(var, sid)
                # print("PRIO_BUILD VAR_DECL ", var, sid)
                #vdecls += [self.resolve_identifier(var.data_type).full_name, " ", sid.name, ";\n"]                
                vdecls += [self.resolve_data_type(var.data_type), " ", sid.name, ";\n"]    
                if var.data_type.is_task:
                    task_refs.append(var)                    
                
                return CppSnippet([""])
            if isinstance(ast_node, ASTNodes.Suspend):
                return CppSnippet(["ctrl->suspend();\n"])
            if isinstance(ast_node, ASTNodes.Return):
                snippet = CppSnippet([])
                if ast_node.value is not None:
                    snippet+= ["ctx->return_value = ", self.__compile_ast_node(ast_node.value, prio_build), ";\n"]
                snippet += f"{{ f_cleanup(ctx, ctrl); ctrl->ret(); return; }}\n"
                return snippet
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
            if isinstance(ast_node, ASTNodes.TaskStart):
                snippet = CppSnippet([])
                #func_name = self.resolve_identifier(func.func_symbol).full_name
                func_name = f"{namespace}"
                assert ast_node.data_type.is_task
                if isinstance(ast_node.task, ASTNodes.FunctionClosure):
                    closure = ast_node.task
                    if len(closure.free_params())>0:
                        raise RuntimeError(f'Cannot launch task with unbonund arguments')
                    
                    ov_name = self.resolve_identifier(closure.function_overload.func_symbol).full_name
                    
                    set_params_lambda = CppSnippet(["[](", func_name, "* ctx, ", ov_name, "* mfctx) {"])
                    
                    for i, arg in enumerate(closure.captured_args):
                        fparam = closure.function_overload.params[i]
                        carg = self.__compile_ast_node(arg, prio_build)
                        set_params_lambda+= ["mfctx->params.", fparam.name, " = ", carg, ";"]
                        print(fparam)
                        print(arg)                
                    
                    set_params_lambda += "}"
                    
                    #task = ast_node.
                    #sid.name, "_data
                    task_data_name = f"{closure.function_overload.func_symbol.name}_task_data"
                    res_type = self.resolve_data_type(ast_node.data_type.result_type)
                    
                    vdecls += [ "Celesta::TaskData<", res_type, "> ", task_data_name, ";\n"  ]
                    
                    snippet += [ self.resolve_data_type(ast_node.data_type), "(&ctx->", task_data_name, ")"]
                    snippet += [ ".init<", func_name, ", ", ov_name , ">(ctrl, ctx, ", set_params_lambda, ")"]
                    
                    return snippet
                else:
                    raise RuntimeError(f'Taskstart currently only supports function closures, found {type(ast_node.task)}')
                
                
                snippet += [ self.resolve_data_type(node.data_type), "()"]
                return snippet
            
            if isinstance(ast_node, ASTNodes.TaskReady):
                snippet = CppSnippet([])
                task = self.__compile_ast_node(ast_node.task, prio_build)
                snippet += [ "(", task, ").is_ready()" ]
                return snippet
            
            return None
        
        defi = CppSnippet([])
        impl = CppSnippet([])
        
        defi += [f"static void f{component['id']}(void* _ctx, Celesta::ExecutionController* ctrl);\n"]
                
        
        impl = CppSnippet([])
        impl += [f"void {namespace}", f"::f{component['id']}(void* _ctx, Celesta::ExecutionController* ctrl)\n"]
        impl += "{\n"
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
                    inner_snippet += [self.__compile_ast_node(node.ast, prio_build), ";\n"]                    
                if len(node.next_nodes)>0:
                    inner_snippet += [f"goto L_{node.next_nodes[0].node_id};\n"]
                else:
                    inner_snippet += "return;\n"                    
            elif node.node_type=='f':
                inner_snippet += [f"ctrl->jump(ctx, ", fname, f"::f{node.data['id']}); return;\n"]               
            elif node.node_type=='e':
                inner_snippet += f"{{ f_cleanup(ctx, ctrl); ctrl->ret(); return; }}\n"
            else:
                inner_snippet += f"/* Node #{node.node_id} {node.node_type} */"                
        
        impl += [inner_snippet.indent(), "\n"]
        impl += "}\n\n"        
    
        return defi, impl

    # Compilation is a destructive process!
    # it alters overload.implementation
    def __compile_function_overload_multiframe_frag(self, overload:FunctionOverload, namespace)->CppFragment:
    
        fragment = CppFragment(overload, namespace)
            
        fun_id = self.resolve_identifier(overload.func_symbol)
        ret_type_id = self.resolve_data_type(overload.return_type)
        
        defi = fragment.definition
        impl = fragment.implementation
        
        defi += ["struct ", fun_id.name, " \n"]
        defi += ["#ifdef CELS_NAMED\n"]
        defi += ["    : public Celesta::ICelsNamed\n"]
        defi += ["#endif\n"]
        defi += ["{\n"]
        inner_snippet = CppSnippet([])
        
        if len(overload.params)>0:
            def verbatim_local_symbol_id(param):
                return CppIdentifier(param, param.name, f"ctx->params.{param.name}")
        
            inner_snippet += "struct\n{\n"
            
            for param in overload.params:
                sid = verbatim_local_symbol_id(param)
                self.identify_symbol(param, sid)                
                
                d = self.resolve_data_type(param.data_type)
                p = self.resolve_identifier(param)
                inner_snippet += [CppSnippet([d, " ", p.name, ";"]).indent(), "\n"]
            inner_snippet+= ["} params;\n\n"]
        
        if overload.return_type != self.env.dtype_void:
            inner_snippet+= [ret_type_id, " ", "return_value;\n"]
        
        cfg = MultiframeCFG(overload)
        cfg.graph.ungroup_ast()
        components = cfg.find_functional_components()
        
        vdecls = []
        
        fdefis = []
        
        task_refs = []
        
        for c in sorted(components.values(), key=lambda _:_['id']):            
            f_defi, f_impl = self.__build_multiframe_component_frag(c, fun_id.name, vdecls,
                namespace=overload.func_symbol.get_full_name(), task_refs=task_refs)
            fdefis.append(f_defi)            
            impl += f_impl            
        
        
        inner_snippet += vdecls
        inner_snippet += fdefis
        
        inner_snippet += "\nstatic void f_cleanup(void* _ctx, Celesta::ExecutionController* ctrl);\n"
        
        cleanup_impl = CppSnippet([])        
        cleanup_impl += [f"void {overload.func_symbol.get_full_name()}", "::f_cleanup(void* _ctx, Celesta::ExecutionController* ctrl)\n"]
        cleanup_impl += "{\n"
        cleanup_impl_inner = CppSnippet([])
        if len(task_refs)>0:
            cleanup_impl_inner += [f"auto* ctx = (", overload.func_symbol.get_full_name(), "*)_ctx;\n"]
            for task_ref in task_refs:
                cleanup_impl_inner += [ self.resolve_identifier(task_ref).full_name, ".detach();\n" ]            
            cleanup_impl += cleanup_impl_inner.indent()
        cleanup_impl += "\n}\n"
        impl += cleanup_impl
        
        
        inner_snippet += ["\n#ifdef CELS_NAMED\n"]
        inner_snippet += f'const char* icels_name() override {{ return "{overload.func_symbol.get_full_name()}"; }}\n'
        inner_snippet += ["#endif\n"]
        
        
        
        defi += inner_snippet.indent() 
        
        
        defi += "\n};\n"

        print(fragment)
        return fragment
     
    def __compile_function_overload_noframe_frag(self, overload:FunctionOverload, namespace:str)->CppFragment:        
        fragment = CppFragment(overload, namespace)
    
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
            
        fragment.definition += [ret_type_id, " ", fun_id.name, "(", *header_pms, ");"]
                
        if overload.implementation is not None:
            impl = fragment.implementation
            if namespace is not None:
                impl += [ret_type_id, " ", namespace, "::", fun_id.name, "(", *header_pms, ")"]
            else:
                impl += [ret_type_id, " ", fun_id.name, "(", *header_pms, ")"]
            impl += "\n"
            impl += self.__compile_ast_node(overload.implementation)
            impl += "\n"
          
        print(fragment)        
    
        return fragment 
     
    def __compile_function_overload_frag(self, overload:FunctionOverload, namespace)->CppFragment:
        if overload.func_symbol.declaring_type is None:        
            if overload.is_multiframe:
                if overload.is_extern:
                    return CppSnippet([f"/* Not Implemented: Extern multiframe functions: {overload} */"])
                return self.__compile_function_overload_multiframe_frag(overload, namespace)
            else:
                return self.__compile_function_overload_noframe_frag(overload, namespace)
        else: # member function            
            if overload.is_multiframe:
                raise NotImplementedError("Multiframe member function")
            return self.__compile_function_overload_noframe_frag(overload, overload.func_symbol.declaring_type.get_full_name())


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
        if isinstance(node, ASTNodes.UnaryOperator):
            operand = self.__compile_ast_node(node.operand, prio_build)
            snippet += self.unop_translator[node.operator](operand)
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
            if node.data_type == self.env.dtype_bool:
                snippet += [("true" if node.value==True else "false")]
                return snippet
            
        if isinstance(node, ASTNodes.FunOverloadCall):
            if node.function_overload.func_symbol.is_method:
                obj_arg = self.__compile_ast_node(node.args[0], prio_build)
                s_args = []
                for i, arg in enumerate(node.args[1:]):
                    if i>0: s_args.append(", ")
                    s_args.append(self.__compile_ast_node(arg, prio_build))
                f_cpp = self.resolve_identifier(node.function_overload.func_symbol)
                snippet += ["(", obj_arg, ")->", f_cpp.name, "(", *s_args, ")"]
                return snippet
            else:
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
        if isinstance(node, ASTNodes.AddressOf):
            snippet += ["&(", self.__compile_ast_node(node.operand, prio_build), ")"]
            return snippet
        if isinstance(node, ASTNodes.IndexAccess):
            expr = self.__compile_ast_node(node.expression, prio_build)
            key = self.__compile_ast_node(node.key, prio_build)
            snippet += [expr, "[", key, "]"]
            return snippet
        if isinstance(node, ASTNodes.TypeConvert):
            expr = self.__compile_ast_node(node.expression, prio_build)
            dtype = self.resolve_data_type(node.data_type)
            snippet += ["((", dtype, ")", "(", expr, "))"]
            return snippet
        if isinstance(node, ASTNodes.TaskStart):
            raise RuntimeError("Wrong route, should have been multiframe prio_build")
        
        return CppSnippet([f"/* Not implemented node {type(node)} */"])
        
    def _parse_scope_tree_helper(self, scope:Scope, on_scope_enter, on_scope_exit, on_symbol_encountered):        
        if on_scope_enter(scope):
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