from __future__ import annotations
from utils import ensure_type
from cels_scope import Symbol, Scope

class SymbolException(Exception):
    def __init__(self, message):
        super().__init__(message)

class DataType:
    def __init__(self, full_name:str):
        self._full_name = ensure_type(full_name, str)
        self._hash_code = hash(self._full_name)
    
    def get_full_name(self): return self._full_name
    
    def __eq__(self, other): return isinstance(other, DataType) and self.get_full_name()==other.get_full_name()
    def __hash__(self): return self._hash_code
    
    def __str__(self): return self.get_full_name()
    
    @property
    def is_primitive(self): return isinstance(self, PrimitiveType)
    
    @property
    def is_static_array(self): return isinstance(self, StaticArrayType)
    
    @property
    def is_pointer(self): return isinstance(self, PointerType)
    
    @property
    def is_struct(self): return isinstance(self, StructType)
    
    def make_pointer(self): return PointerType(self)
    
    def make_array(self, length): return StaticArrayType(self, length)
    

class DataTypeSymbol(Symbol, DataType):
    def __init__(self, name:str, scope:Scope):
        Symbol.__init__(self, name, scope)
        DataType.__init__(self, Symbol.get_full_name(self))
    
    @staticmethod
    def scoped_creator(name:str): 
        def creator(scope:Scope): return DataTypeSymbol(name, scope)
        return creator

class PrimitiveType(DataTypeSymbol):
    def __init__(self, name:str, scope:Scope):
        super(PrimitiveType, self).__init__(name, scope)

    @staticmethod
    def scoped_creator(name:str): 
        def creator(scope:Scope): return PrimitiveType(name, scope)
        return creator

class StaticArrayType(DataType):
    def __init__(self, element_type:DataType, length:int):
        self._element_type = ensure_type(element_type, DataType)
        self._length = ensure_type(length, int)
        DataType.__init__(self, f"{self.element_type}[{self.length}]")
    
    @property
    def element_type(self): return self._element_type
    
    @property
    def length(self): return self._length
    
class PointerType(DataType):
    def __init__(self, element_type:DataType):
        self._element_type = ensure_type(element_type, DataType)        
        DataType.__init__(self, f"{self.element_type}*")
    
    @property
    def element_type(self): return self._element_type


class StructType(DataTypeSymbol):
    def __init__(self, name:str, scope:Scope):
        DataTypeSymbol.__init__(self, name, scope)        
        self._inner_scope = None
        self._members:set[Symbol] = set()
    
    @property
    def members(self): return list(self._members)
    
    def add_member(self, symbol:Symbol):
        self._members.add(symbol)
    
    @property
    def inner_scope(self): return self._inner_scope
    
    @inner_scope.setter
    def inner_scope(self, value: Scope): self._inner_scope = ensure_type(value, Scope)
    

class Variable(Symbol):
    def __init__(self, name:str, scope:Scope, data_type:DataType):
        Symbol.__init__(self, name, scope)
        self._data_type = ensure_type(data_type, DataType)
    
    @property
    def data_type(self): return self._data_type
    
class FormalParameter(Symbol):
    def __init__(self, name:str, scope:Scope, data_type:DataType):
        Symbol.__init__(self, name, scope)
        self._data_type = ensure_type(data_type, DataType)
    
    @property
    def data_type(self): return self._data_type
    
    @staticmethod
    def scoped_creator(name:str, data_type:DataType): 
        def creator(scope:Scope): return FormalParameter(name, scope, data_type)
        return creator
    
    
class Field(Symbol):
    def __init__(self, name:str, scope:Scope, data_type:DataType):
        Symbol.__init__(self, name, scope)
        self._data_type = ensure_type(data_type, DataType)
        self._declaring_type = ensure_type(scope.associated_symbol, StructType)
    
    @property
    def data_type(self): return self._data_type
    
    @property
    def declaring_type(self): return self._declaring_type
    
class FunctionOverload:
    def __init__(self, 
        func_symbol:Function,
        params:list[FormalParameter],
        return_type:DataType,
        is_multiframe:bool=False,
        is_extern:bool=False,
        cpp_include:str|None=None
    ):
        self._func_symbol = func_symbol
        self._params = ensure_type(params, list)
        self._return_type = ensure_type(return_type, DataType)
        self._hash_code = sum(map(lambda p:hash(p.data_type), self.params)) + hash(self.return_type)        
        self._implementation = None
        self._is_multiframe = ensure_type(is_multiframe, bool)
        self._is_extern = ensure_type(is_extern, bool)
        self._cpp_include = ensure_type(cpp_include, str, None)
    
    @property
    def is_multiframe(self): return self._is_multiframe
    
    @property
    def is_extern(self): return self._is_extern
    
    @property
    def cpp_include(self): return self._cpp_include
    
    @property
    def func_symbol(self): return self._func_symbol
    
    @property
    def implementation(self): return self._implementation
    
    @implementation.setter
    def implementation(self, value): self._implementation = value
    
    @property
    def params(self)->list[FormalParameter]: return self._params
    
    @property
    def return_type(self): return self._return_type
    
    def __eq__(self, other): 
        if not isinstance(other, FunctionOverload): return False
        if self.func_symbol != other.func_symbol: return False
        if self.return_type != other.return_type: return False
        if len(self.params) != len(other.params): return False
        for ps, po in zip(self.params, other.params):
            if ps.data_type != po.data_type: return False
        return True
    
    def __hash__(self): return self._hash_code    
    
    def __str__(self):
        params = ', '.join(map(lambda p:f"{p.name}:{p.data_type}" , self.params))
        return f"{self.func_symbol}({params}):{self.return_type}"
    
    
