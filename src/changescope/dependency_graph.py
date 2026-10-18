import ast
from collections import defaultdict


def build_dependency_graph(source_code: str) -> dict[str, set[str]]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return {}

    graph: dict[str, set[str]] = defaultdict(set)

    class FunctionCallVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.function_stack: list[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.function_stack.append(node.name)
            graph.setdefault(node.name, set())
            self.generic_visit(node)
            self.function_stack.pop()

        def visit_AsyncFunctionDef(
            self, node: ast.AsyncFunctionDef
        ) -> None:
            self.function_stack.append(node.name)
            graph.setdefault(node.name, set())
            self.generic_visit(node)
            self.function_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if self.function_stack and isinstance(node.func, ast.Name):
                caller = self.function_stack[-1]
                callee = node.func.id
                graph[caller].add(callee)
            self.generic_visit(node)

    FunctionCallVisitor().visit(tree)
    return dict(graph)


def find_affected_functions(
    graph: dict[str, set[str]],
    changed_functions: set[str],
) -> set[str]:
    affected = set(changed_functions)
    changed = True

    while changed:
        changed = False

        for caller, callees in graph.items():
            if caller not in affected and callees & affected:
                affected.add(caller)
                changed = True

    return affected
