from aiogram import Dispatcher, types
from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_driver 
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMValidateDriver(StatesGroup):
    s_input_phone = State()
    s_input_otp = State()

async def cmd_get_driver_menu(message: types.Message):
    if (await crimgo_db.is_driver_exist(message)) is None:
        await FSMValidateDriver.s_input_phone.set()
        await message.reply('Для валидации введите номер телефона', reply_markup = ReplyKeyboardRemove())
    else: await message.reply('Водитель', reply_markup=kb_driver)

async def validate_driver_phone(message: types.Message, state = FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
    await FSMValidateDriver.s_input_otp.set()
    await message.reply('Введите пароль')

async def validate_driver_otp(message: types.Message, state = FSMContext):
    async with state.proxy() as data:
        data['otp'] = message.text
    if (await crimgo_db.is_driver_valid(state, message)):
        await message.reply('Успешно зарегистрирован') 
    else:
        await message.reply('Водитель не зарегестрирован') 

    await state.finish()

def register_handlers_driver(dp: Dispatcher):
    dp.register_message_handler(cmd_get_driver_menu, commands=['Водитель'])
    dp.register_message_handler(validate_driver_phone, state = FSMValidateDriver.s_input_phone)
    dp.register_message_handler(validate_driver_otp, state = FSMValidateDriver.s_input_otp)
