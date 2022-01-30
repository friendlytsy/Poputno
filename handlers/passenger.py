from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import dp, bot
from database import crimgo_db
from keyboards import kb_pass, kb_driver

from random import randrange

from config import config

class FSMOrder_trip(StatesGroup):
    s_checkout_query = State()
    s_successful_payment = State()

async def commands_start(message: types.Message):
    if (await crimgo_db.is_driver_exist(message) is not None):
        await message.reply('Добрый день', reply_markup=kb_driver)

    else:    
        await message.reply('Это онбординг', reply_markup=kb_pass)
        # If not exist, create a user
        await crimgo_db.check_if_exist(message.from_user)

# Покупка абонемента
async def cmd_subscription(message: types.Message):
    await message.reply('Покупка обонемента') 
    if config.PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
                 await bot.send_message(message.chat.id, 'Тестовая покупа обонемента')

    await bot.send_invoice(message.chat.id,
                       title='Покупка обонемента',
                       description='Покупка обонемента на 12 поездок',
                       provider_token=config.PAYMENTS_PROVIDER_TOKEN,
                       currency='rub',
                       photo_url=config.SHUTTLE_IMAGE_URL,
                       photo_height=512,  # !=0/None, иначе изображение не покажется
                       photo_width=512,
                       photo_size=512,
                       is_flexible=False,  # True если конечная цена зависит от способа доставки
                       prices=[types.LabeledPrice(label='Билет на шаттл', amount=100000)],
                       start_parameter='shuttle-order-example',
                       payload='some-invoice-payload-for-our-internal-use'
                       )

# Покупка одной поездки
async def cmd_order_trip(message: types.Message):
    await message.reply('Бронирование места') 
    if config.PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
                 await bot.send_message(message.chat.id, 'Тестовая покупа')

    await bot.send_invoice(message.chat.id,
                       title='Покупка билета',
                       description='Покупка билета на CrimGo шаттл',
                       provider_token=config.PAYMENTS_PROVIDER_TOKEN,
                       currency='rub',
                       photo_url=config.SHUTTLE_IMAGE_URL,
                       photo_height=512,  # !=0/None, иначе изображение не покажется
                       photo_width=512,
                       photo_size=512,
                       is_flexible=False,  # True если конечная цена зависит от способа доставки
                       prices=[types.LabeledPrice(label='Билет на шаттл', amount=10000)],
                       start_parameter='shuttle-order-example',
                       payload='some-invoice-payload-for-our-internal-use'
                       )

@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

#@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    otp=randrange(1000, 9999, 1)
    await bot.send_message(
        message.chat.id,
        'Платеж на сумму `{total_amount} {currency}` совершен успешно! Приятного пользования сервисом CrimGo. Код для посадки `{otp}`'.format(
        total_amount=message.successful_payment.total_amount // 100,
        currency=message.successful_payment.currency,
        otp=otp
        )
    )
    trips_left = 1
    if (message.successful_payment.total_amount // 100) == 1000:
        trips_left = 12
    await crimgo_db.successful_payment(message, otp, trips_left)

def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(commands_start, commands=['start', 'help'])
    dp.register_message_handler(cmd_order_trip, commands=['Бронирование_поездки'])
    dp.register_message_handler(cmd_subscription, commands=['Купить_абонемент'])
    #dp.register_message_handler(process_pre_checkout_query, state = FSMOrder_trip.s_checkout_query)
    dp.register_message_handler(process_successful_payment, content_types=ContentType.SUCCESSFUL_PAYMENT)
    