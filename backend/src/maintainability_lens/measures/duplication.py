from collections import defaultdict

from maintainability_lens.measures.parsed_file import ParsedFile
from maintainability_lens.schemas import Measure, MeasureName

# SIG (Heitlager, Kuipers and Visser 2007): code blocks of at least 6 lines.
DUPLICATION_BLOCK_LINES = 6

Block = tuple[str, ...]
BlockStart = tuple[ParsedFile, int]


def find_block_starts(parsed_files: list[ParsedFile]) -> dict[Block, list[BlockStart]]:
    block_starts: dict[Block, list[BlockStart]] = defaultdict(list)
    for parsed_file in parsed_files:
        texts = [code_line.text_without_indentation for code_line in parsed_file.code_lines]
        for start in range(len(texts) - DUPLICATION_BLOCK_LINES + 1):
            block = tuple(texts[start : start + DUPLICATION_BLOCK_LINES])
            block_starts[block].append((parsed_file, start))
    return block_starts


def find_duplicated_line_numbers(parsed_files: list[ParsedFile]) -> dict[str, set[int]]:
    duplicated_line_numbers: dict[str, set[int]] = {
        parsed_file.relative_file: set() for parsed_file in parsed_files
    }
    for starts in find_block_starts(parsed_files).values():
        if len(starts) < 2:
            continue
        for parsed_file, start in starts:
            duplicated_line_numbers[parsed_file.relative_file].update(
                code_line.line_number
                for code_line in parsed_file.code_lines[start : start + DUPLICATION_BLOCK_LINES]
            )
    return duplicated_line_numbers


def measure_duplication(parsed_files: list[ParsedFile]) -> list[Measure]:
    duplicated_line_numbers = find_duplicated_line_numbers(parsed_files)
    return [
        Measure(
            name=MeasureName.DUPLICATED_LINES,
            value=len(duplicated_line_numbers[parsed_file.relative_file]),
            file=parsed_file.relative_file,
            line_start=1,
            line_end=max(parsed_file.line_count, 1),
        )
        for parsed_file in parsed_files
    ]
