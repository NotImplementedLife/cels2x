from __future__ import annotations
from utils import ensure_type, indent

class Symbol:
    def __init__(self, name:str, scope:Scope):
        self._name:str = ensure_type(name, str)
        self._scope:Scope = ensure_type(scope, Scope)
        self._full_name = self._scope.get_full_name() + self._scope._sp.separator + self._name
        self._hash_code = hash(self._full_name)
        self._metadata = {}
        
    def get_full_name(self): return self._full_name
    
    @property
    def metadata(self): return self._metadata
    
    @property
    def name(self): return self._name
    
    @property
    def scope(self): return self._scope
    
    def __str__(self): return self.get_full_name()
    
    def __eq__(self, other): return isinstance(other, type(self)) and self._full_name==other._full_name
    def __hash__(self): return self._hash_code
    
    def is_in_scope(self, scope:Scope):
        s = self.scope
        while s is not None and s!=scope:
            s = s.parent
        return s is not None


class ScopeResolveStrategy:
    CREATE        = ["CREATE"]
    GET           = ["GET"]
    GET_OR_CREATE = GET + CREATE    
    

class ScopeException(Exception):
    def __init__(self, message):
        super(ScopeException, self).__init__(message)

class SeparatorProvider:
    def __init__(self, separator:str):
        self._separator = separator
    
    @property
    def separator(self): return self._separator
   
    _Default_instance = None
    
    @staticmethod
    def Default():        
        if SeparatorProvider._Default_instance is None:
            SeparatorProvider._Default_instance = SeparatorProvider('::')
        return SeparatorProvider._Default_instance    

