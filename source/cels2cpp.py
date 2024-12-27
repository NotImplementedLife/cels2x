from __future__ import annotations
from cels_core import ASTNodes, CelsLexer, CelsParser
from cels_core import Symbol, DataType, Variable, Function, FormalParameter
from scopes import ScopeNode
from collections import deque
from ast import ASTNode


import time

class IdProvider:
    def __init__(self):
        self._id=0
    
    def get_id(self):
        self._id+=1
        return self._id
        
    def __call__(self): return self.get_id()

class MultiFrameCFGNode:
    def __init__(self, idp:IdProvider, ast, node_type='i'): # 'i'=instruction, 'c'=conditional, 'f'=functioncall (in MF struct), data points to callable component
        self.idp = idp
        self.node_id = idp()
        self.ast = ast
        self.data = None
        self.next_nodes = []
        self.node_type = node_type
    
    @staticmethod
    def indent(text):
        return "\n    ".join(text.splitlines())
    
    @staticmethod
    def link(n1, n2):
        n1.next_nodes.append(n2)        
     
    def __str__(self):
        if self.node_type!='f':
            return f"{{Node #{self.node_id} {self.node_type}, next={list(map(lambda _:_.node_id,self.next_nodes))}, ast={self.indent(str(self.ast or 'None'))}}}"
        else:
            return f"{{Node #{self.node_id} {self.node_type}, next={list(map(lambda _:_.node_id,self.next_nodes))}, f_head={self.data['id']}}}"
    
    def ungroup_ast(self):
        if isinstance(self.ast, ASTNodes.Block):
            children = self.ast.children
            if len(children)==0:
                return
            n_nodes = self.next_nodes
            nodes = [MultiFrameCFGNode(self.idp, c, 'i') for c in children]
            self.ast = nodes[0].ast            
            self.next_nodes = []                        
            nodes[0]=self
            for i in range(0, len(nodes)-1):
                self.link(nodes[i], nodes[i+1])
            nodes[-1].next_nodes = n_nodes            
                
            for n in nodes:
                n.ungroup_ast()            
            return
        if isinstance(self.ast, ASTNodes.While):
            cond = self.ast.condition
            block = self.ast.block
                        
            assert len(self.next_nodes)==1
            
            n_block = MultiFrameCFGNode(self.idp, block, 'i')
            n_block.next_nodes = [self]            
                        
            self.next_nodes.append(n_block)
            
            self.ast = cond
            self.node_type='c'
            
            n_block.ungroup_ast()
            return
        if isinstance(self.ast, ASTNodes.If):
            cond = self.ast.condition
            then_branch = self.ast.then_branch
            else_branch = self.ast.else_branch            
            
            end_node = MultiFrameCFGNode(self.idp, None, 'i')
            end_node.next_nodes = self.next_nodes
            
            then_node = MultiFrameCFGNode(self.idp, then_branch, 'i')            
            then_node.next_nodes = [end_node]
            self.next_nodes = [end_node, then_node]
            
            else_node = None
            if else_branch is not None:
                else_node = MultiFrameCFGNode(self.idp, else_branch, 'i')
                self.next_nodes[0] = else_node
                else_node.next_nodes = [end_node]
            
            self.ast = cond
            self.node_type = 'c'
            
            then_node.ungroup_ast()
            if else_node is not None:
                else_node.ungroup_ast()            
            
            return            
            
    
    def __copy_structure(self, refs):
        if self.node_id in refs: return refs[self.node_id]
        cnode = MultiFrameCFGNode(lambda: self.node_id, self.ast, self.node_type)
        refs[self.node_id] = cnode
        cnexts = [n.__copy_structure(refs) for n in self.next_nodes]
        cnode.next_nodes = cnexts
        return cnode
        
    def copy(self):
        refs = {}
        return self.__copy_structure(refs)


class PseudoAST_PreMultiframeFunCall(ASTNode):
    def __init__(self, funcall, result_lhs):
        super(PseudoAST_PreMultiframeFunCall, self).__init__()
        self.funcall = funcall
        self.result_lhs = result_lhs
        self.jump_f = None

