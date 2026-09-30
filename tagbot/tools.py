import json
import logging

import discord

from tagbot.config import MAX_EXTRA_MESSAGES
from tagbot.formatting import format_message

log = logging.getLogger(__name__)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "get_message",
        "description": "Fetch a single message from this channel by ID, e.g. a reply target outside the transcript.",
        "parameters": {
            "type": "object",
            "properties": {"message_id": {"type": "string", "description": "Discord message ID"}},
            "required": ["message_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "fetch_earlier_messages",
        "description": (
            "Fetch messages sent before a given message, for background context. "
            f"Limited budget of {MAX_EXTRA_MESSAGES} extra messages per summary."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "before_message_id": {"type": "string", "description": "Fetch messages older than this ID"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 25},
            },
            "required": ["before_message_id", "limit"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_member_info",
        "description": "Look up a user's display name, roles, and whether they are a bot.",
        "parameters": {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "Discord user ID"}},
            "required": ["user_id"],
            "additionalProperties": False,
        },
    },
]


class ToolContext:
    """Per-request tool implementations bound to one channel."""

    def __init__(self, channel):
        self.channel = channel
        self.extra_budget = MAX_EXTRA_MESSAGES

    async def call(self, name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments or "{}")
            handler = getattr(self, f"_tool_{name}", None)
            if handler is None:
                return f"error: unknown tool {name}"
            return await handler(**args)
        except discord.NotFound:
            return "error: not found"
        except discord.Forbidden:
            return "error: missing permission"
        except Exception as exc:  # tools must never raise into the agent loop
            log.exception("tool %s failed", name)
            return f"error: {exc}"

    async def _tool_get_message(self, message_id: str) -> str:
        msg = await self.channel.fetch_message(int(message_id))
        return format_message(msg)

    async def _tool_fetch_earlier_messages(self, before_message_id: str, limit: int) -> str:
        if self.extra_budget <= 0:
            return "error: extra message budget exhausted; summarize with what you have"
        limit = max(1, min(25, int(limit), self.extra_budget))
        before = discord.Object(id=int(before_message_id))
        msgs = [m async for m in self.channel.history(limit=limit, before=before)]
        self.extra_budget -= len(msgs)
        if not msgs:
            return "(no earlier messages)"
        return "\n".join(format_message(m) for m in reversed(msgs))

    async def _tool_get_member_info(self, user_id: str) -> str:
        guild = getattr(self.channel, "guild", None)
        if guild is None:
            return "error: not in a server"
        member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        roles = [r.name for r in member.roles if not r.is_default()]
        return json.dumps({"display_name": member.display_name, "roles": roles, "bot": member.bot})
