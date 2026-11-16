from pathlib import Path

import pytest

from maintainability_lens.measures import measure_project
from maintainability_lens.schemas import Measure, MeasureName


def write_module(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)


def test_function_with_one_if_has_cyclomatic_complexity_two(tmp_path: Path) -> None:
    write_module(tmp_path, "app.py", "def f(x):\n    if x:\n        return 1\n    return 0\n")

    measures = measure_project(tmp_path).measures

    assert (
        Measure(
            name=MeasureName.CYCLOMATIC_COMPLEXITY,
            value=2,
            function="f",
            file="app.py",
            line_start=1,
            line_end=4,
        )
        in measures
    )


def measure_values(root: Path, name: MeasureName) -> dict[str | None, int]:
    return {
        measure.function: measure.value
        for measure in measure_project(root).measures
        if measure.name is name
    }


ELIF = (
    "def f(x):\n    if x == 1:\n        return 1\n"
    "    elif x == 2:\n        return 2\n    return 0\n"
)
EXCEPT = "def f(x):\n    try:\n        return int(x)\n    except ValueError:\n        return 0\n"
COMPREHENSION_FILTER = "def f(xs):\n    return [x for x in xs if x]\n"
ASSERT = "def f(x):\n    assert x\n    return x\n"
MATCH_TWO_CASES = (
    "def f(x):\n    match x:\n        case 1:\n            return 1\n"
    "        case _:\n            return 0\n"
)
BOOLEAN_OPERATORS = "def f(a, b, c):\n    return a and b or c\n"


@pytest.mark.parametrize(
    ("source", "expected_complexity"),
    [
        pytest.param(ELIF, 3, id="elif-adds-a-branch"),
        pytest.param(EXCEPT, 2, id="except-adds-a-branch"),
        pytest.param(COMPREHENSION_FILTER, 3, id="comprehension-loop-and-filter-add-branches"),
        pytest.param(ASSERT, 1, id="assert-is-not-a-branch"),
        pytest.param(MATCH_TWO_CASES, 3, id="each-match-case-adds-a-branch"),
        pytest.param(BOOLEAN_OPERATORS, 3, id="each-boolean-operator-adds-a-branch"),
    ],
)
def test_cyclomatic_complexity_follows_the_lizard_definition(
    tmp_path: Path, source: str, expected_complexity: int
) -> None:
    write_module(tmp_path, "app.py", source)

    assert measure_values(tmp_path, MeasureName.CYCLOMATIC_COMPLEXITY) == {"f": expected_complexity}


def test_code_outside_functions_has_no_cyclomatic_complexity(tmp_path: Path) -> None:
    write_module(tmp_path, "script.py", "import sys\nif sys.argv:\n    print(1)\n")

    assert measure_values(tmp_path, MeasureName.CYCLOMATIC_COMPLEXITY) == {}


def test_function_lines_of_code_skip_comments_and_blank_lines(tmp_path: Path) -> None:
    write_module(tmp_path, "app.py", "def f(x):\n    # explain\n\n    return x\n")

    assert measure_values(tmp_path, MeasureName.FUNCTION_LINES_OF_CODE) == {"f": 2}


def test_cognitive_complexity_adds_the_nesting_level(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "app.py",
        "def f(xs):\n    for x in xs:\n        if x:\n            print(x)\n",
    )

    assert measure_values(tmp_path, MeasureName.COGNITIVE_COMPLEXITY) == {"f": 3}


SAMPLE_PROJECT = Path(__file__).parents[1] / "fixtures" / "sample_project"


def test_sample_project_process_order_measures() -> None:
    process_order = {
        measure.name: measure
        for measure in measure_project(SAMPLE_PROJECT).measures
        if measure.function == "process_order"
    }

    assert {name: measure.value for name, measure in process_order.items()} == {
        MeasureName.CYCLOMATIC_COMPLEXITY: 7,
        MeasureName.COGNITIVE_COMPLEXITY: 8,
        MeasureName.FUNCTION_LINES_OF_CODE: 19,
        MeasureName.PARAMETER_COUNT: 1,
    }
    assert {(m.file, m.line_start, m.line_end) for m in process_order.values()} == {
        ("app.py", 6, 25)
    }


def test_files_in_subfolders_are_cited_relative_to_the_target(tmp_path: Path) -> None:
    write_module(tmp_path, "shop/orders/checkout.py", "def pay():\n    return 1\n")

    assert {measure.file for measure in measure_project(tmp_path).measures} == {
        "shop/orders/checkout.py"
    }


@pytest.mark.parametrize("folder", [".venv", ".tox", "venv", "__pycache__", "node_modules"])
def test_tooling_and_hidden_folders_are_not_measured(tmp_path: Path, folder: str) -> None:
    write_module(tmp_path, "app.py", "def mine():\n    return 1\n")
    write_module(tmp_path, f"{folder}/lib/vendored.py", "def theirs():\n    return 1\n")

    assert {measure.file for measure in measure_project(tmp_path).measures} == {"app.py"}


