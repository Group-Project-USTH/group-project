import pytest

from maintainability_agent.masking import REDACTED, redact


@pytest.mark.parametrize(
    "secret",
    [
        "sk-0a1b2c3d4e5f6a7b-xyzxyz-0000",  # router-style key (fake)
        "sk-proj-abcdefghijklmnopqrstuvwxyz012345",
        "sk-ant-api03-abcdefghijklmnop",
        "sk-lf-1234abcd-12ab-34cd-56ef-1234567890ab",
        "pk-lf-1234abcd-12ab-34cd-56ef-1234567890ab",
        "AKIAIOSFODNN7EXAMPLE",
        "ghp_" + "a" * 36,
    ],
)
def test_known_token_formats_are_redacted(secret: str) -> None:
    out = redact(f"config: {secret} end")
    assert secret not in out
    assert REDACTED in out


def test_private_key_block_is_redacted() -> None:
    block = "-----BEGIN RSA PRIVATE KEY-----\nMIIEow\nabc\n-----END RSA PRIVATE KEY-----"
    assert redact(f"x\n{block}\ny") == f"x\n{REDACTED}\ny"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("DB_PASSWORD=hunter2hunter2", "DB_PASSWORD=[REDACTED]"),
        ('GITHUB_TOKEN: "abcdefgh12345"', 'GITHUB_TOKEN: "[REDACTED]"'),
        # JSON-escaped .env content inside a span attribute: stop at the escaped newline.
        (r"MY_SECRET=abcdefgh1234\nDEBUG=1", r"MY_SECRET=[REDACTED]\nDEBUG=1"),
    ],
)
def test_secret_assignments_keep_name_drop_value(text: str, expected: str) -> None:
    assert redact(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "def process_order(order):",
        "API_KEY = short",  # values under 8 chars are left alone
        "task-1234 and risk-assessment",
        "",
    ],
)
def test_ordinary_text_is_untouched(text: str) -> None:
    assert redact(text) == text
