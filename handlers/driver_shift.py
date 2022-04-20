from email import message
from aiogram import Dispatcher, types
from create_bot import bot
from database import crimgo_db
from keyboards import kb_driver, kb_driver_shift, kb_start_point, kb_start_trip, kb_onboarding_trip, kb_continue_trip, kb_pass_absent, kb_retry_code, kb_outboarding_trip
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config

from text import driver_text

import logging

class FSMStartDriverShift(StatesGroup):
    s_inpute_shuttle_name = State()
    s_select_start_point = State()
    s_select_finish_point = State()

class FSMCodeVerification(StatesGroup):
    s_code_input = State()
    s_onboarding_finish = State()

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
        if callback.data == 'ЖК Ришелье Шато': data['route'] = 1
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
    # await crimgo_db.set_trip_status_start(callback, trip_id, 'started')
    await crimgo_db.set_trip_status_start(callback, 'started')

    # Получить маршрут
    route = await crimgo_db.get_route(callback)

    if route == 1:
        # Получить словарь билетов на рейс
        tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)
        # Если шаттл на начальной а первый pp не равен начальной
        if (await crimgo_db.get_shuttle_position(callback)) == 1 and tickets[0][3] != 1:
            await crimgo_db.set_shuttle_position(callback, route)
    if route == 2:
        # Получить словарь билетов на рейс
        tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)
        drop_points = await crimgo_db.get_dict_of_tickets_by_driver_drop_point(callback.from_user.id)
        # if (await crimgo_db.get_shuttle_position(callback)) == 9 and tickets[0][3] != 9:
        #     await crimgo_db.set_shuttle_position(callback, route)

    # Текущее местоположение шаттла
    shuttle_position = await crimgo_db.get_shuttle_position(callback)

    # Информация о конечной остановке
    ending_station = await crimgo_db.get_ending_station_by_route(route)
    trip_finish_time = await crimgo_db.get_trip_finish_time(callback.from_user.id)

    # Собираем остановки в одно сообщение
    text = ''
    if route == 1:
        for i in tickets:
            if shuttle_position == i[3]:
                text = text +  '->'
            if i[4] == 'cash':
                text = text + 'Ост. {pp}, {time}, {seats}м. Оплата наличными: {total_amount}\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1], total_amount = i[5])
            else:
                text = text + 'Ост. {pp}, {time}, {seats}м.\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
            if i == tickets[-1]:
                text = text + 'Конечная ост. - {pp}, время прибытия - {time}'.format(pp = ending_station, time = trip_finish_time.strftime("%H:%M"))
    if route == 2:
        for i in drop_points:
            # Собираем остановки в одно сообщение
            # text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
            if i[4] == 'cash':
                text = text + 'Высадка ост. {pp}, время {time}, {seats}м. Оплата наличными: {total_amount}\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1], total_amount = i[5])
            else:
                text = text + 'Высадка ост. {pp}, время {time}, {seats}м.\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
        text = text + 'Конечная {pp}, {time}'.format(pp = ending_station, time = trip_finish_time.strftime("%H:%M"))
    # Отобразить кнопку посадка
    await callback.message.answer(text, reply_markup=kb_onboarding_trip)
    
    
