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
    parameter_count: int


def find_units(source: str) -> list[PythonUnit]:
    return list(walk_units(ast.parse(source).body, prefix="", is_class_body=False))


def walk_units(
    statements: list[ast.stmt], prefix: str, is_class_body: bool
) -> Iterator[PythonUnit]:
    for statement in statements:
        if isinstance(statement, FunctionNode):
            qualified_name = prefix + statement.name
            yield to_unit(statement, qualified_name, is_method=is_class_body)
            yield from walk_units(statement.body, prefix=f"{qualified_name}.", is_class_body=False)
        elif isinstance(statement, ast.ClassDef):
            yield from walk_units(
                statement.body, prefix=f"{prefix}{statement.name}.", is_class_body=True
            )
        else:
            yield from walk_units(nested_statements(statement), prefix, is_class_body)


def nested_statements(statement: ast.stmt) -> list[ast.stmt]:
    return [
        child
        for field in ("body", "orelse", "finalbody", "handlers", "cases")
        for node in getattr(statement, field, [])
        for child in ([node] if isinstance(node, ast.stmt) else node.body)
    ]


def is_static_method(node: FunctionNode) -> bool:
    return any(
        isinstance(decorator, ast.Name) and decorator.id == "staticmethod"
        for decorator in node.decorator_list
    )


def count_parameters(node: FunctionNode, is_method: bool) -> int:
    arguments = node.args
    positional_count = len(arguments.posonlyargs) + len(arguments.args)
    if is_method and not is_static_method(node) and positional_count:
        positional_count -= 1
    star_count = (arguments.vararg is not None) + (arguments.kwarg is not None)
    return positional_count + len(arguments.kwonlyargs) + star_count


def to_unit(node: FunctionNode, qualified_name: str, is_method: bool) -> PythonUnit:
    decorator_lines = [decorator.lineno for decorator in node.decorator_list]
    return PythonUnit(
        qualified_name=qualified_name,
        first_line_with_decorators=min([node.lineno, *decorator_lines]),
        line_start=node.lineno,
        line_end=node.end_lineno or node.lineno,
        parameter_count=count_parameters(node, is_method),
    )
