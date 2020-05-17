import logging
import os
import uuid
from random import choice
from typing import List, Dict

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InlineQueryResultCachedPhoto
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler

from game import Game

logging.basicConfig(handlers=[logging.FileHandler('log.txt', 'w', 'utf-8')],
                    level=logging.INFO,
                    format='[*] {%(pathname)s:%(lineno)d} %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

games: Dict[str, Game] = {}
dictionary: List[str] = []

r = redis.Redis(host='redis', port=6379, db=0)

hang_pictures = [
    'AgACAgIAAxkBAAEEoVZevs07VE3PdcU1LaLk3j6papPXjAACbqwxG7ha-Unvnd3ZHfwLlJ8zepEuAAMBAAMCAANtAAOGUwMAARkE',  # 1
    'AgACAgIAAxkBAAEEoVhevs1YbJBHv4tnN8IVwGfRJkihAQACb6wxG7ha-UmM7TRdUkNGYOcc65EuAAMBAAMCAANtAAN99wEAARkE',  # 2
    'AgACAgIAAxkBAAEEoV1evs1wwLSU8briYQQTXCDEpnBRJAACcKwxG7ha-UmWlCXotFm7zJCmgJIuAAMBAAMCAANtAAOCbgEAARkE',  # 3
    'AgACAgIAAxkBAAEEoV9evs17Wy2QPqlTGciAqv2xhDsy3wACcawxG7ha-UkG0WoITztYFh9kyw4ABAEAAwIAA20AA3qkBQABGQQ',  # 4
    'AgACAgIAAxkBAAEEoWZevs2aqpXy7DYLcSFJyvsVKfm8LQACcqwxG7ha-Ul_ZLG4DUwN3e__bZEuAAMBAAMCAANtAAP3UgMAARkE',  # 5
    'AgACAgIAAxkBAAEEoWhevs2one8-n1jj1vDlOrD2boLT3wACc6wxG7ha-Uk-NAQYCznbpW0dwQ4ABAEAAwIAA20AA7UfBgABGQQ',  # 6
    'AgACAgIAAxkBAAEEoWxevs21CTjvHdUFbRvaojKW5CWiJAACdKwxG7ha-Uk6GeJiiIt8w7oPwQ4ABAEAAwIAA20AA7YaBgABGQQ',  # 7
    'AgACAgIAAxkBAAEEoW5evs3BoJt-JblSDzw5m-kpvdMY-QACdawxG7ha-Uns4MyCq4khz2vGwg8ABAEAAwIAA20AA88IBwABGQQ',  # 8
    'AgACAgIAAxkBAAEEoXJevs3TYPp3JLQPlkBTMNbNvB6i6gACdqwxG7ha-UldpbLG1h2hhMEQwQ4ABAEAAwIAA20AA_QcBgABGQQ',  # 9
    'AgACAgIAAxkBAAEEoXRevs3l0hJBBXDsBrL3ZIM_PJoQZAACd6wxG7ha-UkDBWsMxR57pmPzwA4ABAEAAwIAA20AA4IYBgABGQQ',  # 10
    'AgACAgIAAxkBAAEEoXpevs30IhqHYxneedDC74qqb_M1RgACeKwxG7ha-UkNqNvQh0cb0Vnv6ZIuAAMBAAMCAANtAAM5bAEAARkE',  # 11
]


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


class KeyboardMarkup:
    def __init__(self, exclude=[]):
        self.keyboard_markup = InlineKeyboardMarkup(list(split([
            InlineKeyboardButton(
                chr(x), callback_data=chr(x)) for x in range(ord('а'), ord('я') + 1) if x not in exclude], 6)))

    def get_markup(self):
        return self.keyboard_markup


def error(update, context):
    print(f'Update "{update}" caused error "{context.error}"')
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def button(update, context):
    query = update.callback_query
    print(update)
    query.answer()

    if query.data == 'new_game':
        new_game(update, context)

    try:
        game_from_redis = r.get(f'game/{query.inline_message_id}')
        if game_from_redis is None:
            return

        game = Game.from_json(game_from_redis)

        if query.from_user.id != game.player_id:
            return

        char = ord(query.data)
        if char in range(ord('а'), ord('я') + 1):
            guessed_correctly = game.try_letter(query.data)

            if guessed_correctly:

                if game.no_letters_left():
                    context.bot.edit_message_text(
                        f'Вы выиграли!\n\nЗагаданное слово: {game.word}',
                        inline_message_id=query.inline_message_id,
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton('Начать новую игру!', callback_data='new_game')]])
                    )

                    r.delete(f'game/{query.inline_message_id}')

                else:
                    context.bot.edit_message_text(
                        # f'{game.apply_mask()}\n\nОшибки: {", ".join(game.errors())}',
                        f'{game.apply_mask()}\n\nОшибки: {game.errors_str()}',
                        inline_message_id=query.inline_message_id,
                        reply_markup=KeyboardMarkup(game.guessed_letters).get_markup(),
                    )

                    r.set(f'game/{query.inline_message_id}', game.to_json(), ex=3600)

            else:
                stage = game.next_stage()

                if game.last_stage_reached():
                    context.bot.edit_message_text(
                        f'Вы проиграли!\n\nЗагаданное слово: {game.word}',
                        inline_message_id=query.inline_message_id,
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton('Начать новую игру!', callback_data='new_game')]])
                    )

                    r.delete(f'game/{query.inline_message_id}')

                else:
                    context.bot.edit_message_media(
                        inline_message_id=query.inline_message_id,
                        media=InputMediaPhoto(
                            hang_pictures[stage],
                            # caption=f'{game.apply_mask()}\n\nОшибки: {", ".join(game.errors())}'),
                            caption=f'{game.apply_mask()}\n\nОшибки: {game.errors_str()}'),
                    reply_markup=KeyboardMarkup(game.guessed_letters).get_markup(),
                    )

                    r.set(f'game/{query.inline_message_id}', game.to_json(), ex=3600)

    except TypeError:
        pass


def inline_handler(update, context):
    results = [
        InlineQueryResultCachedPhoto(
            id=uuid.uuid4(),
            photo_file_id='AgACAgIAAxkBAAEEoZZevtW-Ec3CiuCQN-q7-ZKt9mQ5mwACf6wxG7ha-UnsMiYogr0G1zAcuZIuAAMBAAMCAAN4AAM4EAIAARkE',
            caption='Нажми кнопку чтобы начать новую игру ⬇️',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Начать игру!', callback_data='new_game')]])
        )
    ]

    res = update.inline_query.answer(results, cache_time=1, is_personal=True)

    print(f'inline_handler answer result: {res}')


def new_game(update, context):
    query = update.callback_query
    game = Game(choice(dictionary), query.from_user.id)

    print(f'New word: {game.word}')

    context.bot.edit_message_media(
        inline_message_id=query.inline_message_id,
        media=InputMediaPhoto(hang_pictures[0], caption=game.apply_mask()),
        reply_markup=KeyboardMarkup().get_markup(),
    )

    r.set(f'game/{query.inline_message_id}', game.to_json(), ex=3600)


def main():
    bot_token = os.getenv('BOT_TOKEN')
    updater = Updater(bot_token, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(InlineQueryHandler(inline_handler))
    dp.add_handler(CallbackQueryHandler(button))

    dp.add_error_handler(error)

    print('Reading dictionary')
    global dictionary
    with open('dict.txt', 'r') as f:
        dictionary = [w.strip() for w in f.readlines()]

    print('Starting polling')
    updater.start_polling(clean=True)
    updater.idle()


if __name__ == '__main__':
    main()
