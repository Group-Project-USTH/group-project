from pathlib import Path
from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from maintainability_lens.measures import measure_project, summarise_worst_functions
from maintainability_lens.ratings import rate_project
from maintainability_lens.schemas import ProjectMeasureSummary, ProjectRatings

DEFAULT_FUNCTION_LIMIT = 20

server = MCPServer("maintainability-lens")


@server.tool(
    name="measure_project",
    description=(
        "Compute Measures (cyclomatic complexity, cognitive complexity, lines of code, "
        "parameter count) for the Python functions under `target`, an absolute directory "
        "path. Returns every Measure of "
        "the `function_limit` functions with the highest cyclomatic complexity, the number of "
        "functions measured, and files that could not be parsed."
    ),
)
def measure_target(
    target: str,
    function_limit: Annotated[int, Field(ge=1)] = DEFAULT_FUNCTION_LIMIT,
) -> ProjectMeasureSummary:
    return summarise_worst_functions(measure_project(Path(target)), function_limit)


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
        "out of every Rating."
    ),
)
def rate_target(target: str) -> ProjectRatings:
    return rate_project(measure_project(Path(target)))


def serve() -> None:
    server.run("stdio")