class PseudoAST_PostMultiframeFunCall(ASTNode):
    def __init__(self, funcall, result_lhs):
        super(PseudoAST_PostMultiframeFunCall, self).__init__()
        self.funcall = funcall
        self.result_lhs = result_lhs

class MultiframeCFG:
    def __init__(self, ast_fundecl: ASTNodes.FunDecl):
        assert isinstance(ast_fundecl, ASTNodes.FunDecl)
        self.idp = idp = IdProvider()
        self.func = ast_fundecl.function        
        self.start_node = MultiFrameCFGNode(idp, None)
        self.graph = MultiFrameCFGNode(idp, self.func.implementation)
        self.end_node = MultiFrameCFGNode(idp, None, 'e')
        MultiFrameCFGNode.link(self.start_node, self.graph)
        MultiFrameCFGNode.link(self.graph, self.end_node)
        
    @staticmethod
    def __enumerate_nodes(node0):
        visited = set()
        stack = [node0]        
        while len(stack)>0:
            n = stack[-1]; stack.pop()
            if not n.node_id in visited:
                visited.add(n.node_id)
                yield n                
                for nxt in n.next_nodes:                    
                    stack.append(nxt)        
    @staticmethod
    def enumerate_nodes(node0): return MultiframeCFG.__enumerate_nodes(node0)
        
    @staticmethod
    def __tree2string(node0):
        result=""
        for n in MultiframeCFG.__enumerate_nodes(node0):
            result+=str(n)+"\n"
        return result
    
    @staticmethod
    def tree2string(node0): return MultiframeCFG.__tree2string(node0)
    
    def __str__(self): return self.__tree2string(self.start_node)
    
    def find_functional_components(self):
        node_label:dict[int, list] = {}
        heads: set[int] = set()
        
        def enumerate_nodes(): return self.__enumerate_nodes(self.start_node)          
        
        mffuncalls = []
        for node in enumerate_nodes():            
            if isinstance(node.ast, ASTNodes.Attr) and isinstance(node.ast.right, ASTNodes.FunCall) and node.ast.right.function.is_multiframe:
                mffuncalls.append(node)
            elif isinstance(node.ast, ASTNodes.FunCall) and node.ast.function.is_multiframe:
                mffuncalls.append(node)
                
        for node in mffuncalls:
            lhs, funcall = None, None
            if isinstance(node.ast, ASTNodes.Attr) and isinstance(node.ast.right, ASTNodes.FunCall) and node.ast.right.function.is_multiframe:
                lhs = node.ast.left
                funcall = node.ast.right
            elif isinstance(node.ast, ASTNodes.FunCall) and node.ast.function.is_multiframe:
                funcall = node.ast            
            
            post = MultiFrameCFGNode(node.idp, PseudoAST_PostMultiframeFunCall(funcall, lhs))
            post.next_nodes = node.next_nodes
            
            node.ast = PseudoAST_PreMultiframeFunCall(funcall, lhs)
            node.next_nodes = [post]

        for node in enumerate_nodes(): node_label[node.node_id] = []
        
        def bfs(start_node, label):
            queue = deque([start_node])
            visited = set()
            suspends = []
            while len(queue)>0:
                node = queue[0]
                queue.popleft()
                visited.add(node.node_id)
                node_label[node.node_id].append(label)
                if isinstance(node.ast, ASTNodes.Suspend) or isinstance(node.ast, PseudoAST_PreMultiframeFunCall):
                    suspends.append(node)
                    continue
                for n in node.next_nodes:
                    if not n.node_id in visited and not n.node_id in heads:
                        queue.append(n)            
            return suspends
      
        label = 1
        
        start_node = self.graph
        heads.add(start_node.node_id)
        heads.add(self.start_node.node_id)
        
        H = [start_node]
        while len(H)>0:
            newH = []
            for h in H:
                suspends = bfs(h, label)
                label+=1
                for s in suspends:
                    nh = s.next_nodes[0]
                    if not nh.node_id in heads:
                        heads.add(nh.node_id)
                        newH.append(nh)            
                for node in enumerate_nodes():
                    for nxt in node.next_nodes:
                        if node_label[node.node_id]!=node_label[nxt.node_id] and len(node_label[node.node_id])*len(node_label[nxt.node_id])>0:
                            if not nxt.node_id in heads:
                                heads.add(nxt.node_id)
                                newH.append(nxt)
            H = newH
        
        nlabels = {}
        for node in enumerate_nodes():
            l = tuple(node_label[node.node_id])
            if not l in nlabels: nlabels[l]=len(nlabels)
            node_label[node.node_id] = nlabels[l]
        
        #print(heads)
        #print(node_label)
        
        cgraph = self.start_node.copy()
        #print(self.__tree2string(cgraph))
        
        components = {}
        
        for head_id in heads:
            comp_id = node_label[head_id]
            
            head = None
            for node in self.__enumerate_nodes(cgraph):
                if node.node_id==head_id:
                    head = node
                    break
            assert head is not None
            
            calls = []
            for node in self.__enumerate_nodes(head):                
                if node_label[node.node_id]!=node_label[head.node_id]: continue                
                for nxt in node.next_nodes:
                    if node_label[nxt.node_id] != node_label[head_id]:                        
                        assert nxt.node_id in heads
                        calls.append((node, nxt))
                    elif nxt.node_id in heads:
                        calls.append((node, nxt))

            component = {
                'id':comp_id,
                'head':head,
                'calls':calls
            }
            components[comp_id] = component
            
        for component in components.values():                    
            head = component['head']           
            for node, nxt in component['calls']:
                ix = node.next_nodes.index(nxt)
                fnode = MultiFrameCFGNode(self.idp, None, 'f')
                fnode.data = components[node_label[nxt.node_id]]
                node.next_nodes[ix] = fnode
            del component['calls']
            
            for node in self.enumerate_nodes(component['head']):
                if isinstance(node.ast, PseudoAST_PreMultiframeFunCall):
                    if len(node.next_nodes)==1 and node.next_nodes[0].node_type=='f':
                        node.ast.jump_f = node.next_nodes[0].data['id']
                        node.ast.next_nodes = node.next_nodes[0].next_nodes                        
                    else:
                        raise RuntimeError(f"PseudoAST_PreMultiframeFunCall can only be followed by an f-jump, got: {list(map(lambda _:_.node_type, node.next_nodes))}")
            
            self.__collapse_linear_paths(component['head'])
        
        # for k,v in components.items(): print(f"{k} => id={v['id']}, graph=\n{self.__tree2string(v['head'])}")
        
        return components

    @staticmethod
    def __collapse_linear_paths(head):
        prevs_count = {}
        for node in MultiframeCFG.__enumerate_nodes(head):
            prevs_count[node.node_id]=0
        
        for node in MultiframeCFG.__enumerate_nodes(head):
            for nxt in node.next_nodes:                
                prevs_count[nxt.node_id]+=1
        for node in MultiframeCFG.__enumerate_nodes(head):
            if node.node_type=='i':
                #assert prevs_count[node.node_id]<=1, f"Failed for node {node.node_id}"
                assert len(node.next_nodes)<=1, f"Failed for node {node.node_id}"
        
        def create_ipairs():
            pairs = []
            visited = set()
            for node in MultiframeCFG.__enumerate_nodes(head):
                if node.node_type!='i': continue
                if node.node_id in visited: continue
                if prevs_count[node.node_id]>1: continue
                if node.ast is None: continue
                for nxt in node.next_nodes:
                    if nxt.node_type!='i': continue
                    if nxt.node_id in visited: continue
                    if prevs_count[nxt.node_id]>1: continue
                    if nxt.ast is None: continue
                    pairs.append((node, nxt))
                    visited.add(node.node_id)
                    visited.add(nxt.node_id)                                    
            return pairs
        
        ipairs = create_ipairs()
        while len(ipairs)>0:
            for n0, n1 in ipairs:                
                n0.ast = ASTNodes.Block(n0.ast, n1.ast)
                n0.next_nodes = n1.next_nodes
            ipairs = create_ipairs()
    

