from __future__ import annotations

PRINT_EPS = "ε"
PRINT_LEFT_ARR = "←"

def set_unicode(value): 
    if value:
        PRINT_EPS = "ε"; PRINT_LEFT_ARR = "←"
    else:
        PRINT_EPS = "eps"; PRINT_LEFT_ARR = "<-"
  
class RuleComponent:
    def __rmul__(self, other:RuleComponent|list[RuleComponent]):
        #print("Here??")
        if isinstance(other, RuleComponent):
            return [other, self]
        if isinstance(other, list):
            return [*other, self]
        raise ValueError("Invalid operand")
  
class Terminal(RuleComponent):
    def __init__(self, value:any, on_match:callable[[any, any], bool] = None): 
        self.value = value
        self.__on_match = on_match if on_match is not None else self.__default_on_match__    
        self.precomputed_hash = hash(self.value)
    def __eq__(self, other)-> bool: return isinstance(other, Terminal) and self.value == other.value
    def __hash__(self): return self.precomputed_hash
    def __str__(self): return repr(self.value)
    def __repr__(self): return f"Terminal<{repr(self.value)}>"
    def __mul__(self, other):  return RuleComponent.__rmul__(other, self)
    
    def match(self, target:any): return self.__on_match(self.value, target)
    
    @staticmethod
    def __default_on_match__(val:any, obj:any)->bool: raise NotImplementedError("Terminal match not implemented")


class NonTerminal(RuleComponent):
    def __init__(self, name): 
        self.name = name
        self.precomputed_hash = hash(self.name)
    def __eq__(self, other)-> bool: return isinstance(other, NonTerminal) and self.name == other.name    
    def __hash__(self): return self.precomputed_hash
    def __str__(self): return self.name
    def __repr__(self): return f"NonTerminal<{self.name}>"
    
    def __mul__(self, other):  return RuleComponent.__rmul__(other, self)
    
    def __lshift__(self, other:RuleComponent | list[RuleComponent]): 
        if isinstance(other, RuleComponent):
            return Rule(self, [other])
        return Rule(self, other)
    
class Epsilon(RuleComponent):
    def __init__(self): self.precomputed_hash = hash("eps")
    def __eq__(self, other)-> bool: return isinstance(other, Epsilon)
    def __hash__(self): return self.precomputed_hash
    def __repr__(self): return PRINT_EPS
    def __str__(self): return PRINT_EPS
    
class RuleComponentFactory:
    def __init__(self, on_match=None):
        self.__on_match = on_match
        self.__terminals = {}
        self.__non_terminals = {}
        self.__epsilon = Epsilon()
    
    def terminal(self, value): 
        if not value in self.__terminals:
            self.__terminals[value] = Terminal(value, self.__on_match)
        return self.__terminals[value]
    
    def non_terminal(self, name):
        if not name in self.__non_terminals:
            self.__non_terminals[name] = NonTerminal(name)
        return self.__non_terminals[name]
    
    def epsilon(self): return self.__epsilon
        

class Rule:
    def __init__(self, lhs:NonTerminal, rhs:list[Terminal|NonTerminal|Epsilon]):
        self.lhs = lhs
        self.rhs = [r for r in rhs if r!=Epsilon()]
        self.__on_build = None
        self.rule_id = -1
        self.precomputed_hash = hash((self.lhs, *self.rhs))
        
    def __repr__(self): return f"Rule<{self.lhs} {PRINT_LEFT_ARR} {' '.join(map(str, self.rhs))}>"
    def __str__(self): return f"{self.lhs} {PRINT_LEFT_ARR} {' '.join(map(str, self.rhs))}"
    
    def on_build(self, f:callable[[list[any]], any]):
        self.__on_build = f
        return self
    
    def process_match(self, children):
        if self.__on_build is None:            
            raise ValueError("Rule build callback not set")
        return self.__on_build(*children)
        
    def __eq__(self, other):
        return isinstance(other, Rule) \
            and self.lhs==other.lhs and self.rhs==other.rhs            
    
    def __hash__(self): return self.precomputed_hash #hash((self.lhs, *self.rhs))

class RuleCallback:
    def __init__(self, fun:callable[[list[any]], any], name="callback"):
        self.__name = name
        self.__fun = fun        
     
    def __repr__(self): return f"RuleCallback[{self.__name}]"
        
    @staticmethod
    def __args_contain_callbacks(args):        
        return any(map(lambda t:isinstance(t, RuleCallback), args))

    def call(self, *args):        
        if self.__args_contain_callbacks(args):
            params = args            
            def f(*args):
                pms = [p.call(*args) if isinstance(p, RuleCallback) else p for p in params]                                
                return self.__fun(*pms)
            return RuleCallback(f, name="internal")        
        if self.__fun is None: raise ValueError("Callback is None")
        return self.__fun(*args)
        
    def apply(self, f): return RuleCallback(f, "apply")(self)
    
    def __call__(self, *args): return self.call(*args)
        
    def __add__(self, other:any): return RuleCallbackSum()(self, other)
    
