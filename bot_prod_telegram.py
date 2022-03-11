from aiogram.utils import executor
from create_bot import dp
from database import crimgo_db 

async def on_startup(_):
    print('Бот вышел онлайн.')
    crimgo_db.crimgo_db_start()

from handlers import admin
from handlers import passenger
from handlers import driver
from handlers import driver_shift

admin.register_handlers_admin(dp)
passenger.register_handlers_client(dp)
driver.register_handlers_driver(dp)
driver_shift.register_handlers_driver_on_shift(dp)

executor.start_polling(dp, skip_updates=True, on_startup=on_startup)