from aiogram import types

import database
from bin.admins import send_admins
from bin.keyboards import finish_keyboard
from bin.strings import get_user_link
from src.const import const_ru


async def add_balance(message: types.Message, payment_type, amount, state):
    user_id = message.chat.id

    user_balance = float(database.get_user_balance(user_id))
    user_balance += amount

    database.set_user_balance(user_id, user_balance)

    keyboard = finish_keyboard(user_id)
    await message.answer(f"✅ Баланс пополнен\n\nСумма пополнения: <b>{amount} руб.</b>\n"
                         f"Текущий баланс: <b>{user_balance} руб.</b>",
                         reply_markup=keyboard)

    await send_admins(f"💳 Пополнение баланса\n"
                      f"Пользователь: <b>{get_user_link(message.chat.id)}</b>\n"
                      f"Сумма пополнения: <b>{amount} руб.</b>\n"
                      f"Способ пополнения: {const_ru[payment_type]}\n"
                      f"Текущий баланс: <b>{user_balance} руб.</b>")

    await message.delete()
    await state.finish()
