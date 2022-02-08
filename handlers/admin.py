from aiogram import Dispatcher, types
from create_bot import dp, bot
from keyboards import kb_admin 
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from database import crimgo_db
from random import randrange

ID = None

# FSM регистрации водителя
class FSMDriverReg(StatesGroup):
    s_name = State()
    s_phone = State()

# FSM регистрации шаттла
class FSMShuttleReg(StatesGroup):
    s_name = State()
    s_capacity = State()


# Вызов админки
async def cmd_get_menu(message: types.Message):
    global ID
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, 'Что надо хозяин?', reply_markup=kb_admin)
    await message.delete()

# Запрос имени водителя
async def cmd_driver_reg(message: types.Message):
    if message.from_user.id == ID:
        await FSMDriverReg.s_name.set()
        await message.reply('Введите имя водителя', reply_markup=ReplyKeyboardRemove()) 

# Обработка имени и запрос номера телефона водителя
async def input_name(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['name'] = message.text
    
        await FSMDriverReg.s_phone.set()
        await message.reply('Введите номер телефона в формате 79876543210')

# Обработка телефона и запись в БД
async def input_phone(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['phone'] = message.text
            data['opt'] = randrange(1000, 9999, 1)
        async with state.proxy() as data:
            await message.reply(str(data))

        await crimgo_db.pre_reg_driver(state)

        await state.finish()

# Выход из машины состояний
#@dp.message_handler(state="*", commands=['отмена'])
#@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply('Ok ')

# Запрос имени шаттла
async def cmd_shuttle_reg(message: types.Message):
    if message.from_user.id == ID:
        await FSMShuttleReg.s_name.set()
        await message.reply('Ввидети имя шаттла', reply_markup=ReplyKeyboardRemove())

# Обработка имени и запрос вместительности
async def input_shuttle_name(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['name'] = message.text
    
        await FSMShuttleReg.s_capacity.set()
        await message.reply('Введите вместительнось шаттла')

# Обработка вместительности и запись в БД
async def input_shuttle_capacity(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data['capacity'] = message.text
        async with state.proxy() as data:
            await message.reply(str(data))

        await crimgo_db.reg_shuttle(state)

        await state.finish()


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(cmd_driver_reg, commands=['Регистрация_водителя'])
    dp.register_message_handler(cancel_handler, state="*", commands=['отмена'])
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(input_name, state=FSMDriverReg.s_name)
    dp.register_message_handler(input_phone, state=FSMDriverReg.s_phone)
    dp.register_message_handler(cmd_shuttle_reg, commands=['Регистрация_шаттла'])
    dp.register_message_handler(input_shuttle_name, state=FSMShuttleReg.s_name)
    dp.register_message_handler(input_shuttle_capacity, state=FSMShuttleReg.s_capacity)
    dp.register_message_handler(cmd_get_menu, commands=['moderator'], is_chat_admin=True)
