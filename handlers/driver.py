from aiogram import Dispatcher, types
from aiogram.types import ReplyKeyboardRemove
from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_driver, kb_driver_shift, kb_generic_start, kb_driver_verification
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from random import randrange

class FSMRegisterDriver(StatesGroup):
    s_share_name = State()
    s_share_contact = State()
    
async def cmd_get_driver_menu(message: types.Message):
    # Если не нет записи в БД, начинается регистрация
    if (await crimgo_db.is_driver_exist(message)) is None:
        await FSMRegisterDriver.s_share_name.set()
        await message.reply('Введите имя для регистарции', reply_markup=ReplyKeyboardRemove())        
    else:
        # Если валиден, otp проверен
        if (await crimgo_db.is_driver_valid(message) is True):
            # То проверка на смену
            if (await crimgo_db.is_on_shift(message)): 
                await message.reply('Добрый день', reply_markup=kb_driver_shift)
            else: 
                await message.reply('Добрый день', reply_markup=kb_driver)
        # То предлагаем пройти валидацию
        else: 
            await message.reply('Ожидается верификация админом', reply_markup=kb_driver_verification)

# Обработка имени
async def get_driver_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        data['otp'] = randrange(1000, 9999, 1)
    await FSMRegisterDriver.s_share_contact.set()
    await message.reply('Поделитесь контактом для регистарции', reply_markup=kb_generic_start)        

# Обработка контакта
async def get_driver_contact(message: types.Message, state: FSMContext):
    # Создаем водителя
    if (await crimgo_db.create_driver(message,state)) is True:
        await message.answer('Спасибо', reply_markup=kb_driver_verification)
    else:
        await message.answer('Произошла ошбика, попробуйте позже', reply_markup=kb_generic_start)
    await state.finish()

def register_handlers_driver(dp: Dispatcher):
    dp.register_message_handler(cmd_get_driver_menu, Text(equals='Водитель', ignore_case=False))
    dp.register_message_handler(get_driver_name, state = FSMRegisterDriver.s_share_name)
    dp.register_message_handler(get_driver_contact, content_types=['contact'], state = FSMRegisterDriver.s_share_contact)
    
