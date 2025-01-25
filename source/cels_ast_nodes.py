from ast_base import ASTNode, ASTBlock, ASTSimpleInstruction
from cels_symbols import DataType, Variable, BinaryOperator, FormalParameter, Function, TypeConverter, FunctionOverload, Field, Indexer, UnaryOperator
from cels_scope import Scope, Symbol
from utils import ensure_type, indent

class ASTException(Exception):
    def __init__(self, message):
        super().__init__(message)


class _AST_ExpressionNode(ASTNode):
    def __init__(self, data_type):
        super(_AST_ExpressionNode, self).__init__()
        self.data_type = data_type

class _AST_Literal(_AST_ExpressionNode):
    def __init__(self, value, data_type : DataType):
        assert isinstance(data_type, DataType), f"_AST_Literal: DataType expected, got {data_type} as {type(data_type)}"
        super(_AST_Literal, self).__init__(data_type)
        self.value= value
    def __str__(self): return f"{repr(self.value)}:{self.data_type}"

    def clone(self): return _AST_Literal(self.value, self.data_type)

class _AST_VDecl(ASTNode):
    def __init__(self, variable:Variable):
        super(_AST_VDecl, self).__init__()
        self._variable =  ensure_type(variable, Variable)

    @property
    def variable(self): return self._variable

    def __str__(self): return f"var {self.variable} : {self.variable.data_type}"
    def clone(self):
        raise RuntimeError("Cloning VDecl is not allowed")

class _AST_Package(ASTNode):
    children = property(ASTNode.simple_children_list_getter("children"))

    def __init__(self, name:str, block:ASTBlock, scope:Scope):
        super(_AST_Package, self).__init__()
        ensure_type(block, ASTBlock)
        self.register_children_list_key("children")

        self.name = ensure_type(name, str)
        self.scope = ensure_type(scope, Scope)

        children = list(block.children)
        for child in children:
            child.set_parent(self, "children")


    def __str__(self):
        content = ";\n".join(map(str, self.children))
        lines = '\n  '.join(content.splitlines())
        return f"package {self.name} begin\n  {lines}\nend"

class _AST_BinaryOperator(_AST_ExpressionNode):
    left = property(ASTNode.simple_child_getter("left"), ASTNode.simple_child_setter("left"))
    right = property(ASTNode.simple_child_getter("right"), ASTNode.simple_child_setter("right"))

    def __init__(self, op:BinaryOperator, left:_AST_ExpressionNode, right:_AST_ExpressionNode):
        super(_AST_BinaryOperator, self).__init__(op.res_type)
        self.register_child_key("left")
        self.register_child_key("right")
        self.operator = op
        self.left = left
        self.right = right

    def __str__(self): return f"({self.left}{self.operator.symbol}{self.right})"

    def clone(self):
        return _AST_BinaryOperator(self.op, self.left.clone(), self.right.clone())

class _AST_UnaryOperator(_AST_ExpressionNode):
    operand = property(ASTNode.simple_child_getter("operand"), ASTNode.simple_child_setter("operand"))

    def __init__(self, op:UnaryOperator, operand:_AST_ExpressionNode):
        super(_AST_UnaryOperator, self).__init__(op.res_type)
        self.register_child_key("operand")
        self.operator = op
        self.operand = operand

    def __str__(self): return f"({self.operator.symbol}{self.operand})"

    def clone(self):
        return _AST_UnaryOperator(self.op, self.operand.clone())

class _AST_Addressable(ASTNode):
    def __init__(self):
        ASTNode.__init__(self)

class _AST_SymbolTerm(_AST_ExpressionNode, _AST_Addressable):
    def __init__(self, symbol:Symbol, data_type:DataType|None = None):
        _AST_Addressable.__init__(self)
        ensure_type(data_type, DataType, None)
        if isinstance(symbol, Variable):
            super(_AST_SymbolTerm, self).__init__(symbol.data_type)
        elif isinstance(symbol, FormalParameter):
            super(_AST_SymbolTerm, self).__init__(symbol.data_type)
        elif isinstance(symbol, DataType):
            super(_AST_SymbolTerm, self).__init__(data_type)
        elif isinstance(symbol, Function):
            super(_AST_SymbolTerm, self).__init__(data_type)
        else:
            raise ASTException(f"Symbol is not allowed in expressions: {symbol}")
        self.symbol = symbol

    def __str__(self): return f"{self.symbol}:{self.data_type}"
    def clone(self): return _AST_SymbolTerm(self.symbol)

