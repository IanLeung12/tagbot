import pytest

from tagbot.config import MAX_MSG_CHARS
from tagbot.formatting import chunk, clamp_n, format_message, parse_mention_n
from tests.helpers import fake_msg


@pytest.mark.parametrize("n,expected", [(None, 25), (0, 1), (-5, 1), (25, 25), (200, 200), (201, 200)])
def test_clamp_n(n, expected):
    assert clamp_n(n) == expected


@pytest.mark.parametrize(
    "content,expected",
    [
        ("<@123456> summarize 50", 50),
        ("<@!123456> 10", 10),
        ("<@123456> summarize", None),
        ("<@123456>", None),
        ("summarize 300 <@123456>", 300),
    ],
)
def test_parse_mention_n(content, expected):
    assert parse_mention_n(content) == expected


def test_format_message_markers():
    line = format_message(fake_msg(id=7, content="yo", reply_to=5, attachments=2, embeds=1))
    assert line == "[7] [2026-09-30 12:00] alice: (reply to 5) yo [2 attachments] [embed]"


def test_format_message_truncates():
    line = format_message(fake_msg(content="x" * (MAX_MSG_CHARS + 50)))
    assert line.endswith("…[truncated]")
    assert "x" * (MAX_MSG_CHARS + 1) not in line


def test_chunk_respects_limit():
    text = "\n\n".join(["para " + "w " * 300] * 10)
    parts = chunk(text, limit=2000)
    assert len(parts) > 1
    assert all(len(p) <= 2000 for p in parts)


def test_chunk_hard_split():
    parts = chunk("a" * 4500, limit=2000)
    assert [len(p) for p in parts] == [2000, 2000, 500]


def test_chunk_short():
    assert chunk("hello") == ["hello"]
