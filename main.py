from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.types.web_app_info import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
import aiohttp
import asyncio
import logging
import sys
import random
import os

from pydantic import BaseModel, Field
from typing import Annotated, Dict

dp = Dispatcher()

api = "https://chinesebeeapi-production.up.railway.app"


class ChineseMatchLookupState(StatesGroup):
    chinese_match = State()
    suggestion_details = State()


class ChineseMatch(BaseModel):
    chinese: str
    pinyin: str
    english: str
    russian: str
    level: Annotated[int, Field(alias="hsk_level")]


class MatchChoiceCallback(CallbackData, prefix="match"):
    choice: int | None = None
    searched_word: str | None = None
    
class SavedInfoCallback(CallbackData, prefix="saved"):
    saved_id: int | None = None
    word_to_see: int | None = None
    back: bool | None = None


class SaveWordCallback(CallbackData, prefix="save"):
    word_to_save: int | None = None
    searched_word: str | None = None
    should_continue: bool | None = None
    
class ClearCallback(CallbackData, prefix="clear"):
    clear: bool

class FlashCardsCallback(CallbackData, prefix="flash_cards"):
    training: bool
    current: int
    previous_question: str | None = None
    previous_answer: str | None = None


async def find_chinese_matches(word: str, bot: Bot, chat_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api}/chinese-match/{word}") as response:
            chinese_match_result = await response.json()
            print(chinese_match_result)
            if chinese_match_result["success"] == True:
                matches = chinese_match_result["match"]
                keyboard_builder = InlineKeyboardBuilder()
                for match in matches:
                    keyboard_builder.button(
                        text=f"{match["chinese"]} - {match["russian"]}",
                        callback_data=MatchChoiceCallback(choice=match["id"], searched_word=word).pack(),
                    )
                keyboard_builder.button(text="🔙 Назад", callback_data=MatchChoiceCallback(choice=None, searched_word=word).pack())
                keyboard_builder.adjust(1, repeat=True)
                await bot.send_message(
                    text="Вот что удалось найти 🕵️", reply_markup=keyboard_builder.as_markup(), chat_id=chat_id
                )


async def find_saved_words(bot: Bot, user_id: int, chat_id: int, message_id: int | None = None):
       async with aiohttp.ClientSession() as session:
        async with session.get(f"{api}/saved-words?user_id={user_id}") as response:
            response_body = await response.json()
            if response_body["success"] == True:
                keyboard_builder = InlineKeyboardBuilder()
                if not response_body["saved_words"]:
                    await bot.send_message(text="Пока нет сохраненных слов :(\nИспользуй /chinese_match, чтобы найти слова", chat_id=chat_id)
                else:
                    for saved_word in response_body["saved_words"]:
                        keyboard_builder.button(text=f"{saved_word["chinese"]} - {saved_word["russian"]}", callback_data=SavedInfoCallback(saved_id=saved_word["saved_id"], word_to_see=saved_word["word_id"]).pack())
                    keyboard_builder.adjust(1, True)
                    # when returning back, we can edit message
                    if message_id:
                        await bot.edit_message_text(text="Твои сохраненные слова для изучения 🌻", reply_markup=keyboard_builder.as_markup(), chat_id=chat_id, message_id=message_id)
                    else:
                        await bot.send_message(text="Твои сохраненные слова для изучения 🌻", reply_markup=keyboard_builder.as_markup(), chat_id=chat_id)


# endpoint trigger, and below, what it would use (handler)
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Как насчет улучшить свой китайский?\nДля начала, чтобы найти слова используй комманду /chinese_match\nЧтобы посмотреть свои сохраненные слова, просто используй /saved_words"
    )

# MARK: dictation
@dp.message(Command("dictation", prefix="/"))
async def dictation_handler(message: Message):
    web_app = WebAppInfo(url=f"https://chinese-bee-dictation-production.up.railway.app/?user_id={message.from_user.id}")
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Открыть прописи", web_app=web_app)
    await message.answer(text="Начать практиковаться в правописании?", reply_markup=keyboard.as_markup())
    

# MARK: flash cards
@dp.callback_query(FlashCardsCallback.filter(F.training == False))
async def flash_cards_end_handler(query: CallbackQuery, callback_data: FlashCardsCallback, bot: Bot):
    await bot.edit_message_text(text="Спасибо, что уделил время на взращивание своих слов!", chat_id=query.message.chat.id, message_id=query.message.message_id)

