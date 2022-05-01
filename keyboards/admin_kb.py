from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_driver_reg = KeyboardButton('/Регистрация_водителя') 
btn_shuttle_reg = KeyboardButton('/Регистрация_шаттла')
btn_check_active_tickets = KeyboardButton('/Активные_билеты')

kb_admin = ReplyKeyboardMarkup(resize_keyboard=True)
kb_admin.add(btn_driver_reg).add(btn_shuttle_reg).add(btn_check_active_tickets)