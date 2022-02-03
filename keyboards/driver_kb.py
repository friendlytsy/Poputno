from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_on_shift = KeyboardButton('Начать смену')
btn_ticket_validation = KeyboardButton('Проверить билет') 

kb_driver = ReplyKeyboardMarkup(resize_keyboard=True)
kb_driver.row(btn_on_shift)