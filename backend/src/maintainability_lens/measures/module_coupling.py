import ast
from collections import defaultdict
from pathlib import PurePosixPath

from maintainability_lens.measures.parsed_file import ParsedFile
from maintainability_lens.measures.production_test_split import is_test_file
from maintainability_lens.schemas import Measure, MeasureName

ModuleName = tuple[str, ...]


class ProjectModules:
    def __init__(self, relative_files: list[str], target_name: str) -> None:
        self.target_name = target_name
        self.package_folders = {
            PurePosixPath(relative_file).parent
            for relative_file in relative_files
            if PurePosixPath(relative_file).name == "__init__.py"
        }
        self.files_by_name: dict[ModuleName, list[str]] = defaultdict(list)
        for relative_file in relative_files:
            self.files_by_name[self.import_name_of(relative_file)].append(relative_file)

    def package_chain_of(self, folder: PurePosixPath) -> ModuleName:
        chain: list[str] = []
        while folder in self.package_folders:
            chain.insert(0, folder.name or self.target_name)
            if folder == folder.parent:
                break
            folder = folder.parent
        return tuple(chain)

    def import_name_of(self, relative_file: str) -> ModuleName:
        path = PurePosixPath(relative_file)
        package_chain = self.package_chain_of(path.parent)
        return package_chain if path.stem == "__init__" else (*package_chain, path.stem)

    def package_of(self, relative_file: str) -> ModuleName:
        import_name = self.import_name_of(relative_file)
        return import_name if relative_file.endswith("__init__.py") else import_name[:-1]

    def resolve(self, module_name: ModuleName, importer: str) -> str | None:
        candidates = self.files_by_name.get(module_name, [])
        if len(candidates) > 1:
            importer_folder = PurePosixPath(importer).parent
            candidates = [
                file for file in candidates if PurePosixPath(file).parent == importer_folder
            ]
        return candidates[0] if len(candidates) == 1 else None

    def relative_base(self, importer: str, level: int) -> ModuleName | None:
        package = self.package_of(importer)
        levels_up = level - 1
        return package[: len(package) - levels_up] if levels_up < len(package) else None


def candidate_module_names(
    node: ast.Import | ast.ImportFrom, importer: str, project_modules: ProjectModules
) -> list[list[ModuleName]]:
    if isinstance(node, ast.Import):
        return [[tuple(alias.name.split("."))] for alias in node.names]
    base = project_modules.relative_base(importer, node.level) if node.level else ()
    if base is None:
        return []
    module_name = base + tuple(node.module.split(".") if node.module else ())
    return [[(*module_name, alias.name), module_name] for alias in node.names]


def find_imported_files(parsed_file: ParsedFile, project_modules: ProjectModules) -> set[str]:
    importer = parsed_file.relative_file
    imported_files = set()
    for node in ast.walk(parsed_file.tree):
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue
        for candidates in candidate_module_names(node, importer, project_modules):
            resolved = (project_modules.resolve(name, importer) for name in candidates)
            imported_file = next((file for file in resolved if file is not None), None)
            if imported_file is not None:
                imported_files.add(imported_file)
    return imported_files - {importer}


def measure_module_coupling(parsed_files: list[ParsedFile], target_name: str) -> list[Measure]:
    project_modules = ProjectModules(
        [parsed_file.relative_file for parsed_file in parsed_files], target_name
    )
    importers_by_file: dict[str, set[str]] = defaultdict(set)
    for parsed_file in parsed_files:
        if is_test_file(parsed_file.relative_file):
            continue
        for imported_file in find_imported_files(parsed_file, project_modules):
            importers_by_file[imported_file].add(parsed_file.relative_file)
    return [
        Measure(
            name=MeasureName.FILE_FAN_IN,
            value=len(importers_by_file[parsed_file.relative_file]),
            file=parsed_file.relative_file,
            line_start=1,
            line_end=max(parsed_file.line_count, 1),
        )
        for parsed_file in parsed_files
    ]
