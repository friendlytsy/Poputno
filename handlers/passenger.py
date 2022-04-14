from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from datetime import datetime, timedelta

from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_pass, kb_driver, kb_path, kb_seat, kb_geoposition, kb_pp_confirmation, kb_trip_confirmation, kb_payment_type, kb_driver_shift, kb_generic_start, kb_start_trip, kb_onboarding_trip

from random import randrange

from config import config

# Машина состояний для покупки билета
class FSMOrder_trip(StatesGroup):
    s_route_selection = State()
    s_seat_selection = State()
    s_geolocation = State()
    s_pp_confirmation = State()
    s_trip_confirmation = State()
    s_payment_type = State()

# Машина состояний для покупки абонемента
class FSMOrder_subscribe(StatesGroup):
    s_payment_subscribe = State()

# Старт и онбординг
async def commands_start(message: types.Message):
    # Проверка на водителя
    if (await crimgo_db.is_driver_exist(message) is not None):
        # Если валиден
        if (await crimgo_db.is_driver_valid(message) is True):
            # То проверка на смену
            if (await crimgo_db.is_on_shift(message)): 
                await message.reply('Добрый день', reply_markup=kb_driver_shift)
            else: 
                await message.reply('Добрый день', reply_markup=kb_driver)
        
    # Проверка на пользователя
    else:
        if await crimgo_db.is_exist(message) is True:
            await message.reply('Здравствуйте 👋\nЭто бот CrimGo. Я помогу вам заказать поездку. Для продолжения использования сервиса прочитайте пользовательское соглашение и инструкцию.', reply_markup=kb_pass)
        if await crimgo_db.is_exist(message) is False:          
            await message.reply('Здравствуйте 👋\nЭто бот CrimGo. Я помогу вам заказать поездку. Для продолжения использования сервиса прочитайте пользовательское соглашение и инструкцию.', reply_markup=kb_generic_start)
        await message.answer('https://teletype.in/@crimgo.ru/3lGEr343Vj2')

# Обработка контакта
async def get_contact(message: types.Message):
    # If not exist, create a user
    await crimgo_db.create_user(message)
    await message.answer('Спасибо', reply_markup=kb_pass)

# Чат поддержки
async def cmd_contact_with_support(message: types.Message):
    #await bot.send_contact(chat_id = message.from_user.id, phone_number = '+7 978 173-26-90', first_name = 'Администрация CrimGo')
    await bot.send_message(chat_id=message.from_user.id, text="<a href='https://t.me/crimgoru'>Администрация CrimGo</a>", parse_mode="HTML")

# Покупка билета
async def cmd_order_trip(message: types.Message, state: FSMContext):
    await FSMOrder_trip.s_route_selection.set()
    msg = await message.answer('Среднее время ожидания начала поездки 20 минут. Более точное время будет известно позже.', reply_markup=kb_path) 
    # Сохраняем ИД сообщения
    await update_msg_list([msg.message_id], state)

