from pathlib import Path
from typing import Annotated

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from maintainability_lens.measures import measure_project, scope_to_file, summarise_worst_functions
from maintainability_lens.ratings import rate_project
from maintainability_lens.schemas import ProjectMeasures, ProjectMeasureSummary, ProjectRatings

DEFAULT_FUNCTION_LIMIT = 20

server = MCPServer("maintainability-lens")

FileArgument = Annotated[
    str | None,
    Field(
        description=(
            "One Python file to scope to, relative to `target` with forward slashes. "
            "Duplication and fan-in are still counted against the whole project."
        )
    ),
]


def measure_scope(target: str, file: str | None) -> ProjectMeasures:
    try:
        project_measures = measure_project(Path(target))
        return project_measures if file is None else scope_to_file(project_measures, file)
    except (NotADirectoryError, ValueError) as error:
        raise ToolError(str(error)) from error


@server.tool(
    name="measure_project",
    description=(
        "Compute Measures (cyclomatic complexity, cognitive complexity, lines of code, "
        "parameter count) for the Python functions under `target`, an absolute directory "
        "path. Returns every Measure of "
        "the `function_limit` functions with the highest cyclomatic complexity, the number of "
        "functions measured, and files that could not be parsed. With `file`, only that "
        "file's functions."
    ),
)
def measure_target(
    target: str,
    function_limit: Annotated[int, Field(ge=1)] = DEFAULT_FUNCTION_LIMIT,
    file: FileArgument = None,
) -> ProjectMeasureSummary:
    return summarise_worst_functions(measure_scope(target, file), function_limit)


@server.tool(
    name="rate_project",
    description=(
        "Rate the maintainability of the Python project under `target`, an absolute directory "
        "path. Returns a Rating (++, +, o, -, --) per ISO/IEC 25010 Characteristic, averaged "
        "from the System properties that have one; `is_partial` and `missing` say which "
        "System properties are not rated yet. Also returns each System property's Rating or "
        "4-star check with its threshold source, the Risk profiles, production and test lines "
        "of code, the duplicated percentage, the production files with the most duplicated "
        "lines and the highest fan-in, and files that could not be parsed. Test code is left "
        "out of every Rating. With `file`, everything is computed for that one file."
    ),
)
def rate_target(target: str, file: FileArgument = None) -> ProjectRatings:
    return rate_project(measure_scope(target, file))


def serve() -> None:
    server.run("stdio")
