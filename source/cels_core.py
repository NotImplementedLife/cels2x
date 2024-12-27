from __future__ import annotations
from lexer import Lexer, RegularExpression, LexicalToken
from grammar import RuleComponentFactory, Rule, Grammar, rule_callbacks as rc
from lr1 import LR1Parser
from scopes import ScopeNode, ScopeTree, ScopeStack, Symbol, ScopeError
from ast import ASTNode, ASTBlock, ASTSimpleInstruction

class Terminals:
    STRING_LITERAL = "STRING_LITERAL"
    DEC_LITERAL = "DEC_LITERAL"
    INT_LITERAL = "INT_LITERAL"    
    KW_VAR = "KW_VAR"    
    KW_CONST = "KW_CONST"    
    KW_INT = "KW_INT"    
    KW_STRING = "KW_STRING"    
    KW_VOID = "KW_VOID"
    KW_BOOL = "KW_BOOL"
    KW_PACKAGE = "KW_PACKAGE"    
    KW_BEGIN = "KW_BEGIN"    
    KW_END = "KW_END"
    KW_DO = "KW_DO"
    KW_IF = "KW_IF"
    KW_THEN = "KW_THEN"
    KW_ELSE = "KW_ELSE" 
    KW_STRUCT = "KW_STRUCT"
    KW_FUNCTION = "KW_FUNCION"
    KW_MULTIFRAME = "KW_MULTIFRAME"
    KW_EXTERN = "KW_EXTERN"
    KW_RETURN = "KW_RETURN"
    KW_BREAK = "KW_BREAK"
    KW_CONTINUE = "KW_CONTINUE"
    KW_SUSPEND = "KW_SUSPEND"
    KW_SCOPE = "KW_SCOPE"
    KW_IMPORT = "KW_IMPORT"
    
    KW_WHILE = "KW_WHILE"    
    
    OP_ATTR = "OP_ATTR"    
    OP_ADD_SUB = "OP_ADD_SUB"    
    OP_MUL_DIV_MOD = "OP_MUL_DIV_MOD"    
    OP_MUL_DIV_MOD = "OP_MUL_DIV_MOD"    
    OP_COMP = "OP_COMP"            
    
    S_SEMICOLON = "S_SEMICOLON"    
    S_COLON = "S_COLON"
    S_LPAREN = "S_LPAREN"
    S_RPAREN = "S_RPAREN"
    S_SCOPEACC = "S_SCOPEACC"
    S_COMMA = "S_COMMA"
    S_LBRACK = "S_LBRACK"
    S_RBRACK = "S_RBRACK"
    S_DOT = "S_DOT"
    S_STAR = "S_STAR"
    S_SLASH = "S_SLASH"
    S_PERCENT = "S_PERCENT"
    
    COMMENT = "COMMENT"
    
    EPS      = "EPS"
    
    ID = "ID"        


class CelsLexer(Lexer):
    def __init__(self):
        Lexer.__init__(self)
        
        self.add_rule("WS", "( |\t|\n|\r)+")
        
        self.add_rule(Terminals.COMMENT, r'/\*(([^*])|(\*[^/]))*\*/')
        
        self.add_rule(Terminals.STRING_LITERAL, r'"([^\\"]|(\\"))*"')
        self.add_rule(Terminals.DEC_LITERAL, r'[0-9]+\.[0-9]*')
        self.add_rule(Terminals.INT_LITERAL, r'[0-9]+')
        
        self.add_rule(Terminals.KW_VAR, r'(var)|(пер)')
        self.add_rule(Terminals.KW_CONST, r'const')
        self.add_rule(Terminals.KW_INT, r'(int)|(цел)')
        self.add_rule(Terminals.KW_STRING, r'string')
        self.add_rule(Terminals.KW_VOID, r'(void)|(ничего)')
        self.add_rule(Terminals.KW_PACKAGE, r'(package)|(пакет)')
        self.add_rule(Terminals.KW_BEGIN, r'(begin)|(начало)')
        self.add_rule(Terminals.KW_END, r'(end)|(конец)')
        self.add_rule(Terminals.KW_WHILE, r'(while)|(пока)')
        self.add_rule(Terminals.KW_DO, r'(do)|(делает)')
        self.add_rule(Terminals.KW_FUNCTION, r'(function)|(функция)')
        self.add_rule(Terminals.KW_MULTIFRAME, r'(multiframe)|(многокадровая)')
        self.add_rule(Terminals.KW_EXTERN, r'extern')        
        self.add_rule(Terminals.KW_VAR, r'var')
        self.add_rule(Terminals.KW_SCOPE, r'scope')
        self.add_rule(Terminals.KW_BOOL, r'bool')
        self.add_rule(Terminals.KW_IMPORT, r'import')
        
        self.add_rule(Terminals.KW_IF, r'if')
        self.add_rule(Terminals.KW_THEN, r'then')
        self.add_rule(Terminals.KW_ELSE, r'else')
        self.add_rule(Terminals.KW_STRUCT, r'struct')        
        self.add_rule(Terminals.KW_RETURN, r'(return)|(возвращает)')
        self.add_rule(Terminals.KW_BREAK, r'break')
        self.add_rule(Terminals.KW_CONTINUE, r'continue')
        self.add_rule(Terminals.KW_SUSPEND, r'(suspend)|(прерывает)')
        
        self.add_rule(Terminals.OP_ATTR, r'=')
        self.add_rule(Terminals.OP_ADD_SUB, r'\+|\-')     
        
        
        self.add_rule(Terminals.S_STAR, r'\*')     
        self.add_rule(Terminals.S_SLASH, r'/')     
        self.add_rule(Terminals.S_PERCENT, r'%')
        

        self.add_rule(Terminals.OP_COMP, r'(<)|(<=)|(>)|(>=)|(==)|(!=)') # there's a bug in regex parser that prevents "<|<=|..."
        
        self.add_rule(Terminals.S_SCOPEACC, r'::')
        self.add_rule(Terminals.S_SEMICOLON, r';')
        self.add_rule(Terminals.S_LPAREN, r'\(')
        self.add_rule(Terminals.S_RPAREN, r'\)')
        self.add_rule(Terminals.S_COMMA, r',')
        self.add_rule(Terminals.S_COLON, r':')
        self.add_rule(Terminals.S_LBRACK, r'\[')
        self.add_rule(Terminals.S_RBRACK, r'\]')
        self.add_rule(Terminals.S_DOT, r"\.")
        
        self.add_rule(Terminals.ID, r'[_A-Za-z][_A-Za-z0-9]*')
        
        self.add_rule(Terminals.EPS, r'')
        
    def parse(self, text):            
        result = Lexer.parse(self, text)        
        
        if not result['success']: return result
        
        tokens = result['tokens']
        
        def is_space_not_allowed_h(tk1, tk2):
            return tk1.token_type.endswith('_LITERAL') and (tk2.token_type.endswith('_LITERAL') or tk2.token_type.startswith('KW_'))
        def is_space_not_allowed(tk1, tk2):
            return is_space_not_allowed_h(tk1, tk2) or is_space_not_allowed_h(tk2, tk1)
        
        for i in range(len(tokens)-1):
            tk1, tk2 = tokens[i], tokens[i+1]            
            if is_space_not_allowed(tk1, tk2):
                return {
                    'tokens':tokens,
                    'success':False,
                    'error': f'There must be a space between consecutive literals and/or keywords (at {(tk2.row, tk2.col)})'
                }

        tokens = list(filter(lambda t:t.token_type!="WS", tokens))        
        
        result['tokens'] = [tk for tk in tokens if tk.token_type!=Terminals.COMMENT]
        
        return result