class ResolutionStack:
    def __init__(self):
        self.stack = []
        
    def push(self, item): self.stack.append(item)
    def pop_until(self, condition):
        result = []
        ok = False
        while len(self.stack)>0 and not ok:
            top = self.stack[-1]
            result.append(top)
            self.stack.pop()          
            ok = condition(top)
        if not ok: raise RuntimeError("Pop_until failed")
        return result[::-1]
    
    def pop(self):
        if len(self.stack)==0: raise RuntimeError("Pop failed")
        item = self.stack[-1]
        self.stack.pop()
        return item

class CppIdentifier:
    def __init__(self, name:str, full_name:str|None=None, headers:list[str]=None):
        self.name = name
        self.full_name = full_name or self.name
        self.headers = headers or []

    
class CppSymbolRepository:
    def __init__(self):
        self.symbol2id:dict[Symbol, CppIdentifier] = {}
    
    def identify_symbol(self, symbol, identifier):
        self.symbol2id[symbol] = identifier
        
    def resolve_symbol(self, symbol:Symbol):
        if symbol in self.symbol2id: return self.symbol2id[symbol]
        if isinstance(symbol, DataType):
            dt = symbol
            if dt.is_pointer:
                cppid = self.resolve_symbol(dt.element_type)
                cppid = CppIdentifier(name=cppid.name+"*", full_name=cppid.full_name+"*", headers=cppid.headers)
                self.symbol2id[symbol] = cppid
                return self.symbol2id[symbol]                
        
        return self.symbol2id[symbol]
    

