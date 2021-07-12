import logging
import os
import uuid
from random import choice
from typing import List, Dict

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InlineQueryResultCachedPhoto
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler
from telegram.error import BadRequest

from game import Game

logging.basicConfig(handlers=[logging.FileHandler('log.txt', 'w', 'utf-8')],
                    level=logging.INFO,
                    format='[*] {%(pathname)s:%(lineno)d} %(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

games: Dict[str, Game] = {}
dictionary: List[str] = []

r = redis.Redis(
    host=os.getenv('BOT_REDIS_HOST'),
    port=os.getenv('BOT_REDIS_PORT') if os.getenv('BOT_REDIS_PORT') else 6379,
    db=os.getenv('BOT_REDIS_DB') if os.getenv('BOT_REDIS_DB') else 0,
)

hang_pictures = {
    0: '',
    1: '',
    2: '',
    3: '',
    4: '',
    5: '',
    6: '',
    7: '',
    8: '',
    9: '',
    10: '',
}

__hang_pictures_fs = {
    0: None,
    1: None,
    2: None,
    3: None,
    4: None,
    5: None,
    6: None,
    7: None,
    8: None,
    9: None,
    10: None,
}

def __upload_pic(stage: int, bot):
    result = bot.send_photo(os.getenv('BOT_SVC_CHAT'), photo=open(__hang_pictures_fs[stage], 'rb'))
    hang_pictures[stage] = result.photo[-1].file_id

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
                    try:
                        context.bot.edit_message_media(
                            inline_message_id=query.inline_message_id,
                            media=InputMediaPhoto(
                                hang_pictures[stage],
                                caption=f'{game.apply_mask()}\n\nОшибки: {game.errors_str()}'),
                        reply_markup=KeyboardMarkup(game.guessed_letters).get_markup(),
                        )
                    except BadRequest as e:
                        __upload_pic(stage, context.bot)
                        context.bot.edit_message_media(
                            inline_message_id=query.inline_message_id,
                            media=InputMediaPhoto(
                                hang_pictures[stage],
                                caption=f'{game.apply_mask()}\n\nОшибки: {game.errors_str()}'),
                        reply_markup=KeyboardMarkup(game.guessed_letters).get_markup(),
                        )

                    r.set(f'game/{query.inline_message_id}', game.to_json(), ex=3600)

    except TypeError:
        pass


def inline_handler(update, context):
    stage = 10

    results = [
        InlineQueryResultCachedPhoto(
            id=uuid.uuid4(),
            photo_file_id=hang_pictures[stage],
            caption='Нажми кнопку чтобы начать новую игру ⬇️',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Начать игру!', callback_data='new_game')]])
        )
    ]

    try:
        res = update.inline_query.answer(results, cache_time=1, is_personal=True)
    except BadRequest as e:
        __upload_pic(stage, context.bot)
        res = update.inline_query.answer(results, cache_time=1, is_personal=True)

    print(f'inline_handler answer result: {res}')


def new_game(update, context):
    query = update.callback_query
    game = Game(choice(dictionary), query.from_user.id)

    print(f'New word: {game.word}')

    try:
        context.bot.edit_message_media(
            inline_message_id=query.inline_message_id,
            media=InputMediaPhoto(hang_pictures[0], caption=game.apply_mask()),
            reply_markup=KeyboardMarkup().get_markup(),
        )
    except BadRequest as e:
        __upload_pic(0, context.bot)
        context.bot.edit_message_media(
            inline_message_id=query.inline_message_id,
            media=InputMediaPhoto(hang_pictures[0], caption=game.apply_mask()),
            reply_markup=KeyboardMarkup().get_markup(),
        )
    except Exception as e:
        print(e)

    r.set(f'game/{query.inline_message_id}', game.to_json(), ex=3600)


def main():
    if not os.getenv('BOT_SVC_CHAT'):
        print('Please provide service chat id (for uploading photos) via BOT_SVC_CHAT env variable')
        return 1

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

    print('Fill assets dict')
    key = lambda i: int(i.split('.')[0])
    assets = sorted(os.listdir('assets'), key=key)
    for asset in assets:
        k = key(asset) - 1
        __hang_pictures_fs[k] = 'assets/' + asset

    print('Starting polling')
    updater.start_polling(drop_pending_updates=True)
    updater.idle()


if __name__ == '__main__':
    main()