class _AST_While(ASTNode):
    condition = property(ASTNode.simple_child_getter("condition"), ASTNode.simple_child_setter("condition"))
    block = property(ASTNode.simple_child_getter("block"), ASTNode.simple_child_setter("block"))

    def __init__(self, cond, block):
        super(_AST_While, self).__init__()
        self.register_child_key("condition")
        self.register_child_key("block")
        assert isinstance(cond, _AST_ExpressionNode)
        assert isinstance(block, ASTNode)

        self.condition=cond
        self.block=block

    def __str__(self):
        return f"while {self.condition} do begin\n{indent(str(self.block))}\nend"

class _AST_If(ASTNode):
    condition = property(ASTNode.simple_child_getter("condition"), ASTNode.simple_child_setter("condition"))
    then_branch = property(ASTNode.simple_child_getter("then_branch"), ASTNode.simple_child_setter("then_branch"))
    else_branch = property(ASTNode.simple_child_getter("else_branch"), ASTNode.simple_child_setter("else_branch"))

    def __init__(self, cond, then_branch, else_branch):
        ASTNode.__init__(self)
        self.register_child_key("condition")
        self.register_child_key("then_branch")
        self.register_child_key("else_branch")
        self.condition = cond
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __str__(self):
        cond_str = str(self.condition)
        then_str = indent(str(self.then_branch))
        if self.else_branch is not None:
            else_str = indent(str(self.else_branch))
            return f"if {cond_str} then\n{then_str}\nelse\n{else_str}\nfi"
        return f"if {cond_str} then\n{then_str}\nfi"


class _AST_Assign(ASTNode):
    left = property(ASTNode.simple_child_getter("left"), ASTNode.simple_child_setter("left"))
    right = property(ASTNode.simple_child_getter("right"), ASTNode.simple_child_setter("right"))

    def __init__(self, left, right):
        ASTNode.__init__(self)
        self.register_child_key("left")
        self.register_child_key("right")

        assert isinstance(left, _AST_ExpressionNode), "_AST_Attr: Non-expression node at the left of the assignment"
        assert isinstance(right, _AST_ExpressionNode), "_AST_Attr: Non-expression node at the right of the assignment"

        self.left = left
        self.right = right

    def __str__(self): return f"{self.left} = {self.right}"
    def clone(self):
        return _AST_Attr(self.left.clone(), self.right.clone())

class _AST_TypeConvert(_AST_ExpressionNode):
    expression = property(ASTNode.simple_child_getter("expression"), ASTNode.simple_child_setter("expression"))
    def __init__(self, expression:_AST_ExpressionNode, converter:TypeConverter):
        ensure_type(converter, TypeConverter)
        _AST_ExpressionNode.__init__(self, converter.output_type)
        self.register_child_key("expression")
        self.expression = ensure_type(expression, _AST_ExpressionNode)
        self.converter = converter

    def __str__(self): return f"conv({self.expression}, {self.data_type})"
    def clone(self): return _AST_TypeConvert(self.expression.clone(), self.converter)


class _AST_IndexAccess(_AST_ExpressionNode):
    expression = property(ASTNode.simple_child_getter("expression"), ASTNode.simple_child_setter("expression"))
    key = property(ASTNode.simple_child_getter("key"), ASTNode.simple_child_setter("key"))
    def __init__(self, expression: _AST_ExpressionNode, key:_AST_ExpressionNode, indexer:Indexer):
        ensure_type(indexer, Indexer)
        _AST_ExpressionNode.__init__(self, indexer.output_type)
        self.register_child_key("expression")
        self.register_child_key("key")
        self.expression = ensure_type(expression, _AST_ExpressionNode)
        self.key = ensure_type(key, _AST_ExpressionNode)
        self.indexer = indexer

    def __str__(self):  return f"(({self.expression})[f{self.key}])"
    def clone(self): return _AST_IndexAccess(self.expression.clone(), self.key.clone(), indexer)

