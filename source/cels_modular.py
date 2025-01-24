from ast_base import ASTBlock
from cels2ast import Cels2AST
from cels_env import CelsEnvironment
import os

def read_file(path):
    with open(path, 'r', encoding="utf8") as f:
        return f.read()

class ImportSolver:
    def __init__(self, cels2ast):
        self.cels2ast = cels2ast
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
        ast = self.cels2ast.build_ast(read_file(full_path))
        self.paths_working.remove(full_path)
        self.paths_done.add(full_path)

        return ast

class ModularCels2AST(Cels2AST):
    def __init__(self, cels_env:CelsEnvironment|None = None, lr1_path=None):
        Cels2AST.__init__(self, cels_env, lr1_path)
        self.import_solver = ImportSolver(self)

    def compile_from_folder(self, dir_path):
        dir_path = os.path.abspath(dir_path)
        self.import_solver.base_dir = dir_path
        asts = []
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for fname in files:
                asts.append(self.import_solver(os.path.join(root, fname)))
        block = ASTBlock(*[ast for ast in asts if ast is not None])
        return block

