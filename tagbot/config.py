import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_N = 25
MAX_N = 200
MAX_TOOL_ROUNDS = 4
MAX_EXTRA_MESSAGES = 50
MAX_MSG_CHARS = 1000
COOLDOWN_SECONDS = 30


@dataclass(frozen=True)
class Config:
    discord_token: str
    openai_api_key: str
    openai_model: str
    dev_guild_id: int | None


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    api_key = os.getenv("OPENAI_API_KEY")
    missing = [name for name, val in (("DISCORD_TOKEN", token), ("OPENAI_API_KEY", api_key)) if not val]
    if missing:
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")
    guild = os.getenv("DEV_GUILD_ID")
    return Config(
        discord_token=token,
        openai_api_key=api_key,
        openai_model=os.getenv("OPENAI_MODEL") or "gpt-6-luna",
        dev_guild_id=int(guild) if guild else None,
    )
