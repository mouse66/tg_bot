import database
from bin.payments.qiwi.qiwi_params import create_qiwi_link, check_qiwi_payment
from bin.payments.yoo_money.yoo_money_params import create_yoomoney_link, check_yoomoney_payment
from src.const import const_ru


def create_payment_form(payment_type, amount, comment):
    """
    Создание оплаты

    :param payment_type:
    :param amount:
    :param comment:
    :return:
    """
    payment_form = dict()

    if payment_type == "qiwi":
        payment_form = create_qiwi_link(amount, comment)
        payment_form[
            'warning'] = "❗️ При оплате через никнейм <b>указывайте комментарий самостоятельно и в ПЕРВОЕ ПОЛЕ</b>, " \
                         "иначе вы НЕ ПОЛУЧИТЕ ПОКУПКУ\n" \
                         "При оплате через номер телефона ничего указывать <b>не нужно</b>. Всё сделано автоматически " \
                         "❗️\n "
    elif payment_type == "yoomoney":
        payment_form = create_yoomoney_link(amount, comment)
        payment_form[
            'warning'] = "❗️ Для оплаты <b>необходимо перейти по ссылке, где все данные указаны автоматически</b>️\n" \
                         "Вам необходимо только нажать <b>Оплатить</b> ❗️\n"
    elif payment_type == "banker":
        payment_form['name'] = const_ru['banker']
        payment_form[
            'warning'] = "❗️ После нажатия <b>Оплатить</b> необходимо будет отправить чек на определенную сумму ❗️"
    elif payment_type == "balance":
        payment_form['name'] = const_ru['balance']
        payment_form[
            'warning'] = ""

    return payment_form


def check_payment(payment_data, user_id=None):
    amount = float(payment_data['amount'])
    payment_type = payment_data['payment']
    comment = ""

    if payment_type != "balance" and payment_type != "banker":
        comment = payment_data['comment']

    has_payment = False

    if payment_type == "qiwi":
        has_payment = check_qiwi_payment(amount, comment)
    elif payment_type == "yoomoney":
        has_payment = check_yoomoney_payment(comment)
    elif payment_type == "balance":
        user_balance = float(database.get_user_balance(user_id))
        has_payment = user_balance >= float(amount)
    elif payment_type == "banker":
        has_payment = payment_data['check']

    return has_payment
