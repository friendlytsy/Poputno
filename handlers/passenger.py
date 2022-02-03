from subprocess import call
from unittest import async_case
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_pass, kb_driver, kb_path, kb_seat, kb_geoposition, kb_pp_confirmation, kb_trip_confirmation, kb_payment_type

from random import randrange

from config import config

class FSMOrder_trip(StatesGroup):
    s_path_selection = State()
    s_seat_selection = State()
    s_geolocation = State()
    s_pp_confirmation = State()
    s_trip_confirmation = State()
    s_payment_type = State()
    s_card_type = State()
    s_cash_type = State()
    s_checkout_query = State()
    s_cash_canceled = State()
    s_successful_payment = State()

# Старт и онбординг
async def commands_start(message: types.Message):
    if (await crimgo_db.is_driver_exist(message) is not None):
        await message.reply('Добрый день', reply_markup=kb_driver)

    else:    
        await message.reply('Как пользоваться сервисом', reply_markup=kb_pass)
        # If not exist, create a user
        await crimgo_db.check_if_exist(message.from_user)
        await message.answer('https://teletype.in/@crimgo.ru/l1stoFUEQqF')

# Чат поддержки
async def cmd_contact_with_support(message:types.Message):
    await message.reply(message.text)

# Покупка абонемента
async def cmd_order_trip(message: types.Message):
    await FSMOrder_trip.s_path_selection.set()
    await message.answer('Среденее время ожидания начала поездки 20 минут. Более точное время будет известно позже.', reply_markup=kb_path) 

# Выбор маршрута
async def menu_path_selection(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_seat_selection.set()
    async with state.proxy() as data:
            data['path'] = callback.data
    await callback.message.answer('Выберете кол-во мест', reply_markup=kb_seat)
    await callback.answer()

# Выбор кол-ва мест
async def menu_seat_selection(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_geolocation.set()
    async with state.proxy() as data:
            data['seat'] = callback.data
    await callback.message.answer(f'Вы выбрали {callback.data} мест')
    await callback.message.answer('Поделитесь геопозицией чтобы мы выбрали наиболее  близкое к вам место посадки', reply_markup=kb_geoposition)
    await callback.answer()

# Геопозиция
async def menu_pp_confirm(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_pp_confirmation.set()
    async with state.proxy() as data:
            data['geo'] = callback.data
    await callback.message.answer('Ближайшая к вам остановка №3 - Х, нажмите подтвердить', reply_markup=kb_pp_confirmation)
    await callback.answer()

# Выбор остановки
async def menu_trip_confirm(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_trip_confirmation.set()
    async with state.proxy() as data:
            data['pp_confirm'] = callback.data
    await callback.message.answer('Х - ориентировочное время посадки в шаттл. Нажмите ОК для перехода к оплате', reply_markup=kb_trip_confirmation)
    await callback.answer()

# Быбор способа оплаты
async def menu_payment_type(callback: types.CallbackQuery, state: FSMContext):
    await FSMOrder_trip.s_payment_type.set()
    async with state.proxy() as data:
            data['trip_confirm'] = callback.data
            seats = data['seat']
    await callback.message.answer(f'Вы заказали {seats} мест, стоимость {int(seats)*100} рублей', reply_markup=kb_payment_type)
    await callback.answer()

# Обработка способа оплаты и выбор соот-го состояния
async def menu_handle_payment(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
            data['payment_type'] = callback.data
    if callback.data == 'Оплата картой':
        FSMOrder_trip.s_card_type
    if callback.data == 'Наличкой водителю':
        FSMOrder_trip.s_cash_type
    
# Оплата наличкой водителю 
# async def menu_cash_payment(callback: types.CallbackQuery, state: FSMContext):
#     await 


# Оплата картой
#

# # Покупка абонемента
# async def cmd_subscription(message: types.Message):
#     await message.reply('Покупка обонемента') 
#     if config.PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
#                  await bot.send_message(message.chat.id, 'Тестовая покупа обонемента')

#     await bot.send_invoice(message.chat.id,
#                        title='Покупка обонемента',
#                        description='Покупка обонемента на 12 поездок',
#                        provider_token=config.PAYMENTS_PROVIDER_TOKEN,
#                        currency='rub',
#                        photo_url=config.SHUTTLE_IMAGE_URL,
#                        photo_height=512,  # !=0/None, иначе изображение не покажется
#                        photo_width=512,
#                        photo_size=512,
#                        is_flexible=False,  # True если конечная цена зависит от способа доставки
#                        prices=[types.LabeledPrice(label='Билет на шаттл', amount=100000)],
#                        start_parameter='shuttle-order-example',
#                        payload='some-invoice-payload-for-our-internal-use'
#                        )

# @dp.pre_checkout_query_handler(lambda query: True)
# async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
#     await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# #@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
# async def process_successful_payment(message: types.Message):
#     otp=randrange(1000, 9999, 1)
#     await bot.send_message(
#         message.chat.id,
#         'Платеж на сумму `{total_amount} {currency}` совершен успешно! Приятного пользования сервисом CrimGo. Код для посадки `{otp}`'.format(
#         total_amount=message.successful_payment.total_amount // 100,
#         currency=message.successful_payment.currency,
#         otp=otp
#         )
#     )
#     trips_left = 1
#     if (message.successful_payment.total_amount // 100) == 1000:
#         trips_left = 12
#     await crimgo_db.successful_payment(message, otp, trips_left)

def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(commands_start, commands=['start', 'help'])
    dp.register_message_handler(cmd_order_trip, Text(equals='Заказать поездку', ignore_case=True))
    #dp.register_message_handler(cmd_subscription, Text(equals='Купить абонемент', ignore_case=True))
    dp.register_message_handler(cmd_contact_with_support, Text(equals='Чат поддержки', ignore_case=True))
    dp.register_callback_query_handler(menu_path_selection, state=FSMOrder_trip.s_path_selection)
    dp.register_callback_query_handler(menu_seat_selection, state=FSMOrder_trip.s_seat_selection)
    dp.register_callback_query_handler(menu_pp_confirm, state=FSMOrder_trip.s_geolocation)
    dp.register_callback_query_handler(menu_trip_confirm, state=FSMOrder_trip.s_pp_confirmation)
    dp.register_callback_query_handler(menu_payment_type, state=FSMOrder_trip.s_trip_confirmation)
#    dp.register_callback_query_handler(menu_cash_payment, state=FSMOrder_trip.s_cash_type)
    #dp.register_callback_query_handler(menu_card_payment, state=FSMOrder_trip.s_payment_type)
    #dp.register_message_handler(process_pre_checkout_query, state = FSMOrder_trip.s_checkout_query)
    #dp.register_message_handler(process_successful_payment, content_types=ContentType.SUCCESSFUL_PAYMENT)