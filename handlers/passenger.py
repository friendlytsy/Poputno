from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from create_bot import bot
from database import crimgo_db
from keyboards import kb_pass, kb_driver, kb_path, kb_seat, kb_geoposition, kb_pp_confirmation, kb_payment_type, kb_driver_shift, kb_generic_start, kb_cancel_reason
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from random import randrange

from config import config

import logging
from keyboards.pass_kb import get_cancel_keyboard

from text import passenger_text
from text import driver_text

from helper import passenger_helper

# Машина состояний для покупки билета
class FSMOrder_trip(StatesGroup):
    s_route_selection = State()
    s_seat_selection = State()
    s_geolocation = State()
    s_pp_confirmation = State()
    s_trip_confirmation = State()
    s_payment_type = State()

# Машина состояний для покупки абонемента
# class FSMOrder_subscribe(StatesGroup):
#     s_payment_subscribe = State()

# Машина состоний для отмены заказа пользователем
class FSMCancel_order(StatesGroup):
    s_cancel_order = State()

# Старт и онбординг
async def commands_start(message: types.Message):
    # Проверка на водителя
    if (await crimgo_db.is_driver_exist(message) is not None):
        # Если валиден
        if (await crimgo_db.is_driver_valid(message) is True):
            # То проверка на смену
            if (await crimgo_db.is_on_shift(message)): 
                await message.reply(driver_text.driver_greetings, reply_markup=kb_driver_shift)
            else: 
                await message.reply(driver_text.driver_greetings, reply_markup=kb_driver)
        
    # Проверка на пользователя
    else:
        if await crimgo_db.is_exist(message) is True:
            await message.reply(passenger_text.user_exist_greetings, reply_markup=kb_pass)
        if await crimgo_db.is_exist(message) is False:          
            await message.reply(passenger_text.user_not_exist_greetings, reply_markup=kb_generic_start)
        await message.answer(passenger_text.about_service)

# Обработка контакта
async def get_contact(message: types.Message):
    # If not exist, create a user
    await crimgo_db.create_user(message)
    await message.answer(passenger_text.thanks, reply_markup=kb_pass)

# Чат поддержки
async def cmd_contact_with_support(message: types.Message):
    #await bot.send_contact(chat_id = message.from_user.id, phone_number = '+7 978 173-26-90', first_name = 'Администрация CrimGo')
    await bot.send_message(chat_id=message.from_user.id, text=passenger_text.contact_with_support_link, parse_mode = passenger_text.html_parse_mode, disable_web_page_preview=True)

# Покупка билета
async def cmd_order_trip(message: types.Message, state: FSMContext):
    await FSMOrder_trip.s_route_selection.set()
    msg = await message.answer(passenger_text.start_trip_awaiting, reply_markup=kb_path) 
    # Сохраняем ИД сообщения
    await passenger_helper.update_msg_list([msg.message_id], state)

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(message.from_user.id, cmd_order_trip.__name__)

# Выбор маршрута
async def menu_route_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data != passenger_text.cancel:
        await FSMOrder_trip.s_seat_selection.set()
        async with state.proxy() as data:
                data['route'] = callback.data
                if callback.data == 'К морю':
                    data['opposite'] = 'От моря'
                else: data['opposite'] = 'К морю'
                # Удаление предыдущего сообщения
                await passenger_helper.remove_messages(callback.from_user.id, data['msg'])

        msg = await callback.message.answer(passenger_text.to_choose_seats, reply_markup=kb_seat)
        # Сохраняем ИД сообщения
        await passenger_helper.update_msg_list([msg.message_id], state)
    else:
        # Удаление предыдущего сообщения
        async with state.proxy() as data:
            await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
        await state.finish()
        await callback.message.answer(passenger_text.order_canceled, reply_markup=kb_pass)

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, menu_route_selection.__name__ + ': ' + callback.data)