class Scope:
    def __init__(self, name: str, parent:Scope|None, separator_provider:SeparatorProvider|None=None):
        self._name:str = ensure_type(name, str)
        self._parent:Scope|None = ensure_type(parent, Scope, None)
        self._sp = separator_provider or (parent._sp if parent is not None else None)
        if self._sp is None:
            self._sp = SeparatorProvider.Default()
        self._visible_scopes:set[Scope] = set()
        self._symbol_aliases:dict[str, Scope] = {}        
        self._child_scopes:list[Scope] = []
        self._child_symbols:list[Symbol] = []
        
        self._full_name = self._sp.separator.join(self.get_full_path())
        self._hash_code = hash(self._full_name)
        
        self._associated_symbol = None
        
        self._metadata:dict = {}
    
    @property
    def metadata(self): return self._metadata

    @property
    def associated_symbol(self): return self._associated_symbol
    
    @associated_symbol.setter
    def associated_symbol(self, value:Symbol): self._associated_symbol = ensure_type(value, Symbol)

    @property
    def name(self): return self._name
    
    @property
    def parent(self): return self._parent
    
    def __str__(self): return self.get_full_name()
    
    def __eq__(self, other):
        return isinstance(other, Scope) and other.get_full_name()==self.get_full_name()
    
    def __hash__(self): return self._hash_code
    
    def get_full_path(self)->list[str]:
        path = []
        scope = self        
        while scope is not None:
            path.append(scope.name)
            scope = scope.parent
        return path[::-1]
    
    def get_full_name(self)->str: return self._full_name        
        
    def _get_subscope_helper(self, path: list[str], index:int, strategy:list[str])->Scope|None:   
        separator = self._sp.separator
        strat_get = ScopeResolveStrategy.GET[0] in strategy
        strat_create = ScopeResolveStrategy.CREATE[0] in strategy
        
        if index==len(path): return self
        
        scope_candidates = [scope for scope in self._child_scopes if scope.name==path[index]]
        
        if len(scope_candidates)==0:
            if strat_create:
                new_scope = Scope(name=path[index], parent=self)
                self._child_scopes.append(new_scope)
                return new_scope._get_subscope_helper(path, index+1, strategy)
            raise ScopeException(f"Scope does not exist: {self.get_full_name()}{separator}{path[index]}")
        
        elif len(scope_candidates)==1:
            if strat_get:
                return scope_candidates[0]._get_subscope_helper(path, index+1, strategy)
            raise ScopeException(f"Scope already exists: {scope_candidates[0].get_full_name()}")
        else:
            raise ScopeException(f"Duplicate scope definition: {self.get_full_name()}{separator}{path[index]}")
        
        
    def get_subscope(self, path:str|list[str], strategy:str=ScopeResolveStrategy.GET_OR_CREATE):
        separator = self._sp.separator
        if isinstance(path, str):
            path = path.split(separator)
        ensure_type(path, list)
        return self._get_subscope_helper(path, 0, strategy)    
        
    def add_visible_scope(self, scope:Scope):
        self._visible_scopes.add(scope)
    
    def add_symbol(self, symbol_creator: callable[[Scope], Symbol])->Symbol:
        symbol = symbol_creator(self)
        if any(map(lambda s:s.name==symbol.name, self._child_symbols)):
            raise ScopeException(f"Duplicate symbol: {symbol.name} under {self.get_full_name()}")        
        self._child_symbols.append(symbol)
        return symbol
    
    def _resolve_symbol_helper(self, path:list[str], index:int):
        if index==len(path): return self
        if index==len(path)-1:
            candidate_symbols = [sym for sym in self._child_symbols if sym.name==path[index]]
            if len(candidate_symbols)==0:
                return []
            return candidate_symbols
        
        candidate_scopes = [scope for scope in self._child_scopes if scope.name==path[index]]
        if len(candidate_scopes)==0:
            return []
        return candidate_scopes[0]._resolve_symbol_helper(path, index+1)
    
    def try_resolve_immediate_symbol(self, name:str)->Symbol|None:
        ensure_type(name, str)
        separator = self._sp.separator
        
        candidate_symbols = []
        for symbol in self._child_symbols:
            if symbol.name==name:
                candidate_symbols.append(symbol)
        
        candidate_symbols = list(set(candidate_symbols))
        
        if len(candidate_symbols)==0:
            return None            
        
        if len(candidate_symbols)>1:
            sym_name = self._sp.separator.join(path)
            matches = ", ".join(map(str, candidate_symbols))
            raise ScopeException(f"Ambiguous symbol {sym_name}. Found matches: {matches}")
        return candidate_symbols[0]
        
    
    def resolve_symbol(self, path:str|list[str]):
        separator = self._sp.separator
        if isinstance(path, str):
            path = path.split(separator)
        ensure_type(path, list)
        
        candidate_symbols = []
        # Look in current scope
        scope = self
        while len(candidate_symbols)==0 and scope is not None:
            candidate_symbols += scope._resolve_symbol_helper(path, 0)
            scope = scope.parent
        
        # Look in visible scopes
        for vscope in self._visible_scopes:
            candidate_symbols += vscope._resolve_symbol_helper(path, 0)
        
        candidate_symbols = list(set(candidate_symbols))
        
        if len(candidate_symbols)==0:
            sym_name = self._sp.separator.join(path)
            raise ScopeException(f'Symbol could not be identified: {sym_name} under {self.get_full_name()}')
        
        if len(candidate_symbols)>1:
            sym_name = self._sp.separator.join(path)
            matches = ", ".join(map(str, candidate_symbols))
            raise ScopeException(f"Ambiguous symbol {sym_name}. Found matches: {matches}")
        return candidate_symbols[0]
        
    def enumerate_subscopes(self):
        for scope in self._child_scopes:
            yield scope
        
    def enumerate_symbols(self, recursive=False):
        for symbol in self._child_symbols:
            yield symbol        
        if not recursive: return
        for scope in self._child_scopes:
            for symbol in scope.enumerate_symbols(True):
                yield symbol
    
    def to_str_recursive(self, mode:str='list'): # mode in ['tree', 'list']
        result = ""
        if mode=='tree':
            if self.parent is None: result+="[Root] "
            result += self.name
        else: 
            result += self.get_full_name() + (" [Root]" if self.parent is None else "")
        
        for scope in self._child_scopes:
            if mode=='tree':
                result += "\n"+indent(scope.to_str_recursive(mode=mode), nspaces=3)
            else:
                result += "\n"+scope.to_str_recursive(mode=mode)
            
        for symbol in self._child_symbols:
            if mode=='tree':
                result += "\n" + indent(symbol.name + f" [{type(symbol).__name__}]")
            else:
                result += "\n" + symbol.get_full_name() + f" [{type(symbol).__name__}]"
            
        return result

class ScopeStack:
    def __init__(self, global_scope:Scope):
        self._global_scope = ensure_type(global_scope, Scope)
        self.stack = [self._global_scope]
        
    def push(self, name:str, strategy=ScopeResolveStrategy.CREATE):
        peek = self.stack[-1]
        new_scope = peek.get_subscope(name, strategy=strategy)
        self.stack.append(new_scope)
        return new_scope
    
    def peek(self)->Scope: return self.stack[-1]
    
    def pop(self)->Scope:
        if len(self.stack)==1:
            raise RuntimeError("Pop called when only the global scope was left in the stack")
        scope = self.stack[-1]
        self.stack.pop()
        return scope

class ScopeNameProvider:
    def __init__(self):
        self.counter=0
    
    def new_name(self):
        self.counter+=1
        return f"@{self.counter}"