import ast
from collections.abc import Iterator
from dataclasses import dataclass

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class PythonUnit:
    qualified_name: str
    first_line_with_decorators: int
    line_start: int
    line_end: int


def find_units(source: str) -> list[PythonUnit]:
    return list(walk_units(ast.parse(source).body, prefix=""))


def walk_units(statements: list[ast.stmt], prefix: str) -> Iterator[PythonUnit]:
    for statement in statements:
        if isinstance(statement, FunctionNode):
            qualified_name = prefix + statement.name
            yield to_unit(statement, qualified_name)
            yield from walk_units(statement.body, prefix=f"{qualified_name}.")
        elif isinstance(statement, ast.ClassDef):
            yield from walk_units(statement.body, prefix=f"{prefix}{statement.name}.")
        else:
            yield from walk_units(nested_statements(statement), prefix)


def nested_statements(statement: ast.stmt) -> list[ast.stmt]:
    return [
        child
        for field in ("body", "orelse", "finalbody", "handlers", "cases")
        for node in getattr(statement, field, [])
        for child in ([node] if isinstance(node, ast.stmt) else node.body)
    ]


def to_unit(node: FunctionNode, qualified_name: str) -> PythonUnit:
    decorator_lines = [decorator.lineno for decorator in node.decorator_list]
    return PythonUnit(
        qualified_name=qualified_name,
        first_line_with_decorators=min([node.lineno, *decorator_lines]),
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
    )
