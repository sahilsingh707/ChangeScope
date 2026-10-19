import ast
from collections import defaultdict
from pathlib import PurePosixPath


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

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.function_stack.append(node.name)
            graph.setdefault(node.name, set())
            self.generic_visit(node)
            self.function_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if self.function_stack and isinstance(node.func, ast.Name):
                graph[self.function_stack[-1]].add(node.func.id)
            self.generic_visit(node)

    FunctionCallVisitor().visit(tree)
    return dict(graph)


def build_repository_dependency_graph(
    sources: dict[str, str],
) -> dict[str, set[str]]:
    raw_graph: dict[str, set[str]] = {}
    function_names: dict[str, set[str]] = defaultdict(set)

    for file_path, source_code in sources.items():
        normalized_path = PurePosixPath(file_path).as_posix()
        local_graph = build_dependency_graph(source_code)

        for function_name, callees in local_graph.items():
            qualified_name = f"{normalized_path}::{function_name}"
            raw_graph[qualified_name] = set(callees)
            function_names[function_name].add(qualified_name)

    resolved_graph: dict[str, set[str]] = {}

    for caller, callees in raw_graph.items():
        caller_file = caller.split("::", maxsplit=1)[0]
        resolved_callees = set()

        for callee_name in callees:
            local_candidate = f"{caller_file}::{callee_name}"

            if local_candidate in raw_graph:
                resolved_callees.add(local_candidate)
                continue

            candidates = function_names.get(callee_name, set())
            if len(candidates) == 1:
                resolved_callees.update(candidates)

        resolved_graph[caller] = resolved_callees

    return resolved_graph


def find_affected_functions(
    graph: dict[str, set[str]],
    changed_functions: set[str],
) -> set[str]:
    affected = set(changed_functions)
    pending = list(changed_functions)

    while pending:
        changed_function = pending.pop()

        for caller, callees in graph.items():
            if changed_function in callees and caller not in affected:
                affected.add(caller)
                pending.append(caller)

    return affected