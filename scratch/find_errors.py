import ast
import builtins

def check_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)

    builtin_names = set(dir(builtins))
    
    # Track defined names at module level and inside functions/classes
    class NameChecker(ast.NodeVisitor):
        def __init__(self):
            self.scopes = [set(builtin_names)]
            self.errors = []

        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                self.scopes[-1].add(name.split('.')[0])
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                self.scopes[-1].add(name)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            self.scopes[-1].add(node.name)
            self.scopes.append(set())
            self.generic_visit(node)
            self.scopes.pop()

        def visit_FunctionDef(self, node):
            self.scopes[-1].add(node.name)
            new_scope = set()
            # Add arguments
            for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
                new_scope.add(arg.arg)
            if node.args.vararg:
                new_scope.add(node.args.vararg.arg)
            if node.args.kwarg:
                new_scope.add(node.args.kwarg.arg)
            self.scopes.append(new_scope)
            self.generic_visit(node)
            self.scopes.pop()

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                self.scopes[-1].add(node.id)
            elif isinstance(node.ctx, ast.Load):
                # Check if it exists in any parent scope
                found = False
                for scope in reversed(self.scopes):
                    if node.id in scope:
                        found = True
                        break
                if not found:
                    self.errors.append((node.lineno, node.col_offset, node.id))
            self.generic_visit(node)

    checker = NameChecker()
    # Pre-populate module scope with class names that are defined later to avoid forward-reference noise
    # (since we are not doing a full multi-pass analysis, but standard python has class names defined)
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            checker.scopes[0].add(node.name)
            
    checker.visit(tree)
    for lineno, col, name in sorted(checker.errors):
        print(f"Line {lineno}, Col {col}: Undefined name '{name}'")

if __name__ == '__main__':
    check_file('src/views/ledger_view.py')
