from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
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



basics_info = [
    "Тональная система\nКитайский язык является тональным, что означает, что смысл слова может изменяться в зависимости от тона, в котором оно произнесено. В мандаринском языке четыре основных тона:\n1. Первый тон: высокий и ровный (妈 mā - мама).\n2. Второй тон: восходящий (麻 má - конопля).\n3. Третий тон: низкий, падающий и поднимающийся (马 mǎ - лошадь).\n4. Четвертый тон: падающий (骂 mà - ругать).",
    "Письменность\nИероглифы: Китайская письменность состоит из иероглифов, каждый из которых представляет собой слово или морфему. Иероглифы могут состоять из одного или более ключей (радикалов) и фонетических компонентов.\nПиньинь: Это фонетическая система записи китайского языка латинскими буквами. Она используется для обучения правильному произношению и является основным инструментом для начального изучения языка. Например, слово '你好' (привет) записывается как 'nǐ hǎo'.",
    "Грамматика\nГрамматика китайского языка отличается от грамматики европейских языков. Вот несколько ключевых моментов:\n- Отсутствие склонений и спряжений: В китайском языке нет изменений слов в зависимости от падежей или времён. Например, глагол не изменяется по лицам и числам (я говорю, ты говоришь, он говорит — всё это '说' (shuō)).\n- Порядок слов: Обычно используется структура подлежащее + сказуемое + дополнение (SVO).  Например: 我爱你 (Wǒ ài nǐ) — 'Я люблю тебя'.\n- Использование счётных слов: Для разных типов предметов используются разные счётные слова. \nНапример, 一个人 (yī gè rén) — 'один человек', 一本书 (yī běn shū) — 'одна книга'.",
    "Культурные аспекты\nИзучение китайского языка тесно связано с культурой Китая. Понимание культурных контекстов и традиций важно для правильного использования языка и эффективного общения. Например:\n- Обращения и вежливость: Уважительное отношение и правильное использование обращений к старшим и начальству очень важны.\n- Праздники: Знание основных китайских праздников, таких как Китайский Новый год и Праздник середины осени, поможет лучше понять культурные особенности и традиции.",
    ("Графемы:\nЧерты объединяются в графемы. Графема - это устойчивые комбинации черт внутри иероглифов. \nКлючи:\nКлючи (ключевые графемы) это тематический классификатор иероглифов, по которым иероглифы упорядочены в словарях. Когда\nне было электронных словарей, в бумажных словарях искали иероглифы именно по этим ключам. Их тематически разделили и можно было легко найти любой иероглиф с помощью этого ключа.", "./assets/keys.png"),
    ("Фонетики - В иероглифах так же часто присутствуют фонетики. Они\nподсказывают произношение иероглифа (его слог), но не тон. \nИероглиф состоит из черт, графем и ключей. Ключ в иероглифе может быть один, а графем может быть очень несколько. Так же в иероглифе часто присутствует фонетик, который подсказывает как читать иероглиф.", "./assets/phonetics.png"),
    ("Существует ряд правил. Вначале, конечно, сложно запомнить порядок\nнаписания, но через пару месяцев активной практики вы уже будете\nинтуитивно знать как пишется любой даже не знакомый вам иероглиф.\n1. Иероглиф пишется сверху вниз.\n2. Иероглиф пишется слева направо.\n3. Сначала пишутся горизонтальные черты, потом вертикальные и откидные. Нижняя горизонтальная черта, если она не пересекается, пишется после вертикальной.\n4. Сначала пишется откидная влево, затем откидная вправо.\n5. Сначала пишутся черты, составляющие внешний контур знака, затем черты внутри него, черта, замыкающая контур внизу пишется в последнюю очередь.\n6. Сначала пишется вертикальная, находящаяся в центре, если она не пересекается горизонтальной, затем боковые черты.\n7. Точка справа пишется в последнюю очередь.", "./assets/parts.png"),
]

facts = [
    "Древность иероглифов: Китайские иероглифы являются одной из самых древних систем письма в мире. Первые письменные знаки были найдены на гадательных костях и датируются примерно 1600 годом до нашей эры, временами династии Шан.",
    "Количество иероглифов: В китайском языке существует более 50 000 иероглифов, хотя для повседневного общения и чтения достаточно знать около 3 000-4 000. Для понимания новостных статей и другой литературы на китайском языке нужно знать примерно 2 000-3 000 иероглифов.",
    "Иероглифы и значения: В китайском языке многие иероглифы имеют множественные значения и произношения. Например, иероглиф '行' может означать 'идти' (xíng) или 'линия' (háng).",
    "Каллиграфия: Китайская каллиграфия считается одним из самых уважаемых видов искусства в Китае. Каждый иероглиф должен быть написан с правильным порядком черт, что делает написание китайских иероглифов не только техническим навыком, но и искусством.",
    "Эволюция иероглифов: Иероглифы постоянно эволюционировали. Существует несколько стилей китайского письма, таких как древнее гадательное письмо, малое и большое печатное письмо, скоропись и регулярное письмо, каждый из которых использовался в разные эпохи китайской истории.",
    "Символы счастья и удачи: Многие китайские иероглифы имеют символическое значение. Например, иероглиф '福' (fú) означае т 'счастье' или 'удача' и часто используется в новогодних украшениях и талисманах.",
    "Письменные реформы: В 1950-х годах правительство Китая провело реформу упрощения иероглифов с целью повысить грамотность населения. В результате были созданы упрощенные иероглифы, которые используются в материковом Китае и Сингапуре, в то время как традиционные иероглифы продолжают использоваться в Гонконге, Макао и Тайване.",
    "Рекордное количество черт: Иероглиф 'biáng' (biang), используемый в названии бианбианских лапши из провинции Шэньси, считается одним из самых сложных китайских иероглифов, состоящим из 58 черт."
]


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
    start_notebook: bool | None = None


