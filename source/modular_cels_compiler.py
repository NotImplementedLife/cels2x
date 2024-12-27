from cels2cpp import Cels2CppCompiler
from ast import ASTBlock
import os

def read_file(path):
    with open(path, 'r', encoding="utf8") as f: 
        return f.read()

class ImportSolver:
    def __init__(self, compiler):
        self.compiler = compiler
        self.paths_done = set()
        self.paths_working = set()        
        self.base_dir = "."
        
    def __call__(self, path):              
        full_path = path        
        if not os.path.isabs(path):
            full_path = os.path.abspath(os.path.join(self.base_dir, path))        
    
        if full_path in self.paths_done: return None
        
        if full_path in self.paths_working: 
            raise RuntimeError(f"Circular dependency: {full_path}")
        
        print("mCels2cpp:", full_path)
        
        self.paths_working.add(full_path)
        ast = self.compiler.build_ast(read_file(full_path))
        self.paths_working.remove(full_path)
        self.paths_done.add(full_path)
                
        return ast

class ModularCels2CppCompiler(Cels2CppCompiler):
    def __init__(self):
        super(ModularCels2CppCompiler, self).__init__()
        self.import_solver = ImportSolver(self)
        self.set_import_solver(self.import_solver)
    
    def compile_from_folder(self, dir_path):
        dir_path = os.path.abspath(dir_path)
        self.import_solver.base_dir = dir_path
        asts = []
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for fname in files:
                asts.append(self.import_solver(os.path.join(root, fname)))
        block = ASTBlock(*[ast for ast in asts if ast is not None])        
        
        return self.cpp_ctx.build(block)
    

"""
def read_file(path):
    with open(path, 'r', encoding="utf8") as f: 
        return f.read()

compiler = Cels2CppCompiler()

cels_dirs = []
cpp_headers_extern = []

for arg in sys.argv[1:]:
    if arg.startswith("-d"):
        cels_dirs.append(arg[2:])
    if arg.startswith("-he"):
        cpp_headers.append(arg[3:])
    if arg.startswith("-hi"):
        cpp_headers.append(arg[3:])
"""


