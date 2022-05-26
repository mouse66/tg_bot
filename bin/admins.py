from loader import bot
from src.config import ADMIN_ID


async def send_admins(message_text, keyboard=None, document=None):
    """
    Отправка сообщений всем админам

    :param message_text: сообщение
    :param keyboard: при необходимости клавиатура
    :param document: при необходимости отправка документа
    :return:
    """
    for admin in ADMIN_ID:
        if document is not None:
            await bot.send_document(admin,
                                    document=open(document, "rb"),
                                    caption=message_text,
                                    reply_markup=keyboard)
        else:
            await bot.send_message(admin, message_text, reply_markup=keyboard)


async def send_admins_doc(document, message_text=None, keyboard=None):
    """
    Отправка документа из Telegram всем админам

    :param message_text:
    :param document: file_id документа
    :param keyboard:
    :return:
    """
    for admin in ADMIN_ID:
        await bot.send_document(admin,
                                document,
                                caption=message_text,
                                reply_markup=keyboard)