class DataType(Symbol):
    def __init__(self, name, scope, props):            
        self.props=props
        self.is_array = 'array' in props
        self.is_struct = 'struct' in props
        self.is_pointer = 'pointer' in props
        self.methods = []
        
        if self.is_array:
            arr_data = props['array']            
            assert isinstance(arr_data['element_type'], DataType)
            assert isinstance(arr_data['array_length'], int)
            self.element_type = arr_data['element_type']
            self.array_length = arr_data['array_length']
            
        if self.is_struct:
            struct_data = props['struct']
            self.fields = []
            self.is_extern = 'extern' in struct_data and struct_data['extern'] == True
            
        if self.is_pointer:
            ptr_data = props['pointer']
            assert isinstance(ptr_data['element_type'], DataType)
            self.element_type = ptr_data['element_type']
            
        
        super(DataType, self).__init__(name, symbol_data=self, scope=scope)
    
    def get_full_name(self):
        if self.is_array:
            return f"{self.element_type.get_full_name()}[{self.array_length}]"
        if self.is_pointer:
            return f"{self.element_type.get_full_name()}*"
        return super(DataType, self).get_full_name()
        
    def __str__(self): return f't~{self.get_full_name()}'
    
    def __eq__(self, other): return isinstance(other, DataType) and self.get_full_name() == other.get_full_name()
    def __hash__(self): return hash(self.get_full_name())
    
class Variable(Symbol):
    def __init__(self, name:str, scope, data_type:DataType):
        assert isinstance(data_type, DataType), f"Variable: DataType expected, got {data_type} as {type(data_type)}"
        super(Variable, self).__init__(name, symbol_data=self, scope=scope)        
        self.data_type=data_type
    def __str__(self):        
        return f'v~{self.get_full_name()}'
        
class FormalParameter(Symbol):
    def __init__(self, name:str, scope, data_type:DataType):
        assert isinstance(data_type, DataType), f"FormalParameter: DataType expected, got {data_type} as {type(data_type)}"
        super(FormalParameter, self).__init__(name, symbol_data=self, scope=scope)
        self.data_type=data_type
    def __str__(self):        
        return f'fp~{self.get_full_name()}'
        
class Function(Symbol):
    def __init__(self, name:str, scope, params:list[FormalParameter], return_type:DataType, props:dict):
        assert isinstance(return_type, DataType)
        super(Function, self).__init__(name, symbol_data=self, scope=scope)
        self.params = params
        self.return_type = return_type
        self.is_multiframe = 'multiframe' in props
        self.is_extern = 'extern' in props
        self.implementation = props['impl'] if 'impl' in props else None
        #assert(self.is_extern ^ (self.implementation is not None))
    def __str__(self):        
        return f'fn~{self.get_full_name()}'

class StructMember(Symbol):
    def __init__(self, name:str, scope, declaring_type:DataType):    
        super(StructMember, self).__init__(name, symbol_data=self, scope=scope)        
        self.declaring_type = declaring_type

class Field(StructMember):
    def __init__(self, name:str, scope, declaring_type:DataType, field_type:DataType):
        super(Field, self).__init__(name, scope, declaring_type)
        self.field_type = field_type
    
    def __str__(self):        
        return f"f~{self.get_full_name()}"


class BinaryOperator:
    def __init__(self, symbol:str, arg1_type:DataType, arg2_type:DataType, res_type:DataType):
        self.symbol = symbol
        self.arg1_type = arg1_type
        self.arg2_type = arg2_type
        self.res_type = res_type
    def __str__(self): return f"operator {self.symbol}({self.arg1_type}, {self.arg2_type}):{self.res_type}"

class TypeConverter:
    def __init__(self, input_type:DataType, output_type:DataType):
        self.input_type = input_type
        self.output_type = output_type
    def __str__(self): return f"conv({self.input_type}):{self.output_type}"

class IndexerArchetype:
    def __init__(self, name:str, condition:callable[[DataType, DataType],bool], indexer_creator:callable[[IndexerArchetype, DataType, DataType], Indexer]):
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
        assert isinstance(inarch, IndexerArchetype)
        assert isinstance(element_type, DataType)
        assert isinstance(index_type, DataType)
        assert isinstance(output_type, DataType)
        self.archetype = inarch
        self.element_type = element_type
        self.index_type = index_type
        self.output_type = output_type
    def __str__(self): return f"indexer {self.element_type}[{self.index_type}]:{self.output_type}"
    
class SymbolsRepository:
    def __init__(self):
        self.symbols = []
    
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
    
class _AST_SymbolTerm(_AST_ExpressionNode):
    def __init__(self, symbol:Symbol):
        if isinstance(symbol, Variable):
            super(_AST_SymbolTerm, self).__init__(symbol.data_type)
        elif isinstance(symbol, FormalParameter):
            super(_AST_SymbolTerm, self).__init__(symbol.data_type)
        elif isinstance(symbol, Function):
            super(_AST_SymbolTerm, self).__init__(symbol.return_type)
        else:
            raise ASTException(f"Symbol is not allowed in expressions: {symbol}")
        self.symbol = symbol        

    def __str__(self): return f"{self.symbol}:{self.data_type}"
    def clone(self): return _AST_SymbolTerm(self.symbol)
    
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

class _AST_VDecl(ASTNode):
    def __init__(self, symbol, dtype:_AST_DataTypeIdentifier, scope_stack=None, scope=None):
        super(_AST_VDecl, self).__init__()
        assert symbol.token_type == Terminals.ID        
        self.symbol = symbol
        self.dtype = dtype.data_type
        if scope_stack is not None:
            v = scope_stack.peek().add_symbol(symbol.value, lambda scope: Variable(symbol.value, scope, self.dtype))
        elif scope is not None:
            v = scope.add_symbol(symbol.value, lambda scope: Variable(symbol.value, scope, self.dtype))
        else:
            raise RuntimeError("Both scope and scope_stack are None")
        self.variable = v
        
    def __str__(self): return f"declare {self.variable} : {self.dtype}"
    def clone(self):
        raise RuntimeError("Cloning VDecl is not allowed")
        
class _AST_TypeConvert(_AST_ExpressionNode):
    expression = property(ASTNode.simple_child_getter("expression"), ASTNode.simple_child_setter("expression"))    
    def __init__(self, expression:_AST_ExpressionNode, converter:TypeConverter):
        super(_AST_TypeConvert, self).__init__(self.converter.output_type)    
        self.register_child_key("expression")
        assert isinstance(expression, _AST_ExpressionNode), f"_AST_TypeConvert: ExpressionNode expected, got {type(expression)}"
        assert isinstance(converter, TypeConverter), f"_AST_TypeConvert: Converter expected, got {type(converter)}"
        self.expression = expression
        self.converter = converter        
        
    def __str__(self): return f"conv({self.expression}, {self.data_type})"
    def clone(self): return _AST_TypeConvert(self.expression.clone(), self.converter)

