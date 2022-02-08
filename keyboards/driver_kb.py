from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# На линии
btn_close_shift = KeyboardButton('Текущее состояние: на линии')
btn_on_charge = KeyboardButton('Зарядка')
btn_contact_support = KeyboardButton('Написать в поддержку')
btn_ticket_validation = KeyboardButton('Проверить билет') 
kb_driver_shift = ReplyKeyboardMarkup(resize_keyboard=True)
kb_driver_shift.add(btn_close_shift).add(btn_on_charge).add(btn_contact_support)

# Не на линии
btn_start_shift = KeyboardButton('Текущее состояние: не на линии')
kb_driver = ReplyKeyboardMarkup(resize_keyboard=True)
kb_driver.row(btn_start_shift).add(btn_contact_support)