from __future__ import annotations
from cels_scope import Scope, Symbol, ScopeStack, ScopeNameProvider, ScopeResolveStrategy
from cels_symbols import Variable, FormalParameter, Function, FunctionOverload, BinaryOperator
from cels_symbols import OperatorSolver
from cels_symbols import DataType, PrimitiveType, StructType, Field
from utils import IdProvider


class CelsEnvironment:
    def __init__(self):
        self._global_scope = Scope("", None)
        self._op_solver = OperatorSolver()
        self._scope_name_provider = ScopeNameProvider()
        self._sym_id_provider = IdProvider()
        
        def glb_add_symbol(symbol_creator):
            return self.add_symbol(self.global_scope, symbol_creator)
                
        self.dtype_int = glb_add_symbol(PrimitiveType.scoped_creator('int'))
        self.dtype_float = glb_add_symbol(PrimitiveType.scoped_creator('float'))
        self.dtype_bool = glb_add_symbol(PrimitiveType.scoped_creator('bool'))
        self.dtype_string = glb_add_symbol(PrimitiveType.scoped_creator('string'))
        self.dtype_void = glb_add_symbol(PrimitiveType.scoped_creator('void'))
        self.dtype_function = glb_add_symbol(PrimitiveType.scoped_creator('builtin@function'))
        self.dtype_instance_method = glb_add_symbol(PrimitiveType.scoped_creator('builtin@instance_method'))
        
    
    @property
    def global_scope(self)->Scope: return self._global_scope
    
    @property
    def op_solver(self)->OperatorSolver: return self._op_solver
    
    @property
    def scope_name_provider(self)->ScopeNameProvider: return self._scope_name_provider
    
    def add_symbol(self, scope, symbol_creator)->Symbol:
        symbol = scope.add_symbol(symbol_creator)
        symbol.metadata['sid'] = self._sym_id_provider.create_id()
        return symbol
        
    @staticmethod
    def create_default()->CelsEnvironment:
        env = CelsEnvironment()      
        
        dtype_int = env.dtype_int
        dtype_bool = env.dtype_bool
        dtype_float = env.dtype_float
        
        env.op_solver.register_binary_operator('+', dtype_int, dtype_int, dtype_int)
        env.op_solver.register_binary_operator('-', dtype_int, dtype_int, dtype_int)
        env.op_solver.register_binary_operator('*', dtype_int, dtype_int, dtype_int)
        env.op_solver.register_binary_operator('/', dtype_int, dtype_int, dtype_int)
        env.op_solver.register_binary_operator('%', dtype_int, dtype_int, dtype_int)
        env.op_solver.register_binary_operator('<', dtype_int, dtype_int, dtype_bool)
        env.op_solver.register_binary_operator('<=', dtype_int, dtype_int, dtype_bool)
        env.op_solver.register_binary_operator('>', dtype_int, dtype_int, dtype_bool)
        env.op_solver.register_binary_operator('>=', dtype_int, dtype_int, dtype_bool)
        env.op_solver.register_binary_operator('==', dtype_int, dtype_int, dtype_bool)
        env.op_solver.register_binary_operator('!=', dtype_int, dtype_int, dtype_bool)
        
        env.op_solver.register_converter(dtype_int, dtype_float)
        
        return env
    
    def enumerate_symbols(self):
        return self.global_scope.enumerate_symbols(recursive=True)
        
        
        
    