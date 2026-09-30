# tagbot

An agentic Discord bot that summarizes the last *n* messages in a channel (default 25, max 200) using the OpenAI API.
The model can call tools to pull missing context (reply targets outside the window, a few earlier messages, member info) before writing the summary.

## Usage

- `/summarize [n]`
- `@tagbot summarize [n]` (or just `@tagbot`, `@tagbot 50`)

## Setup

1. In the [Discord Developer Portal](https://discord.com/developers/applications), create an application and add a bot.
   - Under **Bot**, enable **Message Content Intent**.
   - Under **OAuth2 → URL Generator**, pick the scopes `bot` and `applications.commands`, and the permissions **View Channels**, **Read Message History**, and **Send Messages**. Use the generated URL to invite the bot.
2. Install:
   ```sh
   python -m venv .venv
   .venv\Scripts\activate        # Windows (source .venv/bin/activate elsewhere)
   pip install -e ".[dev]"
   ```
3. Copy `.env.example` to `.env` and fill in `DISCORD_TOKEN` and `OPENAI_API_KEY`. `OPENAI_MODEL` defaults to `gpt-6-luna`.
   Set `DEV_GUILD_ID` to your test server's ID for instant slash-command sync. Global sync can take up to an hour.
4. Run `python -m tagbot`.

## Tests

```sh
pytest
```
