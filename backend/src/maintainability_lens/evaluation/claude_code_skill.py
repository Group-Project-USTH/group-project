import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

from maintainability_lens.evaluation.approach_error import ApproachError
from maintainability_lens.evaluation.recorded_findings import FileFindings
from maintainability_lens.schemas import Characteristic, Finding

MCP_SERVER_NAME = "maintainability-lens"
READ_ONLY_TOOLS = ["Read", "Grep", "Glob", "Skill", "ToolSearch"]
MCP_TOOLS = [f"mcp__{MCP_SERVER_NAME}__rate_project", f"mcp__{MCP_SERVER_NAME}__measure_project"]
# Why: user settings carry the person's own plugins, hooks and claude.ai connectors, which
# would make Runs differ between machines.
SETTING_SOURCES = "project,local"
DEFAULT_MAX_TURNS = 30
DEFAULT_TIMEOUT_SECONDS = 900


class SkillAnswer(BaseModel):
    findings: list[Finding]


@dataclass(frozen=True)
class ClaudeCodeOptions:
    plugin_directory: Path
    model: str
    max_budget_usd: float
    claude_executable: str = "claude"
    max_turns: int = DEFAULT_MAX_TURNS
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


def build_prompt(checkout: Path, file: str) -> str:
    return (
        f"Evaluate the maintainability of the file {file} in the Python project at {checkout}, "
        "for all five Characteristics. Use the /maintainability-lens:evaluate skill."
    )


def write_mcp_config(plugin_directory: Path, folder: Path) -> Path:
    mcp_config_file = folder / "mcp.json"
    server = {
        "command": "uvx",
        "args": ["--from", str(plugin_directory / "backend"), "maintainability-lens", "mcp"],
    }
    mcp_config_file.write_text(json.dumps({"mcpServers": {MCP_SERVER_NAME: server}}))
    return mcp_config_file


def build_command(
    options: ClaudeCodeOptions, checkout: Path, file: str, mcp_config_file: Path
) -> list[str]:
    return [
        options.claude_executable,
        "-p",
        build_prompt(checkout, file),
        "--model",
        options.model,
        "--max-budget-usd",
        str(options.max_budget_usd),
        "--max-turns",
        str(options.max_turns),
        "--plugin-dir",
        str(options.plugin_directory),
        "--setting-sources",
        SETTING_SOURCES,
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_config_file),
        "--tools",
        ",".join(READ_ONLY_TOOLS),
        "--allowedTools",
        ",".join(READ_ONLY_TOOLS + MCP_TOOLS),
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(SkillAnswer.model_json_schema()),
    ]


def run_claude(options: ClaudeCodeOptions, checkout: Path, file: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as folder:
        command = build_command(
            options, checkout, file, write_mcp_config(options.plugin_directory, Path(folder))
        )
        try:
            completed = subprocess.run(
                command,
                cwd=checkout,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=options.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            raise ApproachError(f"claude timed out after {options.timeout_seconds} s") from error
    try:
        result: dict[str, object] = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise ApproachError(f"claude printed no JSON result: {completed.stderr[-500:]}") from error
    return result


def check_every_characteristic(findings: list[Finding]) -> None:
    answered = [finding.characteristic for finding in findings]
    missing = [
        characteristic for characteristic in Characteristic if characteristic not in answered
    ]
    if missing or len(answered) != len(Characteristic):
        raise ApproachError(
            f"expected one Finding per Characteristic, missing: {', '.join(missing) or 'none'}, "
            f"got: {', '.join(answered)}"
        )


def decide_with_claude_code(options: ClaudeCodeOptions, checkout: Path, file: str) -> FileFindings:
    result = run_claude(options, checkout, file)
    if result.get("is_error") or "structured_output" not in result:
        raise ApproachError(f"claude ended with {result.get('subtype', 'no structured output')}")
    try:
        answer = SkillAnswer.model_validate(result["structured_output"])
    except ValidationError as error:
        raise ApproachError(f"claude's answer is not valid: {error}") from error
    check_every_characteristic(answer.findings)
    order = list(Characteristic)
    findings = sorted(answer.findings, key=lambda finding: order.index(finding.characteristic))
    cost_usd = result.get("total_cost_usd")
    return FileFindings(
        findings=findings,
        cost_usd=float(cost_usd) if isinstance(cost_usd, int | float) else None,
        model=options.model,
    )
