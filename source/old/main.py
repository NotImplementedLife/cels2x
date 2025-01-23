from lexer import Lexer, RegularExpression
from grammar import RuleComponentFactory, Rule, Grammar, rule_callbacks as rc
from lr1 import AnalysisElement, LR1CanonicalCollection, LR1AnalysisTable, LR1Parser

L = Lexer()

L.add_rule("INT_LITERAL", r'[0-9]+')
L.add_rule("DEC_LITERAL", r'[0-9]+\.[0-9]*')

L.add_rule("S_ADD", r'\+')
L.add_rule("S_LPAREN", r'\(')
L.add_rule("S_RPAREN", r'\)')

r = L.parse('1+2.3')

print(r['tokens'])
print("Ok" if r['success'] else r['error'])

rcf = RuleComponentFactory(on_match=lambda val, token: val == token.token_type)

S = rcf.non_terminal("S")
E = rcf.non_terminal("E")
T = rcf.non_terminal("T")
s_add = rcf.terminal("S_ADD")
s_lparen = rcf.terminal("S_LPAREN")
s_rparen = rcf.terminal("S_RPAREN")
dec_literal = rcf.terminal("DEC_LITERAL")
int_literal = rcf.terminal("INT_LITERAL")

class Literal:
    def __init__(self, value, dtype, conv=None):
        self.dtype = dtype
        self.value= dtype(conv(value) if conv is not None else value)
        
    def __str__(self): return f"{self.value}:{self.dtype.__name__}"

class Add:
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def __str__(self): return f"({self.left}+{self.right})"
    
def token2text(t): return t.value

G = Grammar([    
    ( S << E                       ).on_build(rc.arg(0)),
    ( E << E * s_add * T           ).on_build(rc.call(Add, rc.arg(0), rc.arg(2))),
    ( E << T * s_add * T           ).on_build(rc.call(Add, rc.arg(0), rc.arg(2))),
    ( T << s_lparen * E * s_rparen ).on_build(rc.arg(1)),
    ( T << dec_literal             ).on_build(rc.call(Literal, rc.arg(0), float, token2text)),
    ( T << int_literal             ).on_build(rc.call(Literal, rc.arg(0), int, token2text)),    
])

print(G)
print(G.non_terminals)
print(G.terminals)

print(G.first1_table)
print(G.follow1_table)

a1 = AnalysisElement(G.rules[0], 0, [])
a2 = AnalysisElement(G.rules[0], 0, [])

#print(a1==a2)
#print("????")
cc = LR1CanonicalCollection(G)

t = LR1AnalysisTable(G)
t.pretty_print()

c = t.find_conflicts()
print(c)

print(t[1, E])

tokens = L.parse("(1+2.3)+(1.2+5)")['tokens']
print(tokens)

parser = LR1Parser(G)

r = parser.parse_tokens(tokens, lambda tk: rcf.terminal(tk.token_type), verbose=True)

print(r)
print(r['value'])


#parser.parse_tokens()

#print(str(cc))

exit(0)
c = G.rules[0].process_match
print(c([Literal(1,int), '+', Literal(2, int)]))

c = G.rules[1].process_match
print(c(['(', Literal(1,int), ')']))

c = G.rules[2].process_match
print(c(['3.14']))

c = G.rules[3].process_match
print(c(['10']))

exit(0)
from lexer import Lexer, RegularExpression
from cels_core import CelsLexer

CL = CelsLexer()

def read_all_text(path): 
    with open(path, 'r') as f: return f.read()

r = CL.parse(read_all_text("examples/0.txt"))

for token in r['tokens']:
    print(token)
print("Ok" if r['success'] else r['error'])


exit(0)

L = Lexer()

L.add_rule("VAR", "var")
L.add_rule("WS", "( |\t|\n|\r)+")
L.add_rule("OP_EQ", "=")
L.add_rule("STRING_LITERAL", r'"([^\\"]|(\\"))*"')

L.rules[-1][1].fa.pretty_print()

L.add_rule("SYMBOL", "[A-Za-z_][A-Za-z0-9+]*")
L.add_rule("NUMBER", "[0-9]+")

r = L.parse('var x=2\n var y = "a\\""')

for token in r['tokens']:
    print(token)
print("Ok" if r['success'] else r['error'])

exit(0)
r = RegularExpression("( |\t|\n|\r)+")

print(r.fa.is_accepted_sequence("#"))
print(r.fa.is_accepted_sequence(" "))
print(r.fa.is_accepted_sequence("  "))
print(r.fa.is_accepted_sequence(" \n "))
print(r.fa.is_accepted_sequence(" \nx "))


exit(0)

from fa import CharsRange, Charset, CharTransitionsSet, TextFiniteAutomaton

r1 = CharsRange('a', 'p') #CharsRange('a', 'z')
r2 = CharsRange('m', 'z')
r3 = CharsRange(0, 127)
print(r3)

c = CharTransitionsSet({
    ("Q0", Charset.digits()): ["Q1", "Q2"],
    ("Q1", Charset.digits()): ["Q1"],
    ("Q1", Charset.alpha()): ["Q2"],        
})

fa = TextFiniteAutomaton(c, "Q0", ["Q2"]).as_deterministic()

fa.pretty_print()

#print(('Q0', Charset.digits()) in fa.transitions.transitions)

#fa = fa._combine(TextFiniteAutomaton.transitions_concat, fa2)
#fa = fa ^ 2

print("___")
#print(fa)
fa.pretty_print()

print(fa.is_accepted_sequence("123a"))
print(fa.is_accepted_sequence("123ab"))
print(fa.find_longest_accepted_sequence_length("123abc"))
print(fa.find_longest_accepted_sequence_length("a99"))


#print(fa.find_longest_accepted_sequence_length("1aff"))
#print(fa.find_longest_accepted_sequence_length("12affdcdcd3"))
print(fa.find_longest_accepted_sequence_length(""))
print(fa.find_longest_accepted_sequence_length("12a"))
print(fa.find_longest_accepted_sequence_length("12a3334f9"))
print(fa.find_longest_accepted_sequence_length("12a3334f99c"))
#print(fa.find_longest_accepted_sequence_length("123a45ff"))
#print(fa.find_longest_accepted_sequence_length("a23"))

