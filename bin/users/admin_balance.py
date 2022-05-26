from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import database
from bin.keyboards import finish_keyboard
from loader import dp, bot


class AdminBalance(StatesGroup):
    balance = State()


async def input_balance(message: types.Message, user_id):
    await message.answer("💵 Введите сумму для пополнения")
    await AdminBalance.balance.set()

    state = Dispatcher.get_current().current_state()
    await state.update_data(user_id=user_id)


@dp.message_handler(state=AdminBalance.balance)
async def add_balance(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️ Некорректное значение")
        return

    amount = int(message.text)
    data = await state.get_data()

    user = database.get_user(data['user_id'])

    user_balance = int(database.get_user_balance(user[0])) + amount
    database.set_user_balance(user[0], user_balance)

    await bot.send_message(user[0],
                           "✅ Зачисление баланса\n\n"
                           f"Сумма пополнения: <b>{amount} руб.</b>\n"
                           f"Текущий баланс: <b>{user_balance} руб.</b>")

    await message.answer("✅ Баланс зачислен\n\n", reply_markup=finish_keyboard(message.chat.id))
    await state.finish()
