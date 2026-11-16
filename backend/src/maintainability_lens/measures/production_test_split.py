from pathlib import PurePosixPath

TEST_FOLDERS = frozenset({"test", "tests"})


def is_test_file(relative_file: str) -> bool:
    path = PurePosixPath(relative_file)
    return (
        path.name == "conftest.py"
        or path.name.startswith("test_")
        or path.stem.endswith("_test")
        or any(folder in TEST_FOLDERS for folder in path.parts[:-1])
    )
