import logging
import os
import uuid
from typing import Dict

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedPhoto
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler

from game import Game

logging.basicConfig(handlers=[logging.FileHandler('log.txt', 'w', 'utf-8')],
                    level=logging.INFO,
                    format='[*] {%(pathname)s:%(lineno)d} %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

games: Dict[str, Game] = {

}

hang_pictures = [
    'AgACAgIAAxkBAAEElvVeut5w_59T8UPAtXdG8MOt4nQWNQACFa0xG0862UkDGIBguDSiMvcBwQ4ABAEAAwIAA20AAyUCBgABGQQ',  # 1
    'AgACAgIAAxkBAAEElvleut7eWdrlHyoeg7rs8PcsZePVVAACF60xG0862Um-2_GyoL56KXpQxZIuAAMBAAMCAANtAAP37wEAARkE',  # 2
    'AgACAgIAAxkBAAEElv9eut8E61wtbElLnixp2oteBogurQACGK0xG0862UmVqOOQh7uITw9p6JIuAAMBAAMCAANtAANLUQEAARkE',  # 3
    'AgACAgIAAxkBAAEElwFeut8ZBjtrX7VbeqzUvExDbUHrSQACGa0xG0862UkDz33pmE2EPVOteJEuAAMBAAMCAANtAAMLLgMAARkE',  # 4
    'AgACAgIAAxkBAAEElwZeut8xLTI-5jIcYZorOJrPaSKMfwACGq0xG0862UnEByrCFqsfmsLv6ZIuAAMBAAMCAANtAAPvUgEAARkE',  # 5
    'AgACAgIAAxkBAAEElwheut9BEG03f-MJi4hoLAsma03GzAACG60xG0862UkRVeFtdKXynDFEyw4ABAEAAwIAA20AA5KQBQABGQQ',  # 6
    'AgACAgIAAxkBAAEElwxeut9QCu1ljQdW6UUg0YzEylRVGQACHK0xG0862UmBT8XSfgFjVMvJw5IuAAMBAAMCAANtAAMu7gEAARkE',  # 7
    'AgACAgIAAxkBAAEElw5eut9bX8GpubfagHQfpN36iQ6xkQACHa0xG0862Um7ll3MmYtz9TwmwQ4ABAEAAwIAA20AA2H4BQABGQQ',  # 8
    'AgACAgIAAxkBAAEElxJeut9oDkLPArTUI4wfk7jv5g60uQACHq0xG0862UmDgFraznJxGSskwQ4ABAEAAwIAA20AAwX-BQABGQQ',  # 9
    'AgACAgIAAxkBAAEElxReut90tnmUfRtlm74aEnVkZxUlPAACH60xG0862UmHpb8Lsml0-7EaCJIuAAMBAAMCAANtAAP7UwEAARkE',  # 10
    'AgACAgIAAxkBAAEElxheut-PsA-wBqCDx2XU7GODUC514wACIK0xG0862Ul8RIuDm_TdKTRr6JIuAAMBAAMCAANtAAO5UAEAARkE',  # 11
]


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


keyboard_markup = InlineKeyboardMarkup(list(split([
    InlineKeyboardButton(chr(x), callback_data=chr(x)) for x in range(ord('а'), ord('я') + 1)], 6)))


def error(update, context):
    print(f'Update "{update}" caused error "{context.error}"')
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def button(update, context):
    query = update.callback_query
    print(update)
    query.answer()


def inline_handler(update, context):
    query = update.inline_query
    print(update)

    results = [
        InlineQueryResultCachedPhoto(
            id=uuid.uuid4(),
            photo_file_id=hang_pictures[0],
            caption=Game(query.query).apply_mask(),
            reply_markup=keyboard_markup,
        )
    ]

    res = update.inline_query.answer(results, cache_time=1, is_personal=True)
    print(f'inline_handler answer result: {res}')


def main():
    bot_token = os.getenv('BOT_TOKEN')
    updater = Updater(bot_token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(InlineQueryHandler(inline_handler))
    dp.add_handler(CallbackQueryHandler(button))

    dp.add_error_handler(error)

    print('Starting polling')
    updater.start_polling(clean=True)
    updater.idle()


if __name__ == '__main__':
    main()
