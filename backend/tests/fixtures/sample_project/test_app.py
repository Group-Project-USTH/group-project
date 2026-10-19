from utils import format_money


def test_format_money():
    assert format_money(1234.5) == "$1,234.50"
