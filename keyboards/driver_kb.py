from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Пройти верификацию
btn_verification = KeyboardButton('Пройти верификацию')
kb_driver_verification = ReplyKeyboardMarkup(resize_keyboard=True)
kb_driver_verification.add(btn_verification)

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


# s_start_point = State()
kb_start_point = InlineKeyboardMarkup()
btn_point_1 = InlineKeyboardButton(text = 'Остановка №1', callback_data='Остановка №1')
btn_point_7 = InlineKeyboardButton(text = 'Остановка №7', callback_data='Остановка №7')
kb_start_point.add(btn_point_1).add(btn_point_7)

# s_awaiting_path = State()
kb_awaiting_trip = InlineKeyboardMarkup()

# s_awaiting_pass = State()
# s_start_path = State()
# s_onboarding = State()
# s_verify_code = State()
# s_path_finished = State()