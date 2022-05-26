from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from bin.keyboards import finish_keyboard
from bin.payments.banker.banker_params import check_handler
from bin.purchase.register_purchase import register_purchase
from loader import dp


class BankerCheque(StatesGroup):
    cheque = State()


async def input_cheque(message: types.Message, purchase_data):
    await message.answer(f"📱 Вставьте ссылку на чек на сумму <b>{purchase_data['amount']} руб.</b>")
    await BankerCheque.cheque.set()

    state = Dispatcher.get_current().current_state()
    await state.update_data(purchase_data=purchase_data)


@dp.message_handler(state=BankerCheque.cheque)
async def check_cheque(message: types.Message, state: FSMContext):
    try:
        cheque = message.text.split("=")[1]
    except Exception as e:
        await message.answer("❗️ Некорректный чек\nВведите еще раз")
        return

    result = await check_handler(cheque)

    if result == -1:
        await message.answer("😟 Ошибка при проверке чека", reply_markup=finish_keyboard(message.chat.id))
        await state.finish()
        return

    data = await state.get_data()
    purchase_data = data['purchase_data']

    purchase_data['check'] = (float(round(result)) == float(purchase_data['amount']))

    if not purchase_data['check']:
        purchase_data['amount'] = result

    await register_purchase(message, purchase_data)
