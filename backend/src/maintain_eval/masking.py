"""Redact likely secrets from trace data before it is exported to Langfuse.

The agent reads arbitrary files in the analysed project (possibly `.env` files or
hard-coded keys), and file contents end up in tool/generation inputs and outputs.
This only protects Langfuse: the LLM provider still sees whatever the agent reads.
"""

import re

from langfuse.types import (
    MaskOtelSpansParams,
    MaskOtelSpansResult,
    OtelSpanIdentifier,
    OtelSpanPatch,
)

REDACTED = "[REDACTED]"

_TOKEN_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\b(?:sk|pk)-[A-Za-z0-9_-]{16,}"),  # OpenAI/Anthropic/router keys, Langfuse keys
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),  # GitHub tokens
]
# `SOME_API_KEY=value` / `PASSWORD: value`: keep the name, drop the value.
# Values stop at whitespace, quotes and backslashes (JSON-escaped newlines in span attributes).
_ASSIGNMENT = re.compile(
    r"\b([A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*)(\s*[=:]\s*[\"']?)([^\s\"'\\]{8,})"
)


def redact(text: str) -> str:
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub(REDACTED, text)
    return _ASSIGNMENT.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", text)


def mask_otel_spans(*, params: MaskOtelSpansParams) -> MaskOtelSpansResult | None:
    """Langfuse `mask_otel_spans` hook: patch only string attributes that contain secrets."""
    patches: dict[OtelSpanIdentifier, OtelSpanPatch | None] = {}
    for identifier, span in params.spans.items():
        changed = {}
        for key, value in span.attributes.items():
            if isinstance(value, str):
                masked = redact(value)
                if masked != value:
                    changed[key] = masked
        if changed:
            patches[identifier] = OtelSpanPatch(set_attributes=changed)
    return MaskOtelSpansResult(span_patches=patches) if patches else None