async def cmd_onboarding(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    # Текущее местоположение шаттла
    shuttle_position = await crimgo_db.get_shuttle_position(callback)

    # Получить кол-во билетов для остановки
    t_otp = await crimgo_db.get_dict_of_tickets_by_shuttle_position(callback.from_user.id, shuttle_position)
    
    await callback.message.answer(driver_text.current_otps, reply_markup=ReplyKeyboardRemove())
    for otp in t_otp:
        await callback.message.answer(otp, reply_markup = InlineKeyboardMarkup().\
            row(InlineKeyboardButton(driver_text.pass_onboarding, callback_data = 'activate {otp}'.format(otp = otp)),\
                (InlineKeyboardButton(driver_text.pass_absent, callback_data = 'cancel {otp}'.format(otp = otp)))))
    # await callback.message.answer('Введите 4х значный секретный код, который назовут пассажиры', reply_markup=ReplyKeyboardRemove())
    # await callback.message.answer('Ожидаем {t_counter} код(а) на проверку'.format(t_counter = t_counter), reply_markup=kb_pass_absent)
    
    await FSMCodeVerification.s_code_input.set()    
    async with state.proxy() as data:
        # data['t_counter'] = t_otp
        data['shuttle_position'] = shuttle_position
 
# получение кодов и проверка
async def cmd_code_verification(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    # Кол-во билетов для остановки и позиция шаттла
    async with state.proxy() as data:
        shuttle_position = data['shuttle_position']

    # Если callback начинается с activate
    if callback.data.startswith('activate '):
        code_status = await crimgo_db.verify_pass_code(callback, callback.data.replace('activate ', ''))
        # Если код прошел проверку
        if code_status is True:
            try:
                await callback.message.edit_text(text = '{otp} - ✔'.format(otp = callback.data.replace('activate ', '')), reply_markup = None)
            except (Exception) as error:
                logging.error(msg = error, stack_info = True)
    
    if callback.data.startswith('cancel '):
        # TODO отмена заказа водителем
        code_status = await crimgo_db.cancel_pass_code(callback, callback.data.replace('cancel ', ''))
        # Если код прошел проверку
        if code_status is True:
            try:
                await callback.message.edit_text(text = '{otp} - 𐄂'.format(otp = callback.data.replace('cancel ', '')), reply_markup = None)
            except (Exception) as error:
                logging.error(msg = error, stack_info = True)

    # Если билетов больше нет
    t_counter = await crimgo_db.get_dict_of_tickets_by_shuttle_position(callback.from_user.id, shuttle_position)
    if len(t_counter) == 0:
        # Завершение состояния s_code_input
        await state.finish()
        await callback.message.answer(driver_text.trip_continue, reply_markup=kb_continue_trip)
    
# Продожить поездку
async def cmd_continue_trip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    # await crimgo_db.set_shuttle_position(callback)    
    route = await crimgo_db.get_route(callback)
    # Если маршрут к морю
    if route == 1:
        # Получить словарь билетов на рейс
        tickets = await crimgo_db.get_dict_of_tickets_by_driver(callback.from_user.id)
        # Если маршрут от морю
    if route == 2:
        tickets = await crimgo_db.get_dict_of_tickets_by_driver_drop_point(callback.from_user.id)

    # Если позиция шатла равна последей pp, значит едем на конечную
    text = ''
    if (await crimgo_db.get_shuttle_position(callback)) == tickets[-1][3]:
        # ИД маршрута
        route_id_by_trip = await crimgo_db.route_id_by_trip(callback.from_user.id)
        # Инфо о конечной
        ending_station = await crimgo_db.get_ending_station_by_route(route_id_by_trip)
        trip_finish_time = await crimgo_db.get_trip_finish_time(callback.from_user.id)
        # Обновление статуса поездки
        await crimgo_db.set_trip_status(callback, 'started', 'finished')
        await callback.message.answer('Конечная ост. - {pp}, время прибытия - {time}'.format(pp = ending_station, time = trip_finish_time.strftime("%H:%M")), reply_markup=kb_continue_trip)
        async with state.proxy() as data:
            data['route'] = route_id_by_trip
        # FSM конечная точка
        await FSMStartDriverShift.s_select_finish_point.set()
    else:
        # Поменять местоположение шаттла
        await crimgo_db.set_shuttle_position(callback, route)

        # Текущее местоположение шаттла
        shuttle_position = await crimgo_db.get_shuttle_position(callback)
            
        # Информация о конечной остановке
        ending_station = await crimgo_db.get_ending_station_by_route(route)
        trip_finish_time = await crimgo_db.get_trip_finish_time(callback.from_user.id)

        for i in tickets:
            if shuttle_position == i[3]:
                text = text +  '->'
            # Собираем остановки в одно сообщение
            # text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
            if i[4] == 'cash':
                text = text + 'Ост. {pp}, {time}, {seats}м. Оплата наличными: {total_amount}\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1], total_amount = i[5])
            else:
                text = text + 'Ост. {pp}, {time}, {seats}м.\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
            if i == tickets[-1]:
                text = text + 'Конечная {pp}, {time}'.format(pp = ending_station, time = trip_finish_time.strftime("%H:%M"))
            # Отобразить кнопку посадка
        if route == 1:
            await callback.message.answer(text, reply_markup=kb_onboarding_trip)
        if route == 2:
            await callback.message.answer(text, reply_markup=kb_outboarding_trip)

async def cmd_stop_shift(message: types.Message):
    assigned_trip = await crimgo_db.is_trip_assigned(message.from_user.id)
    if assigned_trip:
        trip_details = await crimgo_db.check_available_trip_after_trip(message.from_user.id)
        if trip_details is not None:
            await message.answer('Вам назначен рейс {trip_id} "{route}". Старт в {start_time}.'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M")), reply_markup=kb_driver_shift)    
            # Сохраняем ИД сообщения для обновления
            await crimgo_db.set_shuttle_message_id_by_trip(message.message_id, trip_details[0])
    else:
        await crimgo_db.stop_driver_shift(message)
        await message.reply('Смена окончена', reply_markup=kb_driver)

async def cmd_finish_trip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    async with state.proxy() as data:
        if data['route'] == 1:
            data['route'] = 2
            start_point = 'Успенская церковь'
        else:
            data['route'] = 1    
            start_point = 'ЖК Ришелье Шато'
        
        data['driver_chat_id'] = callback.message.chat.id
        data['shuttle_name'] = await crimgo_db.get_shuttle_name_by_driver(callback)
        
        await crimgo_db.set_shuttle_position_by_pp_name(start_point, data['route'])
        await state.finish()

    # Проверяем, если привязан
    if await crimgo_db.is_shuttle_binded(state) is not None or False:
        await callback.message.answer('Спасибо! Вы указали, что стоите на ост. {start_point}. Скоро вам назначат рейс, ожидайте'.format(start_point = start_point), reply_markup=kb_driver_shift)
        # await crimgo_db.set_shuttle_message_id(callback.message.message_id, state)
        # Если есть поездки
        trip_details = await crimgo_db.check_available_trip_after_trip(callback.from_user.id)
        if trip_details is not None:
            await callback.message.answer('Поздравляем, Вам назначен рейс {trip_id} "{route}". Старт в {start_time} от "{start_point}"'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M"), start_point = start_point), reply_markup=kb_driver_shift)    
            async with state.proxy() as data:
                data['trip_id'] = trip_details[0]
            # Сохраняем ИД сообщения для обновления
            await crimgo_db.set_shuttle_message_id(callback.message.message_id, state)
            # Информация о чате для пуша водителю
            driver_chat_id = await crimgo_db.get_driver_chat_id(state)
            text = await crimgo_db.get_message_text_trip_id(state)
            try:
                msg = await bot.send_message(driver_chat_id[0], text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text = 'Начать рейс', callback_data='Начать рейс {trip_id}'.format(trip_id=data['trip_id']))))
            except (Exception) as error:
                print(driver_text.ticket_error_edit, error)
            # Обновляем ИД сообщения
            await crimgo_db.set_shuttle_message_id(msg.message_id, state)
    else:
        await message.reply('Произошла ошибка, повторите позже', reply_markup=ReplyKeyboardRemove())

def register_handlers_driver_on_shift(dp: Dispatcher):
    dp.register_message_handler(cmd_start_shift, Text(equals='Текущее состояние: не на линии', ignore_case=False))
    dp.register_message_handler(cmd_stop_shift, Text(equals='Текущее состояние: на линии', ignore_case=False))
    dp.register_message_handler(cmd_shuttle_bind, state = FSMStartDriverShift.s_inpute_shuttle_name)
    dp.register_callback_query_handler(cmd_start_point, state = FSMStartDriverShift.s_select_start_point)
    dp.register_callback_query_handler(cmd_start_trip, Text(contains='Начать рейс', ignore_case=False))
    dp.register_callback_query_handler(cmd_continue_trip, Text(equals='Продолжить', ignore_case=False))
    dp.register_callback_query_handler(cmd_onboarding, Text(equals='Посадка', ignore_case=False))
    dp.register_callback_query_handler(cmd_code_verification, state = FSMCodeVerification.s_code_input)
    dp.register_callback_query_handler(cmd_finish_trip, state = FSMStartDriverShift.s_select_finish_point)