from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

import database
from bin import keyboards
from bin.admins import send_admins
from bin.keyboards import user_keyboard, admin_keyboard, create_list_keyboard
from bin.states import BotStates
from bin.strings import get_user_link, get_user_info
from bin.support.support_user import select_type
from loader import dp, bot
from src import config
from src.config import is_admin
from src.const import *


# # # Запуск магазина # # #

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """
    Стартовое сообщение

    :param message:
    :return:
    """
    inviting = 0

    ref_id = -1
    if " " in message.text:
        # реферальная ссылка
        ref_id = message.text.split()[1]

        if ref_id.isdigit() and str(message.chat.id) != ref_id:
            ref_user = database.get_user(str(ref_id))
            if ref_user is not None:
                inviting = ref_id

    added_user = database.add_user(message.chat.id, message.chat.username,
                                   message.chat.first_name, message.chat.last_name, inviting)

    if inviting != 0:
        await bot.send_message(ref_id, f"🧑 Пользователь {get_user_link(message.chat.id)} "
                                       f"зарегестрировался по вашей реферальной ссылке")

    if config.is_admin(message.chat.id):
        keyboard = admin_keyboard
    else:
        keyboard = user_keyboard

    if added_user:
        # новый юзер
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row(const_ru['accept_rules'])

        message_text = database.get_param("rules")
        await BotStates.new_user.set()
    else:
        # уже смешарик
        message_text = database.get_param("comeback_message").format(username=message.chat.username)

    await message.answer(message_text, reply_markup=keyboard)


@dp.message_handler(commands='cancel')
@dp.message_handler(Text(equals='Отмена', ignore_case=True))
async def cancel_state(message: types.Message):
    """
    Отмена текущего состояния

    :param message:
    :return:
    """
    if config.is_admin(message.chat.id):
        keyboard = admin_keyboard
    else:
        keyboard = user_keyboard

    await message.answer(f"Отмена действия", reply_markup=keyboard)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='Отмена', ignore_case=True), state='*')
async def cancel_state(message: types.Message, state: FSMContext):
    """
    Отмена текущего состояния

    :param message:
    :param state:
    :return:
    """
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()

    if config.is_admin(message.chat.id):
        keyboard = admin_keyboard
    else:
        keyboard = user_keyboard

    await message.answer(f"Отмена действия", reply_markup=keyboard)


@dp.message_handler(regexp=const_ru['accept_rules'], state=BotStates.new_user)
async def hello_message(message: types.Message, state: FSMContext):
    """
    Вызов приветствия при первом запуске

    :param state:
    :param message:
    :return:
    """
    if config.is_admin(message.chat.id):
        keyboard = admin_keyboard
    else:
        keyboard = user_keyboard
    message_text = database.get_param("hello_message")

    admin_text = "📱 Новый пользователь\n" \
                 f"➖➖➖➖➖➖➖➖➖➖\n" \
                 f"🙍‍♂ Имя: {get_user_link(message.chat.id)}\n" \
                 f"🆔 ID: {message.chat.id}\n"

    await send_admins(admin_text)
    await message.answer(message_text.format(username=message.chat.username), reply_markup=keyboard)
    await state.finish()


# # # Покупки # # #

@dp.message_handler(regexp=const_ru["shop"])
async def shop_message(message: types.Message):
    """
    Вывод категорий для покупки товара

    :param message:
    :return:
    """
    keyboard = keyboards.create_category_keyboard("select_category")
    length = len(json.loads(keyboard.as_json())["inline_keyboard"])

    message_text = "📂 Все доступные категории"
    if length == 0:
        message_text = const_ru["nothing"]

    keyboard.add(keyboards.CLOSE_BTN)

    await message.answer(message_text, reply_markup=keyboard)


# # # О магазине # # #

@dp.message_handler(regexp=const_ru["faq"])
async def faq(message: types.Message):
    """
    FAQ магазина

    :param message:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()

    if is_admin(message.chat.id):
        keyboard.add(types.InlineKeyboardButton(text=const_ru["edit"], callback_data="edit_faq"))

    await message.answer(database.get_param("faq"), reply_markup=keyboard)


@dp.message_handler(regexp=const_ru["rules"])
async def rules(message: types.Message):
    """
    Правила магазина

    :param message:
    :return:
    """
    keyboard = types.InlineKeyboardMarkup()

    if is_admin(message.chat.id):
        keyboard.add(types.InlineKeyboardButton(text=const_ru["edit"], callback_data="edit_rules"))

    await message.answer(database.get_param("rules"), reply_markup=keyboard)


# # # Профиль # # #

@dp.message_handler(regexp=const_ru["profile"])
async def profile(message: types.Message):
    """
    Профиль пользователя

    :param message:
    :return:
    """
    user_data = database.get_user(str(message.chat.id))

    message_text = get_user_info(user_data)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text=const_ru['add_balance'], callback_data="add_balance"))
    # keyboard.add(types.InlineKeyboardButton(text=const_ru['referral_program'],
    #                                         callback_data="referral_program"))
    keyboard.add(keyboards.CLOSE_BTN)
    await message.answer(message_text, reply_markup=keyboard)


# # # Поддержка # # #

@dp.message_handler(regexp=const_ru["support"])
async def support(message: types.Message):
    """
    Поддержка

    :param message:
    :return:
    """
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if config.is_admin(message.chat.id):
        # админ панель
        keyboard.row(const_ru["active_support"], const_ru["close_support"])
    else:
        # юзер панель
        keyboard.row(const_ru["new_support"], const_ru["my_support"])

    keyboard.row(const_ru["back"])
    await message.answer(const_ru["support"], reply_markup=keyboard)


@dp.message_handler(regexp=const_ru["new_support"])
async def new_support(message: types.Message):
    """
    Новое обращение

    :param message:
    :return:
    """
    await select_type(message)


@dp.message_handler(regexp=const_ru["my_support"])
async def my_support(message: types.Message):
    """
    Мои обращения

    :param message:
    :return:
    """
    keyboard = create_list_keyboard(data=database.get_user_supports(message.chat.id),
                                    last_index=0,
                                    page_click=f"get_user_supports={message.chat.id}",
                                    btn_text_param="user_support",
                                    btn_click="get_user_support")
    await message.answer(const_ru["my_support"], reply_markup=keyboard)