class _AST_Attr(ASTNode):
    left = property(ASTNode.simple_child_getter("left"), ASTNode.simple_child_setter("left"))
    right = property(ASTNode.simple_child_getter("right"), ASTNode.simple_child_setter("right"))
    
    def __init__(self, left, right, op_solver):
        super(_AST_Attr, self).__init__()
        self.register_child_key("left")
        self.register_child_key("right")
    
        assert isinstance(left, _AST_ExpressionNode), "_AST_Attr: Non-expression node at the left of the assignment"
        assert isinstance(right, _AST_ExpressionNode), "_AST_Attr: Non-expression node at the right of the assignment"
        
        if left.data_type != right.data_type:            
            converter = op_solver.resolve_converter(right.data_type, left.data_type)
            right = _AST_TypeConvert(right, converter)        
        self.left = left
        self.right = right        
        
    def __str__(self): return f"{self.left} = {self.right}"
    def clone(self):
        return _AST_Attr(self.left.clone(), self.right.clone())

class _AST_IndexAccessor(_AST_ExpressionNode):
    element = property(ASTNode.simple_child_getter("element"), ASTNode.simple_child_setter("element"))    
    index = property(ASTNode.simple_child_getter("index"), ASTNode.simple_child_setter("index"))    
    
    def __init__(self, element: _AST_ExpressionNode, index: _AST_ExpressionNode, indexer:Indexer):        
        assert isinstance(element, _AST_ExpressionNode)
        assert isinstance(index, _AST_ExpressionNode)
        assert isinstance(indexer, Indexer)
        super(_AST_IndexAccessor, self).__init__(indexer.output_type)
        self.register_child_key("element")
        self.register_child_key("index")
        self.element = element
        self.index = index
        self.indexer = indexer        
    
    def __str__(self): return f"({self.element})[{self.index}]:{self.data_type}"
    def clone(self): return _AST_IndexAccessor(self.element.clone(), self.index.clone(), self.indexer)

class _AST_FieldAccessor(_AST_ExpressionNode):
    element = property(ASTNode.simple_child_getter("element"), ASTNode.simple_child_setter("element"))   

    def __init__(self, element:_AST_ExpressionNode, field:Field):
        assert isinstance(element, _AST_ExpressionNode)
        assert isinstance(field, Field)
        super(_AST_FieldAccessor, self).__init__(field.field_type)
        self.register_child_key("element")
        self.element = element
        self.field = field        
        assert isinstance(field.declaring_type, DataType)
        assert isinstance(element.data_type, DataType)
        assert field.declaring_type == element.data_type
        assert isinstance(field.field_type, DataType)
    def __str__(self): return f"({self.element}).{self.field}:{self.data_type}"

    def clone(self): return _AST_FieldAccessor(self.element.clone, self.field)

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
        lines = '\n  '.join(str(self.block).splitlines())
        return f"while {self.condition} do begin\n  {lines}\nend"
        
class _AST_If(ASTNode):
    condition = property(ASTNode.simple_child_getter("condition"), ASTNode.simple_child_setter("condition"))
    then_branch = property(ASTNode.simple_child_getter("then_branch"), ASTNode.simple_child_setter("then_branch"))
    else_branch = property(ASTNode.simple_child_getter("else_branch"), ASTNode.simple_child_setter("else_branch"))

    def __init__(self, cond, then_branch, else_branch):
        super(_AST_If, self).__init__()
        self.register_child_key("condition")
        self.register_child_key("then_branch")
        self.register_child_key("else_branch")
    
        self.condition = cond
        self.then_branch = then_branch
        self.else_branch = else_branch        
    def __str__(self):
        lines_then = '\n  '.join(str(self.then_branch).splitlines())
        if self.else_branch is not None:
            lines_else = '\n  '.join(str(self.else_branch).splitlines())
            return f"if {self.condition} then begin\n  {lines_then}\nend else begin\n  {lines_else}\nend"
        else:
            return f"if {self.condition} then begin\n  {lines_then}\nend"
    
class _AST_DataTypeIdentifier(ASTNode):
    def __init__(self, symbol):        
        if not isinstance(symbol, DataType):
            raise ASTException(f"Data type identifier expected, got {symbol}")
        self.data_type = symbol
    def __str__(self): return f"{self.data_type}"
    
    @staticmethod
    def make_array(element_type: _AST_DataTypeIdentifier, array_length: _AST_Literal):
        assert isinstance(array_length, _AST_Literal), f"Expected Literal, got {type(array_length)}"
        assert isinstance(array_length.value, int)
        data_type = DataType("@Array", None, { 'array': { 'element_type':element_type.data_type, 'array_length':array_length.value } })
        return _AST_DataTypeIdentifier(data_type)
        
    @staticmethod
    def make_pointer(element_type: _AST_DataTypeIdentifier):
        data_type = DataType("@Pointer", None, { 'pointer': { 'element_type':element_type.data_type } })
        return _AST_DataTypeIdentifier(data_type)

class _AST_Package(ASTNode):
    children = property(ASTNode.simple_children_list_getter("children"))

    def __init__(self, name_token, block, scope):
        super(_AST_Package, self).__init__()        
        assert isinstance(block, ASTNodes.Block)
        self.register_children_list_key("children")
        
        self.name = name_token.value
        
        children = list(block.children)
        for child in children:
            child.set_parent(self, "children")
        
        self.scope = scope        
    
    def __str__(self):
        content = ";\n".join(map(str, self.children))
        lines = '\n  '.join(content.splitlines())
        return f"package {self.name} begin\n  {lines}\nend"
        
class _AST_StructDecl(ASTNode):
    def __init__(self, symbol: DataType, members):
        super(_AST_StructDecl, self).__init__()
        assert isinstance(symbol, DataType), "StructDecl: Expected DataType, found {type(symbol)}"
        self.symbol = symbol
        self.members = members if members is not None else []        
    
    def __str__(self):        
        lines = '\n  '.join('\n'.join(list(map(str, self.members))).splitlines())        
        return f"struct {self.symbol} begin\n  {lines}\nend"

class _AST_StructFieldDecl(ASTNode):
    def __init__(self, name_token, field_type:_AST_DataTypeIdentifier, scope_stack):
        super(_AST_StructFieldDecl, self).__init__()
        scope = scope_stack.peek()
        declaring_type = scope.symbolic_value
        assert isinstance(declaring_type, DataType)        
        assert isinstance(field_type, _AST_DataTypeIdentifier)        
        f = scope_stack.peek().add_symbol(name_token.value, lambda scope: Field(name_token.value, scope, None, field_type.data_type))
        f.declaring_type = declaring_type
        declaring_type.fields.append(f)
        self.field = f
    
    def __str__(self): return f"{self.field} : {self.field.field_type}"

class _AST_FunDecl(ASTNode):    

    def get_implementation(self):
        return self.function.implementation
    
    def set_implementation(self, impl):
        self.function.implementation = impl
        if impl is not None:
            self._node_set_implementation(self, impl)
    
    implementation = property(get_implementation, set_implementation)

    def __init__(self, function:Function):
        super(_AST_FunDecl, self).__init__()
        self.register_child_key("implementation")
        self._node_set_implementation = ASTNode.simple_child_setter('implementation')
        
        assert isinstance(function, Function)
        self.function = function
        self.implementation = function.implementation
        
    def __str__(self): 
        params = ", ".join(map(lambda p:f"{p}: {p.data_type}", self.function.params))
        body = '\n  '.join(str(self.function.implementation or "").splitlines())
        if body!="": body="\nbegin\n  "+body+"\nend"
        flags = []
        if self.function.is_extern: flags.append("E")
        if self.function.is_multiframe: flags.append("M")
        flags = ("["+"".join(flags)+"]") if len(flags)>0 else ""
        return f"function{flags} {self.function}({params}) : {self.function.return_type} {body}"
        
