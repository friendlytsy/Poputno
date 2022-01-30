from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_order_trip = KeyboardButton('/Бронирование_поездки') 
btn_order_subscription = KeyboardButton('/Купить_абонемент')

kb_pass = ReplyKeyboardMarkup(resize_keyboard=True)
kb_pass.row(btn_order_trip, btn_order_subscription)