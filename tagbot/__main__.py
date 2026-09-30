import logging

from tagbot.bot import build_bot
from tagbot.config import load_config


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    bot = build_bot(config)
    bot.run(config.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