class _AST_FuncDecl(ASTNode):

    implementation = property(ASTNode.simple_child_getter("implementation"), ASTNode.simple_child_setter("implementation"))

    def __init__(self, func_overload:FunctionOverload):
        ASTNode.__init__(self)
        self.register_child_key("implementation")

        self.func_overload = ensure_type(func_overload, FunctionOverload)
        self.implementation = ensure_type(func_overload.implementation, ASTNode, None)

    def __str__(self):
        params = ", ".join(map(lambda p:f"{p}: {p.data_type}", self.func_overload.params))
        body = '\n  '.join(str(self.func_overload.implementation or "").splitlines())
        if body!="": body="\nbegin\n  "+body+"\nend"
        flags = []
        if self.func_overload.is_extern: flags.append("E")
        if self.func_overload.is_multiframe: flags.append("M")
        if self.func_overload.cpp_include is not None: flags.append("C")
        flags = ("["+"".join(flags)+"]") if len(flags)>0 else ""
        return f"function{flags} {self.func_overload.func_symbol.get_full_name()}({params}) : {self.func_overload.return_type} {body}"

class _AST_StructDecl(ASTNode):
    members = property(ASTNode.simple_children_list_getter("members"))

    def __init__(self, symbol: DataType, members:list):
        ASTNode.__init__(self)
        self.register_children_list_key("members")
        self.symbol = ensure_type(symbol, DataType)

        for member in members:
            member.set_parent(self, "members")

    def __str__(self):
        content = ";\n".join(map(str, self.members))
        return f"struct {self.symbol} begin\n{indent(content, nspaces=2)}\nend"

class _AST_AddressOf(_AST_ExpressionNode):
    operand = property(ASTNode.simple_child_getter("operand"), ASTNode.simple_child_setter("operand"))

    def __init__(self, operand:_AST_Addressable):
        ensure_type(operand, _AST_ExpressionNode)
        ensure_type(operand, _AST_ExpressionNode)
        _AST_ExpressionNode.__init__(self, operand.data_type.make_pointer())
        self.register_child_key("operand")
        self.operand = operand

    def __str__(self): return f"addressof({str(self.operand)}):{self.data_type}"

class _AST_Dereference(_AST_ExpressionNode):
    operand = property(ASTNode.simple_child_getter("operand"), ASTNode.simple_child_setter("operand"))

    def __init__(self, operand:_AST_Addressable):
        ensure_type(operand, _AST_ExpressionNode)

        if not operand.data_type.is_pointer:
            raise ASTException("Dereference operator called on non-pointer")

        _AST_ExpressionNode.__init__(self, operand.data_type.element_type)
        self.register_child_key("operand")
        self.operand = operand

    def __str__(self): return f"dereference({str(self.operand)}):{self.data_type}"

class _AST_FieldDecl(ASTNode):
    def __init__(self, field:Field):
        ASTNode.__init__(self)
        self._field = field

    @property
    def field(self): return self._field

    def __str__(self): return f"field {self.field}: {self.field.data_type}"

class _AST_FieldAccessor(_AST_ExpressionNode):
    def __init__(self, element: _AST_ExpressionNode, field:Field):
        _AST_ExpressionNode.__init__(self, field.data_type)
        self.register_child_key("element")
        self._field = field
        self.element = ensure_type(element, _AST_ExpressionNode)

    @property
    def field(self): return self._field

    def __str__(self): return f"({self.element}).{self.field.name}:{self.data_type}"

    element = property(ASTNode.simple_child_getter("element"), ASTNode.simple_child_setter("element"))

