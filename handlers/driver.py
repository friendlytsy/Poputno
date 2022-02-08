from aiogram import Dispatcher, types
from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_driver, kb_driver_shift
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMValidateDriver(StatesGroup):
    s_input_phone = State()
    s_input_otp = State()

class FSMBindShuttle(StatesGroup):
    s_inpute_shuttle_name = State()

async def cmd_get_driver_menu(message: types.Message):
    if (await crimgo_db.is_driver_exist(message)) is None:
        await FSMValidateDriver.s_input_phone.set()
        await message.reply('Для валидации введите номер телефона', reply_markup = ReplyKeyboardRemove()) 
    
    if (await crimgo_db.is_on_shift(message)): 
        await message.reply('Водитель', reply_markup=kb_driver_shift)
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

async def cmd_start_shift(message: types.Message):
    await FSMBindShuttle.s_inpute_shuttle_name.set()
    await message.reply('Введите имя шаттла', reply_markup=ReplyKeyboardRemove())
    
async def cmd_shuttle_bind(message: types.Message, state: FSMContext):
    if await crimgo_db.bind_shuttle_to_driver(message):
        await message.reply('Шаттл успешно привязан', reply_markup=kb_driver_shift)
    else:
        await message.reply('Произошла ошибка, повторите позже', reply_markup=ReplyKeyboardRemove())

    await state.finish()


def register_handlers_driver(dp: Dispatcher):
    dp.register_message_handler(cmd_get_driver_menu, Text(equals='Водитель', ignore_case=False))
    dp.register_message_handler(validate_driver_phone, state = FSMValidateDriver.s_input_phone)
    dp.register_message_handler(validate_driver_otp, state = FSMValidateDriver.s_input_otp)
    dp.register_message_handler(cmd_start_shift, Text(equals='Текущее состояние: не на линии', ignore_case=False))
    dp.register_message_handler(cmd_shuttle_bind, state = FSMBindShuttle.s_inpute_shuttle_name)
