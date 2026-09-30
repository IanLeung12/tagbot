import logging
import time

import discord
import openai
from discord import app_commands

from tagbot import agent
from tagbot.config import COOLDOWN_SECONDS, DEFAULT_N, MAX_N, Config
from tagbot.formatting import chunk, clamp_n, parse_mention_n

log = logging.getLogger(__name__)


class TagBot(discord.Client):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.config = config
        self.tree = app_commands.CommandTree(self)
        self.openai = openai.AsyncOpenAI(api_key=config.openai_api_key)
        self._mention_cooldowns: dict[int, float] = {}

    async def setup_hook(self) -> None:
        if self.config.dev_guild_id:
            guild = discord.Object(id=self.config.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        log.info("Logged in as %s (model=%s)", self.user, self.config.openai_model)

    async def run_summary(self, channel, n: int, before=None) -> str:
        """Fetch the last n messages (oldest first, excluding our own) and summarize them."""
        try:
            history = [m async for m in channel.history(limit=n, before=before)]
        except discord.Forbidden:
            return "I can't read message history in this channel."
        messages = [m for m in reversed(history) if m.author.id != self.user.id]
        try:
            return await agent.summarize(self.openai, self.config.openai_model, channel, messages)
        except openai.APIError:
            log.exception("OpenAI request failed")
            return "Sorry, the summary request to OpenAI failed. Try again in a bit."

    def _mention_on_cooldown(self, channel_id: int) -> bool:
        now = time.monotonic()
        last = self._mention_cooldowns.get(channel_id, 0.0)
        if now - last < COOLDOWN_SECONDS:
            return True
        self._mention_cooldowns[channel_id] = now
        return False

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or self.user not in message.mentions:
            return
        if self._mention_on_cooldown(message.channel.id):
            await message.reply(f"Slow down, one summary per {COOLDOWN_SECONDS}s per channel.")
            return
        n = clamp_n(parse_mention_n(message.content))
        async with message.channel.typing():
            summary = await self.run_summary(message.channel, n, before=message)
        parts = chunk(f"**Summary of the last {n} messages**\n\n{summary}")
        await message.reply(parts[0])
        for part in parts[1:]:
            await message.channel.send(part)


def build_bot(config: Config) -> TagBot:
    bot = TagBot(config)

    @bot.tree.command(name="summarize", description="Summarize recent messages in this channel")
    @app_commands.describe(n=f"Number of messages to summarize (default {DEFAULT_N}, max {MAX_N})")
    @app_commands.checks.cooldown(1, COOLDOWN_SECONDS, key=lambda i: i.channel_id)
    async def summarize_cmd(
        interaction: discord.Interaction, n: app_commands.Range[int, 1, MAX_N] = DEFAULT_N
    ) -> None:
        await interaction.response.defer(thinking=True)
        summary = await bot.run_summary(interaction.channel, n)
        for part in chunk(f"**Summary of the last {n} messages**\n\n{summary}"):
            await interaction.followup.send(part)

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"Slow down, try again in {error.retry_after:.0f}s."
        else:
            log.exception("slash command failed", exc_info=error)
            msg = "Something went wrong."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    return bot
