import psycopg2
import datetime

from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import config

def crimgo_db_start():
    global connection, cursor
    try:
        # Подключение к существующей базе данных
        connection = psycopg2.connect(user = config.DATABASE['username'],
                                      # пароль, который указали при установке PostgreSQL
                                      password = config.DATABASE['password'],
                                      host = config.DATABASE['host'],
                                      port = config.DATABASE['port'],
                                      dbname = config.DATABASE['database'])
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        if connection:
            print('Подключен к БД')

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)

# Регистрация водителя через админку
async def pre_reg_driver(state):
    async with state.proxy() as data:
        cursor.execute('INSERT INTO driver (name, phone, otp) VALUES (%s, %s, %s)', tuple(data.values()))
        connection.commit()

# Регистрация шаттла через админку
async def reg_shuttle(state):
    async with state.proxy() as data:
        cursor.execute('INSERT INTO shuttle (name, capacity) VALUES (%s, %s)', tuple(data.values()))
        connection.commit()

# Проверка, существует ли пользователь в БД
async def is_exist(message):
    cursor.execute('SELECT telegram_id from passenger where telegram_id = %s', (message.from_user.id,))
    pass_id = cursor.fetchone()
    if pass_id is None:
        return False
    else: 
        return True
        
# Создание пользователя в БД
async def create_user(message):
    cursor.execute('INSERT INTO passenger (telegram_id, telegram_name, phone, timestamp) VALUES (%s, %s, %s, %s)', (message.from_user.id, message.from_user.username, message.contact.phone_number, datetime.datetime.now()))
    connection.commit()

# Создание записи об успешном платеже
async def successful_payment(state):
    # Создаем запись о покупке
    async with state.proxy() as data:
        cursor.execute('INSERT INTO payment (total_amount, telegram_payment_charge_id, provider_payment_charge_id, otp, pass_id, payment_type, timestamp)\
            VALUES (%s, %s, %s, %s, %s, %s, %s)', (data['seat'], data['telegram_payment_charge_id'], data['provider_payment_charge_id'], data['otp'], data['pass_id'], data['payment_type'], datetime.datetime.now()))
        cursor.execute('UPDATE passenger SET (available_trips, timestamp) = (available_trips + %s, %s) WHERE telegram_id = %s', (data['seat'], datetime.datetime.now(), data['pass_id']))
        connection.commit()

# Проверка существует водитель в БД
async def is_driver_exist(message):
    cursor.execute('SELECT telegram_id from driver where telegram_id = %s', (message.from_user.id,))
    driver_id = cursor.fetchone()
    return driver_id

# Проверка водителя на валидность
async def is_driver_valid(state, message):
    is_validated = False
    # Ищем id водителя с комбинацией телефон + пароль
    async with state.proxy() as data:
        cursor.execute('SELECT phone from driver WHERE phone = %s AND otp = %s', tuple(data.values()))
        drv_phone = cursor.fetchone()
    # Если есть, то обновляем данные
    if drv_phone is not None:
        cursor.execute('UPDATE driver SET (telegram_name, telegram_id, timestamp) = (%s, %s, %s) WHERE phone = %s', (message.from_user.username, message.from_user.id, datetime.datetime.now(), drv_phone))
        connection.commit()
        is_validated = True
    return is_validated