class CppSnippet:
    def __init__(self, wildcards:list[str|Symbol|CppSnippet], symbol_repo=None, headers:list[str]=None):
        self.code = ""
        self.headers = headers or []
        for w in wildcards:
            if isinstance(w, str):
                self.code+=w
            elif isinstance(w, Symbol):
                sid = symbol_repo.resolve_symbol(w)
                self.code += sid.full_name                
                self.headers += sid.headers        
            elif isinstance(w, CppSnippet):
                self.code += w.code
                self.headers += w.headers
    def __str__(self): return self.code
    
    @staticmethod
    def join(delim:str, snippets:list[CppSnippet])->CppSnippet:
        code = delim.join(map(lambda _:_.code, snippets))
        headers = []
        for s in snippets: headers += s.headers
        return CppSnippet(code, headers)
            
    def indent(self):                
        code = "    " + ('\n    '.join(self.code.splitlines()))+"\n"
        return CppSnippet(code, self.headers)
        
class CppContext:
    def __init__(self):
        self.res_stack = ResolutionStack()        
        self.scope_stack = []
        self.binop_translator: dict[ASTNodes.BinaryOperator, callable] = {}
        self.indexer_archetype_translator: dict[IndexerArchetype, callable] = {}
        self.symbol_repo = CppSymbolRepository()
        self.sid = 0
        self.dtype_void = None
    
    def get_symbol_name_only(self, sym:Symbol):
        return sym.name
        
    def get_symbol_name_rel(self, sym:Symbol, scope:ScopeNode):
        if isinstance(sym, FormalParameter):
            return sym.name
        sym_path = sym.scope.get_path()[1:]+[sym.name]
        scope_path = scope.get_path()[1:]  # path[0] is always "global" scope
        i=0
        q=0
                
        while i<len(sym_path)-1:
            if sym_path[i].startswith("@"): q=i+1; break
            if sym_path[i]!=scope_path[i]: break
            i+=1
        return '::'.join(sym_path[q:])
    
    def generate_symbol_id(self, sym:Symbol, scope:ScopeNode, type_suffix="", use_sid=True)->CppIdentifier:
        if type_suffix!="": type_suffix="_"+type_suffix
        if use_sid:
            self.sid += 1
            type_suffix+=str(self.sid)
        rel = self.get_symbol_name_rel(sym, scope)+type_suffix
        return CppIdentifier(rel.split('::')[-1], rel)
     
    def verbatim_local_symbol_id(self, sym:Symbol, name, type_suffix="", use_sid=True)->CppIdentifier:
        if len(type_suffix)>0: type_suffix="_"+type_suffix
        if use_sid:
            self.sid += 1
            rel = f"{name}{type_suffix}{self.sid}"
            return CppIdentifier(rel, rel)
        else:
            rel = f"{name}{type_suffix}"
            return CppIdentifier(rel, rel)            
    
    @staticmethod
    def indent(text):
        return "    "+"\n    ".join(text.splitlines())
    
    def __build_multiframe_component(self, component, fname, vdecls)->CppSnippet:            
        
        def prio_build(ast_node)->CppSnippet|None:
            if isinstance(ast_node, ASTNodes.VDecl):                
                var = ast_node.variable                
                sid = self.verbatim_local_symbol_id(var, f"ctx->{var.name}", "l")                
                self.symbol_repo.identify_symbol(var, sid)
                # print("PRIO_BUILD VAR_DECL ", var, sid)
                vdecls.append(f"{self.symbol_repo.resolve_symbol(var.data_type).full_name} {sid.name.split('->')[1]};\n")
                return CppSnippet([""])
            if isinstance(ast_node, ASTNodes.Suspend):
                return CppSnippet(["ctrl->suspend();\n"])
            if isinstance(ast_node, ASTNodes.Return):
                if ast_node.value is None:
                    return CppSnippet(["ctrl->ret(); return;\n"])
                else:
                    return CppSnippet(["ctx->return_value = ", self.build(ast_node.value, prio_build), ";\n", "ctrl->ret(); return;\n"])
            if isinstance(ast_node, PseudoAST_PreMultiframeFunCall):
                func = ast_node.funcall.function
                func_name = self.symbol_repo.resolve_symbol(func).full_name
                wcards = ["{\n", "\tauto* f = ctrl->push<", func_name, ">();\n"]
                for param, arg in zip(ast_node.funcall.function.params, ast_node.funcall.args):
                    wcards += [f"\tf->params.{param.name} = ", self.build(arg, prio_build), ";\n"]
                wcards += [f"\tctrl->call(f, {func_name}::f0, ctx, {fname}::f{ast_node.jump_f});\n", "\treturn;\n", "}\n"]
                return CppSnippet(wcards)
            if isinstance(ast_node, PseudoAST_PostMultiframeFunCall):
                func = ast_node.funcall.function
                func_name = self.symbol_repo.resolve_symbol(func).full_name
                wcards = []
                if ast_node.result_lhs is not None:
                    wcards += [ "{\n", f"\tauto* f = ctrl->peek<{func_name}>();\n", "\t", self.build(ast_node.result_lhs, prio_build), " = f->return_value;\n", "}\n" ]
                wcards += ["ctrl->pop();\n"]
                return CppSnippet(wcards)
            if isinstance(ast_node, ASTNodes.Expression):
                needs_semicolon = False
                if isinstance(ast_node.parent, ASTNodes.Attr):
                    needs_semicolon = False
                elif (isinstance(ast_node.parent, ASTNodes.If) or isinstance(ast_node.parent, ASTNodes.While)):                    
                    if not (ast_node is ast_node.parent.condition):
                        needs_semicolon = True
                elif not isinstance(ast_node.parent, ASTNodes.Expression):
                    needs_semicolon = True
                if needs_semicolon:                    
                    def prio_expr_build(n):
                        if n is ast_node: return None
                        return self.build(n, prio_build)
                    expr = self.build(ast_node, prio_expr_build)
                    return CppSnippet([expr, ";\n"])
            return None
                
        wcards = [f"inline static void f{component['id']}(void* _ctx, Celesta::ExecutionController* ctrl)\n"]                
        wcontent = [f"auto* ctx = ({fname}*)_ctx;\n"]
        wcontent += [f"goto L_{component['head'].node_id};\n"]
        for node in MultiframeCFG.enumerate_nodes(component['head']):
            wcontent+=[f"L_{node.node_id}:\n"]
            
            if node.node_type=='c':
                cond = self.build(node.ast, prio_build)
                wcontent+=["if(",cond,")\n", f"    goto L_{node.next_nodes[1].node_id}; else goto L_{node.next_nodes[0].node_id};\n"]
            elif node.node_type=='i':
                if node.ast is not None:                    
                    wcontent+=[self.build(node.ast, prio_build), "\n"]
                if len(node.next_nodes)>0:
                    wcontent+=[f"goto L_{node.next_nodes[0].node_id};\n"]
                else:
                    wcontent+="return;\n"
            elif node.node_type=='f':
                wcontent.append(f"ctrl->jump(ctx, {fname}::f{node.data['id']}); return;\n")
            elif node.node_type=='e':
                wcontent.append(f"ctrl->ret(); return;\n")
            else:
                wcontent.append(f"/* Node #{node.node_id} {node.node_type} */")
                
        wcards += ["{\n", CppSnippet(wcontent).indent(), "}\n\n"]
        
        #print(MultiframeCFG.tree2string(component['head']))
    
        return CppSnippet(wcards, self.symbol_repo)
    
    def build(self, ast_node, prio_build=None)->CppSnippet:
        if prio_build is not None:
            prio_result = prio_build(ast_node)
            if prio_result is not None:
                return prio_result
        # print(f"BUILD {type(ast_node)}")
        if isinstance(ast_node, ASTNodes.Block):
            wcontent = []
            for i, child in enumerate(ast_node.children):
                if i>0: wcontent.append("\n")
                #print(f"IN BLOCK: {type(child)}")
                wcontent.append(self.build(child, prio_build))
                if isinstance(child, ASTNodes.Expression):
                    wcontent.append(";")                
                    
            return CppSnippet(wcontent)
            #return "\n".join(map(self.build, ast_node.children))                
            
        if isinstance(ast_node, ASTNodes.Package):
            scope = ast_node.scope
            self.scope_stack.append(scope)
            content = CppSnippet.join("\n", list(map(lambda c: self.build(c, prio_build), ast_node.children)))            
            self.scope_stack.pop()
            comm = f"// package: {scope.get_full_name()}"
            return CppSnippet([comm,f"\nnamespace {ast_node.name}\n{{\n", content.indent(),"\n}\n"], self.symbol_repo)

        if isinstance(ast_node, ASTNodes.FunDecl):                              
            if ast_node.function.is_multiframe:
                if ast_node.function.is_extern:
                    return CppSnippet([f"/* Not Implemented: Extern multiframe functions {ast_node.function} */"])
            
                func = ast_node.function                

                self.symbol_repo.identify_symbol(func, self.generate_symbol_id(func, self.scope_stack[-1], type_suffix="mf", use_sid=False))
                symid = self.symbol_repo.resolve_symbol(func)
                
                vdecls = []
                if len(func.params)>0:
                    vdecls.append("struct\n{\n")
                    for param in func.params:
                        sid = self.verbatim_local_symbol_id(param, f"ctx->params.{param.name}", use_sid=False)
                        self.symbol_repo.identify_symbol(param, sid)
                        vdecls.append(f"    {self.symbol_repo.resolve_symbol(param.data_type).full_name} {param.name};\n")
                    vdecls.append("} params;\n")
                
                if func.return_type != self.dtype_void:
                    sid = CppIdentifier("ctx->return_value")
                    vdecls.append(f"{self.symbol_repo.resolve_symbol(func.return_type).full_name} {sid.name.split('->')[1]};\n")
                
                
                cfg = MultiframeCFG(ast_node)
                cfg.graph.ungroup_ast()
                components = cfg.find_functional_components()
                wcomps = [self.__build_multiframe_component(c, symid.name, vdecls).indent() for c in sorted(components.values(), key=lambda _:_['id'])]
                
                wcards = [f"/* multiframe function {ast_node.function} */\n"]
                wcards += [f"struct {symid.name}\n", "{\n", CppSnippet(vdecls).indent(), *wcomps, "};\n"]
                
                return CppSnippet(wcards, self.symbol_repo)
            else:
                func = ast_node.function
                self.symbol_repo.identify_symbol(func, self.generate_symbol_id(func, self.scope_stack[-1], use_sid=False))
                symid = self.symbol_repo.resolve_symbol(func)
                
                ret_type = "void"
                if func.return_type != self.dtype_void:
                    ret_type = self.symbol_repo.resolve_symbol(func.return_type).full_name                    
                
                vdecls = []
                if len(func.params)>0:                    
                    for param in func.params:
                        sid = self.verbatim_local_symbol_id(param, param.name, use_sid=False)
                        self.symbol_repo.identify_symbol(param, sid)
                        vdecls.append(f"{self.symbol_repo.resolve_symbol(param.data_type).full_name} {param.name}")
                        
                if func.is_extern:
                    wcards = [f"extern {ret_type} {symid.name}({', '.join(vdecls)});\n"]
                    return CppSnippet(wcards, self.symbol_repo)
                        
                wcards = [f"inline {ret_type} {symid.name}({', '.join(vdecls)})\n"]     
                wcards.append("{\n")
                wcards.append(self.build(func.implementation, prio_build).indent())
                wcards.append("}\n")
                
                return CppSnippet(wcards, self.symbol_repo)
                
        if isinstance(ast_node, ASTNodes.Attr):
            left = self.build(ast_node.left, prio_build)
            right = self.build(ast_node.right, prio_build)
            return CppSnippet([left, " = ", right, ";"])
        
        if isinstance(ast_node, ASTNodes.BinaryOperator):            
            tr = self.binop_translator[ast_node.operator]
            left = self.build(ast_node.left, prio_build)
            right = self.build(ast_node.right, prio_build)
            return CppSnippet([tr(left, right)])
            
        if isinstance(ast_node, ASTNodes.Literal):
            # print(ast_node.data_type)
            dt = self.symbol_repo.resolve_symbol(ast_node.data_type).full_name
            return CppSnippet([f"(({dt}){ast_node.value})"])
        
        if isinstance(ast_node, ASTNodes.SymbolTerm):            
            return CppSnippet([self.symbol_repo.resolve_symbol(ast_node.symbol).full_name])
        
        if isinstance(ast_node, ASTNodes.Return):
            if ast_node.value is None: 
                return CppSnippet(["return;\n"])
            return CppSnippet(["return ", self.build(ast_node.value), ";\n"])
        
        
        if isinstance(ast_node, ASTNodes.FunCall):
            symid = self.symbol_repo.resolve_symbol(ast_node.function)
            
            wargs = []
            if len(ast_node.args)>0:
                for arg in ast_node.args:
                    wargs.append(self.build(arg, prio_build))
                    wargs.append(", ")
                wargs.pop()
            
            return CppSnippet([symid.full_name, "(", *wargs, ")"])
        
        if isinstance(ast_node, ASTNodes.VDecl):
            var = ast_node.variable
            sid = self.verbatim_local_symbol_id(var, f"{var.name}", "l")
            self.symbol_repo.identify_symbol(var, sid)
            return CppSnippet([f"{self.symbol_repo.resolve_symbol(var.data_type).full_name} {sid.name};\n" ])
        
        if isinstance(ast_node, ASTNodes.If):
            cond = self.build(ast_node.condition, prio_build)
            then_branch = self.build(ast_node.then_branch, prio_build)
            else_branch = self.build(ast_node.else_branch, prio_build) if ast_node.else_branch is not None else None
            
            wcards = ["if (", cond, ") {\n", then_branch.indent(), "}"]
            if else_branch is not None:
                wcards+= ["else {\n", else_branch.indent(), "}"]
            wcards+="\n"
            return CppSnippet(wcards)
        
        if isinstance(ast_node, ASTNodes.While):
            cond = self.build(ast_node.condition, prio_build)
            block = self.build(ast_node.block, prio_build)
            wcards = ["while (", cond, ") {\n", block.indent(), "}\n"]
            return CppSnippet(wcards)
            
        if isinstance(ast_node, ASTNodes.IndexAccessor):
            indexer = ast_node.indexer            
            ix_builder = self.indexer_archetype_translator[indexer.archetype]            
            element = self.build(ast_node.element, prio_build)
            index = self.build(ast_node.index, prio_build)
            return CppSnippet([ix_builder(element, index)])
        
        if isinstance(ast_node, ASTNodes.StructDecl):
            data_type = ast_node.symbol
            
            if data_type.is_struct and data_type.is_extern:            
                self.symbol_repo.identify_symbol(data_type, self.generate_symbol_id(data_type, self.scope_stack[-1], use_sid=False))
                return CppSnippet(["struct ", self.symbol_repo.resolve_symbol(data_type).name, ";\n"])
            raise NotImplementedError("Not implemented: non-extern struct declaration")
        
        if isinstance(ast_node, ASTNodes.Import):
            return CppSnippet(f"/*{ast_node}; node ignored during this step*/")
        
        raise NotImplementedError(f"/* UNK: {type(ast_node).__name__} */")
        return CppSnippet([f"/* UNK: {type(ast_node).__name__} */"])