@dp.callback_query(FlashCardsCallback.filter(F.training == True))
async def flash_cards_train_handler(query: CallbackQuery, callback_data: FlashCardsCallback, bot: Bot):
    if callback_data.previous_question != None and callback_data.previous_question == callback_data.previous_answer:
        await query.answer(f"{callback_data.previous_answer} Правильно! 🐝")
    elif callback_data.previous_question != None and callback_data.previous_question != callback_data.previous_answer:
        await query.answer(f"Правильный ответ - {callback_data.previous_question}")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api}/saved-words?user_id={query.from_user.id}") as response:
            response_body = await response.json()
            if response_body["success"] == True:
                print(query.message.from_user.id)
                print(query.from_user.id)
                print(response_body)
                saved_words = response_body["saved_words"]
                print(len(saved_words))
                print(callback_data.current)
                question_word = saved_words[callback_data.current]
                random.shuffle(saved_words)
                keyboard = InlineKeyboardBuilder()
                for shuffled_word in saved_words:
                    keyboard.button(text=shuffled_word["russian"], callback_data=FlashCardsCallback(training=True if callback_data.current+1 < len(saved_words) else False, current=callback_data.current+1, previous_question=question_word["chinese"], previous_answer=shuffled_word["chinese"]))
                keyboard.adjust(1, True)
                await bot.edit_message_text(text=question_word["chinese"], reply_markup=keyboard.as_markup(), chat_id=query.message.chat.id, message_id=query.message.message_id)
                


@dp.message(Command("flash_cards", prefix="/"))
async def flash_cards_handler(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api}/can-train?user_id={message.from_user.id}") as response:
            response_body = await response.json()
            if response_body["success"]:
                if response_body["can_learn"] == False:
                    await message.answer(response_body["msg"])
                else:
                    keyboard = InlineKeyboardBuilder()
                    keyboard.button(text="Начать", callback_data=FlashCardsCallback(training=True, current=0, previous_question=None, previous_answer=None).pack())
                    keyboard.button(text="Назад", callback_data=ClearCallback(clear=True).pack())
                    await message.answer("Хочешь потренироваться в запоминании иероглифов?", reply_markup=keyboard.as_markup())
            else:
                await message.answer(text=response_body)


@dp.callback_query(ClearCallback.filter(F.clear == True))
async def clear_state_handler(query: CallbackQuery, bot: Bot, state: FSMContext):
    await state.clear()
    await bot.edit_message_text(text="Могу ли я помочь чем нибудь ещё? Посмотри комманды", chat_id=query.message.chat.id, message_id=query.message.message_id)
    


# MARK: saved words

@dp.callback_query(SavedInfoCallback.filter(F.back == True))
async def back_to_saved(query: CallbackQuery, callback_data: SavedInfoCallback, bot: Bot):
    await find_saved_words(bot=bot, user_id=query.from_user.id, chat_id=query.message.chat.id, message_id=query.message.message_id)


@dp.callback_query(SavedInfoCallback.filter((F.saved_id != None) & (F.word_to_see == None)))
async def delete_saved_handler(query: CallbackQuery, callback_data: SavedInfoCallback, bot: Bot, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{api}/saved_word?saved_id={callback_data.saved_id}") as response:
            response_body = await response.json()
            if response_body["success"] == True:
                await state.clear()
                await bot.edit_message_text(text="Удаление прошло успешно", chat_id=query.message.chat.id, message_id=query.message.message_id)

@dp.callback_query(SavedInfoCallback.filter((F.word_to_see != None) & (F.saved_id != None)))
async def see_saved_word_handler(query: CallbackQuery, callback_data: SavedInfoCallback, bot: Bot):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api}/word-details/{callback_data.word_to_see}") as response:
            response_body = await response.json()
            if response_body["success"] == True:
                keyboard_builder = InlineKeyboardBuilder()
                keyboard_builder.button(text="🗑️ Удалить", callback_data=SavedInfoCallback(saved_id=callback_data.saved_id).pack())
                keyboard_builder.button(text="🔙 Назад", callback_data=SavedInfoCallback(back=True).pack())
                await bot.edit_message_text(text="\n".join([f"{key}: {value}" for key, value in response_body["details"].items()]), reply_markup=keyboard_builder.as_markup(), chat_id=query.message.chat.id, message_id=query.message.message_id)
            else:
                print(response_body)


