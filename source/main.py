from cels2tokens import CelsLexer
from cels2ast import Cels2AST
from cels_modular import ModularCels2AST
from cels2cpp import CelsEnv2Cpp

def read_file(path):
    with open(path) as f: return f.read()

c2a = ModularCels2AST(lr1_path="cels_lr1_at.txt")

r = c2a.build_ast(read_file("_test.cels"))

print("__________________________")
print(r)
print("__________________________")

#exit(0)
e2cpp = CelsEnv2Cpp(c2a.env)
snippet = e2cpp.compile_env()

print(snippet.get_full_code())

