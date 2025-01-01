from __future__ import annotations
from grammar import RuleComponent, NonTerminal, Terminal, Rule, Grammar, Prediction1

class AnalysisElement:
    def __init__(self, rule:Rule, dot_position:int, u_predictions:list[Prediction1]):
        assert 0<=dot_position<=len(rule.rhs), f"Invalid dot position: {dot_position} (rule length is {len(rule.rhs)})"
        self.rule = rule
        self.dot_position = dot_position
        self.u_predictions = list(u_predictions)
        self.is_dot_at_end = self.dot_position==len(self.rule.rhs)
        self.precomputed_hash = hash((self.rule, self.dot_position, *self.u_predictions))
        self.after_dot = self.rule.rhs[self.dot_position] if not self.is_dot_at_end else None
    
    def get_after_dot(self)->RuleComponent|None: 
        return self.after_dot
    
    def advance_dot(self):
        return AnalysisElement(self.rule, self.dot_position+1, self.u_predictions)
    
    def __eq__(self, other):
        return isinstance(other, AnalysisElement) \
            and self.rule==other.rule \
            and self.dot_position == other.dot_position \
            and self.u_predictions == other.u_predictions
    
    def __hash__(self): return self.precomputed_hash
    
    def __view_as_string(self):
        r = f"{self.rule.lhs} -> "
        for i in range(len(self.rule.rhs)):
            if self.dot_position==i: r+=". "
            r += f"{self.rule.rhs[i]} "
        if self.is_dot_at_end: r+=". "
        return f"[{r}, {' '.join(map(str, self.u_predictions))}]"
    
    def __repr__(self): return self.__view_as_string()

class CanonicalCollectionNode:
    def __init__(self, grammar:Grammar, _id:int, elements:list[AnalysisElement]):
        self.grammar = grammar
        self.nid = _id
        self.elements = set(elements)
        self.closure: list[AnalysisElement] = []
        self.elements_hash = sum(map(hash, self.elements))
        self.precomputed_hash = hash(self.nid)+self.elements_hash
    
    def get_transitions(self):        
        it = map(lambda _:_.get_after_dot(), self.closure)
        it = filter(lambda _:_ is not None, it)
        return set(it)
    
    def is_equivalent_to(self, other:CanonicalCollectionNode):
        return self.elements_hash == other.elements_hash and self.elements == other.elements
        #intersect_cnt = len(self.elements.intersection(other.elements))
        #return intersect_cnt == len(self.elements) == len(other.elements)
    
    def __eq__(self, other):
        return isinstance(other, CanonicalCollectionNode) and \
            self.nid == other.nid and \
            self.elements == other.elements
    
    def __hash__(self): return self.precomputed_hash #hash((self.nid, *self.elements))
    
    def __str__(self): 
        sep = '\n    '        
        return f"I{self.nid}{sep}{sep.join(map(str,self.elements))}"
    
class CanonicalCollection: 
    def __init__(self, 
        grammar:Grammar, 
        build_closure:callable[[Grammar, CanonicalCollectionNode], None],
        goto: callable[[CanonicalCollectionNode, RuleComponent], CanonicalCollectionNode],
        first_element: callable[[Grammar, AnalysisElement], None]
     ):
        self.grammar = grammar
        self.build_closure = build_closure
        self.goto = goto
        self.states:list[CanonicalCollectionNode] = []
        self.transitions:dict[tuple[CanonicalCollectionNode, RuleComponent], CanonicalCollectionNode] = {}
        self.transitions_count = 0
        
        io = CanonicalCollectionNode(self.grammar, 0, [first_element(self.grammar)])
        self.states.append(io)
        
        self.build_closure(self.grammar, io)
        
        tr_count = self.transitions_count
        st_count = 0
        
        while tr_count!=self.transitions_count or st_count!=len(self.states):
            tr_count = self.transitions_count
            st_count = len(self.states)
            
            for node in self.states:
                for X in node.get_transitions():
                    new_node = self.__get_or_create(self.goto(node, X))
                    if not (node, X) in self.transitions:
                        self.transitions[(node, X)] = new_node
                        self.transitions_count+=1
                    else:
                        if new_node!=self.transitions[(node,X)]:
                            raise ValueError("Invalid transition? (different nodes for same transition)")
                    
    def __get_or_create(self, state:CanonicalCollectionNode)->CanonicalCollectionNode:        
        #equiv = list(filter(lambda _:_.is_equivalent_to(state), self.states))
        equiv = list(filter(state.is_equivalent_to, self.states))
        if len(equiv)==0:
            new_state = CanonicalCollectionNode(self.grammar, len(self.states), state.elements)
            self.states.append(new_state)
            self.build_closure(self.grammar, new_state)
            return new_state
        return equiv[0]
        
    def __str__(self):        
        res = ""
        for s in self.states: res+=f"{str(s)}\n"
        for (node, X), nxt in self.transitions.items():
            res+=f"(I{node.nid}, {X}) -> I{nxt.nid}\n"
        return res