@dp.message(Command("saved_words", prefix="/"))
async def get_saved_words_handler(message: Message, bot: Bot):
    await find_saved_words(bot=bot, user_id=message.from_user.id, chat_id=message.chat.id)


@dp.callback_query(SaveWordCallback.filter((F.word_to_save == None) & (F.searched_word != None)))
async def return_to_picking_handler(query: CallbackQuery, callback_data: SaveWordCallback, bot: Bot):
    await find_chinese_matches(word=callback_data.searched_word, bot=bot, chat_id=query.message.chat.id)


@dp.callback_query(SaveWordCallback.filter(F.should_continue==True))
async def continue_handler(query: CallbackQuery, callback_data: SaveWordCallback, bot: Bot):
    await bot.edit_message_text(text="Введи слово, которое ты ищешь 🔎", chat_id=query.message.chat.id, message_id=query.message.message_id)




@dp.callback_query(SaveWordCallback.filter((F.word_to_save != None) & (F.searched_word != None)))
async def save_word_handler(
    query: CallbackQuery, callback_data: SaveWordCallback, bot: Bot
):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{api}/new-word",
            data={"user_id": query.from_user.id, "word_id": callback_data.word_to_save},
        ) as response:
            response_body = await response.json()
            if response_body["success"] == True:
                keyboard_builder = InlineKeyboardBuilder()
                keyboard_builder.button(text="Продолжить", callback_data=SaveWordCallback(should_continue=True).pack())
                keyboard_builder.button(text="Назад", callback_data=SaveWordCallback(word_to_save=None, searched_word=callback_data.searched_word).pack())
                await bot.edit_message_text(
                    text="Сохранено в сет на изучение 🌱",
                    chat_id=query.message.chat.id,
                    message_id=query.message.message_id,
                    reply_markup=keyboard_builder.as_markup()
                )

# MARK: search words

@dp.callback_query(MatchChoiceCallback.filter(F.choice == None))
async def regect_choices_handler(query: CallbackQuery, bot: Bot):
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="🛑 Закончить", callback_data=ClearCallback(clear=True).pack())
    await bot.edit_message_text(text="Чтобы найти другое слово, просто напиши его как обычно ⌨️\nЕсли ты хочешь закончить искать слова, просто нажми '🛑 Закончить'", reply_markup=keyboard_builder.as_markup(), chat_id=query.message.chat.id, message_id=query.message.message_id)


@dp.callback_query(MatchChoiceCallback.filter(F.choice != None))
async def show_details_handler(
    query: CallbackQuery, callback_data: MatchChoiceCallback, bot: Bot
):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{api}/word-details/{callback_data.choice}"
        ) as response:
            response_body = await response.json()
            if response_body["success"] == True:
                details: Dict = response_body["details"]
                text = "\n".join([f"{key}: {value}" for key, value in details.items()])
                keyboard_builder = InlineKeyboardBuilder()
                keyboard_builder.button(
                    text="Сохранить",
                    callback_data=SaveWordCallback(
                        word_to_save=callback_data.choice,
                        searched_word=callback_data.searched_word
                    ).pack(),
                )
                keyboard_builder.button(
                    text="🔙 Назад",
                    callback_data=SaveWordCallback(word_to_save=None, searched_word=callback_data.searched_word).pack(),
                )
                await bot.edit_message_text(
                    text=text,
                    chat_id=query.message.chat.id,
                    message_id=query.message.message_id,
                    reply_markup=keyboard_builder.as_markup(),
                )


# MARK: chinese match
# we can allow to through put to the endpoint the data we want, like message, to then answer, or state to set it
@dp.message(Command("chinese_match", prefix="/"))
async def chinese_match_command_handler(message: Message, state: FSMContext):
    print("test")
    await state.set_state(ChineseMatchLookupState.chinese_match)
    await message.answer("Введи слово, которое ты ищешь 🔎")

@dp.message(ChineseMatchLookupState.chinese_match)
async def search_match_handler(message: Message, bot: Bot):
    await find_chinese_matches(word=message.text, bot=bot, chat_id=message.chat.id)



# mark: main


async def main():
    bot = Bot(token=os.environ.get("TG_KEY"))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main=main())