# Выбор маршрута
async def menu_route_selection(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Отмена':
        await FSMOrder_trip.s_seat_selection.set()
        async with state.proxy() as data:
                data['route'] = callback.data
                if callback.data == 'К морю':
                    data['opposite'] = 'От моря'
                else: data['opposite'] = 'К морю'
                # # Удаление предыдущего сообщения
                await remove_messages(callback.from_user.id, data['msg'])

        msg = await callback.message.answer('Выберете кол-во мест', reply_markup=kb_seat)
        # Сохраняем ИД сообщения
        await update_msg_list([msg.message_id], state)
        await callback.answer()
    else:
        # Удаление предыдущего сообщения
        async with state.proxy() as data:
            await remove_messages(callback.from_user.id, data['msg'])

        await callback.answer()
        await state.finish()
        await callback.message.answer('Заказ отменен', reply_markup=kb_pass)

# Выбор кол-ва мест
async def menu_seat_selection(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Отмена':
        await FSMOrder_trip.s_geolocation.set()
        async with state.proxy() as data:
                data['seat'] = callback.data
                # Удаление предыдущего сообщения
                await remove_messages(callback.from_user.id, data['msg'])
        msg_seats = await callback.message.answer(f'Вы выбрали {callback.data} мест(а)')
        if data['route'] == 'К морю':
            msg = await callback.message.answer('Выберите наиболее  близкое к вам место посадки', reply_markup=kb_geoposition)
        if data['route'] == 'От моря':
            msg = await callback.message.answer('Выберите ближайшую остановку к Вашему дому', reply_markup=kb_geoposition)
        # Сохраняем ИД сообщения
        await update_msg_list([msg.message_id, msg_seats.message_id], state)
        await callback.answer()
    else:
        # Удаление предыдущего сообщения
        async with state.proxy() as data:
            await remove_messages(callback.from_user.id, data['msg'])
        await callback.answer()
        await state.finish()
        await callback.message.answer('Заказ отменен', reply_markup=kb_pass)    

# Геопозиция
async def menu_pp_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Отмена':
        if callback.data != 'Назад':
            await FSMOrder_trip.s_pp_confirmation.set()
            async with state.proxy() as data:
                # Удаление предыдущего сообщения
                await remove_messages(callback.from_user.id, data['msg'])
                # Если маршрут к морю
                if data['route'] == 'К морю':
                    data['pickup_point'] = callback.data
                    data['drop_point'] = 'Успенская церковь'
                # Если от моря
                if data['route'] == 'От моря':
                    data['pickup_point'] = 'Успенская церковь'
                    data['drop_point'] = callback.data
            pp_location = await crimgo_db.get_pp_location(callback.data, data['route'])
            msg_location = await bot.send_location(chat_id=callback.from_user.id, latitude=pp_location[0], longitude=pp_location[1])
            async with state.proxy() as data:
                data['msg_location'] = [msg_location.message_id]
            if data['route'] == 'К морю':
                msg = await callback.message.answer('Вы выбрали остановку {pp}, нажмите подтвердить'.format(pp = data['pickup_point']), reply_markup=kb_pp_confirmation)
            if data['route'] == 'От моря':
                msg = await callback.message.answer('Вы выбрали остановку {dp}, нажмите подтвердить'.format(dp = data['drop_point']), reply_markup=kb_pp_confirmation)
            # Сохраняем ИД сообщения
            await update_msg_list([msg.message_id], state)
        else:
            async with state.proxy() as data:
                # Удаление предыдущего сообщения
                await remove_messages(callback.from_user.id, data['msg'])
            await FSMOrder_trip.s_seat_selection.set()
            msg = await callback.message.answer('Выберете кол-во мест', reply_markup=kb_seat)
            # Сохраняем ИД сообщения
            await update_msg_list([msg.message_id], state)
        await callback.answer()
    else:
        # Удаление предыдущего сообщения
        async with state.proxy() as data:
            await remove_messages(callback.from_user.id, data['msg'])
        await callback.answer()
        await state.finish()
        await callback.message.answer('Заказ отменен', reply_markup=kb_pass)

# Выбор остановки
async def menu_trip_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Отмена':
        if callback.data != 'Повторить':
            await FSMOrder_trip.s_trip_confirmation.set()
            async with state.proxy() as data:
                    data['pp_confirm'] = callback.data
                    # Ищем цена билета и считаем итог
                    price = await crimgo_db.get_pickup_point_price(data['pickup_point'], data['route'])
                    if price is not None: 
                        data['total_amount'] = int(data['seat'])*price
                    # Удаление предыдущего сообщения
                    await remove_messages(callback.from_user.id, data['msg'])
            #########
            #########
            # если нет trip с указаным маршрутом, создаем его
            trip_id = await crimgo_db.is_trip_with_route(state)
            if (trip_id is None):
                trip_id = await crimgo_db.create_trip(state)
                # Определить 
                if (trip_id is False):
                    msg = await callback.message.answer('Сервис временно не доступен, попробуйте позже')
                    # Сохраняем ИД сообщения
                    await update_msg_list([msg.message_id], state)
                    await callback.answer()
                    await state.finish()
                else:
                    async with state.proxy() as data:
                        data['trip_id'] = trip_id 
            else:
                async with state.proxy() as data:
                    data['trip_id'] = trip_id 
            # Проверка нужен ли пуш, если None, route ближейшего шаттла не равно data['route'] билета
            is_push_needed = await crimgo_db.is_push_needed(state)
            if is_push_needed is None:
                # Обновляем время в поездке, прибавялем 30 минуту
                ADD_DELTA_TIME = timedelta(minutes = 30)
                await crimgo_db.update_trip_set_time_delta(state, ADD_DELTA_TIME)

            # Проверка на кол-во доступных мест
            if (await crimgo_db.seat_availability(state)) is True:
                aprox_time = await crimgo_db.calculate_raw_pickup_time(state)
                async with state.proxy() as data:
                    data['aprox_time'] = aprox_time
                msg = await callback.message.answer('Ориентировочное время посадки в шаттл - {time}. Нажмите ОК для перехода к оплате'.format(time = aprox_time), reply_markup=kb_trip_confirmation)
                # Сохраняем ИД сообщения
                await update_msg_list([msg.message_id], state)
                await callback.answer()
            else:
#               if trip_id is None or False:
                await callback.message.answer('К сожалению нет такого кол-ва доступных мест в ближайшем рейсе.', reply_markup=kb_pass)
                # Сохраняем ИД сообщения
                await update_msg_list([msg.message_id], state)
                await callback.answer()
                await state.finish()
        else:
            await FSMOrder_trip.s_geolocation.set()
            await callback.answer()
            async with state.proxy() as data:
                route = data['route']
            if route == 'К морю':
                msg = await callback.message.answer('Выберите наиболее  близкое к вам место посадки', reply_markup=kb_geoposition)
            if route == 'От моря':
                msg = await callback.message.answer('Выберите ближайшую остановку к Вашему дому', reply_markup=kb_geoposition)
            async with state.proxy() as data:
                # Удаление предыдущего сообщения
                await remove_messages(callback.from_user.id, data['msg'])
                await remove_messages(callback.from_user.id, data['msg_location'])
            # Сохраняем ИД сообщения
            await update_msg_list([msg.message_id], state)
    else:
        async with state.proxy() as data:
            # Удаление предыдущего сообщения
            await remove_messages(callback.from_user.id, data['msg'])
            await remove_messages(callback.from_user.id, data['msg_location'])
        await callback.answer()
        await state.finish()
        await callback.message.answer('Заказ отменен', reply_markup=kb_pass)

# Быбор способа оплаты
async def menu_payment_type(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'Ок':
        await FSMOrder_trip.s_payment_type.set()
        async with state.proxy() as data:
            data['trip_confirm'] = callback.data
            # Удаление предыдущего сообщения
            await remove_messages(callback.from_user.id, data['msg'])
        msg = await callback.message.answer('Вы заказали {seat} мест(а), стоимость {total_amount} рублей'.format(seat = data['seat'], total_amount= data['total_amount']), reply_markup=kb_payment_type)
        await update_msg_list([msg.message_id], state)
    else:
        await crimgo_db.restore_booked_seats(state)
        await callback.message.answer('Заказ отменен')
        await state.finish()
    await callback.answer()

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
            await remove_messages(callback.from_user.id, data['msg'])
        
        payment_id = await crimgo_db.successful_payment(state)
        total_amount = await crimgo_db.get_total_amount(payment_id)
        msg = await callback.message.answer('Оплатите водителю сумму `{total_amount}` РУБ при посадке! Приятного пользования сервисом CrimGo. Код для посадки `{otp}`'.format(total_amount=total_amount, otp=data['otp']))
        # Запись в БД данных для пуша пассажиру
        await crimgo_db.save_pass_message_id(callback.from_user.id, msg.message_id, msg.chat.id)
        # Проверка нужен ли пуш, если None, route ближейшего шаттла не равно data['route'] билета
        is_push_needed = await crimgo_db.is_push_needed(state)
        # Создание билета в БД       
        ticket_id = await crimgo_db.create_ticket(state, payment_id)
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

# Пуш водителю или пасажару
async def push_messages(user_id, state, ticket_id, driver_chat_id):
    async with state.proxy() as data:
            # Если чат ID не пуст
        if driver_chat_id[0] is not None:
            is_first_ticket = await crimgo_db.is_first_ticket(state)
            # Первый билет в рейсе
            if is_first_ticket is True:
                trip_details = await crimgo_db.trip_details(state)
                await bot.send_message(driver_chat_id[0], 'Поздравляем, Вам назначен рейс {trip_id} "{route}". Старт в {start_time}'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M")), reply_markup=kb_driver_shift)
                if data['route'] == 'К морю':
                    text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['pickup_point'], pickup_time = data['aprox_time'], seats = data['seat'])    
                if data['route'] == 'От моря':
                    ticket_dp_time = await crimgo_db.ticket_dp_time(ticket_id)
                    text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['drop_point'], pickup_time = (ticket_dp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
                msg = await bot.send_message(driver_chat_id[0], text, reply_markup=kb_start_trip)
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
                        text = 'Внимание, время начало рейса обновлено: {start_time}\n'.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in tickets:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                    # Если от моря то собираем сообщения через drop_point
                    if data['route'] == 'От моря':
                        drop_point = await crimgo_db.get_dict_of_drop_points_by_trip(state)
                        text = 'Внимание, время начало рейса обновлено: {start_time}\n'.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in drop_point:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                   
                    # Получаем обновленные чат ИД
                    driver_chat_id = await crimgo_db.get_driver_chat_id(state)

                    # Редактируем последее сообщение(удаляем/отправляем и сохраняем)
                    # await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
                    await bot.delete_message(chat_id = driver_chat_id[0], message_id = driver_chat_id[1])
                    updated_msg = bot.send_message(chat_id = driver_chat_id[0], text = text, reply_markup = kb_start_trip)
                    await crimgo_db.set_shuttle_message_id(updated_msg.message_id, state)
                    await crimgo_db.save_message_id_and_text(state, text)


                    # Редактируем сообщения пользователей
                    pass_trip_details = await crimgo_db.get_pass_trip_details(state)
                    for push in pass_trip_details:
                        try: 
                            text = 'Внимание, новое время посадки: {time}\nМесто посадки: {pp}\nКод посадки: {otp}'.format(time = (push[2]).strftime("%H:%M"), pp = push[3], otp = push[4])
                            await bot.delete_message(chat_id = push[0], message_id = push[1])
                            updated_msg = await bot.send_message(chat_id = push[0], text = text, reply_markup = None)
                            # Запись в БД данных для пуша пассажиру
                            await crimgo_db.save_pass_message_id(user_id, updated_msg.message_id, updated_msg.chat.id)
                            # await bot.edit_message_text(chat_id = push[0], message_id = push[1], text = text, reply_markup=None)
                        except (Exception) as error:
                            print("Ошибка при отправке сообщения пользователю: ", error)
                        # text = 'Внимание, новое время посадки: {time}\nМесто посадки: {pp}\nКод посадки: {otp}'.format(time = (push[2]).strftime("%H:%M"), pp = push[3], otp = push[4])
                        # await bot.edit_message_text(chat_id = push[0], message_id = push[1], text = text, reply_markup=None)                

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
                await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
                await crimgo_db.save_message_id_and_text(state, text)
                # Проверка статуса рейса и отправка нотификации водителю и пассажиру об изменении начала рейса
                status = await crimgo_db.trip_status(state)
                if status == 'scheduled':
                    start_time = await crimgo_db.get_trip_start_time_by_id(state)
                    # Если к морю то собираем собщения через pickup_point 
                    if data['route'] == 'К морю':
                        tickets = await crimgo_db.get_dict_of_tickets_by_trip(state)
                        text = 'Внимание, время начало рейса обновлено: {start_time}\n'.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in tickets:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                    # Если от моря то собираем сообщения через drop_point
                    if data['route'] == 'От моря':
                        drop_point = await crimgo_db.get_dict_of_drop_points_by_trip(state)
                        text = 'Внимание, время начало рейса обновлено: {start_time}\n'.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                        # Собираем остановки в одно сообщение
                        for i in drop_point:
                            text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                   
                    # Редактируем последее сообщение
                    # await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
                    await bot.delete_message(chat_id = driver_chat_id[0], message_id = driver_chat_id[1])
                    updated_msg = await bot.send_message(chat_id = driver_chat_id[0], text = text, reply_markup = kb_start_trip)
                    await crimgo_db.set_shuttle_message_id(updated_msg.message_id, state)
                    await crimgo_db.save_message_id_and_text(state, text)

                    # Редактируем сообщения пользователей
                    pass_trip_details = await crimgo_db.get_pass_trip_details(state)
                    for push in pass_trip_details:
                        try: 
                            text = 'Внимание, новое время посадки: {time}\nМесто посадки: {pp}\nКод посадки: {otp}'.format(time = (push[2]).strftime("%H:%M"), pp = push[3], otp = push[4])
                            await bot.delete_message(chat_id = push[0], message_id = push[1])
                            updated_msg = await bot.send_message(chat_id = push[0], text = text, reply_markup = None)
                            # Запись в БД данных для пуша пассажиру
                            await crimgo_db.save_pass_message_id(user_id, updated_msg.message_id, updated_msg.chat.id)
                            # await bot.edit_message_text(chat_id = push[0], message_id = push[1], text = text, reply_markup=None)
                        except (Exception) as error:
                            print("Ошибка при отправке сообщения пользователю: ", error)

# Удаления сообщений в списке msg_id_list
async def remove_messages(chat_id, msg_id_list):
    for msg in msg_id_list:
        await bot.delete_message(chat_id=chat_id, message_id=msg)

# Добавления сообщений в data['msg']
async def update_msg_list(msg_id_list, state: FSMContext):
    async with state.proxy() as data:
        # Пустой лист
        msg_list = []
        # Добавляем ИД в список
        msg_list.extend(msg_id_list)
        data['msg'] = msg_list

def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(commands_start, commands=['start', 'help'])
    dp.register_message_handler(get_contact, content_types=['contact'])
    dp.register_message_handler(cmd_order_trip, Text(equals='Заказать поездку', ignore_case=True))
    dp.register_message_handler(cmd_contact_with_support, Text(equals='Чат поддержки', ignore_case=True))
    dp.register_callback_query_handler(menu_route_selection, state=FSMOrder_trip.s_route_selection)
    dp.register_callback_query_handler(menu_seat_selection, state=FSMOrder_trip.s_seat_selection)
    dp.register_callback_query_handler(menu_pp_confirm, state=FSMOrder_trip.s_geolocation)
    dp.register_callback_query_handler(menu_trip_confirm, state=FSMOrder_trip.s_pp_confirmation)
    dp.register_callback_query_handler(menu_payment_type, state=FSMOrder_trip.s_trip_confirmation)
    dp.register_callback_query_handler(menu_handle_payment, state=FSMOrder_trip.s_payment_type)
