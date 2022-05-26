from aiogram import Dispatcher, types

import database
from bin.admins import send_admins, send_admins_doc
from bin.payments.payments import check_payment
from bin.strings import get_buy_message, get_cheque_num, get_now_date, get_user_link
from loader import bot
from src import config
from src.config import DIR
from src.const import const_ru


async def register_purchase(message: types.Message, data):
    """
    Регистрация покупки

    :param message:
    :param data:
    :return:
    """
    has_payment = check_payment(data, message.chat.id)

    item_id = data['item_id']
    amount = int(data['amount'])
    count = data['count']

    item_info = database.get_item(item_id)
    user_info = database.get_user(message.chat.id)

    if has_payment:
        # оплата прошла успешно
        state = Dispatcher.get_current().current_state()
        await state.finish()
        await message.delete()

        items_data = database.get_item_data(item_id, count, True)

        # вся инфа о покупке
        purchase_data = dict()
        purchase_data['user_id'] = message.chat.id
        purchase_data['item_name'] = item_info[1]
        purchase_data['amount'] = amount
        purchase_data['count'] = count
        purchase_data['date'] = get_now_date()
        purchase_data['cheque'] = get_cheque_num()
        purchase_data['payment_type'] = const_ru[data['payment']]

        # запись покупки в БД и получение ID
        sale_id = database.add_buy(purchase_data)
        database.add_sold_item_data(sale_id, items_data)
        purchase_data['sale_id'] = sale_id

        user_text = get_buy_message(purchase_data, True)
        admin_text = get_buy_message(purchase_data, False)

        item_text = ""
        item_files = []

        item_size = len(items_data)
        for item in items_data:
            item_data = item[2].split("=", 2)

            if item_data[0] == "text":
                # текстовый товар
                item_text += f"{item_data[1]}\n"
            elif item_data[0] == "file":
                # файловый товар
                item_files.append(item_data[1])

        for i in range(len(item_files)):
            # отправка файловых товаров
            await message.answer_document(item_files[i])
            await send_admins_doc(item_files[i])

        if item_size > 10:
            # генерация файла чека с данными
            await generate_cheque(message, purchase_data['cheque'], item_text, user_text, admin_text)
        else:
            await message.answer(user_text + item_text)
            await send_admins(admin_text + item_text)

        if data['payment'] == "balance":
            user_balance = float(user_info[4]) - amount
            database.set_user_balance(message.chat.id, round(user_balance, 2))

        # обновление информации о пользователе
        database.update_user(message.chat.id, message.chat.username,
                             message.chat.first_name, message.chat.last_name)

        # добавление баланса рефералу
        if user_info[5] != 0:
            percent = float(amount * (float(database.get_param("referral_percent")) / 100))
            balance = database.get_user_balance(user_info[5]) + percent
            database.set_user_balance(user_info[5], round(balance, 2))

            await bot.send_message(user_info[5], f"🧑 Покупка реферала {get_user_link(message.chat.id)}\n\n"
                                                 f"Процент с покупки: <b>{percent} руб.</b>\n"
                                                 f"Текущий баланс: <b>{balance} руб.</b>")
    else:
        # ошибка при оплате
        if data['payment'] == "banker":
            user = database.get_user(message.chat.id)
            user_balance = float(database.get_user_balance(user[0])) + float(amount)
            database.set_user_balance(user[0], round(user_balance, 2))

            await message.answer("❗️ Ошибка при проверке оплаты\n"
                                 "Деньги были зачислены на ваш баланс\n\n"
                                 f"Текущий баланс: <b>{database.get_user_balance(user[0])} руб.</b>")
        elif data['payment'] == "balance":
            await message.answer("❗️ Недостаточно средств на балансе ❗️\n"
                                 "Пополните баланс и попробуйте еще раз")
            await message.delete()
            state = Dispatcher.get_current().current_state()
            await state.finish()
        else:
            await message.answer("❗️ Ошибка при проверке оплаты ❗️\nПроверьте оплату еще раз")


async def generate_cheque(message, cheque, items, user_text, admin_text):
    config.create_folder("cheques")

    with open(f"{DIR}/cheques/{cheque}.txt", "w") as f:
        f.write(items)
        f.close()

    with open(f"{DIR}/cheques/{cheque}.txt", "rb") as f:
        await message.answer_document(document=f, caption=user_text)

    await send_admins(admin_text, document=f"cheques/{cheque}.txt")