# Выбор кол-ва мест
async def menu_seat_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    if callback.data != 'Отмена':
        await FSMOrder_trip.s_geolocation.set()
        async with state.proxy() as data:
                data['seat'] = callback.data
                # Удаление предыдущего сообщения
                await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
        msg_seats = await callback.message.answer(passenger_text.chosen_seats.format(seats = callback.data))
        if data['route'] == 'К морю':
            msg = await callback.message.answer(passenger_text.to_choose_pickup_point, reply_markup=kb_geoposition)
        if data['route'] == 'От моря':
            msg = await callback.message.answer(passenger_text.to_choose_drop_point, reply_markup=kb_geoposition)
        # Сохраняем ИД сообщения
        await passenger_helper.update_msg_list([msg.message_id, msg_seats.message_id], state)
    else:
        # Удаление предыдущего сообщения
        async with state.proxy() as data:
            await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
        await state.finish()
        await callback.message.answer(passenger_text.order_canceled, reply_markup=kb_pass)    

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, menu_seat_selection.__name__ + ': ' + callback.data)

# Геопозиция
async def menu_pp_confirm(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data != passenger_text.cancel:
        if callback.data != passenger_text.go_back:
            await FSMOrder_trip.s_pp_confirmation.set()
            async with state.proxy() as data:
                # Удаление предыдущего сообщения
                await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
                # Если маршрут к морю
                if data['route'] == 'К морю':
                    data['pickup_point'] = callback.data
                    data['drop_point'] = 'Успенская церковь'
                # Если от моря
                if data['route'] == 'От моря':
                    data['pickup_point'] = 'Успенская церковь'
                    data['drop_point'] = callback.data
            pp_location = await crimgo_db.get_pp_location(callback.data, data['route'])
            try:
                msg_location = await bot.send_location(chat_id=callback.from_user.id, latitude=pp_location[0], longitude=pp_location[1])
            except (Exception) as error:
                logging.error(msg = error, stack_info = True)
            async with state.proxy() as data:
                data['msg_location'] = [msg_location.message_id]
            if data['route'] == 'К морю':
                msg = await callback.message.answer(passenger_text.you_chosen_pickup_point.format(pp = data['pickup_point']), reply_markup=kb_pp_confirmation)
            if data['route'] == 'От моря':
                msg = await callback.message.answer(passenger_text.you_chosen_drop_point.format(dp = data['drop_point']), reply_markup=kb_pp_confirmation)
            # Сохраняем ИД сообщения
            await passenger_helper.update_msg_list([msg.message_id], state)
        else:
            async with state.proxy() as data:
                # Удаление предыдущего сообщения
                await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
            await FSMOrder_trip.s_seat_selection.set()
            msg = await callback.message.answer(passenger_text.to_choose_seats, reply_markup=kb_seat)
            # Сохраняем ИД сообщения
            await passenger_helper.update_msg_list([msg.message_id], state)
        
    else:
        # Удаление предыдущего сообщения
        async with state.proxy() as data:
            await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
        await state.finish()
        await callback.message.answer(passenger_text.order_canceled, reply_markup=kb_pass)

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, menu_pp_confirm.__name__ + ': ' + callback.data)

# Выбор остановки
async def menu_trip_confirm(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data != passenger_text.cancel:
        if callback.data != 'Повторить':
            await FSMOrder_trip.s_payment_type.set()
            # await FSMOrder_trip.s_trip_confirmation.set()
            # Сохраняем total_amount
            await passenger_helper.update_state_with_total_amount(callback, state)
            # Удаление предыдущего сообщения
            await passenger_helper.remove_messages(callback.from_user.id, await passenger_helper.get_data_from_state('msg', state))
            #########
            # Создание и назначение поездки
            #########
            # Если есть есть хоть кто-то в смене
            if (await crimgo_db.is_any_on_shift() != 0):
                trip_id = await crimgo_db.is_trip_with_route_and_seats(state)
                # Если нет открытых поездкок с ожидающим шаттом на текущем маршруте, учитываем кол-во желаемых мест
                if trip_id is None:
                    # Содание поездки
                    trip_id = await crimgo_db.create_trip(state)   
                    # Если успешно создана
                    if (trip_id is False):
                        msg = await callback.message.answer(passenger_text.service_temporary_unavailable)
                        await state.finish()
                    else:
                        await passenger_helper.save_data_to_state(trip_id, 'trip_id', state)
                        # Считаем время приблизительное подбора
                        aprox_time = await crimgo_db.calculate_raw_pickup_time(state)
                        seat = await passenger_helper.get_data_from_state('seat', state)
                        total_amount = round(await passenger_helper.get_data_from_state('total_amount', state))
                        # Сохраняет aprox_time в state
                        await passenger_helper.save_data_to_state(aprox_time, 'aprox_time', state)
                        # Отвечаем пассмажиру с приблизительным временем посадки
                        msg = await callback.message.answer(passenger_text.approx_pickup_time.format(time = aprox_time, seat = seat, total_amount= total_amount), reply_markup=kb_payment_type)
                        # Сохраняем ИД сообщения
                        await passenger_helper.update_msg_list([msg.message_id], state)
                # Если найдена поездка которую можно дополнить пассажирами
                else:
                    await passenger_helper.save_data_to_state(trip_id, 'trip_id', state)
                    # Считаем время приблизительное подбора
                    aprox_time = await crimgo_db.calculate_raw_pickup_time(state)
                    seat = await passenger_helper.get_data_from_state('seat', state)
                    total_amount = round(await passenger_helper.get_data_from_state('total_amount', state))
                    # Сохраняет aprox_time в state
                    await passenger_helper.save_data_to_state(aprox_time, 'aprox_time', state)
                    # Отвечаем пассмажиру с приблизительным временем посадки
                    msg = await callback.message.answer(passenger_text.approx_pickup_time.format(time = aprox_time, seat = seat, total_amount= total_amount), reply_markup=kb_payment_type)
                    # Сохраняем ИД сообщения
                    await passenger_helper.update_msg_list([msg.message_id], state)
            # в противном случае кидаем сообщение что сервис не доступен
            else:
                await passenger_helper.notify_service_unavailable(callback, state)
        else:
            await FSMOrder_trip.s_geolocation.set()
            async with state.proxy() as data:
                route = data['route']
            if route == 'К морю':
                msg = await callback.message.answer(passenger_text.to_choose_pickup_point, reply_markup=kb_geoposition)
            if route == 'От моря':
                msg = await callback.message.answer(passenger_text.to_choose_drop_point, reply_markup=kb_geoposition)
            async with state.proxy() as data:
                # Удаление предыдущего сообщения
                await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
                await passenger_helper.remove_messages(callback.from_user.id, data['msg_location'])
            # Сохраняем ИД сообщения
            await passenger_helper.update_msg_list([msg.message_id], state)
    else:
        async with state.proxy() as data:
            # Удаление предыдущего сообщения
            await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
            await passenger_helper.remove_messages(callback.from_user.id, data['msg_location'])
        await state.finish()
        await callback.message.answer(passenger_text.order_canceled, reply_markup=kb_pass)

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, menu_trip_confirm.__name__ + ': ' + callback.data)

# # Быбор способа оплаты
# async def menu_payment_type(callback: types.CallbackQuery, state: FSMContext):
#     if callback.data == 'Ок':
#         await FSMOrder_trip.s_payment_type.set()
#         async with state.proxy() as data:
#             data['trip_confirm'] = callback.data
#             # Удаление предыдущего сообщения
#             await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
#         msg = await callback.message.answer(passenger_text.pre_order.format(seat = data['seat'], total_amount= data['total_amount']), reply_markup=kb_payment_type)
#         await passenger_helper.update_msg_list([msg.message_id], state)
#     else:
#         await crimgo_db.restore_booked_seats(state)
#         await callback.message.answer(passenger_text.order_canceled)
#         await state.finish()
#     await callback.answer()

# Обработка способа оплаты и выбор соот-го состояния
async def menu_handle_payment(callback: types.CallbackQuery, state: FSMContext):          
    await callback.answer()
    # Оплата наличкой
    if callback.data == 'Наличкой водителю':
        # Добавляем пустые поля для оплаты наличкой
        async with state.proxy() as data:
            data['payment_type'] = 'cash'
            data['telegram_payment_charge_id'] = 'null'
            data['provider_payment_charge_id'] = 'null'
            data['otp'] = randrange(1000, 9999, 1)
            data['pass_id'] = callback.from_user.id
            # Удаление предыдущего сообщения
            await passenger_helper.remove_messages(callback.from_user.id, data['msg'])
        
        payment_id = await crimgo_db.successful_payment(state)
        total_amount = round(await crimgo_db.get_total_amount(payment_id))
        driver_name = await crimgo_db.get_driver_name_by_trip(data['trip_id'])
        cancel_keyboard = await get_cancel_keyboard(payment_id)
        msg = await callback.message.answer(passenger_text.check_order.format(total_amount=total_amount, otp=data['otp'], aprox_time = data['aprox_time'], driver_name = driver_name, pickup_point = data['pickup_point'], drop_point = data['drop_point']), reply_markup = cancel_keyboard)
        # Запись в БД данных для пуша пассажиру
        await crimgo_db.save_pass_message_id(callback.from_user.id, msg.message_id, msg.chat.id)
        # Проверка нужен ли пуш, если None, route ближейшего шаттла не равно data['route'] билета
        is_push_needed = await crimgo_db.is_push_needed(state)
        # Создание билета в БД       
        ticket_id = await crimgo_db.create_ticket(state, payment_id)
        if is_push_needed:
            # Пересмотр статуса поездки
            await crimgo_db.trip_status_review(state)
        # Информация о чате для пуша водителю
        driver_chat_id = await crimgo_db.get_driver_chat_id(state)
        
        # Пуш или сохранения сообщение водителя
        if is_push_needed:
            await push_messages(callback.from_user.id, state, ticket_id, driver_chat_id)
        else:
            # Сохраняем сообщение в базу
            if data['route'] == 'К морю':
                text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['pickup_point'], pickup_time = data['aprox_time'], seats = data['seat'])    
            if data['route'] == 'От моря':
                ticket_dp_time = await crimgo_db.ticket_dp_time(ticket_id)
                text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['drop_point'], pickup_time = (ticket_dp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
                #msg = await bot.send_message(driver_chat_id[0], text, reply_markup=kb_start_trip)
            # await crimgo_db.set_shuttle_message_id(msg.message_id, state)
            await crimgo_db.save_message_id_and_text(state, text)

        await state.finish()

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, menu_handle_payment.__name__ + ': ' + callback.data)

# Пуш водителю или пасажару
async def push_messages(user_id, state, ticket_id, driver_chat_id):
    async with state.proxy() as data:
        # Если чат ID не пуст
        if driver_chat_id[0] is not None:
            is_first_ticket = await crimgo_db.is_first_ticket(state)
            # Первый билет в рейсе
            if is_first_ticket is True:
                trip_details = await crimgo_db.trip_details(state)
                await bot.send_message(driver_chat_id[0], driver_text.trip_assigned.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M")), reply_markup=kb_driver_shift)
                if data['route'] == 'К морю':
                    text = driver_text.new_ticket_assigned.format(pickup_point = data['pickup_point'], pickup_time = data['aprox_time'], seats = data['seat'])    
                if data['route'] == 'От моря':
                    ticket_dp_time = await crimgo_db.ticket_dp_time(ticket_id)
                    text = driver_text.new_ticket_assigned.format(pickup_point = data['drop_point'], pickup_time = (ticket_dp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
                # msg = await bot.send_message(driver_chat_id[0], text, reply_markup=kb_start_trip)
                # В callback вставляю id поездки
                msg = await bot.send_message(driver_chat_id[0], text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text = 'Начать рейс', callback_data='Начать рейс {trip_id}'.format(trip_id=data['trip_id'])))) 
                await crimgo_db.set_shuttle_message_id(msg.message_id, state)
                await crimgo_db.save_message_id_and_text(state, text)

                # Если статус поездки поменялся 
                # Проверка статуса рейса и отправка нотификации водителю и пассажиру об изменении начала рейса
                status = await crimgo_db.trip_status(state)
                if status == 'scheduled':
                    start_time = await crimgo_db.get_trip_start_time_by_id(state)
                    # Если к морю то собираем собщения через pickup_point 
                    if data['route'] == 'К морю':
                        tickets = await crimgo_db.get_dict_of_tickets_by_trip(state)
                        text = driver_text.trip_start_time_changed.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in tickets:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                    # Если от моря то собираем сообщения через drop_point
                    if data['route'] == 'От моря':
                        drop_point = await crimgo_db.get_dict_of_drop_points_by_trip(state)
                        text = driver_text.trip_start_time_changed.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in drop_point:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                   
                    # Получаем обновленные чат ИД
                    driver_chat_id = await crimgo_db.get_driver_chat_id(state)

                    # Редактируем последее сообщение(удаляем/отправляем и сохраняем)
                    await bot.delete_message(chat_id = driver_chat_id[0], message_id = driver_chat_id[1])
                    updated_msg = await bot.send_message(chat_id = driver_chat_id[0], text = text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text = 'Начать рейс', callback_data='Начать рейс {trip_id}'.format(trip_id=data['trip_id']))))
                    await crimgo_db.set_shuttle_message_id(updated_msg.message_id, state)
                    await crimgo_db.save_message_id_and_text(state, text)

                    # Редактируем сообщения пользователей
                    pass_trip_details = await crimgo_db.get_pass_trip_details(state, 'active')
                    driver_name = await crimgo_db.get_driver_name_by_trip(data['trip_id'])
                    drop_point = await crimgo_db.get_drop_point_by_trip(data['trip_id'], ticket_id)
                    total_amount = round(await crimgo_db.get_total_amount_by_trip(data['trip_id'], ticket_id))
                    for push in pass_trip_details:
                        try: 
                            text = passenger_text.new_pickup_point_time.format(time = (push[2]).strftime("%H:%M"), pickup_point = push[3], otp = push[4], driver_name = driver_name, drop_point = drop_point, total_amount = total_amount)
                            await bot.delete_message(chat_id = push[0], message_id = push[1])
                            updated_msg = await bot.send_message(chat_id = push[0], text = text, reply_markup = await get_cancel_keyboard(push[5]))
                            # Запись в БД данных для пуша пассажиру
                            await crimgo_db.save_pass_message_id(user_id, updated_msg.message_id, updated_msg.chat.id)
                        except (Exception) as error:
                            logging.info(msg = error, stack_info = False)

            else:
                # Нотификация водителя о новых билетах
                tmp = await crimgo_db.get_message_id_and_text(state)
                if tmp is None: 
                    tmp = ''
                if data['route'] == 'К морю':
                    text = tmp + '\nОст. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['pickup_point'], pickup_time = data['aprox_time'], seats = data['seat'])    
                if data['route'] == 'От моря':
                    ticket_dp_time = await crimgo_db.ticket_dp_time(ticket_id)
                    text = tmp + '\nОст. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['drop_point'], pickup_time = (ticket_dp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
                try:
                    await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text = 'Начать рейс', callback_data='Начать рейс {trip_id}'.format(trip_id=data['trip_id']))))
                except (Exception) as error:
                    logging.info(msg = error, stack_info = False)
                
                await crimgo_db.save_message_id_and_text(state, text)
                # Проверка статуса рейса и отправка нотификации водителю и пассажиру об изменении начала рейса
                status = await crimgo_db.trip_status(state)
                if status == 'scheduled':
                    start_time = await crimgo_db.get_trip_start_time_by_id(state)
                    # Если к морю то собираем собщения через pickup_point 
                    if data['route'] == 'К морю':
                        tickets = await crimgo_db.get_dict_of_tickets_by_trip(state)
                        text = driver_text.trip_start_time_changed.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in tickets:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                    # Если от моря то собираем сообщения через drop_point
                    if data['route'] == 'От моря':
                        drop_point = await crimgo_db.get_dict_of_drop_points_by_trip(state)
                        text = driver_text.trip_start_time_changed.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in drop_point:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                   
                    # Редактируем последее сообщение
                    await bot.delete_message(chat_id = driver_chat_id[0], message_id = driver_chat_id[1])
                    updated_msg = await bot.send_message(chat_id = driver_chat_id[0], text = text, reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(text = 'Начать рейс', callback_data='Начать рейс {trip_id}'.format(trip_id=data['trip_id']))))
                    await crimgo_db.set_shuttle_message_id(updated_msg.message_id, state)
                    await crimgo_db.save_message_id_and_text(state, text)

                    # Редактируем сообщения пользователей
                    pass_trip_details = await crimgo_db.get_pass_trip_details(state, 'active')
                    driver_name = await crimgo_db.get_driver_name_by_trip(data['trip_id'])
                    drop_point = await crimgo_db.get_drop_point_by_trip(data['trip_id'], ticket_id)
                    total_amount = round(await crimgo_db.get_total_amount_by_trip(data['trip_id'], ticket_id))
                    for push in pass_trip_details:
                        try: 
                            text = passenger_text.new_pickup_point_time.format(time = (push[2]).strftime("%H:%M"), pickup_point = push[3], otp = push[4], driver_name = driver_name, drop_point = drop_point, total_amount = total_amount)
                            await bot.delete_message(chat_id = push[0], message_id = push[1])
                            updated_msg = await bot.send_message(chat_id = push[0], text = text, reply_markup = await get_cancel_keyboard(push[5]))
                            # Запись в БД данных для пуша пассажиру
                            await crimgo_db.save_pass_message_id(user_id, updated_msg.message_id, updated_msg.chat.id)
                        except (Exception) as error:
                            logging.info(msg = error, stack_info = False)