class _AST_MethodAccessor(_AST_ExpressionNode):
    def __init__(self, element: _AST_ExpressionNode, method:Function, expr_type:DataType):
        _AST_ExpressionNode.__init__(self, ensure_type(expr_type, DataType))
        self.register_child_key("element")
        self._method = ensure_type(method, Function)
        self.element = ensure_type(element, _AST_ExpressionNode)

    @property
    def method(self): return self._method

    def __str__(self): f"({self.element}).{self.function.name}"


class _AST_FunOverloadCall(_AST_ExpressionNode):
    args = property(ASTNode.simple_children_list_getter('args'))
    impl_ref = property(ASTNode.simple_child_getter('impl_ref'), ASTNode.simple_child_setter('impl_ref'))

    def __init__(self, func_overload:FunctionOverload, args:list[_AST_ExpressionNode], include_impl_node:bool=False):
        ensure_type(func_overload, FunctionOverload)
        ensure_type(args, list)
        _AST_ExpressionNode.__init__(self, func_overload.return_type)
        self.register_children_list_key("args")
        self.register_children_list_key("impl_ref")
        self._function_overload = func_overload
        for arg in args:
            arg.set_parent(self, "args")

        if include_impl_node:
            self.impl_ref = self.function_overload.implementation

    @property
    def function_overload(self): return self._function_overload

    def clone(self):
        return _AST_FunOverloadCall(self.function_overload, [arg.clone() for arg in self.args])

    def __str__(self):
        args_str = ', '.join([str(arg) for arg in self.args])
        mf = "<M>" if self.function_overload.is_multiframe else ""
        return f"{self.function_overload.func_symbol}{mf}({args_str})"

class _AST_Return(ASTNode):
    value = property(ASTNode.simple_child_getter('value'), ASTNode.simple_child_setter('value'))

    def __init__(self, value:_AST_ExpressionNode|None):
        ensure_type(value, _AST_ExpressionNode, None)
        ASTNode.__init__(self)
        self.register_child_key('value')
        self.value = value

    def __str__(self): return f"return {str(self.value or '')}"

class _AST_Suspend(ASTSimpleInstruction):
    def __init__(self):
        ASTSimpleInstruction.__init__(self, "suspend")

class _AST_Break(ASTSimpleInstruction):
    def __init__(self):
        ASTSimpleInstruction.__init__(self, "break")

class _AST_Continue(ASTSimpleInstruction):
    def __init__(self):
        ASTSimpleInstruction.__init__(self, "continue")

class _AST_FunctionClosure(_AST_ExpressionNode):
    captured_args = property(ASTNode.simple_children_list_getter('captured_args'))
    implementation = property(ASTNode.simple_child_getter("implementation"), ASTNode.simple_child_setter("implementation"))


    def __init__(self, func_overload:FunctionOverload, closure_type:DataType, captured_args:list[_AST_ExpressionNode]):
        _AST_ExpressionNode.__init__(self, ensure_type(closure_type, DataType))
        self.register_children_list_key('captured_args')
        self.register_child_key("implementation")
        self._function_overload = ensure_type(func_overload, FunctionOverload)
        self.implementation = ensure_type(func_overload.implementation, ASTNode)

        for arg in captured_args:
            arg.set_parent(self, 'captured_args')

    @property
    def function_overload(self): return self._function_overload

    def free_params(self): return self.function_overload.params[len(self.captured_args):]

    def __str__(self):
        str_captures = ', '.join([str(arg) for arg in self.captured_args])
        flags = []
        if self.function_overload.is_extern: flags.append("E")
        if self.function_overload.is_multiframe: flags.append("M")
        if self.function_overload.cpp_include is not None: flags.append("C")
        flags = ("["+"".join(flags)+"]") if len(flags)>0 else ""

        return f"(lambda{flags} {self.function_overload.func_symbol.get_full_name()}[{str_captures}]=>{self.implementation})"


class _AST_TaskStart(_AST_ExpressionNode):
    def __init__(self, task, expr_type:DataType):
        _AST_ExpressionNode.__init__(self, ensure_type(expr_type, DataType))
        self.task = task

    def __str__(self):
        return f"taskstart {self.task}"

    def clone(self):
        return _AST_TaskStart(self.task.clone(), self.data_type)

