"""
from lexer import RegularExpression
re = RegularExpression(r"/\*(([^*])|(\*[^/]))*\*/")
print(re.fa)
comment = "/* This is a ** */ comment */"
print(re.fa.find_longest_accepted_sequence_length(comment), "/", len(comment))
exit(0)
"""

from cels2cpp import Cels2CppCompiler
from modular_cels_compiler import ModularCels2CppCompiler
from ast import ASTNode
import os

compiler = ModularCels2CppCompiler()

r = compiler.compile_from_folder("examples/celstris")
print(r)
#r = compiler.compile(read_file('examples/celstris.cels'))

with open("celstris.cels.hpp.txt", 'w') as f:
    f.write('#include "cels_stack.hpp"\n\n')
    f.write(r.code)

exit(0)

while True:
    try:
        code = input(">> ")
        if code=="exit": break
        elif code=="cls": os.system("cls")
        elif code=="reset": compiler = Cels2CppCompiler()
        elif code.startswith('load'):
            with open(code.split()[1]) as f:
                print(compiler.compile(f.read()))
        else:
            print(compiler.compile(code))
    except Exception as e:
        print(e)

#compiler.compile("var x:int;")
#compiler.compile("x=2;")

exit(0)

from cels_core import CelsLexer, CelsParser

def profile():
    import cProfile
    cProfile.run('CelsParser()')
    
#profile(); exit()

CL = CelsLexer()

def read_all_text(path): 
    with open(path, 'r') as f: return f.read()

r = CL.parse(read_all_text("examples/1.txt"))

for token in r['tokens']:
    print(token)
print("Ok" if r['success'] else r['error'])


import time
t1 = time.time()
p = CelsParser()
t2 = time.time()

r = p.parse_tokens(r['tokens'], verbose=False)

print("\n AST:")
print(r)

print(t2-t1)
