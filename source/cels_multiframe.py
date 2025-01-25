from cels_ast_nodes import ASTNodes, ASTNode
from cels_symbols import FunctionOverload
from utils import IdProvider
from collections import deque

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

    def _ungroup_ast(self, state):
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
                n._ungroup_ast(state)
            return
        if isinstance(self.ast, ASTNodes.While):
            cond = self.ast.condition
            block = self.ast.block
            
            breaks = []
            continues = []
            
            def identify_jumps(node):
                # Do not look into nested loops
                if isinstance(node, ASTNodes.While) and node is not self.ast:
                    return True
                if isinstance(node, ASTNodes.Break):
                    breaks.append(node)
                if isinstance(node, ASTNodes.Continue):
                    continues.append(node)
                return False
            
            self.ast.parse(identify_jumps)

            assert len(self.next_nodes)==1

            n_block = MultiFrameCFGNode(self.idp, block, 'i')
            n_block.next_nodes = [self]

            self.next_nodes.append(n_block)

            self.ast = cond
            self.node_type='c'
            
            for b in breaks: state['break_links'][b] = [self.next_nodes[0]]
            for c in continues: state['continue_links'][c] = [self]

            n_block._ungroup_ast(state)
            return
        if isinstance(self.ast, ASTNodes.Break):            
            self.next_nodes = state['break_links'][self.ast]
            return
        if isinstance(self.ast, ASTNodes.Continue):
            self.next_nodes = state['continue_links'][self.ast]
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

            then_node._ungroup_ast(state)
            if else_node is not None:
                else_node._ungroup_ast(state)
            return
    
    def ungroup_ast(self): 
        state = { 'break_links':{}, 'continue_links':{} }
        return self._ungroup_ast(state)
    

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
        ASTNode.__init__(self)
        self.funcall = funcall
        self.result_lhs = result_lhs
        self.jump_f = None

class PseudoAST_PostMultiframeFunCall(ASTNode):
    def __init__(self, funcall, result_lhs):
        ASTNode.__init__(self)
        self.funcall = funcall
        self.result_lhs = result_lhs

class MultiframeCFG:
    def __init__(self, overload: FunctionOverload):
        assert isinstance(overload, FunctionOverload)
        self.idp = idp = IdProvider()
        self.func = overload
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
            if isinstance(node.ast, ASTNodes.Assign) and isinstance(node.ast.right, ASTNodes.FunOverloadCall) and node.ast.right.function_overload.is_multiframe:
                mffuncalls.append(node)
            elif isinstance(node.ast, ASTNodes.FunOverloadCall) and node.ast.function_overload.is_multiframe:
                mffuncalls.append(node)

        for node in mffuncalls:
            lhs, funcall = None, None
            if isinstance(node.ast, ASTNodes.Assign) and isinstance(node.ast.right, ASTNodes.FunOverloadCall) and node.ast.right.function_overload.is_multiframe:
                lhs = node.ast.left
                funcall = node.ast.right
            elif isinstance(node.ast, ASTNodes.FunOverloadCall) and node.ast.function_overload.is_multiframe:
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
