import os.path

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from telethon import TelegramClient

import database
from loader import dp
from src.const import is_const, const_ru


class Client:
    client = TelegramClient("1", "1", "1")


class BankerEditor(StatesGroup):
    api_id = State()
    api_hash = State()

    phone = State()
    code = State()

    session_file = State()


async def banker_id(message: types.Message):
    """
    Запрос api_id приложения

    :param message:
    :return:
    """
    await message.answer("📱 Введите <b>api_id</b>\n\n"
                         "Его можно получить <a href='https://my.telegram.org/apps'>здесь</a>")
    await BankerEditor.api_id.set()


@dp.message_handler(state=BankerEditor.api_id)
async def banker_hash(message: types.Message, state: FSMContext):
    """
    Запрос api_hash

    :param message:
    :param state:
    :return:
    """
    api_id = message.text
    if is_const(api_id) and not api_id.isdigit():
        await message.answer(const_ru['invalid_value'])
        return

    await state.update_data(api_id=int(api_id))
    await BankerEditor.next()
    await message.answer("📱 Введите <b>api_hash</b> полученный при регистрации")


@dp.message_handler(state=BankerEditor.api_hash)
async def session_file(message: types.Message, state: FSMContext):
    """
    Запрос телефона

    :param message:
    :param state:
    :return:
    """
    api_hash = message.text
    if is_const(api_hash):
        await message.answer(const_ru['invalid_value'])
        return

    await state.update_data(api_hash=api_hash)

    data = await state.get_data()
    if os.path.exists("bot.session"):
        os.remove("bot.session")

    Client.client = TelegramClient('bot', data['api_id'], data['api_hash'])
    await Client.client.connect()

    if not await Client.client.is_user_authorized():
        await message.answer("📱 Введите номер телефона вашего аккаунта, на который вы сделали приложение ранее\n\n"
                             "Это необходимо для корректной работы проверки чеков")
        await BankerEditor.next()
    else:
        await message.answer("✅ Авторизация прошла успешно")
        await state.finish()


@dp.message_handler(state=BankerEditor.phone)
async def password(message: types.Message, state: FSMContext):
    """
    Запрос пароля

    :param message:
    :param state:
    :return:
    """
    phone = message.text
    if is_const(phone) or not phone.isdigit():
        await message.answer("❗️ Введите корректный номер телефона")
        return

    await state.update_data(phone=phone)

    phone_code = await Client.client.send_code_request(phone)
    await state.update_data(phone_code_hash=phone_code.phone_code_hash)

    await message.answer("📱 Введите код авторизации, отправленный Telegram\n"
                         "❗️ Перед кодом добавьте любую букву, иначе сообщение с кодом не будет отправляться\n"
                         "Это уже проблемы библиотеки, а не бота")
    await BankerEditor.next()


@dp.message_handler(state=BankerEditor.code)
async def get_pass(message: types.Message, state: FSMContext):
    """
    Проверка кода

    :param message:
    :param state:
    :return:
    """
    code = f"a{message.text}"
    if is_const(code):
        await message.answer("❗️ Введите корректный код")
        return

    await state.update_data(code=code)
    await auth(message, state)


async def auth(message: types.Message, state: FSMContext):
    """
    Авторизация

    :param message:
    :param state:
    :return:
    """
    auth_data = await state.get_data()

    await Client.client.sign_in(phone=auth_data['phone'],
                                code=auth_data['code'],
                                phone_code_hash=auth_data['phone_code_hash'])

    client_data = await Client.client.get_me()

    if client_data is not None:
        await Client.client.disconnect()

        database.edit_banker(auth_data)
        await message.answer("✅ Авторизация прошла успешно")
        await state.finish()
    else:
        await message.answer("❗️ Ошибка авторизации, попробуйте снова ❗️")
        await state.finish()
