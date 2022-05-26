from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import database
from bin import keyboards
from bin.keyboards import finish_keyboard, cancel_keyboard
from bin.strings import get_user_info
from loader import dp
from src.const import const_ru


class UserFinder(StatesGroup):
    get_user = State()


async def get_user_id(message: types.Message):
    """
    Поиск пользователя по нику или id

    :param message:
    :return:
    """
    await message.answer("📝 Введите ID пользователя или ник через @", reply_markup=cancel_keyboard)
    await UserFinder.get_user.set()


@dp.message_handler(state=UserFinder.get_user)
async def user_info(message: types.Message, state: FSMContext):
    """
    Информация о пользователе

    :param message:
    :param state:
    :return:
    """
    username = message.text
    user_data = database.get_user(username)

    keyboard = finish_keyboard(message.chat.id)

    if user_data is None:
        message_text = const_ru["user_not_found"]
    else:
        message_text = get_user_info(user_data)
        await message.answer("✅ Пользователь найден", reply_markup=keyboard)

        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton(text=const_ru['give_balance'],
                                                callback_data=f"give_balance={user_data[0]}"),
                     types.InlineKeyboardButton(text=const_ru['send_message'],
                                                callback_data=f"send_message={user_data[0]}"))
        keyboard.add(keyboards.CLOSE_BTN)

    await state.finish()
    await message.answer(message_text, reply_markup=keyboard)