class _AST_TaskReady(_AST_ExpressionNode):
    def __init__(self, task:_AST_ExpressionNode, expr_type:DataType):
        _AST_ExpressionNode.__init__(self, ensure_type(expr_type, DataType))
        if not task.data_type.is_task:
            raise ASTException("Non-task argument provided to taskready()")
        self.task = task

    def __str__(self):
        return f"taskready({self.task})"
        
class _AST_ObjectCreate(_AST_ExpressionNode):
    args = property(ASTNode.simple_children_list_getter('args'))

    def __init__(self, obj_type:DataType, constr_overload:FunctionOverload|None, constr_args:list[_AST_ExpressionNode]):
        _AST_ExpressionNode.__init__(self, ensure_type(obj_type, DataType))
        if not obj_type.is_struct:
            raise ASTException(f"Struct type expected, got {obj_type}")
        self.register_children_list_key('args')
        self.obj_type = obj_type
        self.constr_overload = constr_overload # None = default

        for arg in constr_args:
            ensure_type(arg, _AST_ExpressionNode).set_parent(self, 'args')
    
    def __str__(self): return f"create({', '.join(map(str, [self.obj_type] + self.args))})"
    
    def clone(self):
        return _AST_ObjectCreate(self.obj_type, [arg.clone() for arg in self.args])
        
class _AST_MultiframeLaunch(ASTNode):
    funcall = property(ASTNode.simple_child_getter('funcall'), ASTNode.simple_child_setter('funcall'))
    on_frame_start = property(ASTNode.simple_child_getter('on_frame_start'), ASTNode.simple_child_setter('on_frame_start'))
    on_frame_end = property(ASTNode.simple_child_getter('on_frame_end'), ASTNode.simple_child_setter('on_frame_end'))
    
    def __init__(self, funcall:_AST_FunOverloadCall, on_frame_start:ASTBlock, on_frame_end:ASTBlock):
        ASTNode.__init__(self)
        self.register_child_key('funcall')
        self.register_child_key('on_frame_start')
        self.register_child_key('on_frame_end')
        self.funcall = ensure_type(funcall, _AST_FunOverloadCall)
        self.on_frame_start = ensure_type(on_frame_start, ASTBlock)
        self.on_frame_end = ensure_type(on_frame_end, ASTBlock)
    
    def __str__(self):
        return f'multiframe launch {self.funcall} (on_frame_start={self.on_frame_start}, on_frame_end={self.on_frame_end})'
    
    def clone(self):        
        return _AST_MultiframeLaunch(self.funcall.clone(), self.on_frame_start.clone(), self.on_frame_end.clone())

class ASTNodes:
    Block = ASTBlock
    ExpressionNode = _AST_ExpressionNode
    Literal = _AST_Literal
    VDecl = _AST_VDecl
    Package = _AST_Package
    BinaryOperator = _AST_BinaryOperator
    SymbolTerm = _AST_SymbolTerm
    While = _AST_While
    Assign = _AST_Assign
    TypeConvert = _AST_TypeConvert
    FuncDecl = _AST_FuncDecl
    StructDecl = _AST_StructDecl
    AddressOf = _AST_AddressOf
    Dereference = _AST_Dereference
    FieldDecl = _AST_FieldDecl
    FieldAccessor = _AST_FieldAccessor
    MethodAccessor = _AST_MethodAccessor
    FunOverloadCall = _AST_FunOverloadCall
    If = _AST_If
    Return = _AST_Return
    Suspend = _AST_Suspend
    Break = _AST_Break
    Continue = _AST_Continue
    FunctionClosure = _AST_FunctionClosure
    IndexAccess = _AST_IndexAccess

    TaskStart = _AST_TaskStart
    TaskReady = _AST_TaskReady

    UnaryOperator = _AST_UnaryOperator
    
    ObjectCreate = _AST_ObjectCreate
    
    MultiframeLaunch = _AST_MultiframeLaunch