class Cels2CppCompiler:
    def __init__(self):
        self.lexer = CelsLexer()
        t1 = time.time()
        self.parser = parser = CelsParser()
        t2 = time.time()
        print(f"Parser initialized in {t2-t1:.4f} seconds.\n")
        
        self.cpp_ctx = cpp_ctx = CppContext()
        cpp_ctx.scope_stack.append(parser.global_scope)
        cpp_ctx.dtype_void = self.parser.dtype_void
        
        cpp_ctx.symbol_repo.identify_symbol(parser.dtype_int, CppIdentifier('int'))
        cpp_ctx.symbol_repo.identify_symbol(parser.dtype_float32, CppIdentifier('float'))
        cpp_ctx.symbol_repo.identify_symbol(parser.dtype_void, CppIdentifier('void'))
        cpp_ctx.symbol_repo.identify_symbol(parser.dtype_bool, CppIdentifier('bool'))
        cpp_ctx.symbol_repo.identify_symbol(parser.dtype_string, CppIdentifier('string'))
                
        
        rbo = parser.op_solver.resolve_binary_operator
        
        cpp_ctx.binop_translator[rbo('+', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " + ", y, ")"])
        cpp_ctx.binop_translator[rbo('-', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " - ", y, ")"])
        cpp_ctx.binop_translator[rbo('*', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " * ", y, ")"])
        cpp_ctx.binop_translator[rbo('/', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " / ", y, ")"])
        cpp_ctx.binop_translator[rbo('%', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " % ", y, ")"])
        cpp_ctx.binop_translator[rbo('>', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " > ", y, ")"])
        cpp_ctx.binop_translator[rbo('<', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " < ", y, ")"])
        cpp_ctx.binop_translator[rbo('==', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " == ", y, ")"])
        cpp_ctx.binop_translator[rbo('!=', parser.dtype_int, parser.dtype_int)] = lambda x,y: CppSnippet(["(", x, " != ", y, ")"])
        
        
        cpp_ctx.indexer_archetype_translator[parser.inarch_array_index] = lambda E, I: CppSnippet([E, "[", I, "]"])
        cpp_ctx.indexer_archetype_translator[parser.ptr_index_inarch] = lambda E, I: CppSnippet([E, "[", I, "]"])
        
    def set_import_solver(self, solver):
        self.parser.import_solver = solver
        
    def build_ast(self, code:str):
        lexer_result = self.lexer.parse(code)
        if not lexer_result['success']:
            raise RuntimeError(lexer_result['error'])
        tokens = lexer_result['tokens']
        
        ast_root = self.parser.parse_tokens(tokens, verbose=False, debug=False)
        return ast_root
        
        
    def compile(self, code:str):
        ast_root = self.build_ast(code)        

        #print(ast_root)
        #return ast_root
                
        res = self.cpp_ctx.build(ast_root)
        #print(f"Res = \n{res}")
        
        return res