class LR1CanonicalCollection(CanonicalCollection):
    @staticmethod
    def __build_closure(g:Grammar, node:CanonicalCollectionNode):
        tmp_elems = set(node.elements)
        new_elems = []
        
        while True:
            for elem in tmp_elems:
                nxt = elem.get_after_dot()
                if nxt is None: continue
                if not isinstance(nxt, NonTerminal): continue
                beta = set()
                beta.update(g._first1_sequence_(elem.rule.rhs[elem.dot_position+1:]))
                if len(beta)==0 or Prediction1.empty() in beta:                    
                    beta.update(elem.u_predictions)                
                beta = [p for p in beta if p!=Prediction1.empty()]
                
                for rule in g.get_derivations_of(nxt):
                    for b in beta:                        
                        a_elem = AnalysisElement(rule, 0, [b])
                        if not a_elem in tmp_elems:
                            new_elems.append(a_elem)
            tmp_elems.update(new_elems)
            # tmp_elems = tmp_elems + new_elems
            
            #print("____________________________")
            #for e in new_elems: print(e)
                
            if len(new_elems)==0: break
            new_elems.clear()
        node.closure = tmp_elems
    
    @staticmethod
    def __goto(n:CanonicalCollectionNode, r:RuleComponent):        
        elems = filter(lambda a:a.get_after_dot()==r, n.closure)
        elems = list(map(lambda _:_.advance_dot(), elems))
        return CanonicalCollectionNode(n.grammar, -1, elems)
        
    @staticmethod
    def __first_element(g:Grammar):
        return AnalysisElement(g.rules[0], 0, [Prediction1.end_of_word()])
    
    def __init__(self, grammar:Grammar):
        CanonicalCollection.__init__(self, grammar, self.__build_closure, self.__goto, self.__first_element)


