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

async def pre_reg_driver(state):
    async with state.proxy() as data:
        cursor.execute('INSERT INTO driver (name, phone, otp) VALUES (%s, %s, %s)', tuple(data.values()))
        connection.commit()

async def check_if_exist(from_user):
    cursor.execute('SELECT telegram_id from passenger where telegram_id = %s', (from_user.id,))
    pass_id = cursor.fetchone()
    if pass_id is None:
        cursor.execute('INSERT INTO passenger (telegram_id, telegram_name, timestamp) VALUES (%s, %s, %s)', (from_user.id, from_user.username, datetime.datetime.now()))
        connection.commit()

# async def successful_payment(state):


# async def successful_payment(message, otp, trips_left):
#     # Ищем pass_id клиента 
#     cursor.execute('SELECT id from passenger where telegram_id = %s', (message.from_user.id,))
#     pass_id = cursor.fetchone()
#     # Обновляем кол-во доступных поездок
#     cursor.execute('UPDATE passenger SET trips_left = trips_left + %s, timestamp = %s WHERE id = %s', (trips_left, datetime.datetime.now(), pass_id))
#     # Создаем запись о покупке
#     cursor.execute('INSERT INTO payment (total_amount, telegram_payment_charge_id, provider_payment_charge_id, otp, passenger_id, timestamp)\
#          VALUES (%s, %s, %s, %s, %s, %s)', (message.successful_payment.total_amount // 100,\
#              message.successful_payment.telegram_payment_charge_id, message.successful_payment.provider_payment_charge_id, \
#                  otp, pass_id, datetime.datetime.now()))
#     connection.commit()

async def is_driver_exist(message):
    cursor.execute('SELECT telegram_id from driver where telegram_id = %s', (message.from_user.id,))
    driver_id = cursor.fetchone()
    return driver_id

async def is_driver_valid(state, message):
    is_validated = False
    # Ищем id водителя с комбинацией телефон + пароль
    async with state.proxy() as data:
        cursor.execute('SELECT phone from driver WHERE phone = %s AND otp = %s', tuple(data.values()))
        drv_phone = cursor.fetchone()
    # Если есть, то обновляем данные
    if drv_phone is not None:
        cursor.execute('UPDATE driver SET (telegram_name, telegram_id, timestamp) = (%s, %s, %s) WHERE phone = %s', (message.from_user.username, message.from_user.id, drv_phone, datetime.datetime.now()))
        connection.commit()
        is_validated = True
    return is_validated