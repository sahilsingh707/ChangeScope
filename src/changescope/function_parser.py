import ast
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FunctionInfo:
    name: str
    line_number: int
    end_line_number: int


def extract_functions(source_code: str) -> list[FunctionInfo]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                FunctionInfo(
                    name=node.name,
                    line_number=node.lineno,
                    end_line_number=node.end_lineno or node.lineno,
                )
            )

    return sorted(functions, key=lambda function: function.line_number)
