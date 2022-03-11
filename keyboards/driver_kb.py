from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Пройти верификацию
btn_verification = KeyboardButton('Ожидайте верификацию')
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
btn_point_1 = InlineKeyboardButton(text = '№1 Шале', callback_data='№1 Шале')
btn_point_7 = InlineKeyboardButton(text = '№7 Море', callback_data='№7 Море')
kb_start_point.add(btn_point_1).add(btn_point_7)

# s_awaiting_path = State()
kb_awaiting_trip = InlineKeyboardMarkup()

# s_awaiting_pass = State()
# s_start_path = State()
kb_start_trip = InlineKeyboardMarkup()
btn_start_trip = InlineKeyboardButton(text = 'Начать рейс', callback_data='Начать рейс')
kb_start_trip.add(btn_start_trip)

# s_onboarding = State()
kb_onboarding_trip = InlineKeyboardMarkup()
btn_onboarding_trip = InlineKeyboardButton(text = 'Посадка', callback_data='Посадка')
# btn_nopassenger_trip = InlineKeyboardButton(text = 'Нет пассажира', callback_data='Нет пассажира')
kb_onboarding_trip.add(btn_onboarding_trip)

kb_continue_trip = InlineKeyboardMarkup()
btn_continue_trip = InlineKeyboardButton(text = 'Продолжить', callback_data='Продолжить')
btn_retry_onboarding = InlineKeyboardButton(text = 'Повторить ввод', callback_data='Повторить ввод')
kb_continue_trip.add(btn_continue_trip).add(btn_retry_onboarding)

kb_pass_absent = InlineKeyboardMarkup()
btn_pass_absent = InlineKeyboardButton(text = 'Нет пассажира', callback_data='Нет пассажира')
kb_pass_absent.add(btn_pass_absent)

# s_verify_code = State()
#kb_verify_code = InlineKeyboardMarkup()
#btn_verify_code = InlineKeyboardButton(text = '')
# s_path_finished = State()