from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import config

import logging

storage = MemoryStorage()

logging.basicConfig(filename='crimgo_bot.log', format=u'%(filename)s [ LINE:%(lineno)+3s ]#%(levelname)+8s [%(asctime)s] %(funcName)20s() %(message)s', level=logging.INFO)

bot=Bot(config.CRIMGOBOT_TOKEN)
dp=Dispatcher(bot, storage=storage)