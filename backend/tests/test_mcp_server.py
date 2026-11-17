import asyncio
from pathlib import Path
from typing import Any

from mcp import Client

from maintainability_lens.mcp_server import server
from maintainability_lens.measures import measure_project

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"


def call_tool(arguments: dict[str, Any]) -> Any:
    async def call() -> Any:
        async with Client(server) as client:
            return await client.call_tool("measure_project", arguments)

    return asyncio.run(call())


def test_measure_tool_returns_the_same_measures_as_measure_project() -> None:
    result = call_tool({"target": str(SAMPLE)})

    assert not result.is_error
    expected = measure_project(SAMPLE).model_dump(mode="json")
    function_measures = [measure for measure in expected["measures"] if measure["function"]]
    assert result.structured_content["measures"] == function_measures
    assert result.structured_content["function_count"] == 3
    assert result.structured_content["unparsed_files"] == []


def test_measure_tool_keeps_only_the_most_complex_functions() -> None:
    result = call_tool({"target": str(SAMPLE), "function_limit": 1})

    measures = result.structured_content["measures"]
    assert {(measure["function"], measure["name"]) for measure in measures} == {
        ("process_order", "cyclomatic_complexity"),
        ("process_order", "function_lines_of_code"),
        ("process_order", "cognitive_complexity"),
        ("process_order", "parameter_count"),
    }
    assert result.structured_content["function_count"] == 3


def test_measure_tool_reports_a_missing_target_as_an_error(tmp_path: Path) -> None:
    result = call_tool({"target": str(tmp_path / "nope")})

    assert result.is_error


def test_measure_tool_leaves_out_file_measures_even_for_a_function_on_line_one(
    tmp_path: Path,
) -> None:
    (tmp_path / "app.py").write_text("def f(x):\n    if x:\n        return 1\n    return 0\n")

    result = call_tool({"target": str(tmp_path), "function_limit": 1})

    assert {measure["function"] for measure in result.structured_content["measures"]} == {"f"}
