import sys
sys.path.insert(0, '../../source')

from modular_cels_compiler import ModularCels2CppCompiler

with open("example.cels") as f:
    example_cels = f.read()


compiler = ModularCels2CppCompiler()

ast = compiler.build_ast(example_cels)
with open("example_ast.txt", 'w') as f:
    f.write(str(ast))

# reset the compiler, otherwise would parse the same
# code again and give a symbol duplicate error
compiler = ModularCels2CppCompiler()

cpp_code = compiler.compile(example_cels).code
with open("example.cpp", 'w') as f:
    f.write(cpp_code)