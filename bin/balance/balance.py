import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import StatesGroup, State

from bin.balance.balance_add import add_balance
from bin.keyboards import cancel_keyboard, finish_keyboard, get_payment_keyboard
from bin.payments.banker.banker_cheque import input_cheque
from bin.payments.payments import create_payment_form, check_payment
from bin.strings import create_comment, get_pay_message
from loader import dp, bot
from src.const import is_const, const_ru
from src.throttling import rate_limit


class UserBalance(StatesGroup):
    amount = State()
    payment = State()
    check = State()


async def amount_balance(message: types.Message):
    await message.answer("Введите сумму пополнения баланса\n\n"
                         "Минимальная сумма: <b>1 руб.</b>\n"
                         "Максимальная сумма: <b>15000 руб.</b> ",
                         reply_markup=cancel_keyboard)
    await UserBalance.amount.set()


@dp.message_handler(state=UserBalance.amount)
async def payment_balance(message: types.Message, state: FSMContext):
    amount = message.text
    if is_const(amount) or not amount.isdigit():
        await message.answer(const_ru['invalid_value'])
        return

    amount = int(amount)
    if 1 > amount > 15000:
        await message.answer(const_ru['invalid_value'])
        return

    await state.update_data(amount=int(amount))

    keyboard = get_payment_keyboard()
    length = len(json.loads(keyboard.as_json())["inline_keyboard"])

    if length > 0:
        await message.answer("💳 Выберите способ пополнения баланса", reply_markup=keyboard)
        await UserBalance.next()
    else:
        await message.answer("😔 К сожалению, оплата в данный момент не работает",
                             reply_markup=finish_keyboard(message.chat.id))
        await state.finish()


@dp.callback_query_handler(Regexp("payment"), state=UserBalance.payment)
async def payment(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()

    call_data = call.data.split("=")

    await state.update_data(payment=call_data[1])
    await create_payment(call.message, state)


async def create_payment(message: types.Message, state: FSMContext):
    """
    Создание оплаты

    :param message:
    :param state:
    :return:
    """
    data = await state.get_data()

    payment_type = data['payment']
    comment = create_comment()
    amount = data['amount']

    payment_form = create_payment_form(payment_type, amount, comment)
    message_text = get_pay_message(f"Пополнение баланса", payment_form, comment, amount)

    keyboard = types.InlineKeyboardMarkup()
    if len(payment_form) > 0:
        keyboard.row(types.InlineKeyboardButton(text=const_ru['buy_item'], url=payment_form['link']),
                     types.InlineKeyboardButton(text=const_ru['check_buy'], callback_data="check_pay"))
    else:
        callback = ""
        if payment_type == "banker":
            callback = f"get_cheque={amount}"
        elif payment_type == "balance":
            callback = "check_buy"
        keyboard.row(types.InlineKeyboardButton(text=const_ru['buy_item'], callback_data=callback))

    keyboard.row(types.InlineKeyboardButton(text=const_ru['cancel_buy'], callback_data="cancel_pay"))

    await message.answer(message_text, reply_markup=keyboard)
    await state.update_data(comment=comment)
    await UserBalance.next()


@dp.callback_query_handler(Regexp("get_cheque"), state=UserBalance.check)
async def get_cheque(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()

    call_data = call.data.split("=")
    await input_cheque(call.message, call_data[1])


@dp.callback_query_handler(Regexp("check_pay"), state=UserBalance.check)
@rate_limit(5, "check_pay")
async def check_pay(call: types.CallbackQuery, state: FSMContext):
    """
    Проверка оплаты

    :param call:
    :param state:
    :return:
    """
    data = await state.get_data()

    has_payment = check_payment(data, call.message.chat.id)

    amount = float(data['amount'])
    payment_type = data['payment']

    if has_payment:
        await add_balance(call.message, payment_type, amount, state)
    else:
        # ошибка при оплате
        await bot.answer_callback_query(callback_query_id=call.id, show_alert=True,
                                        text="❗️ Пополнение не найдено ❗️\n Попробуйте еще раз")


@dp.callback_query_handler(Regexp("cancel_pay"), state=UserBalance.check)
async def cancel_pay(call: types.CallbackQuery, state: FSMContext):
    """
    Отмена оплаты

    :param call:
    :param state:
    :return:
    """
    await call.message.delete()
    await state.finish()
    await call.message.answer("Отмена пополнения", reply_markup=finish_keyboard(call.message.chat.id))