class _AST_Break(ASTSimpleInstruction):
    def __init__(self):
        super(_AST_Break, self).__init__("break") 

class _AST_Continue(ASTSimpleInstruction):
    def __init__(self):
        super(_AST_Continue, self).__init__("continue") 

class _AST_Suspend(ASTSimpleInstruction):
    def __init__(self):
        super(_AST_Suspend, self).__init__("suspend") 
    
class _AST_Return(ASTNode):
    value = property(ASTNode.simple_child_getter("value"), ASTNode.simple_child_setter("value"))

    def __init__(self, value:_AST_ExpressionNode|None, void_type:DataType):
        super(_AST_Return, self).__init__()
        self.register_child_key("value")
        assert value is None or isinstance(value, _AST_ExpressionNode)
        assert isinstance(void_type, DataType)
        self.value = value
        self.return_type = void_type if value is None else self.value.data_type        
        
    def __str__(self): return "return" if self.value is None else f"return {self.value}"

class _AST_FunCall(_AST_ExpressionNode):
    args = property(ASTNode.simple_children_list_getter("args"))
    
    def __init__(self, func:Function, args:list[_AST_ExpressionNode]):        
        assert isinstance(func, Function)
        super(_AST_FunCall, self).__init__(func.return_type)
        self.register_children_list_key("args")
        
        params = func.params
        if len(params)!=len(args):
            raise ASTException(f"Invalid number of arguments to call {func}: expected {len(params)}, got {len(args)}")
        for i, (p,a) in enumerate(zip(params, args)):
            if p.data_type!=a.data_type:
                raise ASTException(f"Invalid argument {i+1} when calling {func}: expected {p.data_type}, got {a.data_type}")
        
        self.function = func        
        for arg in args:
            assert isinstance(arg, ASTNode)
            arg.set_parent(self, "args")
    
    def __str__(self):
        return f"(call {self.function}({', '.join(map(str, self.args))}))"
    
    def clone(self):
        return _AST_FunCall(self.function, list(map(lambda a:a.clone(), self.args)))

class _AST_Import(ASTNode):    
    def __init__(self, path):
        super(_AST_Import, self).__init__()
        self.path=path
    
    def __str__(self): return f'import "{self.path}"'
    def clone(self): return _AST_Import(self.path)

class __namespace: pass
ASTNodes = __namespace()
ASTNodes.Literal = _AST_Literal
ASTNodes.SymbolTerm = _AST_SymbolTerm
ASTNodes.BinaryOperator = _AST_BinaryOperator
ASTNodes.IndexAccessor = _AST_IndexAccessor
ASTNodes.FieldAccessor = _AST_FieldAccessor
ASTNodes.FunCall = _AST_FunCall
ASTNodes.Block = ASTBlock
ASTNodes.VDecl = _AST_VDecl
ASTNodes.Attr = _AST_Attr
ASTNodes.DataTypeIdentifier = _AST_DataTypeIdentifier
ASTNodes.While = _AST_While
ASTNodes.Package = _AST_Package
ASTNodes.If = _AST_If
ASTNodes.StructDecl = _AST_StructDecl
ASTNodes.StructFieldDecl = _AST_StructFieldDecl
ASTNodes.FunDecl = _AST_FunDecl
ASTNodes.Break = _AST_Break
ASTNodes.Continue = _AST_Continue
ASTNodes.Suspend = _AST_Suspend
ASTNodes.Return = _AST_Return
ASTNodes.Expression = _AST_ExpressionNode
ASTNodes.Import = _AST_Import


class ScopeNameProvider:
    def __init__(self):
        self.counter=0
    
    def new_name(self):
        self.counter+=1
        return f"@{self.counter}"

class OperatorSolver:
    def __init__(self):
        self.binary_operators: dict[tuple[str, DataType, DataType], BinaryOperator] = {}
        self.converters: dict[tuple[DataType, DataType], TypeConverter] = {}
        self.indexers: dict[tuple[DataType, DataType], Indexer] = {}
        self.indexer_archetypes: list[IndexerArchetype] = []
        
    def __register(self, dct, key, value_fun, err_fun):
        if key in dct: raise ASTException(err_fun())
        dct[key] = it = value_fun()
        return it
    
    def __resolve(self, dct, key, err_fun):
        if not key in dct: raise ASTException(err_fun())
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

    def register_indexer_archetype(self, inarch):
        self.indexer_archetypes.append(inarch)        
            
    def resolve_indexer(self, element_type, index_type):
        for inarch in self.indexer_archetypes:
            if inarch.validate(element_type, index_type):                
                A = inarch.create_indexer(element_type, index_type)                
                return inarch.create_indexer(element_type, index_type)
        
        if element_type.is_pointer:
            return Indexer()
            
        
        raise ASTException(f"No indexer found for {element_type}[{index_type}]")        

