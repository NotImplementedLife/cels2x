class Symbol:
    def __init__(self, name, symbol_data, scope=None):
        self.name = name
        self.symbol_data = symbol_data
        self.scope = scope        
        self.associated_scope = None
    
    def get_full_name(self):
        return self.scope.get_full_name()+"::"+self.name
    
    def __str__(self): return f'<Symbol {self.get_full_name()}, symbol_data={self.symbol_data if self.symbol_data!=self else "<self>"}>'
        
        
class ScopeError(Exception):
    def __init__(self, message):
        super(ScopeError, self).__init__(message)
        self.message = message

class ScopeNode:
    def __init__(self, name, parent=None, children=None):
        self.name = name
        self.parent = parent
        self.children:list[ScopeNode] = [] if children is None else children
        self.symbols:list[Symbol] = []
        self.symbolic_value = None
        self.properties = {}
        
    def set_symbolic_value(self, symbol_provider):         
        self.symbolic_value = symbol_provider(self.parent) 
        self.symbolic_value.associated_scope = self
        
    def get_full_name(self):
        n = self.name
        s = self.parent        
        while s is not None:
            n = f"{s.name}::{n}"
            s = s.parent            
        return n
        
    def get_path(self):
        if self.parent is None: return [self.name]
        p = self.parent.get_path()
        p.append(self.name)
        return p
        
    def find_property(self, key):
        # print("Find:", self.get_full_name(), self.properties)
        if key in self.properties: return self.properties[key]
        if self.parent is None: return None
        return self.parent.find_property(key)

    def get_scope(self, name, strategy="create"): # "create", "get", "get_or_create"
        scope_search = list(filter(lambda s:s.name==name, self.children))
        if len(scope_search)>0: 
            if strategy=="get" or strategy=="get_or_create":                
                return scope_search[0]
            raise ScopeError(f"Scope `{name}` already exists under `{self.get_full_name()}`")
        if strategy=="create" or strategy=="get_or_create":
            if name in map(lambda s:s.name, self.symbols):
                raise ScopeError(f"Duplicate identifier: A scope cannot have the same name as a symbol: {name} in {self.get_full_name()}")
            scope = ScopeNode(name, parent=self)
            self.children.append(scope)
            return scope
        raise ScopeError(f"Scope `{name}` does not exist under `{self.get_full_name()}`")
        
    def add_symbol(self, name, data):
        if name in map(lambda s:s.name, self.children):
            raise ScopeError(f"Duplicate identifier: A symbol cannot have the same name as a scope: {name} in {self.get_full_name()}")
        if name in map(lambda s:s.name, self.symbols):
            raise ScopeError(f"Duplicate identifier: There are two symbols named {name} in {self.get_full_name()}")        
        if callable(data):
            symbol = data(self)
        else:
            symbol = Symbol(name, data, self)
        self.symbols.append(symbol)
        return symbol
    
    def parse(self, action, filter_=None): # filter_ in ['symbols', 'scopes']
        if filter_ is None or filter_=='scopes':
            action(self)
        if filter_ is None or filter_=='symbols':
            for s in self.symbols: action(s)
        for c in self.children: c.parse(action)
           
    def __resolve_symbol(self, path:list[str], ix):                        
        if ix == len(path)-1:
            scope_search = list(filter(lambda s:s.name==path[ix], self.children))
            if len(scope_search)>0:
                scope = scope_search[0]
                if scope.symbolic_value is None:
                    raise ValueError(f"Invalid identifier {path[ix]} in {self.get_full_name()}: is is a scope but not a symbol")
                return scope.symbolic_value
        
            sym_search = list(filter(lambda s:s.name==path[ix], self.symbols))
            if len(sym_search)==0:
                raise ScopeError(f'Identifier not found: {path[ix]} in {self.get_full_name()}')
            return sym_search[0]
        scope_search = list(filter(lambda s:s.name==path[ix], self.children))
        if len(scope_search)==0:
            str_path = '::'.join(path)
            raise ScopeError(f'Identifier not found: {path[ix]} in {self.get_full_name()}')
        return scope_search[0].__resolve_symbol(path, ix+1)            
        
    def resolve_symbol(self, path:str|list[str], recursive:bool=True):
        if isinstance(path, str): path = path.split('::')
        if len(path)==0: raise ValueError('Invalid scope path: scope path was empty')
        if not recursive:                        
            return self.__resolve_symbol(path, 0)
        else:
            first = path[0]
            node = self
            while node is not None:                
                sym_search = list(filter(lambda s:s.name==first, node.symbols))
                if len(sym_search)>0:
                    return sym_search[0]
                scope_search = list(filter(lambda s:s.name==first, node.children))                
                # print("Enter", node.get_full_name(), list(map(lambda _:_.name, node.children)), scope_search, first)
                if len(scope_search)>0:
                    return node.__resolve_symbol(path, 0)
                node = node.parent
            raise ScopeError(f"Could not resolve symbol: {'::'.join(path)}, in scope {self.get_full_name()}")        
            
        
    
class ScopeTree:
    def __init__(self):
        self.global_scope = ScopeNode("global")
    
    def __str__(self):
        res=""
        def write(s):
            nonlocal res
            metadata = ""
            if isinstance(s, Symbol): metadata = f' (sym:{type(s)})'
            if isinstance(s, ScopeNode) and s.symbolic_value is not None:
                metadata = f' symval:{type(s.symbolic_value)}'
            res+=s.get_full_name()+ metadata + "\n"                
        self.global_scope.parse(write)
        return res
    
class ScopeStack:
    def __init__(self, scope_tree:ScopeTree):
        self.scope_tree = scope_tree
        self.global_scope = self.scope_tree.global_scope
        self.stack = [self.global_scope]
        
    def push(self, name:str, strategy='create'):
        peek = self.stack[-1]
        new_scope = peek.get_scope(name, strategy=strategy)
        self.stack.append(new_scope)
        return new_scope
    
    def peek(self)->ScopeNode: return self.stack[-1]
    
    def pop(self)->ScopeNode:
        if len(self.stack)==1:
            raise RuntimeError("Pop called when only the global scope was left in the stack")
        scope = self.stack[-1]
        self.stack.pop()
        return scope
