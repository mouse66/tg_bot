import collections
import random
from datetime import datetime

import database
from src.config import COMMENT
from src.const import const_ru


def format_stat(dict_data):
    """
    Форматирование данных для статистики

    :param dict_data: словарь с данными
    :return:
    """
    result = ""
    for key, value in collections.Counter(dict_data).most_common(10):
        result += f"▫ {key} - {value}\n"

    return result


def item_format(item):
    """
    Создание текста для кнопки с товаром

    :param item: объект из БД с товаром
    :return:
    """
    return f"{item[1]} | {item[4]} руб. | {database.get_item_count(item[0])} шт."


def create_comment():
    """
    Генерация комментария для оплаты

    :return:
    """
    key_pass = list("1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm")
    random.shuffle(key_pass)
    key_buy = "".join([random.choice(key_pass) for i in range(10)])

    return f"{COMMENT}:{key_buy}"


def get_now_date():
    """
    Получение текущей даты

    :return:
    """
    now_data = datetime.now()

    return now_data.strftime("%d/%m/%Y %H:%M:%S")


def get_cheque_num():
    """
    Генерация номера чека

    :return:
    """
    key_pass = list("1234567890QWERTYUIOPASDFGHJKLZXCVBNM")
    random.shuffle(key_pass)
    return "#" + "".join([random.choice(key_pass) for i in range(8)])


def get_user_link(user_id):
    """
    Получение ссылка на юзера

    :param user_id: id юзера
    :return:
    """
    user = database.get_user(str(user_id))
    if user is None:
        return ""

    if user[2] is None:
        nickname = user[0]
    else:
        nickname = user[2]

    return f"<a href='tg://user?id={user[0]}'>{nickname}</a>"


def get_user_info(user):
    """
    Получение информации о пользователе

    :param user: данные пользователя
    :return:
    """
    sales_list = database.get_user_buy(user[0])

    user_info = f"🙍‍♂ Пользователь: {get_user_link(user[0])}\n" \
                f"🆔 ID: <b>{user[0]}</b>\n" \
                f"💳 Сумма баланса: <b>{user[4]} руб.</b>\n" \
                f"➖➖➖➖➖➖➖➖➖➖\n" \
                f"🛒 Количество покупок: <b>{len(sales_list)} шт.</b>\n" \
                f"💰 Общая сумма: <b>{sum(row[3] for row in sales_list)} руб.</b>\n" \
                f"➖➖➖➖➖➖➖➖➖➖\n" \
                f"📱 Последние 10 покупок:\n\n"

    sales_list = sales_list[::-1][:10]

    for sale in sales_list:
        user_info += f"▫ {sale[2]} | {sale[4]} шт. | {sale[3]} руб. | {sale[6]}\n"

    return user_info


def get_pay_message(name_buy, payment_form: dict, comment, amount):
    """
    Создание сообщения для оплаты

    :param name_buy: название покупки
    :param payment_form: информация об оплате
    :param comment: комментарий
    :param amount: стоимость оплаты
    :return:
    """
    pay_info = f"💳 Способ оплаты: <b>{payment_form['name']}</b>\n"

    if payment_form['name'] == const_ru['qiwi']:
        pay_info += f"📱 {payment_form['key']}: <b>{payment_form['value']}</b>\n" \
                    f"📋 Комментарий: <b>{comment}</b>\n"

    return f"💳 {name_buy}\n" \
           f"Для оплаты нажмите <b>{const_ru['buy_item']}</b>\n" \
           f"Поля менять <b>не нужно</b>\n" \
           f"{payment_form['warning']}\n" \
           f"После оплаты нажмите <b>{const_ru['check_buy']}</b>\n\n" \
           f"➖➖➖➖➖➖➖➖➖➖\n" \
           f"{pay_info}" \
           f"💵 Сумма оплаты: <b>{amount} руб.</b>\n" \
           f"➖➖➖➖➖➖➖➖➖➖"


def get_buy_message(purchase_data, user_mode):
    """
    Получение сообщения о покупке

    :param user_id: id пользователя
    :param purchase_data: данные о покупке
    :param user_mode: true - режим пользователя, false - админ
    :return:
    """
    if user_mode:
        return "🛒 Информация о покупке\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"🆔 Чек: <b>{purchase_data['cheque']}</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📙 Название товара: <b>{purchase_data['item_name']}</b>\n" \
               f"📦 Количество: <b>{purchase_data['count']} шт.</b>\n" \
               f"💰 Сумма покупки: <b>{purchase_data['amount']} руб.</b>\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📱 Данные:\n\n"
    else:
        return "🛒 Информация о покупке\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"🆔 Чек: <b>{purchase_data['cheque']}</b>\n" \
               f"🙍‍♂ Покупатель: {get_user_link(purchase_data['user_id'])}\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📙 Название товара: <b>{purchase_data['item_name']}</b>\n" \
               f"📦 Количество: <b>{purchase_data['count']} шт</b>\n" \
               f"💰 Сумма покупки: <b>{purchase_data['amount']} руб.</b>\n" \
               f"💳 Способ оплаты: {purchase_data['payment_type']}\n" \
               f"📆 Дата покупки: {purchase_data['date']}\n" \
               f"➖➖➖➖➖➖➖➖➖➖\n" \
               f"📱 Данные:\n\n"
