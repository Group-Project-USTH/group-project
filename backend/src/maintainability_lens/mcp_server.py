from pathlib import Path
from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from maintainability_lens.measures import measure_project, summarise_worst_functions
from maintainability_lens.schemas import ProjectMeasureSummary

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


def serve() -> None:
    server.run("stdio")
