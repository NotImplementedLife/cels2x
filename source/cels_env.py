from __future__ import annotations
from cels_scope import Scope, Symbol, ScopeStack, ScopeNameProvider, ScopeResolveStrategy
from cels_symbols import Variable, FormalParameter, Function, FunctionOverload, BinaryOperator, IndexerArchetype, Indexer, UnaryOperatorType
from cels_symbols import OperatorSolver
from cels_symbols import DataType, PrimitiveType, StructType, Field
from utils import IdProvider


class CelsEnvironment:
    def __init__(self):
        self._global_scope = Scope("", None)
        self._op_solver = OperatorSolver()
        self._scope_name_provider = ScopeNameProvider()
        self._sym_id_provider = IdProvider()
        self._internal_sym_id_provider = IdProvider()

        def glb_add_symbol(symbol_creator):
            return self.add_symbol(self.global_scope, symbol_creator)

        self.dtype_int = glb_add_symbol(PrimitiveType.scoped_creator('int'))
        self.dtype_uint = glb_add_symbol(PrimitiveType.scoped_creator('uint'))
        self.dtype_short = glb_add_symbol(PrimitiveType.scoped_creator('short'))
        self.dtype_ushort = glb_add_symbol(PrimitiveType.scoped_creator('ushort'))
        self.dtype_float = glb_add_symbol(PrimitiveType.scoped_creator('float'))
        self.dtype_bool = glb_add_symbol(PrimitiveType.scoped_creator('bool'))
        self.dtype_string = glb_add_symbol(PrimitiveType.scoped_creator('string'))
        self.dtype_void = glb_add_symbol(PrimitiveType.scoped_creator('void'))
        self.dtype_function = glb_add_symbol(PrimitiveType.scoped_creator('builtin@function'))
        self.dtype_instance_method = glb_add_symbol(PrimitiveType.scoped_creator('builtin@instance_method'))
        self.dtype_closure_function = glb_add_symbol(PrimitiveType.scoped_creator('builtin@closure_function'))

    @property
    def internal_sym_id_provider(self): return self._internal_sym_id_provider

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
        dtype_short = env.dtype_short
        dtype_bool = env.dtype_bool
        dtype_float = env.dtype_float
        dtype_ushort = env.dtype_ushort
        dtype_uint = env.dtype_uint

        def register_arithmetics(dtype, ops = None):
            ops = ops or ['+', '-', '*', '/', '%']
            for op in ops:
                env.op_solver.register_binary_operator(op, dtype, dtype, dtype)

        def register_comparisons(dtype, ops = None):
            ops = ops or ['<', '<=', '>', '>=', '==', '!=']
            for op in ops:
                env.op_solver.register_binary_operator(op, dtype, dtype, dtype_bool)

        register_arithmetics(dtype_int)
        register_arithmetics(dtype_short)
        register_arithmetics(dtype_float)

        register_comparisons(dtype_int)
        register_comparisons(dtype_short)
        register_comparisons(dtype_float)

        register_comparisons(dtype_bool, ['==', '!='])

        env.op_solver.register_binary_operator('and', dtype_bool, dtype_bool, dtype_bool)
        env.op_solver.register_binary_operator('or', dtype_bool, dtype_bool, dtype_bool)
        env.op_solver.register_binary_operator('xor', dtype_bool, dtype_bool, dtype_bool)
        env.op_solver.register_binary_operator('nand', dtype_bool, dtype_bool, dtype_bool)
        env.op_solver.register_binary_operator('nor', dtype_bool, dtype_bool, dtype_bool)

        env.op_solver.register_binary_operator('+', dtype_bool, dtype_bool, dtype_int)

        env.op_solver.register_unary_operator('not', dtype_bool, dtype_bool)

        env.op_solver.register_unary_operator('-', dtype_int, dtype_int)
        env.op_solver.register_unary_operator('-', dtype_uint, dtype_int)

        env.op_solver.register_unary_operator('+', dtype_int, dtype_int)
        env.op_solver.register_unary_operator('+', dtype_uint, dtype_uint)

        def register_inc_dec(dtype):
            env.op_solver.register_unary_operator('++', dtype, dtype, UnaryOperatorType.PREFIX)
            env.op_solver.register_unary_operator('--', dtype, dtype, UnaryOperatorType.PREFIX)
            env.op_solver.register_unary_operator('++', dtype, dtype, UnaryOperatorType.POSTFIX)
            env.op_solver.register_unary_operator('--', dtype, dtype, UnaryOperatorType.POSTFIX)

        register_inc_dec(dtype_int)
        register_inc_dec(dtype_uint)
        register_inc_dec(dtype_short)
        register_inc_dec(dtype_ushort)

        env.op_solver.register_converter(dtype_int, dtype_float)
        env.op_solver.register_converter(dtype_int, dtype_short)
        env.op_solver.register_converter(dtype_int, dtype_ushort)
        env.op_solver.register_converter(dtype_int, dtype_uint)

        env.op_solver.register_converter(dtype_short, dtype_int)

        env.op_solver.register_converter(dtype_ushort, dtype_int)

        env.op_solver.register_indexer_archetype(IndexerArchetype(
            name="static_array_indexer",
            condition=lambda E,K: E.is_static_array and K in [dtype_int, dtype_short],
            indexer_creator=lambda A, E,K: Indexer(A, E, K, E.element_type)
        ))

        return env

    def enumerate_symbols(self):
        return self.global_scope.enumerate_symbols(recursive=True)


    def generate_lambda_function(self):
        name = f"icels_lambda_{self.internal_sym_id_provider.create_id()}"
        lambda_sym = self.add_symbol(self.global_scope, Function.scoped_creator(name))
        scope_name = f"@{name}_ov{lambda_sym.get_overloads_count()+1}"
        lambda_scope = self.global_scope.get_subscope(scope_name, strategy=ScopeResolveStrategy.CREATE)
        lambda_scope.associated_symbol = lambda_sym
        return lambda_sym, lambda_scope
