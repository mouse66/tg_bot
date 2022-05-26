from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

import database
from bin.keyboards import cancel_keyboard, finish_keyboard, CLOSE_BTN
from bin.strings import get_buy_message
from loader import dp
from src.config import DIR


class PurchaseFind(StatesGroup):
    get_cheque = State()


async def purchase_cheque(message: types.Message):
    """
    Ввод чека покупки

    :param message:
    :return:
    """
    await message.answer("📝 Введите чек о покупке", reply_markup=cancel_keyboard)
    await PurchaseFind.get_cheque.set()


@dp.message_handler(state=PurchaseFind.get_cheque)
async def find_purchase(message: types.Message, state: FSMContext):
    """
    Вывод покупки

    :param message:
    :param state:
    :return:
    """
    cheque = message.text

    purchase_info = database.find_purchase(cheque)

    await state.finish()

    keyboard = finish_keyboard(message.chat.id)
    if purchase_info is None:
        message_text = "❗️ Покупка не найдена ❗️"

        await message.answer(message_text, reply_markup=keyboard)
    else:
        await message.answer("✅ Покупка найдена", reply_markup=keyboard)
        purchase_data = dict()
        purchase_data['user_id'] = purchase_info[1]
        purchase_data['item_name'] = purchase_info[2]
        purchase_data['amount'] = purchase_info[3]
        purchase_data['count'] = purchase_info[4]
        purchase_data['date'] = purchase_info[5]
        purchase_data['cheque'] = purchase_info[6]
        purchase_data['payment_type'] = purchase_info[7]

        message_text = get_buy_message(purchase_data, False)

        items_data = database.get_purchase_items(purchase_info[0])
        item_files = []

        item_size = len(items_data)
        for item in items_data:
            item_data = item[1].split("=")

            if item_data[0] == "text":
                # текстовый товар
                message_text += f"{item_data[1]}\n"
            elif item_data[0] == "file":
                # файловый товар
                item_files.append(item_data[1])

        for i in range(len(item_files)):
            # отправка файловых товаров
            await message.answer_document(item_files[i])

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(CLOSE_BTN)

        if item_size > 10:
            # генерация файла чека с данными
            await message.answer_document(document=open(f"{DIR}/cheques/{cheque}.txt", "rb"),
                                          caption=message_text,
                                          reply_markup=keyboard)
        else:
            await message.answer(message_text, reply_markup=keyboard)
