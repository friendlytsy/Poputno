from email import message
from subprocess import call
from aiogram import Dispatcher, types
from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_driver, kb_driver_shift, kb_start_point, kb_start_trip, kb_onboarding_trip
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config

class FSMStartDriverShift(StatesGroup):
    s_inpute_shuttle_name = State()
    s_select_start_point = State()

async def cmd_start_shift(message: types.Message):
    await FSMStartDriverShift.s_inpute_shuttle_name.set()
    await message.reply('Введите имя шаттла', reply_markup=ReplyKeyboardRemove())
    
async def cmd_shuttle_bind(message: types.Message, state: FSMContext): 
    await FSMStartDriverShift.s_select_start_point.set()
    async with state.proxy() as data:
            data['shuttle_name'] = message.text
    await message.reply('Приветствуем, скоро вам будет назначем рейс, укажите на какой конечной станции вы находитесь.', reply_markup=kb_start_point)

async def cmd_start_point(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['start_point'] = callback.data
        data['driver_chat_id'] = callback.message.chat.id
    # Привязываем шаттл
    await crimgo_db.bind_shuttle_to_driver(state, callback)
    # Проверяем, если привязан
    if await crimgo_db.is_shuttle_binded(state) is not None or False:
        await callback.message.answer('Спасибо! Вы указали, что стоите на ост. {start_point}. Скоро вам назначат рейс, ожидайте'.format(start_point = callback.data), reply_markup=kb_driver_shift)
        # await crimgo_db.set_shuttle_message_id(callback.message.message_id, state)
        # Записать чат message id
        trip_details = await crimgo_db.check_available_trip(state)
        if trip_details is not None:
            await callback.message.answer('Поздравляем, Вам назначен рейс {trip_id} "{route}". Старт в {start_time} от "{start_point}"'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M"), start_point = data['start_point']), reply_markup=kb_start_trip)
        # else:
        #     await callback.message.reply('Спасибо! Вы указали, что стоите на ост. {start_point}, скоро вам назначат рейс, ожидайте'.format(start_point = callback.data), reply_markup=kb_driver_shift)
            
    else:
        await message.reply('Произошла ошибка, повторите позже', reply_markup=ReplyKeyboardRemove())
        await state.finish()

    await callback.answer()
    await state.finish()

async def cmd_start_trip(callback: types.CallbackQuery):
    # Получить словарь билетов на рейс
    tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)
    text = ''
    pointer = '->'
    for i in tickets:
        # Собираем остановки в одно сообщение
        text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
    # Отобразить кнопку посадка
    await callback.message.answer(text, reply_markup=kb_onboarding_trip)
    await callback.answer()
    
    # Поменять местоположение шаттла

async def cmd_stop_shift(message: types.Message):
    await crimgo_db.stop_driver_shift(message)
    await message.reply('Смена окончена', reply_markup=kb_driver)

def register_handlers_driver_on_shift(dp: Dispatcher):
    dp.register_message_handler(cmd_start_shift, Text(equals='Текущее состояние: не на линии', ignore_case=False))
    dp.register_message_handler(cmd_stop_shift, Text(equals='Текущее состояние: на линии', ignore_case=False))
    dp.register_message_handler(cmd_shuttle_bind, state = FSMStartDriverShift.s_inpute_shuttle_name)
    dp.register_callback_query_handler(cmd_start_point, state = FSMStartDriverShift.s_select_start_point)
    dp.register_callback_query_handler(cmd_start_trip, Text(equals='Начать рейс', ignore_case=False))