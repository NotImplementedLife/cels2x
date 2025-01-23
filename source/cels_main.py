from cels_modular import ModularCels2AST
from cels2cpp import CelsEnv2Cpp
import sys, os

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

c2a = ModularCels2AST(lr1_path=os.path.join(os.path.dirname(__file__), "cels_lr1_at.txt"))
ast = c2a.compile_from_folder(source_dir)

e2cpp = CelsEnv2Cpp(c2a.env)
snippet = e2cpp.compile_env()


with open(out_file, 'w') as f:
    f.writelines(cpp_headers)
    f.write(snippet.get_full_code())
