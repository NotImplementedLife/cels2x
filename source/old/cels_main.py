from modular_cels_compiler import ModularCels2CppCompiler
import sys

source_dir = None
out_file = None
cpp_headers = []

for arg in sys.argv[1:]:
    if arg.startswith('-d'):
        source_dir = arg[2:]
    elif arg.startswith('-o'):
        out_file = arg[2:]
    if arg.startswith("-he"):
        cpp_headers.append(f'#include <{arg[3:]}>\n')
    if arg.startswith("-hi"):
        cpp_headers.append(f'#include "{arg[3:]}"\n')

if source_dir is None:
    print("Source not specified (-d/.../source_dir)")
    exit(-1)

if out_file is None:
    print("Output file not specified (-o/.../output.cels.hpp)")
    exit(-1)

compiler = ModularCels2CppCompiler()
r = compiler.compile_from_folder(source_dir)

with open(out_file, 'w') as f:
    f.writelines(cpp_headers)
    f.write(r.code)
