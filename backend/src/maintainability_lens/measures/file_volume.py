import ast
import io
import tokenize

from maintainability_lens.schemas import Measure, MeasureName

NOT_CODE_TOKENS = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
)
DOCUMENTED_NODES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def find_code_line_numbers(source: str, tree: ast.Module) -> set[int]:
    lines_with_tokens = {
        line_number
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type not in NOT_CODE_TOKENS
        for line_number in range(token.start[0], token.end[0] + 1)
    }
    return lines_with_tokens - find_docstring_line_numbers(tree)


def find_docstring_line_numbers(tree: ast.Module) -> set[int]:
    return {
        line_number
        for node in ast.walk(tree)
        if isinstance(node, DOCUMENTED_NODES) and has_docstring(node)
        for line_number in range(node.body[0].lineno, (node.body[0].end_lineno or 0) + 1)
    }


def has_docstring(node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    first = node.body[0] if node.body else None
    return (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    )


def measure_file_volume(relative_file: str, source: str, tree: ast.Module) -> Measure:
    return Measure(
        name=MeasureName.FILE_LINES_OF_CODE,
        value=len(find_code_line_numbers(source, tree)),
        file=relative_file,
        line_start=1,
        line_end=max(len(source.splitlines()), 1),
    )
