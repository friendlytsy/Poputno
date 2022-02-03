from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

#   /start
btn_share_contact = KeyboardButton('Поделиться контактом', request_contact = True) 

kb_pass_start = ReplyKeyboardMarkup(resize_keyboard=True)
kb_pass_start.add(btn_share_contact)

#   /menu
btn_order_trip = KeyboardButton('Заказать поездку') 
btn_order_subscription = KeyboardButton('Купить абонемент')
btn_contact_support = KeyboardButton('Чат поддержки')

kb_pass = ReplyKeyboardMarkup(resize_keyboard=True)
kb_pass.add(btn_order_trip).add(btn_contact_support).add(btn_order_subscription)

#   s_path_selection = State()
kb_path = InlineKeyboardMarkup()
btn_path_to_sea = InlineKeyboardButton(text = 'К морю', callback_data='К морю')
btn_path_from_sea = InlineKeyboardButton(text = 'От моря', callback_data='От моря')
kb_path.add(btn_path_to_sea).add(btn_path_from_sea)

#    s_seat_selection = State()
kb_seat = InlineKeyboardMarkup(row_width=5)
btn_seat_1 = InlineKeyboardButton(text = '1', callback_data='1')
btn_seat_2 = InlineKeyboardButton(text = '2', callback_data='2')
btn_seat_3 = InlineKeyboardButton(text = '3', callback_data='3')
btn_seat_4 = InlineKeyboardButton(text = '4', callback_data='4')
btn_seat_5 = InlineKeyboardButton(text = '5', callback_data='5')
kb_seat.row(btn_seat_1, btn_seat_2, btn_seat_3, btn_seat_4, btn_seat_5)
#kb_seat.add().add().add().add().add()

#    s_geolocation = State()
kb_geoposition = InlineKeyboardMarkup()
btn_share_gp = InlineKeyboardButton(text = 'Передать геопозицию', callback_data='Передать геопозицию')
btn_cancel_gp = InlineKeyboardButton(text = 'Назад', callback_data='Назад')
kb_geoposition.add(btn_share_gp).add(btn_cancel_gp)

#    s_pp_confirmation = State()
kb_pp_confirmation = InlineKeyboardMarkup()
btn_pp_accept = InlineKeyboardButton(text = 'Подтвердить', callback_data='Подтвердить')
btn_pp_repeat = InlineKeyboardButton(text = 'Повторить', callback_data='Повторить')
kb_pp_confirmation.add(btn_pp_accept).add(btn_pp_repeat)

#    s_trip_confirmation = State()
kb_trip_confirmation = InlineKeyboardMarkup()
btn_trip_accept = InlineKeyboardButton(text = 'Ок', callback_data='Ок')
btn_trip_cancel = InlineKeyboardButton(text = 'Не устраивает', callback_data='Не устраивает')
kb_trip_confirmation.add(btn_trip_accept).add(btn_trip_cancel)

#    s_payment_type = State()
kb_payment_type = InlineKeyboardMarkup()
btn_type_card = InlineKeyboardButton(text = 'Оплата картой', callback_data='Оплата картой')
btn_type_cash = InlineKeyboardButton(text = 'Наличкой водителю', callback_data='Наличкой водителю')
kb_payment_type.add(btn_type_card).add(btn_type_cash)

#    s_cash_canceled = State()
kb_cash_canceled = InlineKeyboardMarkup()
btn_cash_cancel = InlineKeyboardButton(text = 'Я передумал', callback_data='Я передумал')
kb_cash_canceled.add(btn_cash_cancel)

#    s_checkout_query = State()
#    s_successful_payment = State()