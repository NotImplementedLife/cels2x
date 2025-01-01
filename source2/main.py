#import cProfile

from cels2tokens import CelsLexer
from cels2ast import Cels2AST
from cels2cpp import CelsEnv2Cpp

def read_file(path):
    with open(path) as f: return f.read()

lexer = CelsLexer()

t = lexer.parse(read_file("_test.cels"))['tokens']

c2a = Cels2AST(lr1_path="cels_lr1_at.txt")
#c2a = Cels2AST()

r = c2a.parse_tokens(t)
print("__________________________")
print(r)
print("__________________________")

e2cpp = CelsEnv2Cpp(c2a.env)


snippet = e2cpp.compile_env()
print(snippet.code)

