import os

from dotenv import load_dotenv

load_dotenv()


def main():
    bot_token = os.getenv('BOT_TOKEN')


if __name__ == '__main__':
    main()
