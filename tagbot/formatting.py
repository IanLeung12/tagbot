import re

from tagbot.config import DEFAULT_N, MAX_MSG_CHARS, MAX_N

_MENTION_RE = re.compile(r"<@[!&]?\d+>")
_INT_RE = re.compile(r"-?\d+")


def clamp_n(n: int | None) -> int:
    if n is None:
        return DEFAULT_N
    return max(1, min(MAX_N, n))


def parse_mention_n(content: str) -> int | None:
    """Return the first integer in the message after stripping mentions."""
    match = _INT_RE.search(_MENTION_RE.sub(" ", content))
    return int(match.group()) if match else None


def format_message(msg) -> str:
    ts = msg.created_at.strftime("%Y-%m-%d %H:%M")
    content = msg.content or ""
    if len(content) > MAX_MSG_CHARS:
        content = content[:MAX_MSG_CHARS] + "…[truncated]"
    parts = [f"[{msg.id}] [{ts}] {msg.author.display_name}:"]
    ref = getattr(msg, "reference", None)
    if ref is not None and getattr(ref, "message_id", None):
        parts.append(f"(reply to {ref.message_id})")
    if content:
        parts.append(content)
    if msg.attachments:
        parts.append(f"[{len(msg.attachments)} attachments]")
    if msg.embeds:
        parts.append("[embed]")
    return " ".join(parts)


def chunk(text: str, limit: int = 2000) -> list[str]:
    """Split text into pieces <= limit, preferring paragraph then line boundaries."""
    chunks: list[str] = []
    remaining = text.strip()
    while len(remaining) > limit:
        cut = remaining.rfind("\n\n", 0, limit)
        if cut <= 0:
            cut = remaining.rfind("\n", 0, limit)
        if cut <= 0:
            cut = remaining.rfind(" ", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks
