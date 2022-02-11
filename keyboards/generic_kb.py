from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

btn_share_contact = KeyboardButton('Поделиться контактом', request_contact = True) 

kb_generic_start = ReplyKeyboardMarkup(resize_keyboard=True)
kb_generic_start.add(btn_share_contact)