class LR1AnalysisTable:
    class TableColumn:
        def __init__(self, component: RuleComponent|None):
            self.component = component
            self.is_end_of_word = component is None
            self.precomputed_hash = hash(self.component)
        
        @staticmethod
        def of(val: RuleComponent|Prediction1):
            if isinstance(val, RuleComponent):
                return LR1AnalysisTable.TableColumn(val)
            if isinstance(val, Prediction1):
                comp = None if val.is_end_of_word else val.value
                return LR1AnalysisTable.TableColumn(comp)
            #print(val, type(val),RuleComponent, issubclass(type(val), RuleComponent))
            raise ValueError("Could not create TableColumn")
        
        @staticmethod
        def end_of_word(): return LR1AnalysisTable.TableColumn(None)
        
        def __str__(self): return "$" if self.is_end_of_word else str(self.component)
        def __repr__(self): return f"<TableColumn {str(self)}>"
        def __eq__(self, other):
            return isinstance(other, LR1AnalysisTable.TableColumn) and self.component == other.component
        def __hash__(self): return self.precomputed_hash #hash(self.component)
    
    class TableItem:
        def __init__(self, type_:str, value:int):
            self.type_ = type_
            self.value = value
            self.is_shift = self.type_=='s'
            self.is_reduce = self.type_=='r'
            self.is_accepted = self.type_=='a'
            self.precomputed_hash = hash((self.type_, self.value))
        
        @staticmethod 
        def shift(value): return LR1AnalysisTable.TableItem("s", value)
        @staticmethod
        def reduce(value): return LR1AnalysisTable.TableItem("r", value)
        @staticmethod
        def accepted(): return LR1AnalysisTable.TableItem("a", -1)
        def __eq__(self, other):
            return isinstance(other, LR1AnalysisTable.TableItem) and self.type_==other.type_ and self.value==other.value
        def __hash__(self): return self.precomputed_hash
        def __str__(self): return self.type_ + (str(self.value) if self.value>=0 else "")
        def __repr__(self): return f"TableItem<{str(self)}>"
    
    def __init__(self, grammar:Grammar, path:str=None):
        from time import time
        
        self.table:dict[tuple[int, LR1AnalysisTable.TableColumn], set[LR1AnalysisTable.TableItem]] = {}
        
        self.grammar = grammar
        
        if path is not None:
            if self.load(path, grammar):
                return

        self.cc = LR1CanonicalCollection(grammar)

        # shift
        for state, sym in self.cc.transitions.keys():                  
            key = (state.nid, LR1AnalysisTable.TableColumn.of(sym))
            self.__add_to_table(key, LR1AnalysisTable.TableItem.shift(self.cc.transitions[(state, sym)].nid))
        
        # reduce/acc
        for state in self.cc.states:
            for elem in state.closure:
                if not elem.is_dot_at_end: continue
                sym = elem.u_predictions[0]
                if sym.is_end_of_word and elem.rule.lhs == grammar.start_symbol:                    
                    key = (state.nid, LR1AnalysisTable.TableColumn.of(sym))
                    self.__add_to_table(key, LR1AnalysisTable.TableItem.accepted())
                elif sym.is_end_of_word or not sym.is_empty:
                    key = (state.nid, LR1AnalysisTable.TableColumn.of(sym))
                    self.__add_to_table(key, LR1AnalysisTable.TableItem.reduce(elem.rule.rule_id))
        
        if path is not None:
            self.save(path)
        
        print(f"TABLE SIZE = {len(self.table)}")
    
    def save(self, path:str):
        print(list(self.table.items())[:20])
        lines = []
        lines.append(str(self.grammar.checksum())+"\n")
        with open(path, 'w') as f:
            f.writelines(lines)
            for key, value in self.table.items():
                n, tcol = key
                
                if tcol.component is None: tcol = 'e $'
                else:
                    if isinstance(tcol.component, Terminal):
                        tcol = 't ' + str(tcol.component.value)
                    elif isinstance(tcol.component, NonTerminal):
                        tcol = 'n ' + tcol.component.name
                    else:
                        raise RuntimeError("Analysis table serialization failed")
                v = ' '.join([str(val) for val in value])
                
                f.writelines(f"{n} {tcol} {v}\n")
        
    def load(self, path:str, grammar:Grammar):
        with open(path, 'r') as f:
            lines = f.read().splitlines()
            if lines[0]!=str(grammar.checksum()):
                print("LR1 load: Wrong checksum, outdated grammar")
                return False
                #raise RuntimeError("Failed to load analysis table: wrong checksum")
            
            for line in lines[1:]:
                L = line.strip()
                if L=="": continue
                L = line.split()
                n, t, v = L[:3]
                
                if t=='n': t = grammar.get_nonterminal_by_name(v)
                elif t=='t': t = grammar.get_terminal_by_value(v)
                elif t=='e': t = Prediction1.end_of_word()
                else: raise RuntimeError(f"Invalid component type: {t}")
                
                items = []
                for it in L[3:]:
                    if it=='a': items.append(LR1AnalysisTable.TableItem.accepted())
                    elif it.startswith('r'): items.append(LR1AnalysisTable.TableItem.reduce(int(it[1:])))
                    elif it.startswith('s'): items.append(LR1AnalysisTable.TableItem.shift(int(it[1:])))
                    else: raise RuntimeError(f"Invalid table item: {it}")
                
                key = (int(n), LR1AnalysisTable.TableColumn.of(t))
                for it in items:
                    self.__add_to_table(key, it)
            
            return True
        
    def __add_to_table(self, key:tuple[int, LR1AnalysisTable.TableColumn], item:TableItem):
        if not key in self.table: self.table[key] = set()
        self.table[key].add(item)
        
    def pretty_print(self):
        TC = LR1AnalysisTable.TableColumn        
        columns = list(map(TC.of, self.grammar.non_terminals))
        columns += list(map(TC.of, self.grammar.terminals))
        columns.append(TC.end_of_word())
        disp_columns = [""] + list(map(str, columns))
        
        rows = []
        col_len = list(map(len, disp_columns))            
        
        for state in self.cc.states:
            row = [f"I{state.nid}"] 
            col_len[0] = max(col_len[0], len(row[0]))
            for i, c in enumerate(columns):                
                key = (state.nid, c)                
                if not key in self.table: row.append("")
                else: row.append(', '.join(map(str,  self.table[key])))
                col_len[i+1] = max(col_len[i+1], len(row[i+1]))
            rows.append(row)
        
        result = ""
                
        for row in [disp_columns, *rows]:            
            line = ""
            for content, length in zip(row, col_len):
                line += " | " + content.ljust(length, " ")
            result+=line+" |\n"
        
        print(result)
        
    
    def find_conflicts(self)-> list[tuple[list[Rule], LR1AnalysisTable.TableColumn, str]]:
        def item2text(it):
            if it.is_shift: return "shift"
            if it.is_reduce: return "reduce"
            if it.is_accepted: return "acc"
            print(it)
            raise ValueError("Item if not shift/reduce/acc")
        
        def mapper(kv):
            k,v = kv
            rules = list(set(map(lambda _:_.rule, self.cc.states[k[0]].elements)))
            col = k[1]
            val = '/'.join(map(item2text, v))            
            return rules, col, val            
    
        it = filter(lambda _:len(_[1])>1, self.table.items()) # list[(k,[v1, v2, ...])]
        it = map(mapper, it)
        return list(it)
    
    def __getitem__(self, key:tuple[int, RuleComponent|None]):
        state, pred = key
        TC = LR1AnalysisTable.TableColumn
        pred = TC.of(pred) if pred is not None else TC.end_of_word()
        key = (state, pred)
        if key in self.table: return list(self.table[key])
        return []

