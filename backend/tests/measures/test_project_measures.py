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


@pytest.mark.parametrize(
    ("relative_path", "is_test_code"),
    [
        pytest.param("test_app.py", True, id="test-prefix"),
        pytest.param("app_test.py", True, id="test-suffix"),
        pytest.param("conftest.py", True, id="pytest-conftest"),
        pytest.param("tests/helpers.py", True, id="inside-tests-folder"),
        pytest.param("shop/test/factories.py", True, id="inside-nested-test-folder"),
        pytest.param("app.py", False, id="production"),
        pytest.param("testing_tools.py", False, id="test-is-only-a-prefix-of-a-word"),
        pytest.param("latest.py", False, id="test-is-only-a-suffix-of-a-word"),
        pytest.param("contest/app.py", False, id="folder-name-only-ends-in-test"),
    ],
)
def test_measures_of_test_files_are_tagged_as_test_code(
    tmp_path: Path, relative_path: str, is_test_code: bool
) -> None:
    write_module(tmp_path, relative_path, "def check():\n    return 1\n")

    assert {measure.is_test_code for measure in measure_project(tmp_path).measures} == {
        is_test_code
    }


TOTAL_AS_FUNCTION = (
    "def total(items):\n"
    "    subtotal = 0\n"
    "    for item in items:\n"
    "        subtotal += item.price\n"
    "    tax = subtotal * 0.1\n"
    "    shipping = 5\n"
    "    return subtotal + tax + shipping\n"
)
TOTAL_AS_METHOD_WITH_A_COMMENT = (
    "class Cart:\n"
    "    def total(self, items):\n"
    "        subtotal = 0\n"
    "        for item in items:\n"
    "            subtotal += item.price\n"
    "\n"
    "        # ten percent\n"
    "        tax = subtotal * 0.1\n"
    "        shipping = 5\n"
    "        return subtotal + tax + shipping\n"
)


def test_a_six_line_block_copied_across_files_is_duplicated_in_both(tmp_path: Path) -> None:
    write_module(tmp_path, "orders.py", TOTAL_AS_FUNCTION)
    write_module(tmp_path, "cart.py", TOTAL_AS_METHOD_WITH_A_COMMENT)
    write_module(tmp_path, "unique.py", "def ping():\n    return 'pong'\n")

    assert measure_values_by_file(tmp_path, MeasureName.DUPLICATED_LINES) == {
        "orders.py": 6,
        "cart.py": 6,
        "unique.py": 0,
    }


def test_a_copied_block_shorter_than_six_lines_is_not_duplication(tmp_path: Path) -> None:
    five_line_body = "".join(TOTAL_AS_FUNCTION.splitlines(keepends=True)[1:6])
    write_module(tmp_path, "a.py", "def first(items):\n" + five_line_body)
    write_module(tmp_path, "b.py", "def second(items):\n" + five_line_body)

    assert measure_values_by_file(tmp_path, MeasureName.DUPLICATED_LINES) == {"a.py": 0, "b.py": 0}


def fan_in_of(root: Path, files: dict[str, str]) -> dict[str, int]:
    for relative_path, source in files.items():
        write_module(root, relative_path, source)
    return measure_values_by_file(root, MeasureName.FILE_FAN_IN)


def test_fan_in_counts_the_files_that_import_a_module(tmp_path: Path) -> None:
    assert fan_in_of(
        tmp_path,
        {
            "shop/__init__.py": "",
            "shop/pricing.py": "def price():\n    return 1\n",
            "shop/orders.py": "from shop.pricing import price\n",
            "shop/cart.py": "import shop.pricing\nimport json\n",
            "app.py": "from shop import orders\n",
        },
    ) == {
        "shop/__init__.py": 0,
        "shop/pricing.py": 2,
        "shop/orders.py": 1,
        "shop/cart.py": 0,
        "app.py": 0,
    }


