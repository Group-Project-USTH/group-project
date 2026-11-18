import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path

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
DocumentedNode = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class CodeLine:
    line_number: int
    text_without_indentation: str


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    relative_file: str
    tree: ast.Module
    line_count: int
    code_lines: list[CodeLine]


def parse_file(path: Path, relative_file: str) -> ParsedFile | None:
    try:
        with tokenize.open(path) as source_file:
            source = source_file.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError, ValueError):
        return None
    lines = source.splitlines()
    return ParsedFile(
        path=path,
        relative_file=relative_file,
        tree=tree,
        line_count=len(lines),
        code_lines=[
            CodeLine(line_number, lines[line_number - 1].strip())
            for line_number in sorted(find_code_line_numbers(source, tree))
        ],
    )


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
        if isinstance(node, DocumentedNode) and has_docstring(node)
        for line_number in range(node.body[0].lineno, (node.body[0].end_lineno or 0) + 1)
    }


def has_docstring(node: DocumentedNode) -> bool:
    first = node.body[0] if node.body else None
    return (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    )