class RuleCallbackArg(RuleCallback):
    def __init__(self, index):
        def f(*args): return args[index]
        super(RuleCallbackArg, self).__init__(f, name="arg")

class RuleCallbackSum(RuleCallback):
    def __init__(self, default_value=None):
        def f(*args):
            if len(args)==0: return default_value
            s = args[0]
            for i in range(1, len(args)): s = s + args[i]
            return s
        super(RuleCallbackSum, self).__init__(f, name="sum")
        
class RuleCallbackListOf(RuleCallback):
    def __init__(self, *lst):                
        def f(*x): return list(x)
        cb = RuleCallback(f, name="id")(*lst)
        super(RuleCallbackListOf, self).__init__(cb, name="listof")
        
class RuleCallbackCall(RuleCallback):
    def __init__(self, f, *lst):
        def do(*args):
            fun = f(*args) if isinstance(f, RuleCallback) else f            
            g = RuleCallback(fun, name="_icall")(*lst)
            if isinstance(g, RuleCallback): return g(*args)
            return g
        #cb = RuleCallback(f, name="call")(*lst)
        super(RuleCallbackCall, self).__init__(do, name="call")
        
class RuleCallbackSelect(RuleCallback):    
    def __init__(self, source, f):
        def solve(expr, args):
            if isinstance(expr, RuleCallback): return expr(*args)
            return expr
        def do(*args):            
            return f(solve(source, args))
        super(RuleCallbackSelect, self).__init__(do, name="select")

class RuleCallbackSwitch(RuleCallback):
    def __init__(self, query, values:list[tuple[any, any]]):
        def solve(expr, args):
            if isinstance(expr, RuleCallback): return expr(*args)
            return expr    
        def f(*args):
            it = solve(query, args)                   
            v = []
            for x,y in values:
                if solve(x,args) == it: return solve(y, args)
            raise RuntimeError(f"RuleCallback Switch failed: {it} in {values}")
        super(RuleCallbackSwitch, self).__init__(f, name="switch")

class RuleCallbackNoCall(RuleCallback):
    def __init__(self, val):
        super(RuleCallbackNoCall, self).__init__(lambda *args:val, name="nocall")

class Namespace(object): pass

rule_callbacks = Namespace()
rule_callbacks.apply = RuleCallback
rule_callbacks.arg = RuleCallbackArg
rule_callbacks.sum = RuleCallbackSum
rule_callbacks.listof = RuleCallbackListOf
rule_callbacks.call = RuleCallbackCall
rule_callbacks.switch = RuleCallbackSwitch
rule_callbacks.nocall = RuleCallbackNoCall
rule_callbacks.select = RuleCallbackSelect

class IterQuery:
    def __init__(self, collection):
        self.collection = collection
    def map(self, function): 
        self.collection = map(function, self.collection)
        return self
    def filter(self, function): 
        self.collection = filter(function, self.collection)
        return self
    def distinct(self): 
        self.collection = set(self.collection)
        return self
    def select_many(self, function):
        self.collection = [j for i in map(function, self.collection) for j in i]
        return self
    def to_list(self): return list(self.collection)
    def to_set(self): return set(self.collection)

class Prediction1:
    def __init__(self, value, is_value, is_end_of_word, is_empty):
        self.value = value; self.is_value=is_value
        self.is_end_of_word = is_end_of_word; self.is_empty=is_empty        
    
    @staticmethod
    def of(value:Terminal|any): 
        val = value if value is not Terminal else value.value
        return Prediction1(val, True, False, False)
       
    
        
    @staticmethod
    def end_of_word(): return Prediction1Constants.end_of_word
    @staticmethod
    def empty(): return Prediction1Constants.empty
    
    def __repr__(self):
        if self.is_end_of_word: return "$"
        if self.is_empty: return "''"
        return repr(self.value)
    
    def __eq__(self, other):
        return isinstance(other, Prediction1) \
            and self.value == other.value \
            and self.is_value == other.is_value \
            and self.is_end_of_word == other.is_end_of_word \
            and self.is_empty == other.is_empty
    
    def __hash__(self):
        return hash((self.value, self.is_value, self.is_end_of_word, self.is_empty))

class Prediction1Constants:
    end_of_word = Prediction1(None, False, True, False)
    empty = Prediction1(None, False, False, True)