def test_unparsable_file_is_listed_and_the_rest_is_still_measured(tmp_path: Path) -> None:
    write_module(tmp_path, "good.py", "def fine():\n    return 1\n")
    write_module(tmp_path, "broken.py", "def broken(:\n    return 1\n")

    project_measures = measure_project(tmp_path)

    assert project_measures.unparsed_files == ["broken.py"]
    assert {measure.file for measure in project_measures.measures} == {"good.py"}


DECORATED_METHOD = (
    "class Cart:\n"
    "    @staticmethod\n"
    "    def make(a):\n"
    "        if a:\n"
    "            return a\n"
    "        return None\n"
)


def test_every_measure_of_a_method_names_its_class_and_shares_one_line_range(
    tmp_path: Path,
) -> None:
    write_module(tmp_path, "cart.py", DECORATED_METHOD)

    assert {
        (measure.name, measure.function, measure.line_start, measure.line_end)
        for measure in measure_project(tmp_path).measures
        if measure.function is not None
    } == {
        (MeasureName.CYCLOMATIC_COMPLEXITY, "Cart.make", 3, 6),
        (MeasureName.FUNCTION_LINES_OF_CODE, "Cart.make", 3, 6),
        (MeasureName.COGNITIVE_COMPLEXITY, "Cart.make", 3, 6),
        (MeasureName.PARAMETER_COUNT, "Cart.make", 3, 6),
    }


NESTED_FUNCTION = "def outer(x):\n    def inner(y):\n        return y\n    return inner(x)\n"


def test_a_nested_function_is_named_after_its_enclosing_function(tmp_path: Path) -> None:
    write_module(tmp_path, "app.py", NESTED_FUNCTION)

    assert {
        measure.function
        for measure in measure_project(tmp_path).measures
        if measure.name is MeasureName.CYCLOMATIC_COMPLEXITY
    } == {"outer", "outer.inner"}


CONDITIONAL_DEFINITIONS = (
    "import sys\n"
    "if sys.platform == 'win32':\n"
    "    def home():\n"
    "        return 'C:'\n"
    "else:\n"
    "    def home():\n"
    "        return '/'\n"
    "try:\n"
    "    import ujson\n"
    "except ImportError:\n"
    "    def loads(text):\n"
    "        return text\n"
)


def test_functions_defined_inside_if_and_try_blocks_are_measured(tmp_path: Path) -> None:
    write_module(tmp_path, "compat.py", CONDITIONAL_DEFINITIONS)

    assert {
        (measure.function, measure.line_start)
        for measure in measure_project(tmp_path).measures
        if measure.name is MeasureName.COGNITIVE_COMPLEXITY
    } == {("home", 3), ("home", 6), ("loads", 11)}


PARAMETER_SHAPES = (
    "class Cart:\n"
    "    def add(self, item, qty=1):\n"
    "        return item\n"
    "\n"
    "    @classmethod\n"
    "    def build(cls, items):\n"
    "        return cls()\n"
    "\n"
    "    @staticmethod\n"
    "    def make(a, b):\n"
    "        return a\n"
    "\n"
    "\n"
    "def fetch(url, /, *, timeout=3):\n"
    "    return url\n"
    "\n"
    "\n"
    "def forward(*args, **kwargs):\n"
    "    return args\n"
)


def test_parameter_count_skips_self_cls_and_the_bare_star(tmp_path: Path) -> None:
    write_module(tmp_path, "cart.py", PARAMETER_SHAPES)

    assert measure_values(tmp_path, MeasureName.PARAMETER_COUNT) == {
        "Cart.add": 2,
        "Cart.build": 1,
        "Cart.make": 2,
        "fetch": 2,
        "forward": 2,
    }


SCRIPT_WITH_DOCSTRING_AND_COMMENTS = (
    '"""Print the arguments.\n'
    "\n"
    'Run it from the shell."""\n'
    "\n"
    "import sys\n"
    "\n"
    "# one line per argument\n"
    "for argument in sys.argv:\n"
    "    print(argument)\n"
)


def test_file_lines_of_code_skip_docstrings_comments_and_blank_lines(tmp_path: Path) -> None:
    write_module(tmp_path, "script.py", SCRIPT_WITH_DOCSTRING_AND_COMMENTS)

    assert [
        measure
        for measure in measure_project(tmp_path).measures
        if measure.name is MeasureName.FILE_LINES_OF_CODE
    ] == [
        Measure(
            name=MeasureName.FILE_LINES_OF_CODE,
            value=3,
            function=None,
            file="script.py",
            line_start=1,
            line_end=9,
        )
    ]


def test_an_empty_file_has_zero_lines_of_code(tmp_path: Path) -> None:
    write_module(tmp_path, "pkg/__init__.py", "")

    assert measure_values_by_file(tmp_path, MeasureName.FILE_LINES_OF_CODE) == {
        "pkg/__init__.py": 0
    }


def measure_values_by_file(root: Path, name: MeasureName) -> dict[str, int]:
    return {
        measure.file: measure.value
        for measure in measure_project(root).measures
        if measure.name is name
    }
