from aiogram import Dispatcher, types
from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_driver, kb_driver_shift, kb_start_point
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

class FSMDriverShift(StatesGroup):
    s_start_point = State()
    s_awaiting_path = State()
    s_awaiting_pass = State()
    s_start_path = State()
    s_onboarding = State()
    s_verify_code = State()
    s_path_finished = State()

class FSMBindShuttle(StatesGroup):
    s_inpute_shuttle_name = State()

async def cmd_start_shift(message: types.Message):
    await FSMBindShuttle.s_inpute_shuttle_name.set()
    await message.reply('Введите имя шаттла', reply_markup=ReplyKeyboardRemove())
    
async def cmd_shuttle_bind(message: types.Message, state: FSMContext):
    # Привязываем шаттл
    await crimgo_db.bind_shuttle_to_driver(message)
    # Проверяем, если привязан
    if await crimgo_db.is_shuttle_binded(message) is not None or False:
        await message.reply('Шаттл успешно привязан', reply_markup=kb_driver_shift)
        await message.reply('Приветствуем, скоро вам будет назначем рейс, укажите на какой конечной станции вы находитесь.', reply_markup=kb_start_point)
    else:
        await message.reply('Произошла ошибка, повторите позже', reply_markup=ReplyKeyboardRemove())

    await state.finish()

async def shift_start_point(callback: types.CallbackQuery, state: FSMContext):
    await FSMDriverShift.s_start_point.set()

def register_handlers_driver_on_shift(dp: Dispatcher):
    dp.register_message_handler(cmd_start_shift, Text(equals='Текущее состояние: не на линии', ignore_case=False))
    dp.register_message_handler(cmd_shuttle_bind, state = FSMBindShuttle.s_inpute_shuttle_name)