class Grammar:
    def __init__(self, rules: list[Rule], start_symbol: NonTerminal|None = None):
        assert len(rules)>0, "Grammar must contain at least one rule"
        self.rules = rules                
        for i in range(len(self.rules)):
            self.rules[i].rule_id = i
        
        self.start_symbol = start_symbol if start_symbol is not None else rules[0].lhs
        assert any(map(lambda r:r.lhs==self.start_symbol, rules)), "Start symbol must be defined by a rule"
            
        self.non_terminals = IterQuery(self.rules) \
            .map(lambda r:r.lhs).distinct() .to_list()

        #list(set(map(lambda r:r.lhs, self.rules)))
        self.terminals = IterQuery(self.rules) \
            .select_many(lambda r:r.rhs) \
            .filter(lambda it: isinstance(it, Terminal)) \
            .distinct().to_list()        
        
        undefined_non_terminals = IterQuery(self.rules) \
            .select_many(lambda r:r.rhs) \
            .distinct() \
            .filter(lambda c: isinstance(c, NonTerminal) and not c in self.non_terminals) \
            .map(lambda t: t.name) \
            .to_list()
        
        assert len(undefined_non_terminals)==0, f"No rules to define non-terminal symbols: {', '.join(undefined_non_terminals)}"
        
        self._cached_derivations:dict[NonTerminal, list[Rule]] = {}        
        
        self.first1_table: dict[NonTerminal, set[Prediction1]] = {}
        self.__build_first1_table__()
        
        self.follow1_table: dict[NonTerminal, set[Prediction1]] = {}
        self.__build_follow1_table__()

        
    def __build_first1_table__(self):
        self.first1_table.clear()
        for A in self.non_terminals:
            rules = self.get_derivations_of(A)
            self.first1_table[A] = IterQuery(rules) \
                .filter(lambda r:len(r.rhs)>0) \
                .map(lambda r:r.rhs[0]) \
                .filter(lambda c:isinstance(c, Terminal)) \
                .map(Prediction1.of) \
                .to_set()
            if any(map(lambda r:len(r.rhs)==0, rules)):
                self.first1_table[A].add(Prediction1.empty())

        running=True
        while running:
            new_table:dict[NonTerminal, set[Prediction1]] = {}
            for A in self.non_terminals:
                new_table[A] = set()
            for r in self.rules:
                for f1 in self._first1_sequence_(r.rhs):
                    new_table[r.lhs].add(f1)
            running = False
            for A in self.non_terminals:
                if len(self.first1_table[A])!=len(new_table[A]):
                    running=True
                    break
            self.first1_table = new_table
    
    def _first1_sequence_(self, components: list[RuleComponent])->list[Prediction1]:
        S: set[Prediction1] = set()
        for comp in components:
            if isinstance(comp, Terminal):
                S.add(Prediction1.of(comp))
                return list(S)
            if isinstance(comp, NonTerminal):
                f1 = self.first1_table[comp]
                for c in f1:
                    if not c.is_empty:
                        S.add(c)
                if not Prediction1.empty() in f1:
                    return list(S)
        S.add(Prediction1.empty())
        return list(S)
        
    def __build_follow1_table__(self):
        for A in self.non_terminals:
            self.follow1_table[A] = set()
        self.follow1_table[self.start_symbol].add(Prediction1.end_of_word())
        newly_added = 1
        while newly_added>0:
            newly_added = 0
            for rule in self.rules:
                A = rule.lhs
                for i in range(len(rule.rhs)):
                    if isinstance(rule.rhs[i], NonTerminal):
                        B = rule.rhs[i]
                        beta = rule.rhs[i+1:]
                        first1Beta = self._first1_sequence_(beta)
                        for p in first1Beta:
                            if p.is_empty: continue
                            if not p in self.follow1_table[B]:
                                newly_added+=1
                                self.follow1_table[B].add(p)
                        if Prediction1.empty() in first1Beta:
                            for p in self.follow1_table[A]:
                                if not p in self.follow1_table[B]:
                                    newly_added+=1
                                    self.follow1_table[B].add(p)
    

    def get_derivations_of(self, n:NonTerminal):
        if not n in self._cached_derivations:
            self._cached_derivations[n] = [r for r in self.rules if r.lhs==n]
        return self._cached_derivations[n]        
        #return [r for r in self.rules if r.lhs==n] #IterQuery(self.rules).filter(lambda r:r.lhs==n).to_list()
    
    def __str__(self): return '\n'.join(map(str, self.rules))
    
    def checksum(self):
        return len(self.rules)
        
    def get_terminal_by_value(self, value, comp=None):
        comp = comp or (lambda x,y: x==y)
        candidates = [t for t in self.terminals if comp(t.value, value)]
        return candidates[0]
    
    def get_nonterminal_by_name(self, name):        
        candidates = [n for n in self.non_terminals if n.name==name]
        return candidates[0]