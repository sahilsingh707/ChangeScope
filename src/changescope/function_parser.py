import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FunctionInfo:
    name: str
    line_number: int
    end_line_number: int
    class_name: str | None = None

    @property
    def qualified_name(self) -> str:
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name


def extract_functions(source_code: str) -> list[FunctionInfo]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    functions: list[FunctionInfo] = []

    class FunctionVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.class_stack: list[str] = []
            self.function_depth = 0

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node)

        def visit_AsyncFunctionDef(
            self,
            node: ast.AsyncFunctionDef,
        ) -> None:
            self._visit_function(node)

        def _visit_function(
            self,
            node: ast.FunctionDef | ast.AsyncFunctionDef,
        ) -> None:
            class_name = (
                ".".join(self.class_stack)
                if self.class_stack and self.function_depth == 0
                else None
            )

            functions.append(
                FunctionInfo(
                    name=node.name,
                    line_number=node.lineno,
                    end_line_number=node.end_lineno or node.lineno,
                    class_name=class_name,
                )
            )

            self.function_depth += 1
            self.generic_visit(node)
            self.function_depth -= 1

    FunctionVisitor().visit(tree)

    return sorted(functions, key=lambda function: function.line_number)
