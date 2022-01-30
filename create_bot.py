from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import config

storage = MemoryStorage()

bot=Bot(config.CRIMGOBOT_TOKEN)
dp=Dispatcher(bot, storage=storage)