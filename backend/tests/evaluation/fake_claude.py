import json
import stat
from pathlib import Path
from typing import Any

import pytest

from maintainability_lens.evaluation import ClaudeCodeOptions
from maintainability_lens.schemas import Characteristic

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
call = {"argv": sys.argv[1:], "cwd": os.getcwd()}
Path(os.environ["FAKE_CLAUDE_CALL"]).write_text(json.dumps(call))
mcp_config = sys.argv[sys.argv.index("--mcp-config") + 1]
Path(os.environ["FAKE_CLAUDE_MCP"]).write_text(Path(mcp_config).read_text())
prompt = sys.argv[sys.argv.index("-p") + 1]
failing = os.environ.get("FAKE_CLAUDE_FAIL_FOR")
if failing and failing in prompt:
    print(json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True}))
else:
    print(Path(os.environ["FAKE_CLAUDE_RESULT"]).read_text())
"""


def finding(characteristic: Characteristic) -> dict[str, Any]:
    return {
        "characteristic": characteristic.value,
        "verdict": "fail",
        "evidence": [{"file": "app.py", "line_start": 3, "line_end": 9}],
        "rationale": "process_order has cyclomatic complexity 21 (Heitlager 2007).",
    }


def success(findings: list[dict[str, Any]], cost_usd: float = 0.42) -> dict[str, Any]:
    return {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "total_cost_usd": cost_usd,
        "structured_output": {"findings": findings},
    }


class FakeClaude:
    def __init__(self, folder: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self.executable = folder / "claude"
        self.executable.write_text(FAKE_CLAUDE)
        self.executable.chmod(self.executable.stat().st_mode | stat.S_IXUSR)
        self.call_file = folder / "call.json"
        self.mcp_file = folder / "mcp.json"
        self.result_file = folder / "result.json"
        monkeypatch.setenv("FAKE_CLAUDE_CALL", str(self.call_file))
        monkeypatch.setenv("FAKE_CLAUDE_MCP", str(self.mcp_file))
        monkeypatch.setenv("FAKE_CLAUDE_RESULT", str(self.result_file))

    def answer(self, result: dict[str, Any]) -> None:
        self.result_file.write_text(json.dumps(result))

    def call(self) -> dict[str, Any]:
        loaded: dict[str, Any] = json.loads(self.call_file.read_text())
        return loaded

    def option(self, name: str) -> str:
        argv = self.call()["argv"]
        value: str = argv[argv.index(name) + 1]
        return value

    def options(self, plugin_directory: Path) -> ClaudeCodeOptions:
        return ClaudeCodeOptions(
            plugin_directory=plugin_directory,
            model="claude-sonnet-5-5",
            max_budget_usd=1.5,
            claude_executable=str(self.executable),
        )


def answer_every_characteristic(fake: FakeClaude) -> None:
    fake.answer(success([finding(characteristic) for characteristic in Characteristic]))
