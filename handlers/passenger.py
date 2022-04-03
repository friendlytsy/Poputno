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
    await message.reply(message.text)

# Покупка абонемента
async def cmd_subscription(message: types.Message, state: FSMContext):
    await FSMOrder_subscribe.s_payment_subscribe.set()
    await message.answer('Покупка абонемента на 10 поездок.', reply_markup=kb_pass)
    async with state.proxy() as data:
            data['seat'] = '12'
            data['total_amount'] = '1000'
    await message.reply('Покупка абонемента') 
    if config.PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
                 await bot.send_message(message.chat.id, 'Тестовая покупа')

    await bot.send_invoice(message.chat.id,
                       title='Покупка обонемента',
                       description=('Покупка {seat} билета(ов)'.format(seat=data['seat'])),
                       provider_token=config.PAYMENTS_PROVIDER_TOKEN,
                       currency='rub',
                       photo_url=config.SHUTTLE_IMAGE_URL,
                       photo_height=512,  # !=0/None, иначе изображение не покажется
                       photo_width=512,
                       photo_size=512,
                       is_flexible=False,  # True если конечная цена зависит от способа доставки
                       prices=[types.LabeledPrice(label='Билет(ы) на шаттл', amount=(int(data['total_amount'])*100))],
                       start_parameter='shuttle-order-example',
                       payload='some-invoice-payload-for-our-internal-use'
                       )

@dp.pre_checkout_query_handler(lambda query: True, state=FSMOrder_subscribe.s_payment_subscribe)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT, state=FSMOrder_subscribe.s_payment_subscribe)
async def process_successful_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # Добавляем необходимые данные о платеже
        data['payment_type'] = 'card'
        data['total_amount'] = message.successful_payment.total_amount // 100
        data['telegram_payment_charge_id'] = message.successful_payment.telegram_payment_charge_id
        data['provider_payment_charge_id'] = message.successful_payment.provider_payment_charge_id
        data['pass_id'] = message.from_user.id
        
        # Сообщение пользователю
        await bot.send_message(
            message.chat.id,
            'Платеж на сумму `{total_amount} {currency}` совершен успешно! Приятного пользования сервисом CrimGo.'.format(
            total_amount=data['total_amount'],
            currency=message.successful_payment.currency
            )
        )
    # Запись в БД и завершение FSM    
    await crimgo_db.successful_payment(state)
    await state.finish()

# Покупка билета
async def cmd_order_trip(message: types.Message):
    await FSMOrder_trip.s_route_selection.set()
    await message.answer('Среднее время ожидания начала поездки 20 минут. Более точное время будет известно позже.', reply_markup=kb_path) 

