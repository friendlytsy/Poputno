from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from datetime import datetime, timedelta

from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_pass, kb_driver, kb_path, kb_seat, kb_geoposition, kb_pp_confirmation, kb_trip_confirmation, kb_payment_type, kb_driver_shift, kb_generic_start, kb_driver_verification


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
            await message.reply('На данный момент работает заказ одноразовой поездки от Моря и к Морю. А так же регистрация водителя и шаттла.', reply_markup=kb_pass)
        if await crimgo_db.is_exist(message) is False:          
            await message.reply('На данный момент работает заказ одноразовой поездки от Моря и к Морю. А так же регистрация водителя и шаттла. Как пользоваться сервисом', reply_markup=kb_generic_start)
        await message.answer('https://teletype.in/@crimgo.ru/l1stoFUEQqF')

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
    await message.answer('Среденее время ожидания начала поездки 20 минут. Более точное время будет известно позже.', reply_markup=kb_path) 

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
        await callback.message.answer('Выбирите наиболее  близкое к вам место посадки', reply_markup=kb_geoposition)
    if data['route'] == 'От моря':
        await callback.message.answer('Выбирите ближайшую остановку к Вашему дому', reply_markup=kb_geoposition)
    await callback.answer()

# Геопозиция
async def menu_pp_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data != 'Назад':
        await FSMOrder_trip.s_pp_confirmation.set()
        async with state.proxy() as data:
                data['geo'] = callback.data
        await callback.message.answer('Вы выбрали остановку {pp}, нажмите подтвердить'.format(pp = data['geo']), reply_markup=kb_pp_confirmation)
    else:
        await FSMOrder_trip.s_seat_selection.set()
        await callback.message.answer('Выберете кол-во мест', reply_markup=kb_seat)
    await callback.answer()

# Выбор остановки
async def menu_trip_confirm(callback: types.CallbackQuery, state: FSMContext):
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
        await callback.message.answer('Ориентировочное время посадки в шаттл - {time}. Нажмите ОК для перехода к оплате'.format(time = aprox_time), reply_markup=kb_trip_confirmation)
        await callback.answer()
    else:
        await callback.message.answer('К сожалению нет такого кол-ва доступных мест', reply_markup=kb_path)
        await callback.answer()
        await state.finish()

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
        await crimgo_db.create_ticket(state, payment_id)
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
    await crimgo_db.create_ticket(state, payment_id)
    await state.finish()

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