def test_fan_in_follows_relative_imports(tmp_path: Path) -> None:
    assert (
        fan_in_of(
            tmp_path,
            {
                "pkg/__init__.py": "from .b import f\n",
                "pkg/a.py": "from .b import f\n",
                "pkg/b.py": "def f():\n    return 1\n",
                "pkg/c.py": "from . import b\n",
                "pkg/sub/__init__.py": "",
                "pkg/sub/d.py": "from ..b import f\n",
            },
        )["pkg/b.py"]
        == 4
    )


def test_fan_in_resolves_src_layout_and_script_style_imports(tmp_path: Path) -> None:
    assert fan_in_of(
        tmp_path,
        {
            "src/app/__init__.py": "",
            "src/app/config.py": "DEBUG = True\n",
            "src/app/main.py": "from app.config import DEBUG\n",
            "scripts/helpers.py": "def run():\n    return 1\n",
            "scripts/deploy.py": "from helpers import run\n",
            "tools/helpers.py": "def run():\n    return 2\n",
        },
    ) == {
        "src/app/__init__.py": 0,
        "src/app/config.py": 1,
        "src/app/main.py": 0,
        "scripts/helpers.py": 1,
        "scripts/deploy.py": 0,
        "tools/helpers.py": 0,
    }


def test_fan_in_counts_each_production_importer_once(tmp_path: Path) -> None:
    assert (
        fan_in_of(
            tmp_path,
            {
                "pricing.py": "def price():\n    return 1\n",
                "orders.py": (
                    "import pricing\nfrom pricing import price\n\n\ndef f():\n    import pricing\n"
                ),
                "tests/test_pricing.py": "from pricing import price\n",
            },
        )["pricing.py"]
        == 1
    )


def test_fan_in_of_a_package_measured_on_its_own_follows_imports_up_to_the_target(
    tmp_path: Path,
) -> None:
    assert (
        fan_in_of(
            tmp_path,
            {
                "__init__.py": "",
                "schemas.py": "class Measure:\n    pass\n",
                "measures/__init__.py": "",
                "measures/volume.py": (
                    "from ..schemas import Measure\nfrom ...outside import thing\n"
                ),
            },
        )["schemas.py"]
        == 1
    )


def test_fan_in_of_a_package_target_follows_imports_that_name_the_package(
    tmp_path: Path,
) -> None:
    package = tmp_path.name
    assert (
        fan_in_of(
            tmp_path,
            {
                "__init__.py": "",
                "messages.py": "class Message:\n    pass\n",
                "prompts/__init__.py": "",
                "prompts/chat.py": f"from {package}.messages import Message\n",
            },
        )["messages.py"]
        == 1
    )


def test_fan_in_ignores_a_standard_library_import_named_like_a_project_module(
    tmp_path: Path,
) -> None:
    assert (
        fan_in_of(
            tmp_path,
            {
                "utils/__init__.py": "",
                "utils/uuid.py": "def short_id():\n    return 'a'\n",
                "app.py": "from uuid import uuid4\n",
            },
        )["utils/uuid.py"]
        == 0
    )


def test_file_in_the_encoding_its_coding_line_declares_is_measured(tmp_path: Path) -> None:
    source = "# -*- coding: latin-1 -*-\ndef f(x):\n    return 'café' + x\n"
    (tmp_path / "latin.py").write_bytes(source.encode("latin-1"))

    project_measures = measure_project(tmp_path)

    lines_of_code = [
        measure.value
        for measure in project_measures.measures
        if measure.name is MeasureName.FILE_LINES_OF_CODE
    ]
    assert lines_of_code == [2]
    assert project_measures.unparsed_files == []


def test_file_that_cannot_be_decoded_is_reported_as_unparsed(tmp_path: Path) -> None:
    (tmp_path / "garbled.py").write_bytes(b"def f():\n    return '\xfa'\n")
    write_module(tmp_path, "fine.py", "def g(x):\n    return x\n")

    project_measures = measure_project(tmp_path)

    assert project_measures.unparsed_files == ["garbled.py"]
