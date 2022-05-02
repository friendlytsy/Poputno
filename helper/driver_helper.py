import logging
from aiogram.dispatcher import FSMContext
from create_bot import bot
from aiogram import types
from database import crimgo_db


# Удаления сообщений в списке msg_id_list
async def save_driver_action(telegram_id, action):
    await crimgo_db.save_driver_action(telegram_id, action)