async def cmd_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    # Записать code билета в FSM
    await passenger_helper.save_data_to_state(callback.data.replace('cancel ', ''), 'payment_id', state)

    # Выбор Причины отказа 
    await callback.message.reply(passenger_text.cancel_reason_options, reply_markup = kb_cancel_reason)
    
    # Перейти в статут ожидания ответа
    await FSMCancel_order.s_cancel_order.set()

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, cmd_cancel_order.__name__ + ': ' + callback.data)

async def cmd_cancel_reason(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    # Сохраняем причину отказа и ИД пассижира в state
    await passenger_helper.save_data_to_state(callback.data.replace('cancel_reason ', ''), 'cancel_reason', state)
    await passenger_helper.save_data_to_state(callback.from_user.id, 'pass_id', state)
    # Записать ИД поедзки, ИД пассажира номер билета и причину отказа в БД
    await crimgo_db.save_cancel_details(state)
    # Меняем статус билета
    await crimgo_db.update_ticket_status(state)
    # Благодарим за пояснение причины отказа
    await callback.message.reply(passenger_text.order_canceled_with_reason, reply_markup=kb_pass)
    # Оповестить водителя?
    
    await state.finish()

    # Сохраняем действие пассажира
    await passenger_helper.save_passenger_action(callback.from_user.id, cmd_cancel_reason.__name__ + ': ' + callback.data)

def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(commands_start, commands=['start', 'help'])
    dp.register_message_handler(get_contact, content_types=['contact'])
    dp.register_message_handler(cmd_order_trip, Text(equals='Заказать прогулку', ignore_case=True))
    dp.register_message_handler(cmd_order_trip, Text(equals='Заказать поездку', ignore_case=True))
    dp.register_message_handler(cmd_contact_with_support, Text(equals='Чат поддержки', ignore_case=True))
    dp.register_callback_query_handler(menu_route_selection, state=FSMOrder_trip.s_route_selection)
    dp.register_callback_query_handler(menu_seat_selection, state=FSMOrder_trip.s_seat_selection)
    dp.register_callback_query_handler(menu_pp_confirm, state=FSMOrder_trip.s_geolocation)
    dp.register_callback_query_handler(menu_trip_confirm, state=FSMOrder_trip.s_pp_confirmation)
    # dp.register_callback_query_handler(menu_payment_type, state=FSMOrder_trip.s_trip_confirmation)
    dp.register_callback_query_handler(menu_handle_payment, state=FSMOrder_trip.s_payment_type)
    dp.register_callback_query_handler(cmd_cancel_order, Text(startswith='cancel ', ignore_case=True))
    dp.register_callback_query_handler(cmd_cancel_reason, state=FSMCancel_order.s_cancel_order)
