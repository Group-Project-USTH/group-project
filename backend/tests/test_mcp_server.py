import asyncio
from pathlib import Path
from typing import Any

from mcp import Client

from maintainability_lens.mcp_server import server
from maintainability_lens.measures import measure_project

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"


def call_tool(arguments: dict[str, Any], tool: str = "measure_project") -> Any:
    async def call() -> Any:
        async with Client(server) as client:
            return await client.call_tool(tool, arguments)

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


def test_rate_tool_rates_each_characteristic_from_the_rated_system_properties() -> None:
    result = call_tool({"target": str(SAMPLE)}, tool="rate_project")

    assert not result.is_error
    ratings = result.structured_content
    assert {
        entry["characteristic"]: (entry["rating"], entry["is_partial"])
        for entry in ratings["characteristic_ratings"]
    } == {
        "modularity": (None, False),
        "reusability": (None, False),
        "analysability": ("++", True),
        "modifiability": ("++", True),
        "testability": ("++", True),
    }
    assert (ratings["production_lines_of_code"], ratings["test_lines_of_code"]) == (22, 3)
    assert ratings["duplicated_percentage"] == 0.0


def test_rate_tool_lists_the_files_with_the_most_duplication_and_fan_in(tmp_path: Path) -> None:
    block = "".join(f"value_{index} = {index}\n" for index in range(6))
    (tmp_path / "copy_a.py").write_text(block)
    (tmp_path / "copy_b.py").write_text(block + "import copy_a\n")
    (tmp_path / "unique.py").write_text("import copy_a\n")

    ratings = call_tool({"target": str(tmp_path)}, tool="rate_project").structured_content

    assert [
        (measure["file"], measure["value"]) for measure in ratings["most_duplicated_files"]
    ] == [("copy_a.py", 6), ("copy_b.py", 6)]
    assert [(measure["file"], measure["value"]) for measure in ratings["highest_fan_in_files"]] == [
        ("copy_a.py", 2)
    ]


def test_rate_tool_reports_a_missing_target_as_an_error(tmp_path: Path) -> None:
    assert call_tool({"target": str(tmp_path / "nope")}, tool="rate_project").is_error


def test_rate_tool_with_a_file_rates_that_file_against_its_whole_project(tmp_path: Path) -> None:
    block = "".join(f"value_{index} = {index}\n" for index in range(6))
    (tmp_path / "copy_a.py").write_text(block)
    (tmp_path / "copy_b.py").write_text(block + "import copy_a\n")
    (tmp_path / "unique.py").write_text("import copy_a\n")

    ratings = call_tool(
        {"target": str(tmp_path), "file": "copy_a.py"}, tool="rate_project"
    ).structured_content

    assert ratings["production_lines_of_code"] == 6
    assert ratings["duplicated_percentage"] == 100.0
    assert [(measure["file"], measure["value"]) for measure in ratings["highest_fan_in_files"]] == [
        ("copy_a.py", 2)
    ]


def test_rate_tool_reports_a_file_outside_the_project_as_an_error(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def f(x):\n    return x\n")

    result = call_tool({"target": str(tmp_path), "file": "missing.py"}, tool="rate_project")

    assert result.is_error
    assert "missing.py" in result.content[0].text


def test_rate_tool_tells_the_model_why_a_target_is_rejected(tmp_path: Path) -> None:
    result = call_tool({"target": str(tmp_path / "nope")}, tool="rate_project")

    assert "not a directory" in result.content[0].text


def test_measure_tool_with_a_file_returns_only_that_files_functions(tmp_path: Path) -> None:
    (tmp_path / "first.py").write_text("def f(x):\n    if x:\n        return 1\n    return 0\n")
    (tmp_path / "second.py").write_text("def g(x):\n    return x\n\n\ndef h(x):\n    return x\n")

    result = call_tool({"target": str(tmp_path), "file": "second.py"})

    assert {measure["function"] for measure in result.structured_content["measures"]} == {"g", "h"}
    assert result.structured_content["function_count"] == 2
