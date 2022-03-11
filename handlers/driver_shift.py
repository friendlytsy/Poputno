from email import message
from subprocess import call
from aiogram import Dispatcher, types
from create_bot import dp, bot
from database import crimgo_db, crimgo_db_crud
from keyboards import kb_driver, kb_driver_shift, kb_start_point, kb_start_trip, kb_onboarding_trip, kb_continue_trip
from aiogram.types import ReplyKeyboardRemove

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config

class FSMStartDriverShift(StatesGroup):
    s_inpute_shuttle_name = State()
    s_select_start_point = State()
    s_select_finish_point = State()

class FSMCodeVerification(StatesGroup):
    s_code_verification = State()

async def cmd_start_shift(message: types.Message):
    await FSMStartDriverShift.s_inpute_shuttle_name.set()
    await message.reply('Введите имя шаттла', reply_markup=ReplyKeyboardRemove())
    
async def cmd_shuttle_bind(message: types.Message, state: FSMContext): 
    if (await crimgo_db.check_shuttle_name_and_status(message.text)):
        await FSMStartDriverShift.s_select_start_point.set()
        async with state.proxy() as data:
            data['shuttle_name'] = message.text
        await message.reply('Приветствуем, скоро вам будет назначем рейс, укажите на какой конечной станции вы находитесь.', reply_markup=kb_start_point)
    else:
        await message.reply('Ошибка, неверное имя шаттла или шаттл занят', reply_markup=kb_driver)
        await state.finish()

async def cmd_start_point(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['start_point'] = callback.data
        data['driver_chat_id'] = callback.message.chat.id
        if callback.data == '№1 Шале': data['route'] = 1
        else: data['route'] = 2
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
    await callback.answer()

    # Обновление статуса поездки
    await crimgo_db.set_trip_status(callback, 'scheduled', 'started')
    
    # Получить словарь билетов на рейс
    tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)

    # Получить маршрут
    route = await crimgo_db.get_route(callback)

    if route == 1:
        # Если шаттл на начальной а первый pp не равен начальной
        if (await crimgo_db.get_shuttle_position(callback)) == 1 and tickets[0][3] != 1:
            await crimgo_db.set_shuttle_position(callback)
    if route == 2:
        if (await crimgo_db.get_shuttle_position(callback)) == 8 and tickets[0][3] != 8:
            await crimgo_db.set_shuttle_position(callback)

    # Текущее местоположение шаттла
    shuttle_position = await crimgo_db.get_shuttle_position(callback)

    text = ''
    for i in tickets:
        # Собираем остановки в одно сообщение
        if shuttle_position == i[3]:
            text = text +  '->'
        if i[4] == 'cash':
            text = text + 'Ост. {pp}, {time}, {seats}м. Оплата наличными: {total_amount}\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1], total_amount = i[5])
        else:
            text = text + 'Ост. {pp}, {time}, {seats}м.\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])

    # Отобразить кнопку посадка
    await callback.message.answer(text, reply_markup=kb_onboarding_trip)
    
    
async def cmd_onboarding(callback: types.CallbackQuery):
    await callback.answer()

    # Получить словарь билетов на рейс
    tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)

    # Текущее местоположение шаттла
    shuttle_position = await crimgo_db.get_shuttle_position(callback)
    
    # TODO нужно оптимизировать
    t_counter = 0
    for i in tickets:
        if shuttle_position == i[3]:
            t_counter = t_counter + 1 

    await callback.message.answer('Введите 4х значный секртеный код, который назовут пассажиры.\n--\nОжидаем {t_counter} код(а) на проверку'.format(t_counter = t_counter), reply_markup=ReplyKeyboardRemove())
    await FSMCodeVerification.s_code_verification.set()
    

# получение кодов и проверка
async def cmd_code_verification(message: types.Message, state: FSMContext):
    await state.finish()
    codes = message.text.split()
    for code in codes:
        if (await crimgo_db.verify_pass_code(message, code)) is True:
            await message.reply('Код {code} прошел проверку'.format(code = code), reply_markup=ReplyKeyboardRemove())
    await message.answer('Продолжить поездку или повторить ввод кодов не прошедших проверку?', reply_markup=kb_continue_trip)

