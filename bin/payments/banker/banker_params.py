import re
from asyncio import sleep

from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

import database


async def check_handler(regex):
    data = database.get_banker()
    try:
        client = TelegramClient('bot', data[1], data[2])
        if not client.is_connected():
            await client.connect()

        await client.send_message('BTC_CHANGE_BOT', f'/start {regex}')
        channel_entity = await client.get_entity('BTC_CHANGE_BOT')
        await sleep(0.5)
        posts = await client(
            GetHistoryRequest(peer=channel_entity, limit=1, offset_date=None, offset_id=0, max_id=0, min_id=0,
                              add_offset=0, hash=0))
        mesages = posts.messages

        for i in mesages:
            answer = i.message

        await client.disconnect()
        if 'Вы получили' in str(answer):
            return float(re.findall('(\d+.\d+ RUB)', answer)[0].replace('RUB', '').replace(',', '.').strip())
        elif 'Упс, кажется, данный чек успел обналичить кто-то другой 😟' in str(answer):
            return -1
    except Exception as e:
        return -1