class LR1Parser:
    def __init__(self, grammar:Grammar, path:str=None):
        self.grammar = grammar
        self.analysis_table = LR1AnalysisTable(self.grammar, path)
        self.__test_for_conflicts()
        
    def __test_for_conflicts(self):
        conflicts = self.analysis_table.find_conflicts()
        if len(conflicts)>0:
            print("Conflicts found:", conflicts)
            raise RuntimeError("Conflicts in LR1 analysis table")
    
    def parse_tokens(self, tokens:list[any], tk2term:callable[[any], Terminal],
        verbose:bool=False):
        work_stack = [0]
        out_stack = []
        tk_pos = 0
        
        class StackRuleComponent:
            def __init__(self, r:RuleComponent, value=None):
                self.component = r
                self.value = value    
            def __str__(self): return f"[{self.component}|{self.value}]"
        
        def get_next_action(s:RuleComponent|None)->LR1AnalysisTable.TableItem:
            work_top = work_stack[-1]            
            # print(work_top, s)
            if not isinstance(work_top, int): return None            
            nxt = self.analysis_table[work_top, s]
            if len(nxt)==0: return None
            return nxt[0]
        
        def push(s:StackRuleComponent|None)->LR1AnalysisTable.TableItem:            
            nxt = get_next_action(s.component) if s is not None else None
            if nxt is None: return None
            if not nxt.is_shift: return None
            work_stack.append(s)
            work_stack.append(nxt.value)
            return nxt
        
        def pop(N:int)->list[RuleComponent]|None:
            if len(work_stack)<2*N-1: return None
            poped = []
            for i in range(2*N,0,-1):
                it = work_stack[-1]
                work_stack.pop()                                     
                if isinstance(it, StackRuleComponent):                     
                    poped.append(it.value)
            return poped[::-1]
        
        def do_shift()->LR1AnalysisTable.TableItem:
            nonlocal tk_pos            
            c = StackRuleComponent(tk2term(tokens[tk_pos]), tokens[tk_pos]) if tk_pos<len(tokens) else None
            push_result = push(c)
            if push_result is None: return None
            if tk_pos<len(tokens): tk_pos += 1
            return push_result
            
        def do_reduce()->LR1AnalysisTable.TableItem:           
            c = tk2term(tokens[tk_pos]) if tk_pos<len(tokens) else None
            nxt = get_next_action(c)
            if nxt is None or not nxt.is_reduce: return None
            rule = self.grammar.rules[nxt.value]
            poped = pop(len(rule.rhs))
            if poped is None: return None
                        
            attributes = list(map(lambda _:_.value if isinstance(_, NonTerminal) else _, poped))            
            if push(StackRuleComponent(rule.lhs, rule.process_match(attributes))) is None:
                for p in poped: push(p)
                return None
            out_stack.append(rule.rule_id)
            return nxt
        
        def do_accept():
            #c = StackRuleComponent(tk2term(tokens[tk_pos]), tokens[tk_pos]) if tk_pos<len(tokens) else None
            c = tk2term(tokens[tk_pos]) if tk_pos<len(tokens) else None
            nxt = get_next_action(c)
            if nxt is None or not nxt.is_accepted: return None
            return nxt
        
        def do_next() -> str:            
            n = do_shift(); 
            if n is not None: return str(n)
            n = do_reduce(); 
            if n is not None: return str(n)
            n = do_accept(); 
            if n is not None: return str(n)
            return "err"
                
        try:
            output = None
            while True:            
                if verbose:                
                    res = f"({''.join(map(str, work_stack))}; "
                    res += f"{','.join(map(str, tokens[tk_pos:]))}$; "
                    res += f"{','.join(map(str, out_stack[::-1]))}; "
                    res += f") |-"
                    print(res, end="")
                r = do_next()
                if verbose: print(r)
                if r=='err' or r=='a':
                    break
        except Exception as e:
            return {
                'success': False,
                'message': f'Parse failed at {tokens[tk_pos].row}:{tokens[tk_pos].col} (near `{tokens[tk_pos].value}`): {str(e)}',
                'error': e
            }            
            
        if r=="err":        
            if tk_pos>=len(tokens):
                return {
                    'success': False,
                    'message': f'Unexpected end of input'
                }            
            return {
                'success': False,
                'message': f'Parse failed at {tokens[tk_pos].row}:{tokens[tk_pos].col}: Unexpected token `{tokens[tk_pos].value}`'
            }            
        if r=="a":                
            result = work_stack[-2].value
            return {
                'success': True,
                'value': result
            }