class Function(Symbol):
    def __init__(self, name:str, scope:Scope, declaring_type:DataType|None=None):
        Symbol.__init__(self, name, scope)        
        self._overloads:set[FunctionOverload] = set()
        self._declaring_type = declaring_type
        
    @property
    def overloads(self): return self._overloads
    
    def add_overload(self, overload:FunctionOverload):
        ensure_type(overload, FunctionOverload)
        if overload in self.overloads:
            raise SymbolException(f"Function overload already exists: {overload}")
        self.overloads.add(overload)
        return overload
    
    def get_overloads_count(self): return len(self.overloads)
    
    @property
    def is_method(self): return self._declaring_type is not None
    
    @property
    def declaring_type(self): return self._declaring_type
    
    @staticmethod
    def scoped_creator(name:str, declaring_type:DataType|None=None): 
        def creator(scope:Scope): return Function(name, scope, declaring_type)
        return creator
    
class BinaryOperator:
    def __init__(self, symbol:str, arg1_type:DataType, arg2_type:DataType, res_type:DataType):
        self.symbol = symbol
        self.arg1_type = ensure_type(arg1_type, DataType)
        self.arg2_type = ensure_type(arg2_type, DataType)
        self.res_type = ensure_type(res_type, DataType)
    def __str__(self): return f"operator {self.symbol}({self.arg1_type}, {self.arg2_type}):{self.res_type}"

class TypeConverter:
    def __init__(self, input_type:DataType, output_type:DataType):
        self.input_type = ensure_type(input_type, DataType)
        self.output_type = ensure_type(output_type, DataType)
    def __str__(self): return f"conv({self.input_type}):{self.output_type}"

class IndexerArchetype:
    def __init__(self, name:str, condition:callable[[DataType, DataType],bool], indexer_creator:callable[[IndexerArchetype, DataType, DataType], Indexer]):
        print("HERE?????")
        self.name = name
        self.condition = condition
        self.indexer_creator = indexer_creator
    
    def validate(self, element_type:DataType, index_type:DataType):
        return self.condition(element_type, index_type)
    
    def create_indexer(self, element_type:DataType, index_type:DataType):
        assert self.validate(element_type, index_type), f"Unable to create indexer {element_type}[{index_type}] using archetype {self.name}"
        return self.indexer_creator(self, element_type, index_type)
    
    def __eq__(self, other): return isinstance(other, IndexerArchetype) and self.name==other.name
    def __hash__(self): return hash(self.name)
    

class Indexer:
    def __init__(self, inarch:IndexerArchetype, element_type:DataType, index_type:DataType, output_type:DataType):        
        self.archetype = ensure_type(inarch, IndexerArchetype)
        self.element_type = ensure_type(element_type, DataType)
        self.index_type = ensure_type(index_type, DataType)
        self.output_type = ensure_type(output_type, DataType)
    def __str__(self): return f"indexer {self.element_type}[{self.index_type}]:{self.output_type}"

class OperatorSolver:
    def __init__(self):
        self.binary_operators: dict[tuple[str, DataType, DataType], BinaryOperator] = {}
        self.converters: dict[tuple[DataType, DataType], TypeConverter] = {}
        self.indexers: dict[tuple[DataType, DataType], Indexer] = {}
        self.indexer_archetypes: list[IndexerArchetype] = []
        
    def __register(self, dct, key, value_fun, err_fun):
        if key in dct: raise SymbolException(err_fun())
        dct[key] = it = value_fun()
        return it
    
    def __resolve(self, dct, key, err_fun):
        if not key in dct: raise SymbolException(err_fun())
        return dct[key]
    
    def register_binary_operator(self, symbol:str, arg1_type:DataType, arg2_type:DataType, return_type:DataType)->BinaryOperator:
        return self.__register(self.binary_operators, key=(symbol, arg1_type, arg2_type), 
            value_fun=lambda: BinaryOperator(symbol, arg1_type, arg2_type, return_type),
            err_fun=lambda: f"Operator {symbol}({arg1_type}, {arg2_type}) is already defined" )        
        
    def resolve_binary_operator(self, symbol:str, arg1_type:DataType, arg2_type:DataType)->BinaryOperator:
        return self.__resolve(self.binary_operators, key=(symbol, arg1_type, arg2_type),
            err_fun=lambda:f"No definition for operator {symbol}({arg1_type}, {arg2_type})")        
        
    def register_converter(self, input_type, output_type):
        assert isinstance(input_type, DataType), f"DataType expected, got {type(input_type)}"
        assert isinstance(output_type, DataType), f"DataType expected, got {type(output_type)}"
        return self.__register(self.converters, key=(input_type, output_type),
            value_fun=lambda: TypeConverter(input_type, output_type),
            err_fun=lambda: f"Converter from {input_type} to {output_type} already exists")
        
    def resolve_converter(self, input_type, output_type):        
        assert isinstance(input_type, DataType), f"DataType expected, got {type(input_type)}"
        assert isinstance(output_type, DataType), f"DataType expected, got {type(output_type)}"        
        return self.__resolve(self.converters, key=(input_type, output_type),
            err_fun=lambda:f"Could not convert {input_type} to {output_type}")        

    def can_convert(self, input_type:DataType, output_type:DataType)->bool:
        ensure_type(input_type, DataType)
        ensure_type(output_type, DataType)
        return (input_type, output_type) in self.converters

    def register_indexer_archetype(self, inarch):
        self.indexer_archetypes.append(inarch)
            
    def resolve_indexer(self, element_type, index_type):
        for inarch in self.indexer_archetypes:
            if inarch.validate(element_type, index_type):                
                A = inarch.create_indexer(element_type, index_type)                
                return inarch.create_indexer(element_type, index_type)
        
        if element_type.is_pointer:
            return Indexer()
            
        
        raise SymbolException(f"No indexer found for {element_type}[{index_type}]")        