# Выбор маршрута
async def menu_route_selection(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_seat_selection.set()
    async with state.proxy() as data:
            data['route'] = callback.data
    await callback.message.answer('Выберете кол-во мест', reply_markup=kb_seat)
    await callback.answer()


# Выбор кол-ва мест
async def menu_seat_selection(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_geolocation.set()
    async with state.proxy() as data:
            data['seat'] = callback.data
            data['total_amount'] = int(data['seat'])*100
    await callback.message.answer(f'Вы выбрали {callback.data} мест(а)')
    if data['route'] == 'К морю':
        await callback.message.answer('Выберите наиболее  близкое к вам место посадки', reply_markup=kb_geoposition)
    if data['route'] == 'От моря':
        await callback.message.answer('Выберите ближайшую остановку к Вашему дому', reply_markup=kb_geoposition)
    await callback.answer()

# Геопозиция
async def menu_pp_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Назад':
        await FSMOrder_trip.s_pp_confirmation.set()
        async with state.proxy() as data:
                data['geo'] = callback.data
        pp_location = await crimgo_db.get_pp_location(callback.data, data['route'])
        await bot.send_location(chat_id=callback.from_user.id, latitude=pp_location[0], longitude=pp_location[1])
        await callback.message.answer('Вы выбрали остановку {pp}, нажмите подтвердить'.format(pp = data['geo']), reply_markup=kb_pp_confirmation)
    else:
        await FSMOrder_trip.s_seat_selection.set()
        await callback.message.answer('Выберете кол-во мест', reply_markup=kb_seat)
    await callback.answer()

# Выбор остановки
async def menu_trip_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Повторить':
        await FSMOrder_trip.s_trip_confirmation.set()
        async with state.proxy() as data:
                data['pp_confirm'] = callback.data
        
        #########
        #########
        # если нет trip с указаным маршрутом, создаем его
        trip_id = await crimgo_db.is_trip_with_route(state)
        if (trip_id is None):
            trip_id = await crimgo_db.create_trip(state)
            if (trip_id is False):
                await callback.message.answer('Сервис временно не доступен, попробуйте позже')
                await callback.answer()
                await state.finish()
            else:
                async with state.proxy() as data:
                    data['trip_id'] = trip_id 
        else:
            async with state.proxy() as data:
                data['trip_id'] = trip_id 

        # Проверка на кол-во доступных мест
        if (await crimgo_db.seat_availability(state)) is True:
            aprox_time = await crimgo_db.calculate_raw_pickup_time(state)
            async with state.proxy() as data:
                data['aprox_time'] = aprox_time
            await callback.message.answer('Ориентировочное время посадки в шаттл - {time}. Нажмите ОК для перехода к оплате'.format(time = aprox_time), reply_markup=kb_trip_confirmation)
            await callback.answer()
        else:
            if trip_id is None or False:
                await callback.message.answer('К сожалению нет такого кол-ва доступных мест', reply_markup=kb_path)
            await callback.answer()
            await state.finish()
    else:
        await FSMOrder_trip.s_geolocation.set()
        await callback.answer()
        async with state.proxy() as data:
            route = data['route']
        if route == 'К морю':
            await callback.message.answer('Выбирите наиболее  близкое к вам место посадки', reply_markup=kb_geoposition)
        if route == 'От моря':
            await callback.message.answer('Выбирите ближайшую остановку к Вашему дому', reply_markup=kb_geoposition)

# Быбор способа оплаты
async def menu_payment_type(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'Ок':
        await FSMOrder_trip.s_payment_type.set()
        async with state.proxy() as data:
            data['trip_confirm'] = callback.data
        await callback.message.answer('Вы заказали {seat} мест(а), стоимость {total_amount} рублей'.format(seat = data['seat'], total_amount= data['total_amount']), reply_markup=kb_payment_type)
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

        payment_id = await crimgo_db.successful_payment(state)
        await callback.message.answer('Оплатите водителю сумму `{total_amount}` РУБ при посадке! Приятного пользования сервисом CrimGo. Код для посадки `{otp}`'.format(
            total_amount=int(data['seat'])*100, otp=data['otp']))
        # Создание билета в БД       
        ticket_id = await crimgo_db.create_ticket(state, payment_id)
        # Пересмотр статуса поездки
        await crimgo_db.trip_status_review(state)
        # Пуш водителю
        driver_chat_id = await crimgo_db.get_driver_chat_id(state)
        # Если чат ID не пуст
        if driver_chat_id[0] is not None:
            is_first_ticket = await crimgo_db.is_first_ticket(state)
            # Первый билет в рейсе
            if is_first_ticket is True:
                trip_details = await crimgo_db.trip_details(state)
                await bot.send_message(driver_chat_id[0], 'Поздравляем, Вам назначен рейс {trip_id} "{route}". Старт в {start_time}'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M")), reply_markup=kb_driver_shift)
                if data['route'] == 'К морю':
                    text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = data['aprox_time'], seats = data['seat'])    
                if data['route'] == 'От моря':
                    ticket_pp_time = await crimgo_db.ticket_pp_time(ticket_id)
                    text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = (ticket_pp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
                msg = await bot.send_message(driver_chat_id[0], text, reply_markup=kb_start_trip)
                await crimgo_db.set_shuttle_message_id(msg.message_id, state)
                await crimgo_db.save_message_id_and_text(state, text)
            else:
                # Нотификация водителя о новых билетах
                tmp = await crimgo_db.get_message_id_and_text(state)
                if data['route'] == 'К морю':
                    text = tmp + '\nОст. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = data['aprox_time'], seats = data['seat'])    
                if data['route'] == 'От моря':
                    ticket_pp_time = await crimgo_db.ticket_pp_time(ticket_id)
                    text = tmp + '\nОст. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = (ticket_pp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
                await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
                await crimgo_db.save_message_id_and_text(state, text)
                # Проверка статуса рейса и отправка нотификации водителю об изменении начала рейса
                status = await crimgo_db.trip_status(state)
                if status == 'scheduled':
                    start_time = await crimgo_db.get_trip_start_time_by_id(state)
                    tickets = await crimgo_db.get_dict_of_tickets_by_trip(state)
                    text = 'Внимание, время начало рейса обновлено: {start_time}\n'.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                    # Собираем остановки в одно сообщение
                    for i in tickets:
                        text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                    # Редактируем последее сообщение
                    await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
        
        await state.finish()

    # Оплата картой
    if callback.data =='Оплата картой':
        await cmd_card_payment(state, callback.message)

# Функция оплаты картой
async def cmd_card_payment(state: FSMContext, message: types.Message):
    async with state.proxy() as data:
            data['otp'] = randrange(1000, 9999, 1)

    await message.reply('Покупка билета') 
    if config.PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
                 await bot.send_message(message.chat.id, 'Тестовая покупа')

    await bot.send_invoice(message.chat.id,
                       title='Покупка билета',
                       description=('Покупка {seat} билета(ов)'.format(seat=data['seat'])),
                       provider_token=config.PAYMENTS_PROVIDER_TOKEN,
                       currency='rub',
                       photo_url=config.SHUTTLE_IMAGE_URL,
                       photo_height=512,  # !=0/None, иначе изображение не покажется
                       photo_width=512,
                       photo_size=512,
                       is_flexible=False,  # True если конечная цена зависит от способа доставки
                       prices=[types.LabeledPrice(label='Билет(ы) на шаттл', amount=(int(data['total_amount'])*100))],
                       start_parameter='shuttle-order-example',
                       payload='some-invoice-payload-for-our-internal-use'
                       )

@dp.pre_checkout_query_handler(lambda query: True, state=FSMOrder_trip.s_payment_type)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT, state=FSMOrder_trip.s_payment_type)
async def process_successful_payment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        # Добавляем необходимые данные о платеже
        data['payment_type'] = 'card'
        data['total_amount'] = message.successful_payment.total_amount // 100
        data['telegram_payment_charge_id'] = message.successful_payment.telegram_payment_charge_id
        data['provider_payment_charge_id'] = message.successful_payment.provider_payment_charge_id
        data['pass_id'] = message.from_user.id
        
        # Сообщение пользователю
        await bot.send_message(
            message.chat.id,
            'Платеж на сумму `{total_amount} {currency}` совершен успешно! Приятного пользования сервисом CrimGo. Код для посадки `{otp}`'.format(
            total_amount=data['total_amount'],
            currency=message.successful_payment.currency,
            otp=data['otp']
            )
        )
    # Запись в БД и завершение FSM    
    payment_id = await crimgo_db.successful_payment(state)
    ticket_id = await crimgo_db.create_ticket(state, payment_id)
    await crimgo_db.trip_status_review(state)


    ###########
    # Пуш водителю
    driver_chat_id = await crimgo_db.get_driver_chat_id(state)
    # Если чат ID не пуст
    if driver_chat_id[0] is not None:
        is_first_ticket = await crimgo_db.is_first_ticket(state)
        # Первый билет в рейсе
        if is_first_ticket is True:
            trip_details = await crimgo_db.trip_details(state)
            await bot.send_message(driver_chat_id[0], 'Поздравляем, Вам назначен рейс {trip_id} "{route}". Старт в {start_time}'.format(trip_id = trip_details[0], route = trip_details[1], start_time = (config.TIME_OFFSET + trip_details[2]).strftime("%H:%M")), reply_markup=kb_driver_shift)
            if data['route'] == 'К морю':
                text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = data['aprox_time'], seats = data['seat'])    
            if data['route'] == 'От моря':
                ticket_pp_time = await crimgo_db.ticket_pp_time(ticket_id)
                text = 'Ост. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = (ticket_pp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])    
            msg = await bot.send_message(driver_chat_id[0], text, reply_markup=kb_start_trip)
            await crimgo_db.set_shuttle_message_id(msg.message_id, state)
            await crimgo_db.save_message_id_and_text(state, text)
        else:
            # Нотификация водителя о новых билетах
            tmp = await crimgo_db.get_message_id_and_text(state)
            if data['route'] == 'К морю':
                text = tmp + '\nОст. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = data['aprox_time'], seats = data['seat'])
            if data['route'] == 'От моря':
                ticket_pp_time = await crimgo_db.ticket_pp_time(ticket_id)
                text = tmp + '\nОст. {pickup_point}, {pickup_time}, {seats}м'.format(pickup_point = data['geo'], pickup_time = (ticket_pp_time + config.TIME_OFFSET).strftime("%H:%M"), seats = data['seat'])
            await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
            await crimgo_db.save_message_id_and_text(state, text)
            # Проверка статуса рейса и отправка нотификации водителю об изменении начала рейса
            status = await crimgo_db.trip_status(state)
            if status == 'scheduled':
                start_time = await crimgo_db.get_trip_start_time_by_id(state)
                tickets = await crimgo_db.get_dict_of_tickets_by_trip(state)
                text = 'Внимание, время начало рейса обновлено: {start_time}\n'.format(start_time = (start_time + config.TIME_OFFSET).strftime("%H:%M"))
                # Собираем остановки в одно сообщение
                for i in tickets:
                    text = text + 'Ост. {pp}, {time}, {seats}м\n'.format(pp = i[0], time = (i[2] + config.TIME_OFFSET).strftime("%H:%M"), seats = i[1])
                # Редактируем последее сообщение
                await bot.edit_message_text(chat_id = driver_chat_id[0], message_id = driver_chat_id[1], text = text, reply_markup=kb_start_trip)
    ###########
    await state.finish()

#async def pp_recalcutation():
    # если мест осталось одно и меньше место

def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(commands_start, commands=['start', 'help'])
    dp.register_message_handler(get_contact, content_types=['contact'])
    dp.register_message_handler(cmd_order_trip, Text(equals='Заказать поездку', ignore_case=True))
    dp.register_message_handler(cmd_subscription, Text(equals='Купить абонемент', ignore_case=True))
    dp.register_message_handler(cmd_contact_with_support, Text(equals='Чат поддержки', ignore_case=True))
    dp.register_callback_query_handler(menu_route_selection, state=FSMOrder_trip.s_route_selection)
    dp.register_callback_query_handler(menu_seat_selection, state=FSMOrder_trip.s_seat_selection)
    dp.register_callback_query_handler(menu_pp_confirm, state=FSMOrder_trip.s_geolocation)
    dp.register_callback_query_handler(menu_trip_confirm, state=FSMOrder_trip.s_pp_confirmation)
    dp.register_callback_query_handler(menu_payment_type, state=FSMOrder_trip.s_trip_confirmation)
    dp.register_callback_query_handler(menu_handle_payment, state=FSMOrder_trip.s_payment_type)