# Продожить поездку
async def cmd_continue_trip(callback: types.CallbackQuery):
    await callback.answer()
    # await crimgo_db.set_shuttle_position(callback)
    # Получить словарь билетов на рейс
    tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)
    
    # Если позиция шатла равна последей pp, значит едем на конечную
    text = ''
    if (await crimgo_db.get_shuttle_position(callback)) == tickets[-1][3]:
        # TODO менять статус рейса + нормальное сообщение водителю
        # Обновление статуса поездки
        await crimgo_db.set_trip_status(callback, 'started', 'finished')
        await callback.message.answer('Остановок в рейсе больше нет, укажите на какую конечную вы направляетесь', reply_markup=kb_start_point)
        await FSMStartDriverShift.s_select_finish_point.set()
        await callback.answer()
    else:
        # Поменять местоположение шаттла
        await crimgo_db.set_shuttle_position(callback)

        # Текущее местоположение шаттла
        shuttle_position = await crimgo_db.get_shuttle_position(callback)

        for i in tickets:
            if shuttle_position == i[3]:
                text = text +  '->'
            # Собираем остановки в одно сообщение
            # text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
            if i[4] == 'cash':
                text = text + 'Ост. {pp}, {time}, {seats}м. Оплата наличными: {total_amount}\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1], total_amount = i[5])
            else:
                text = text + 'Ост. {pp}, {time}, {seats}м.\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
         # Отобразить кнопку посадка
        await callback.message.answer(text, reply_markup=kb_onboarding_trip)
    

async def cmd_stop_shift(message: types.Message):
    await crimgo_db.stop_driver_shift(message)
    await message.reply('Смена окончена', reply_markup=kb_driver)

async def cmd_finish_trip(callback: types.CallbackQuery, state: FSMContext):
    
    await state.finish()
   
    async with state.proxy() as data:
        data['start_point'] = callback.data
        data['driver_chat_id'] = callback.message.chat.id
        data['shuttle_name'] = await crimgo_db.get_shuttle_name_by_driver(callback)
        if callback.data == '№1 Шале': 
            data['route'] = 1
        else: 
            data['route'] = 2
    
        await crimgo_db.set_shuttle_position_by_pp_name(data['start_point'], data['route'])
    # Проверяем, если привязан
    if await crimgo_db.is_shuttle_binded(state) is not None or False:
        await callback.message.answer('Спасибо! Вы указали, что стоите на ост. {start_point}. Скоро вам назначат рейс, ожидайте'.format(start_point = callback.data), reply_markup=kb_driver_shift)
        # await crimgo_db.set_shuttle_message_id(callback.message.message_id, state)
        # Записать чат message id
        trip_details = await crimgo_db.check_available_trip(state)
        if trip_details is not None:
            await callback.message.answer('Поздравляем, Вам назначен рейс {trip_id} "{route}". Старт в {start_time} от "{start_point}"'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M"), start_point = data['start_point']), reply_markup=kb_start_trip)    
    else:
        await message.reply('Произошла ошибка, повторите позже', reply_markup=ReplyKeyboardRemove())

def register_handlers_driver_on_shift(dp: Dispatcher):
    dp.register_message_handler(cmd_start_shift, Text(equals='Текущее состояние: не на линии', ignore_case=False))
    dp.register_message_handler(cmd_stop_shift, Text(equals='Текущее состояние: на линии', ignore_case=False))
    dp.register_message_handler(cmd_shuttle_bind, state = FSMStartDriverShift.s_inpute_shuttle_name)
    dp.register_callback_query_handler(cmd_start_point, state = FSMStartDriverShift.s_select_start_point)
    dp.register_callback_query_handler(cmd_start_trip, Text(equals='Начать рейс', ignore_case=False))
    dp.register_callback_query_handler(cmd_continue_trip, Text(equals='Продолжить', ignore_case=False))
    dp.register_callback_query_handler(cmd_onboarding, Text(equals='Посадка', ignore_case=False))
    dp.register_message_handler(cmd_code_verification, state = FSMCodeVerification.s_code_verification)
    dp.register_callback_query_handler(cmd_finish_trip, state = FSMStartDriverShift.s_select_finish_point)