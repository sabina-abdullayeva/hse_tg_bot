from dotenv import load_dotenv

import bot
import db


def main() -> None:
    load_dotenv(override=True)
    bot.run()


if __name__ == "__main__":
    main()