class NotebookCallback(CallbackData, prefix="notebook"):
    open_main: bool | None = None
    open_guide: bool | None = None
    open_page: bool | None = None


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

class LearnBasicsCallback(CallbackData, prefix="basics"):
    learn: int


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
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Да, хочу!", callback_data=LearnBasicsCallback(learn=0).pack())
    keyboard.button(text="Уже знаю", callback_data=LearnBasicsCallback(learn=-1).pack())
    await message.answer(f"Привет, {message.from_user.first_name}! Как насчет улучшить свой китайский?\nПрежде чем начать, хочешь узнать о том как устроeны иероглифы?", reply_markup=keyboard.as_markup())


@dp.callback_query(LearnBasicsCallback.filter(F.learn == -1))
async def already_know_basics_hander(query: CallbackQuery, callback_data: LearnBasicsCallback, bot: Bot):
    if query.message.photo != None:
        await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
        await bot.send_message(text="Хорошо, для начала, чтобы найти слова используй комманду /chinese_match\nЧтобы посмотреть свои сохраненные слова, просто используй /saved_words", chat_id=query.message.chat.id)
    else:
        await bot.edit_message_text(text="Хорошо, для начала, чтобы найти слова используй комманду /chinese_match\nЧтобы посмотреть свои сохраненные слова, просто используй /saved_words", chat_id=query.message.chat.id, message_id=query.message.message_id)


# to remove repeating functions
@dp.callback_query(LearnBasicsCallback.filter(F.learn >= 0))
async def learn_basics_handler(query: CallbackQuery, callback_data: LearnBasicsCallback, bot: Bot):
    keyboard = InlineKeyboardBuilder()
    if callback_data.learn == len(basics_info) - 1:
        keyboard.button(text="Продолжить", callback_data=LearnBasicsCallback(learn=-1).pack())
    else:   
        keyboard.button(text="Далее", callback_data=LearnBasicsCallback(learn=callback_data.learn + 1).pack())
        if callback_data.learn > 0:
            keyboard.button(text="Назад", callback_data=LearnBasicsCallback(learn=callback_data.learn - 1).pack())
    
    if type(basics_info[callback_data.learn]) == str:
        if query.message.photo != None:
            await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
            await bot.send_message(text=basics_info[callback_data.learn], chat_id=query.message.chat.id, reply_markup=keyboard.as_markup())
        else:
            await bot.edit_message_text(text=basics_info[callback_data.learn], chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=keyboard.as_markup())
    else:
        await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
        await bot.send_photo(photo=FSInputFile(basics_info[callback_data.learn][1]), caption=basics_info[callback_data.learn][0], chat_id=query.message.chat.id, reply_markup=keyboard.as_markup())


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
    if query.message.photo != None:
        await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
        await bot.send_message(text="Могу ли я помочь чем нибудь ещё? Посмотри комманды", chat_id=query.message.chat.id)
    else:
        await bot.edit_message_text(text="Могу ли я помочь чем нибудь ещё? Посмотри комманды", chat_id=query.message.chat.id, message_id=query.message.message_id)


# MARK: saved words and notebook


@dp.callback_query(NotebookCallback.filter(F.open_page == True))
async def open_page_handler(query: CallbackQuery, bot: Bot):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Продолжить", callback_data=ClearCallback(clear=True).pack())
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await bot.send_photo(caption="Твой лист заполнения", photo=FSInputFile("./assets/blank_form.png"), chat_id=query.message.chat.id, reply_markup=keyboard.as_markup())


@dp.callback_query(NotebookCallback.filter(F.open_guide == True))
async def open_guide_handler(query: CallbackQuery, bot: Bot):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Продолжить", callback_data=ClearCallback(clear=True).pack())
    await bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
    await bot.send_media_group(media=[InputMediaPhoto(media=FSInputFile("./assets/similar.png"), caption="Правила работы:\n1. Запомните иероглиф и определите его структуру, разделив на графемы и записав их порядок.\n2. Запишите произношение и значение, а также пиньинь. Повторите произношение с правильным тоном.\n3. Запишите порядок черт иероглифа и сверьте его с онлайн-словарем. При необходимости разбейте иероглиф на части.\n4. Укажите визуально и фонетически похожие иероглифы и запишите их отличия.\n5. Придумайте мнемонику – слово-ассоциацию для запоминания.\n6. Запишите несколько примеров – фраз или предложений.\n7. Пропишите иероглиф в графе «Практика письма» и напишите с ним несколько примеров."),InputMediaPhoto(media=FSInputFile("./assets/structure.png")),InputMediaPhoto(media=FSInputFile("./assets/filled.png"))], chat_id=query.message.chat.id)


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
                keyboard_builder.button(text="📘 Открыть лист тетради", callback_data=NotebookCallback(open_page=True).pack())
                keyboard_builder.button(text="🤔 Как пользоваться тетрадью?", callback_data=NotebookCallback(open_guide=True).pack())
                keyboard_builder.button(text="🗑️ Удалить", callback_data=SavedInfoCallback(saved_id=callback_data.saved_id).pack())
                keyboard_builder.button(text="🔙 Назад", callback_data=SavedInfoCallback(back=True).pack())
                keyboard_builder.adjust(1, repeat=True)
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

# MARK: facts

@dp.message(Command("fact", prefix="/"))
async def fact_handler(message: Message):
    await message.answer(text=facts[random.randint(0, len(facts)-1)])


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
