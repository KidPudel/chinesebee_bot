from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.enums import ParseMode
import aiohttp
import asyncio
import logging
import sys

from pydantic import BaseModel, Field
from typing import Annotated, Dict

dp = Dispatcher()

api = "http://localhost:8000"


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
    choice: int | None


class SaveWordCallback(CallbackData, prefix="save"):
    word_to_save: int | None


# endpoint trigger, and below, what it would use (handler)
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Привет! совсем скоро я смогу помогать тебе с освоением иероглифов!!!"
    )


@dp.callback_query(SaveWordCallback.filter(F.word_to_save != None))
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
                await bot.edit_message_text(
                    text="Сохранено в сет на изучение 🌱",
                    chat_id=query.message.chat.id,
                    message_id=query.message.message_id,
                )


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
                        word_to_save=callback_data.choice
                    ).pack(),
                )
                keyboard_builder.button(
                    text="Назад",
                    callback_data=SaveWordCallback(word_to_save=None).pack(),
                )
                await bot.edit_message_text(
                    text=text,
                    chat_id=query.message.chat.id,
                    message_id=query.message.message_id,
                    reply_markup=keyboard_builder.as_markup(),
                )


@dp.message(ChineseMatchLookupState.chinese_match)
async def search_match_handler(message: Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api}/chinese-match/{message.text}") as response:
            chinese_match_result = await response.json()
            print(chinese_match_result)
            if chinese_match_result["success"] == True:
                matches = chinese_match_result["match"]
                keyboard_builder = InlineKeyboardBuilder()
                for match in matches:
                    keyboard_builder.button(
                        text=match["russian"],
                        callback_data=MatchChoiceCallback(choice=match["id"]).pack(),
                    )
                keyboard_builder.adjust(1, repeat=True)
                await message.answer(
                    "Вот что удалось найти 🕵️", reply_markup=keyboard_builder.as_markup()
                )


# MARK: chinese match
# we can allow to through put to the endpoint the data we want, like message, to then answer, or state to set it
@dp.message(Command("chinese_match", prefix="/"))
async def chinese_match_command_handler(message: Message, state: FSMContext):
    print("test")
    await state.set_state(ChineseMatchLookupState.chinese_match)
    await message.answer("Введи слово и я дам тебе варианты и примеры")


# mark: main


async def main():
    bot = Bot(
        token="7063305727:AAFmiV9XfZvD09GUeiX3EY4roTN37WJ_OsU",
        parse_mode=ParseMode.HTML,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main=main())