class CelsParser:
    def __init__(self):
        self.rcf = rcf = RuleComponentFactory(on_match=lambda val, token: val == token.token_type)
                
        S = rcf.non_terminal("S") # Start symbol                        
        P = rcf.non_terminal("P") # Program                        
        B = rcf.non_terminal("B") # Code Block
        E = rcf.non_terminal("E") # Expression
        A = rcf.non_terminal("A") # Additive term
        M = rcf.non_terminal("M") # Multiplicative term
        T = rcf.non_terminal("T") # Expression terminal        
        
        DTYPE = rcf.non_terminal("DTYPE")
        VDECL = rcf.non_terminal("VDECL")        
        DTYPE = rcf.non_terminal("DTYPE")
        ATTR = rcf.non_terminal("ATTR")
        ACCESSOR = rcf.non_terminal("ACCESSOR")        
        SYMBOL = rcf.non_terminal("SYMBOL")
        SYMBOL_TERM = rcf.non_terminal("SYMBOL_TERM")
        BLOCK = rcf.non_terminal("BLOCK")        
        PACKAGE_DECL = rcf.non_terminal("PACKAGE_DECL")
        BBODY = rcf.non_terminal("BBODY")        
        SYM_ACC = rcf.non_terminal("SYM_ACC")
        SYM_CHAIN = rcf.non_terminal("SYM_CHAIN")        
        MEMBER_LIST = rcf.non_terminal("MEMBER_LIST")
        STRUCT_MEMBER = rcf.non_terminal("STRUCT_MEMBER")
        FPARAMS_LIST = rcf.non_terminal("FPARAMS_LIST")
        FPARAMS_LIST_W_PARENS = rcf.non_terminal("FPARAMS_LIST_W_PARENS")
        FPARAM = rcf.non_terminal("FPARAM")
        FUN_HEADER = rcf.non_terminal("FUN_HEADER")
        E_LIST = rcf.non_terminal("E_LIST")
        FARGS_LIST_W_PARENS = rcf.non_terminal("FARGS_LIST_W_PARENS")
        FARGS_LIST = rcf.non_terminal("FARGS_LIST")
        
        SCOPED_BEGIN = rcf.non_terminal("SCOPED_BEGIN")
        SCOPED_BLOCK = rcf.non_terminal("SCOPED_BLOCK")
        SCOPED_DO = rcf.non_terminal("SCOPED_DO")
        SCOPED_THEN = rcf.non_terminal("SCOPED_THEN")
        SCOPED_ELSE = rcf.non_terminal("SCOPED_ELSE")        
        SCOPED_STRUCT_DECL = rcf.non_terminal("SCOPED_STRUCT_DECL")
        
        SCOPE_PUSH_BEGIN = rcf.non_terminal("SCOPE_PUSH_BEGIN")
        SCOPE_POP_END = rcf.non_terminal("SCOPE_POP_END")
        
        s_star =  rcf.terminal(Terminals.S_STAR)
        s_slash =  rcf.terminal(Terminals.S_SLASH)
        s_percent =  rcf.terminal(Terminals.S_PERCENT)
        
        s_add_sub = rcf.terminal(Terminals.OP_ADD_SUB)        
        s_comp = rcf.terminal(Terminals.OP_COMP)
        s_lparen = rcf.terminal(Terminals.S_LPAREN)
        s_rparen = rcf.terminal(Terminals.S_RPAREN)
        s_scopeacc = rcf.terminal(Terminals.S_SCOPEACC)
        s_comma = rcf.terminal(Terminals.S_COMMA)
        s_semicolon = rcf.terminal(Terminals.S_SEMICOLON)
        s_colon = rcf.terminal(Terminals.S_COLON)
        s_lbrack = rcf.terminal(Terminals.S_LBRACK)
        s_rbrack = rcf.terminal(Terminals.S_RBRACK)
        s_dot = rcf.terminal(Terminals.S_DOT)
        
        dec_literal = rcf.terminal(Terminals.DEC_LITERAL)
        int_literal = rcf.terminal(Terminals.INT_LITERAL)
        string_literal = rcf.terminal(Terminals.STRING_LITERAL)
        kw_int = rcf.terminal(Terminals.KW_INT)
        kw_string = rcf.terminal(Terminals.KW_STRING)
        kw_void = rcf.terminal(Terminals.KW_VOID)
        kw_package = rcf.terminal(Terminals.KW_PACKAGE)
        kw_while = rcf.terminal(Terminals.KW_WHILE)
        kw_begin = rcf.terminal(Terminals.KW_BEGIN)
        kw_end = rcf.terminal(Terminals.KW_END)
        kw_do = rcf.terminal(Terminals.KW_DO)
        kw_if = rcf.terminal(Terminals.KW_IF)
        kw_then = rcf.terminal(Terminals.KW_THEN)
        kw_else = rcf.terminal(Terminals.KW_ELSE)
        kw_struct = rcf.terminal(Terminals.KW_STRUCT)
        kw_function = rcf.terminal(Terminals.KW_FUNCTION)
        kw_multiframe = rcf.terminal(Terminals.KW_MULTIFRAME)
        kw_extern = rcf.terminal(Terminals.KW_EXTERN)
        kw_return = rcf.terminal(Terminals.KW_RETURN)
        kw_break = rcf.terminal(Terminals.KW_BREAK)
        kw_continue = rcf.terminal(Terminals.KW_CONTINUE)
        kw_suspend = rcf.terminal(Terminals.KW_SUSPEND)
        kw_var = rcf.terminal(Terminals.KW_VAR)
        kw_scope = rcf.terminal(Terminals.KW_SCOPE)
        kw_bool = rcf.terminal(Terminals.KW_BOOL)
        kw_import = rcf.terminal(Terminals.KW_IMPORT)
        
        op_attr = rcf.terminal(Terminals.OP_ATTR)
        eps = rcf.terminal(Terminals.EPS)
        
        t_id = rcf.terminal(Terminals.ID)

        def token2text(t): return t.value             
        
        self.scope_tree = scope_tree = ScopeTree()
        self.global_scope = global_scope = scope_tree.global_scope
        self.internal_scope = global_scope.get_scope("cels_internal", strategy="create")
        self.internal_id = 0
        scope_stack = ScopeStack(scope_tree)
        scope_name_provider = ScopeNameProvider()
        
        self.dtype_float32 = dtype_float32 = global_scope.add_symbol('float', lambda scope: DataType('float', scope, {}))
        self.dtype_int = dtype_int = global_scope.add_symbol('int', lambda scope: DataType('int', scope, {}))
        self.dtype_string = dtype_string = global_scope.add_symbol('string', lambda scope: DataType('string', scope, {}))
        self.dtype_void = dtype_void = global_scope.add_symbol('void', lambda scope: DataType('void', scope, {}))
        self.dtype_bool = dtype_bool = global_scope.add_symbol('bool', lambda scope: DataType('bool', scope, {}))
        
        self.op_solver = op_solver = OperatorSolver()
        op_solver.register_binary_operator('+', dtype_int, dtype_int, dtype_int)
        op_solver.register_binary_operator('-', dtype_int, dtype_int, dtype_int)
        op_solver.register_binary_operator('*', dtype_int, dtype_int, dtype_int)
        op_solver.register_binary_operator('/', dtype_int, dtype_int, dtype_int)
        op_solver.register_binary_operator('%', dtype_int, dtype_int, dtype_int)
        op_solver.register_binary_operator('<', dtype_int, dtype_int, dtype_bool)
        op_solver.register_binary_operator('>', dtype_int, dtype_int, dtype_bool)
        op_solver.register_binary_operator('<=', dtype_int, dtype_int, dtype_bool)
        op_solver.register_binary_operator('>=', dtype_int, dtype_int, dtype_bool)
        op_solver.register_binary_operator('==', dtype_int, dtype_int, dtype_bool)
        op_solver.register_binary_operator('!=', dtype_int, dtype_int, dtype_bool)
        
        op_solver.register_converter(dtype_int, dtype_float32)
        
        self.inarch_array_index = IndexerArchetype("array_index",
            condition = lambda E,I: E.is_array and I==dtype_int,
            indexer_creator = lambda A,E,I: Indexer(A,E,I,E.element_type)
        )        
        op_solver.register_indexer_archetype(self.inarch_array_index)
        
        self.ptr_index_inarch = IndexerArchetype("ptr_ix", 
            lambda E,I: E.is_pointer and I==dtype_int,
            lambda A, E, I: Indexer(A, E, I, E.element_type)
        )
        op_solver.register_indexer_archetype(self.ptr_index_inarch)
        
        def resolve_sym(token): return scope_stack.peek().resolve_symbol(token.value, recursive=True)
        def resolve_sym_chain(tokens): 
            return scope_stack.peek().resolve_symbol([token.value for token in tokens], recursive=True)        
        def resolve_pack_decl(token): 
            scope_stack.push(token.value, strategy='get_or_create')
            return token
                
        def build_package_node(name_token, block):
            scope = scope_stack.peek()        
            package = ASTNodes.Package(name_token, block, scope)
            #print(scope_stack.peek().get_full_name())
            #raise ""
            scope_stack.pop()            
            return package
            
        def begin_scope(arg, scope_name=None):
            scope_stack.push(scope_name_provider.new_name() if scope_name is None else scope_name.value)            
            return arg
        
        def end_scope(arg):
            scope_stack.pop()
            return arg
            
        def declare_scoped_data_type(arg, props:dict={}):    
            name = arg.value
            scope_stack.push(name)
            scope_stack.peek().set_symbolic_value(lambda scope: DataType(name, scope, props={'struct':props}))
            data_type = scope_stack.peek().symbolic_value
            #print("\nSVAL =",scope_stack.peek().symbolic_value,"\n!!!!!!!!!!!")                        
            return data_type
            
        def declare_scoped_function(arg):
            name = arg.value
            scope_stack.push(name)
            scope_stack.peek().set_symbolic_value(lambda scope: Function(name, scope, props={}))
            return arg
            
        def pop_push_scope(arg):
            scope_stack.pop()
            scope_stack.push(scope_name_provider.new_name())
            return arg
        
        def build_scoped_block(block):
            scope_stack.pop()
            return block
            
        def build_scoped_struct_decl(symbol, members):
            struct = ASTNodes.StructDecl(symbol, members)            
            scope_stack.pop()
            return struct
            
        def build_extern_scoped_struct_decl(symbol):
            struct = ASTNodes.StructDecl(symbol, [])
            scope_stack.pop()
            return struct
        
        def prepend_list(s, lst): return [s] + (lst if lst is not None else [])
        
        def empty_block(): return ASTNodes.Block()
        
        def create_formal_param_data(name_token, data_type):
            name = name_token.value
            #param = scope_stack.peek().add_symbol(name, lambda scope:FormalParameter(name, scope, data_type))
            return (name, data_type)
        
        def build_fun_header(name_token, params:list|None, return_type:_AST_DataTypeIdentifier, props):
            assert isinstance(return_type, _AST_DataTypeIdentifier)
            return_type = return_type.data_type
            assert isinstance(return_type, DataType)
            
            scope = scope_stack.peek()
            is_method = False
            if isinstance(scope.symbolic_value, DataType):
                is_method = True
                declaring_type = scope.symbolic_value
                params = [("this", declaring_type)] + params
        
            name = name_token.value
            fun_scope = scope_stack.push(name)
            
            scope = scope_stack.peek()
            
            params = list(map(lambda p: scope.add_symbol(p[0], lambda scope:FormalParameter(p[0], scope, p[1])), params or []))             
            
            scope_stack.peek().set_symbolic_value(lambda scope: Function(name, scope, params, return_type, props or {}))
            
            if is_method:
                fun_scope.properties['this_solver'] = params[0]
                declaring_type.methods.append(scope_stack.peek().symbolic_value)
            
            return scope_stack.peek().symbolic_value
        
        def reduce_function_decl(f:Function, body):                        
            f.implementation = body
            #print("!!!!!!!!!!\n~~~~~~~~~~~=", scope_stack.peek().get_full_name(), "\n\n")
            scope_stack.pop()
            return ASTNodes.FunDecl(f)
            
        def reduce_binary_operator(left:_AST_ExpressionNode, op_token, right:_AST_ExpressionNode):                        
            operator = op_solver.resolve_binary_operator(op_token.value, left.data_type, right.data_type)
            return ASTNodes.BinaryOperator(operator, left, right)
            
        def token2int_literal(token):
            return rc.call(ASTNodes.Literal, rc.call(int, rc.call(token2text, token)), dtype_int)        
            
        def empty_list(): return []
        
        def reduce_indexer(element:_AST_ExpressionNode, index:_AST_ExpressionNode):
            assert isinstance(element, _AST_ExpressionNode)
            assert isinstance(index, _AST_ExpressionNode)            
            e_type = element.data_type
            i_type = index.data_type
            indexer = op_solver.resolve_indexer(e_type, i_type)
            return ASTNodes.IndexAccessor(element, index, indexer)     

        def reduce_while(cond, body):
            scope_stack.pop()
            return ASTNodes.While(cond, body)
            
        def reduce_symbol_term(symbol):
            if isinstance(symbol, Variable) or isinstance(symbol, FormalParameter):
                return ASTNodes.SymbolTerm(symbol)
            if isinstance(symbol, Field):
                scope = scope_stack.peek()                
                this_solver:Symbol = scope.find_property("this_solver")
                if this_solver is None:
                    raise ASTException(f"Unable to solve formal parameter {symbol}: `this` is not defined in this context")
                this_term = ASTNodes.SymbolTerm(this_solver)
                return ASTNodes.FieldAccessor(this_term, symbol)
            if isinstance(symbol, Function):
                return ASTNodes.SymbolTerm(symbol)
            
            
            raise RuntimeError(f"reduce_symbol_term: Not implemented: {symbol}")
            
        class ObjectClosure:
            def __init__(self, obj, method):
                self.obj=obj
                self.method = method
            
        def reduce_dot_accessor(element:_AST_ExpressionNode, id_token):
            assert isinstance(element, _AST_ExpressionNode)
            data_type = element.data_type
            assert isinstance(data_type, DataType)            
            
            if data_type.is_struct:
                field_search = [f for f in data_type.fields if f.name==id_token.value]
                if len(field_search)>0:
                    return ASTNodes.FieldAccessor(element, field_search[0])
            
            method_search = [m for m in data_type.methods if m.name==id_token.value]
            if len(method_search)>0:
                return ObjectClosure(element, method_search[0])
            
            raise ASTException(f"Could not find member `{id_token.value}` under {element.data_type}")
        
        def reduce_funcall(fun, args:list[_AST_ExpressionNode]):            
            if isinstance(fun, ObjectClosure):
                args = [fun.obj] + args
                fun = fun.method
            
            assert isinstance(fun, ASTNodes.SymbolTerm)
            fun = fun.symbol
            
            if not isinstance(fun, Function):
                raise ASTException(f"Expected callable expression, got {fun}")
            
            assert isinstance(fun, Function)
            assert isinstance(args, list)
            assert all([isinstance(item, _AST_ExpressionNode) for item in args])
            return ASTNodes.FunCall(fun, args)
            
        def print_scope():
            print("Debug scope:", scope_stack.peek().get_full_name())
            return ASTNodes.Block()
            
        def build_block(*children):
            b = ASTNodes.Block(*children)
            b.properties['scope'] = scope_stack.peek()
            return b
        
        def build_initial_value_vdecl(t_id, dtype, expr):
            if dtype is None:
                dtype = _AST_DataTypeIdentifier(expr.data_type)
            vdecl = ASTNodes.VDecl(t_id, dtype, scope_stack)
            attr = ASTNodes.Attr(ASTNodes.SymbolTerm(vdecl.variable), expr, op_solver)
            return build_block(vdecl, attr)
            
        def reduce_import(path):
            if scope_stack.peek() != global_scope:
                raise ASTException("Import statements must be declared in global scope")
            #print(f"IMPORT {path}")
            if self.import_solver is None:
                return ASTNodes.Import(path)
            return self.import_solver(path) or ASTNodes.Block()
        
        self.import_solver = None
        
        G = Grammar([
            ( S << P                       ).on_build(rc.arg(0)),
            ( P << BLOCK                   ).on_build(rc.arg(0)),            
            ( BLOCK << B * s_semicolon * BLOCK ).on_build(rc.call(build_block, rc.arg(0), rc.arg(2))),            
            ( BLOCK << B * s_semicolon       ).on_build(rc.call(build_block, rc.arg(0))),
            
            ( B << VDECL                    ).on_build(rc.arg(0)),
            # Assign
            ( B << ACCESSOR * op_attr * E   ).on_build(rc.call(ASTNodes.Attr, rc.arg(0), rc.arg(2), op_solver)),
            ( B << kw_scope   ).on_build(rc.call(print_scope)),
            
            # Import clause
            #( B << kw_import * string_literal).on_build(rc.call(ASTNodes.Import, rc.call(lambda lit:eval(lit.value), rc.arg(1)))),
            ( B << kw_import * string_literal).on_build(rc.call(reduce_import, rc.call(lambda lit:eval(lit.value), rc.arg(1)))),
            
            # Package
            ( B << PACKAGE_DECL * kw_begin * BLOCK * kw_end).on_build(rc.call(build_package_node, rc.arg(0), rc.arg(2))),            
            ( B << PACKAGE_DECL * kw_begin * kw_end).on_build(rc.call(build_package_node, rc.arg(0), rc.call(empty_block))),
            
            #while body
            ( B << kw_while * E * SCOPED_DO * BBODY).on_build(rc.call(reduce_while, rc.arg(1), rc.arg(3))),            
            ( B << kw_break ).on_build(rc.call(ASTNodes.Break)),
            ( B << kw_continue ).on_build(rc.call(ASTNodes.Continue)),
            ( B << kw_suspend ).on_build(rc.call(ASTNodes.Suspend)),
            
            # struct declaration
            ( B << SCOPED_STRUCT_DECL).on_build(rc.call(build_scoped_struct_decl, rc.arg(0), None)),
            ( B << SCOPED_STRUCT_DECL * kw_begin * kw_end).on_build(rc.call(build_scoped_struct_decl, rc.arg(0), None)),
            ( B << SCOPED_STRUCT_DECL * kw_begin * MEMBER_LIST * kw_end).on_build(rc.call(build_scoped_struct_decl, rc.arg(0), rc.arg(2))),            
            
            # function 
            ( B << FUN_HEADER * SCOPE_PUSH_BEGIN * BLOCK * SCOPE_POP_END ).on_build(rc.call(reduce_function_decl, rc.arg(0), rc.arg(2))),
            ( B << FUN_HEADER * SCOPE_PUSH_BEGIN * SCOPE_POP_END ).on_build(rc.call(reduce_function_decl, rc.arg(0), rc.call(build_block))),
            ( B << FUN_HEADER ).on_build(rc.call(reduce_function_decl, rc.arg(0), None)),
            
            ( B << kw_return ).on_build(rc.call(_AST_Return, None, dtype_void)),
            ( B << kw_return * E ).on_build(rc.call(_AST_Return, rc.arg(1), dtype_void)),
            
            # if body
            ( B << kw_if * E * SCOPED_THEN * BBODY * s_semicolon * SCOPED_ELSE * BBODY * s_semicolon * SCOPE_POP_END).on_build(rc.call(ASTNodes.If, rc.arg(1), rc.arg(3), rc.arg(6))),
            ( B << kw_if * E * SCOPED_THEN * BBODY * s_semicolon * SCOPE_POP_END).on_build(rc.call(ASTNodes.If, rc.arg(1), rc.arg(3), None)),
            
            ( BBODY << kw_begin * BLOCK * kw_end).on_build(rc.arg(1)),
            ( BBODY << kw_begin * kw_end).on_build(rc.call(empty_block)),
            ( BBODY << B).on_build(rc.arg(0)),
            
            ( SCOPED_DO << kw_do).on_build(rc.call(begin_scope, rc.arg(0))),                        
            ( SCOPED_THEN << kw_then).on_build(rc.call(begin_scope, rc.arg(0))),            
            ( SCOPED_ELSE << kw_else).on_build(rc.call(pop_push_scope, rc.arg(0))),            
            ( SCOPED_STRUCT_DECL << kw_struct * t_id).on_build(rc.call(declare_scoped_data_type, rc.arg(1))),   
            ( SCOPED_STRUCT_DECL << kw_extern * kw_struct * t_id).on_build(rc.call(declare_scoped_data_type, rc.arg(2), {'extern':True})),
            
            ( SCOPE_PUSH_BEGIN << kw_begin).on_build(rc.call(begin_scope, rc.arg(0))),
            ( SCOPE_POP_END << kw_end).on_build(rc.call(end_scope, rc.arg(0))),
            
            ( PACKAGE_DECL << kw_package * t_id ).on_build(rc.call(resolve_pack_decl, rc.arg(1))),
            
            ( FUN_HEADER << kw_function * t_id * FPARAMS_LIST_W_PARENS * s_colon * DTYPE).on_build(rc.call(build_fun_header, rc.arg(1), rc.arg(2), rc.arg(4), {})),            
            ( FUN_HEADER << kw_extern * kw_function * t_id * FPARAMS_LIST_W_PARENS * s_colon * DTYPE).on_build(rc.call(build_fun_header, rc.arg(2), rc.arg(3), rc.arg(5), {'extern':1})),           
            ( FUN_HEADER << kw_multiframe * kw_function * t_id * FPARAMS_LIST_W_PARENS * s_colon * DTYPE).on_build(rc.call(build_fun_header, rc.arg(2), rc.arg(3), rc.arg(5), {'multiframe':1})),           
            ( FUN_HEADER << kw_extern * kw_multiframe * kw_function * t_id * FPARAMS_LIST_W_PARENS * s_colon * DTYPE).on_build(rc.call(build_fun_header, rc.arg(3), rc.arg(4), rc.arg(6), {'extern':1, 'multiframe':1})),           
            
            ( FPARAMS_LIST_W_PARENS << s_lparen * FPARAMS_LIST * s_rparen ).on_build(rc.arg(1)),
            ( FPARAMS_LIST_W_PARENS << s_lparen * s_rparen ).on_build(rc.call(empty_list)),
            
            ( FPARAMS_LIST << FPARAM * s_comma * FPARAMS_LIST ).on_build(rc.call(prepend_list, rc.arg(0), rc.arg(2))),
            ( FPARAMS_LIST << FPARAM ).on_build(rc.call(prepend_list, rc.arg(0), None)),
            
            ( FPARAM << t_id * s_colon * DTYPE ).on_build(rc.call(create_formal_param_data, rc.arg(0), rc.call(lambda _:_.data_type, rc.arg(2)))),
            
            ( MEMBER_LIST << STRUCT_MEMBER * s_semicolon * MEMBER_LIST ).on_build(rc.call(prepend_list, rc.arg(0), rc.arg(2))),
            ( MEMBER_LIST << STRUCT_MEMBER * s_semicolon ).on_build(rc.call(prepend_list, rc.arg(0), None)),
            
            # Field
            ( STRUCT_MEMBER << kw_var * t_id * s_colon * DTYPE).on_build(rc.call(ASTNodes.StructFieldDecl, rc.arg(1), rc.arg(3), scope_stack)),            
            # Method
            ( STRUCT_MEMBER << FUN_HEADER * SCOPE_PUSH_BEGIN * BLOCK * SCOPE_POP_END ).on_build(rc.call(reduce_function_decl, rc.arg(0), rc.arg(2))),            
            ( STRUCT_MEMBER << FUN_HEADER ).on_build(rc.call(reduce_function_decl, rc.arg(0), None)),
            
            ( VDECL << kw_var * t_id * s_colon * DTYPE ).on_build(rc.call(ASTNodes.VDecl, rc.arg(1), rc.arg(3), scope_stack)),
            ( VDECL << kw_var * t_id * s_colon * DTYPE * op_attr * E).on_build(rc.call(build_initial_value_vdecl, rc.arg(1), rc.arg(3), rc.arg(5))),
            ( VDECL << kw_var * t_id * op_attr * E).on_build(rc.call(build_initial_value_vdecl, rc.arg(1), None, rc.arg(3))),
            
            ( DTYPE << SYMBOL              ).on_build(rc.call(ASTNodes.DataTypeIdentifier, rc.arg(0))),
            ( DTYPE << kw_int              ).on_build(rc.call(ASTNodes.DataTypeIdentifier, dtype_int)),
            ( DTYPE << kw_string           ).on_build(rc.call(ASTNodes.DataTypeIdentifier, dtype_string)),
            ( DTYPE << kw_void             ).on_build(rc.call(ASTNodes.DataTypeIdentifier, dtype_void)),
            ( DTYPE << kw_bool             ).on_build(rc.call(ASTNodes.DataTypeIdentifier, kw_bool)),
            ( DTYPE << DTYPE * s_lbrack * int_literal * s_rbrack).on_build(rc.call(ASTNodes.DataTypeIdentifier.make_array, rc.arg(0), token2int_literal(rc.arg(2)))),
            ( DTYPE << DTYPE * s_star).on_build(rc.call(ASTNodes.DataTypeIdentifier.make_pointer, rc.arg(0))),
            
            ( B << E                       ).on_build(rc.arg(0)),
            
            ( E << E * s_comp * A          ).on_build(rc.call(reduce_binary_operator, rc.arg(0), rc.arg(1), rc.arg(2))),
            ( E << A                       ).on_build(rc.arg(0)),
            
            #( A << A * s_add_sub * M       ).on_build(rc.call(rc_op_as_switch, rc.arg(0), rc.arg(2))),
            ( A << A * s_add_sub * M       ).on_build(rc.call(reduce_binary_operator, rc.arg(0), rc.arg(1), rc.arg(2))),
            ( A << M                       ).on_build(rc.arg(0)),
            
            ( M << M * s_star * T   ).on_build(rc.call(reduce_binary_operator, rc.arg(0), rc.arg(1), rc.arg(2))),
            ( M << M * s_slash * T   ).on_build(rc.call(reduce_binary_operator, rc.arg(0), rc.arg(1), rc.arg(2))),
            ( M << M * s_percent * T   ).on_build(rc.call(reduce_binary_operator, rc.arg(0), rc.arg(1), rc.arg(2))),
            
            ( M << T                       ).on_build(rc.arg(0)),
            ( T << s_lparen * E * s_rparen ).on_build(rc.arg(1)),
            ( T << dec_literal             ).on_build(rc.call(ASTNodes.Literal, rc.call(float, rc.call(token2text, rc.arg(0))), dtype_float32)),
            ( T << int_literal             ).on_build(rc.call(ASTNodes.Literal, rc.call(int, rc.call(token2text, rc.arg(0))), dtype_int)),
            ( T << string_literal          ).on_build(rc.call(ASTNodes.Literal, rc.call(str, rc.call(token2text, rc.arg(0))), dtype_string)),
            ( T << ACCESSOR                ).on_build(rc.arg(0)),
            ( T << T * s_lbrack * E * s_rbrack ).on_build(rc.call(reduce_indexer, rc.arg(0), rc.arg(2))),
            ( T << T * s_dot * t_id ).on_build(rc.call(reduce_dot_accessor, rc.arg(0), rc.arg(2))),
            ( T << T * s_lparen * E_LIST * s_rparen ).on_build(rc.call(reduce_funcall, rc.arg(0), rc.arg(2))),
            ( T << T * s_lparen * s_rparen ).on_build(rc.call(reduce_funcall, rc.arg(0), rc.call(empty_list))),
            
            ( E_LIST << E * s_comma * E_LIST).on_build(rc.call(prepend_list, rc.arg(0), rc.arg(2))),
            ( E_LIST << E).on_build(rc.call(prepend_list, rc.arg(0), None)),
            
            ( ACCESSOR << SYMBOL_TERM      ).on_build(rc.arg(0)), # A::B::C::D
                        
            ( SYMBOL_TERM << SYMBOL        ).on_build(rc.call(reduce_symbol_term, rc.arg(0))),            
            
            ( SYMBOL << SYM_CHAIN         ).on_build(rc.call(resolve_sym_chain, rc.arg(0))),
            ( SYM_CHAIN << t_id * s_scopeacc * SYM_CHAIN).on_build(rc.call(prepend_list, rc.arg(0), rc.arg(2))),
            ( SYM_CHAIN << t_id).on_build(rc.call(prepend_list, rc.arg(0), None)),
            
  
        ])

    
        self.parser = LR1Parser(G)
    
    def parse_tokens(self, tokens, verbose=False, debug=True):
        parse_result = self.parser.parse_tokens(tokens, lambda tk: self.rcf.terminal(tk.token_type), verbose=verbose)                
        if debug:
            print(self.scope_tree)
            if 'error' in parse_result:
                print("\n", parse_result['message'], "\n")
                raise parse_result['error']            
        if not parse_result['success']:
            raise RuntimeError(parse_result['message'])
        ast = parse_result['value']        
        return self.post_process(ast)

    def post_process(self, ast):
        ast = self.__ast_extract_multiframe_calls_in_block(ast)        
        return ast        
        
    def gen_internal_var_name(self):
        self.internal_id += 1
        return f"cels_s{self.internal_id}"
     
    def __ast_extract_multiframe_calls_in_block(self, ast):
        stack = [ast]
        
        mf_calls = []        
        def identify_multiframe_calls(node):
            if isinstance(node, ASTNodes.FunCall) and node.function.is_multiframe:
                mf_calls.append(node)
                return True
            return False
            
        def extract_mf_call(mf_call):
            # Converts Expr(mfcall(x)) to internal_var = mf_call(x); Expr(internal_var)
            # In case of nested multiframe calls, they are extracted recursively        
            
            block = mf_call
            instr = None
            parent_iterative = None            
            while block is not None and not isinstance(block, ASTNodes.Block):                                
                instr = block
                block = block.parent                
                if isinstance(block, ASTNodes.While) and instr is block.condition:
                    parent_iterative = block
                    
            if block is None:
                raise RuntimeError("Invalid AST: multiframe function call does not have a block among its parents")
            
            result = []
                      
            if instr is not mf_call:  
                block_scope = block.properties['scope']
                
                sym_name = self.gen_internal_var_name()

                vdecl = ASTNodes.VDecl(LexicalToken(sym_name, Terminals.ID, -1, 0, 0), _AST_DataTypeIdentifier(mf_call.function.return_type), scope=block_scope)
                symbol = vdecl.variable

                sterm_l = ASTNodes.SymbolTerm(symbol)
                sterm_r = ASTNodes.SymbolTerm(symbol)            
                 
                mf_call.replace_with(sterm_r)
                attr = ASTNodes.Attr(sterm_l, mf_call, self.op_solver)
                    
                instr.insert_before_it(vdecl)
                instr.insert_before_it(attr)
                
                result.append(mf_call)
            else:
                result.append(mf_call)
                
            # while(MF) { BLOCK; } ==> var cond = MF; while(cond) { BLOCK; cond = MF; }
            if parent_iterative is not None:
                l_clone = sterm_l.clone()
                r_clone = mf_call.clone()
                parent_iterative.block.insert_at_end(ASTNodes.Attr(l_clone, r_clone, self.op_solver))
                result.append(r_clone)
            
            return result
        
        while len(stack)>0:
            mf_calls.clear()
            node = stack[-1]
            stack.pop()
            node.parse(identify_multiframe_calls)            
            
            for mf_call in mf_calls:
                extracts = extract_mf_call(mf_call)
                for extract in extracts:
                    for child in extract.enumerate_children():
                        stack.append(child)            
        
        """
        def check_import_statements()-> list[str]:            
            imports = []
            for node in ast.enumerate_children_deep():                
                if not isinstance(node, ASTNodes.Import): continue                
                if not (isinstance(node.parent, ASTNodes.Block) and node.parent.parent is None):
                    raise ASTException("Import statement must be declared in global scope")                                
                imports.append(node.path)
            return imports
                
        imports = check_import_statements()
        print(imports)
        """
        
        
        return ast
