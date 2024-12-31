from lexer import RegularExpression, Lexer
from utils import ensure_type, IdProvider

class CelsTokenType:
    def __init__(self, idp:IdProvider, name:str, regex_str:str):
        ensure_type(idp, IdProvider)        
        ensure_type(name, str)
        ensure_type(regex_str, str)
        self.token_type_id = idp.create_id()
        self.name = name
        self.regex_str = regex_str
        
    def __str__(self): return f"CelsTokenType{{{self.token_type_id}:{self.name}}}"
    def __repr__(self): return self.__str__()

class CelsTokenTypes:
    __idp = IdProvider()
    
    WS             = CelsTokenType(__idp, "WS"            , '( |\t|\n|\r)+')
    COMMENT        = CelsTokenType(__idp, "COMMENT"       , r'/\*(([^*])|(\*[^/]))*\*/')
    
    LITERAL_BOOL   = CelsTokenType(__idp, "LITERAL_BOOL"  , r'(true)|(false)')
    LITERAL_DEC    = CelsTokenType(__idp, "LITERAL_DEC"   , r'[0-9]+\.[0-9]*')
    LITERAL_INT    = CelsTokenType(__idp, "LITERAL_INT"   , r'[0-9]+')
    LITERAL_STR    = CelsTokenType(__idp, "LITERAL_STR"   , r'"([^\\"]|(\\"))*"')
    
    KW_BEGIN       = CelsTokenType(__idp, "KW_BEGIN"      , r'begin')
    KW_BOOL        = CelsTokenType(__idp, "KW_BOOL"       , r'bool')
    KW_BREAK       = CelsTokenType(__idp, "KW_BREAK"      , r'break')
    KW_CONST       = CelsTokenType(__idp, "KW_CONST"      , r'const')
    KW_CONTINUE    = CelsTokenType(__idp, "KW_CONTINUE"   , r'continue')
    KW_CPP_INCLUDE = CelsTokenType(__idp, "KW_CPP_INCLUDE", r'cppinclude')
    KW_DO          = CelsTokenType(__idp, "KW_DO"         , r'do')
    KW_END         = CelsTokenType(__idp, "KW_END"        , r'end')
    KW_ELSE        = CelsTokenType(__idp, "KW_ELSE"       , r'else')
    KW_EXTERN      = CelsTokenType(__idp, "KW_EXTERN"     , r'extern')
    KW_FI          = CelsTokenType(__idp, "KW_FI"         , r'fi')
    KW_FUNCTION    = CelsTokenType(__idp, "KW_FUNCION"    , r'function')
    KW_IF          = CelsTokenType(__idp, "KW_IF"         , r'if')
    KW_IMPORT      = CelsTokenType(__idp, "KW_IMPORT"     , r'import')
    KW_INT         = CelsTokenType(__idp, "KW_INT"        , r'int')
    KW_MULTIFRAME  = CelsTokenType(__idp, "KW_MULTIFRAME" , r'multiframe')
    KW_PACKAGE     = CelsTokenType(__idp, "KW_PACKAGE"    , r'package')
    KW_RETURN      = CelsTokenType(__idp, "KW_RETURN"     , r'return')
    KW_SCOPE       = CelsTokenType(__idp, "KW_SCOPE"      , r'scope')
    KW_STRING      = CelsTokenType(__idp, "KW_STRING"     , r'string')
    KW_STRUCT      = CelsTokenType(__idp, "KW_STRUCT"     , r'struct')
    KW_SUSPEND     = CelsTokenType(__idp, "KW_SUSPEND"    , r'suspend')
    KW_THEN        = CelsTokenType(__idp, "KW_THEN"       , r'then')    
    KW_VAR         = CelsTokenType(__idp, "KW_VAR"        , r'var')
    KW_VOID        = CelsTokenType(__idp, "KW_VOID"       , r'void')
    KW_WHILE       = CelsTokenType(__idp, "KW_WHILE"      , r'while')
       
    S_LRARROW      = CelsTokenType(__idp, "S_LRARROW"     , r'\->')
    S_DOUBLECOLON  = CelsTokenType(__idp, "S_DOUBLECOLON" , r'::')
    S_GTE          = CelsTokenType(__idp, "S_GTE"         , r'>=')
    S_EQEQ         = CelsTokenType(__idp, "S_EQEQ"        , r'==')
    S_LTE          = CelsTokenType(__idp, "S_LTE"         , r'<=')
    S_NEQ          = CelsTokenType(__idp, "S_NEQ"         , r'!=')

    S_AMPERSAND    = CelsTokenType(__idp, "S_AMPERSAND"   , r'\&')    
    S_COLON        = CelsTokenType(__idp, "S_COLON"       , r':')    
    S_COMMA        = CelsTokenType(__idp, "S_COMMA"       , r',')
    S_DOT          = CelsTokenType(__idp, "S_DOT"         , r'\.')
    S_GT           = CelsTokenType(__idp, "S_GT"          , r'>')
    S_EQUAL        = CelsTokenType(__idp, "S_EQUAL"       , r'=')
    S_LBRACK       = CelsTokenType(__idp, "S_LBRACK"      , r'\[')
    S_LPAREN       = CelsTokenType(__idp, "S_LPAREN"      , r'\(')
    S_LT           = CelsTokenType(__idp, "S_LT"          , r'<')
    S_MINUS        = CelsTokenType(__idp, "S_MINUS"       , r'\-')
    S_PERCENT      = CelsTokenType(__idp, "S_PERCENT"     , r'%')
    S_PLUS         = CelsTokenType(__idp, "S_PLUS"        , r'\+')
    S_RBRACK       = CelsTokenType(__idp, "S_RBRACK"      , r'\]')
    S_RPAREN       = CelsTokenType(__idp, "S_RPAREN"      , r'\)')
    S_SEMICOLON    = CelsTokenType(__idp, "S_SEMICOLON"   , r';')
    S_SLASH        = CelsTokenType(__idp, "S_SLASH"       , r'/')
    S_STAR         = CelsTokenType(__idp, "S_STAR"        , r'\*')
    
    ID             = CelsTokenType(__idp, "ID"            , r'[_A-Za-z][_A-Za-z0-9]*')
    
    @staticmethod
    def get_all_types():
        return sorted([t for t in vars(CelsTokenTypes).values() if isinstance(t, CelsTokenType)], 
            key=lambda t:t.token_type_id)

class CelsLexer(Lexer):
    def __init__(self):
        Lexer.__init__(self)        
        for token_type in CelsTokenTypes.get_all_types():
            self.add_rule(token_type.name, token_type.regex_str)
    
    def parse(self, text):            
        result = Lexer.parse(self, text)        
        
        if not result['success']: return result
        
        tokens = result['tokens']
        
        def is_space_not_allowed_h(tk1, tk2):
            return tk1.token_type.startswith('LITERAL_') and (tk2.token_type.startswith('LITERAL_') or tk2.token_type.startswith('KW_'))
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
        
        result['tokens'] = [tk for tk in tokens if tk.token_type!=CelsTokenTypes.COMMENT.name]
        
        return result