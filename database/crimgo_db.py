import psycopg2
import datetime

from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import config
from datetime import timedelta

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

# Регистрация водителя
async def create_driver(message, state):
    try:
        async with state.proxy() as data:
            cursor.execute('INSERT INTO driver (telegram_id, telegram_name, name, phone, otp, timestamp) VALUES (%s, %s, %s, %s, %s, %s)', (message.from_user.id, message.from_user.username, data['name'], message.contact.phone_number, data['otp'], datetime.datetime.now()))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

# Получение пароля для водителя
async def get_driver_otp(message):
    try:
        cursor.execute('SELECT otp FROM driver WHERE phone = %s', (message.text,))
        driver_otp = cursor.fetchone()
        return driver_otp
    except Exception as err:
        print(err)
        return False

# Проверка валидации водителя
async def is_driver_valid(message):
    try:
        cursor.execute('SELECT validated FROM driver WHERE telegram_id = %s', (message.from_user.id,))
        is_valid = cursor.fetchone()[0]
        return is_valid
    except Exception as err:
        print(err)
        return False


# Валидация валидация
async def validate_driver_otp(message):
    try:
        cursor.execute('UPDATE driver SET validated = TRUE WHERE telegram_id = %s AND otp = %s', (message.from_user.id, message.text))
        connection.commit()
        return True
    except Exception as err:
        print(err)
        return False

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
        cursor.execute('INSERT INTO payment (total_amount, telegram_payment_charge_id, provider_payment_charge_id, pass_id, payment_type, timestamp) VALUES (%s, %s, %s, %s, %s, %s)', \
                (data['total_amount'], data['telegram_payment_charge_id'], data['provider_payment_charge_id'], data['pass_id'], data['payment_type'], datetime.datetime.now()))
        
        cursor.execute('UPDATE passenger SET (available_trips, timestamp) = (available_trips + %s, %s) WHERE telegram_id = %s', (data['seat'], datetime.datetime.now(), data['pass_id']))
        connection.commit()

        cursor.execute('SELECT currval(pg_get_serial_sequence(\'payment\',\'id\'))')
        payment_id = cursor.fetchone()[0]
        return payment_id

# Проверка существует водитель в БД
async def is_driver_exist(message):
    try:
        cursor.execute('SELECT telegram_id from driver where telegram_id = %s', (message.from_user.id,))
        driver_id = cursor.fetchone()
        return driver_id
    except Exception as err:
        print(err)
        return None

# Привязан ли шаттл к водителю
async def is_shuttle_binded(message):
    try:
        cursor.execute('SELECT driver_id FROM shuttle WHERE name = %s', (message.text,))
        driver_id = cursor.fetchone()[0]
        return driver_id

    except Exception as err:
        print(err)
        return False

# Привзяка шаттла к водителю
async def bind_shuttle_to_driver(message):
    # Ищем шаттл по имени
    try:
        cursor.execute('UPDATE driver SET (on_shift, timestamp) = (TRUE, %s) WHERE telegram_id = %s', (datetime.datetime.now(), message.from_user.id))
        cursor.execute('UPDATE shuttle SET driver_id = %s WHERE name = %s', (message.from_user.id, str(message.text)))
        connection.commit()
        return True
    except Exception as err:
        print(err)
        return False

# Проверяем находится ли водитель в смене 
async def is_on_shift(message):    
    try:
        cursor.execute('SELECT on_shift FROM driver where telegram_id = %s', (message.from_user.id,))
        on_shift = cursor.fetchone()[0]
        return on_shift
    except Exception as err:
        print(err)
        return False

# Создание поездки
async def create_trip(state):
    try:
        async with state.proxy() as data:
            # создание рейса и привязка шаттла, бросит исключение из-за "null value in column "shuttle_id" violates not-null constraint"
            cursor.execute('INSERT INTO trip (shuttle_id, status, route, creation_time, available_seats, timestamp) VALUES ((SELECT id FROM shuttle WHERE driver_id IS NOT NULL), %s, (SELECT id FROM route WHERE name = %s), %s, (SELECT capacity FROM shuttle WHERE driver_id IS NOT NULL), %s)', ('draft', data['route'],  datetime.datetime.now(), datetime.datetime.now()))
            connection.commit()
            cursor.execute('SELECT currval(pg_get_serial_sequence(\'trip\',\'id\'))')
            trip_id = cursor.fetchone()[0]
        return trip_id
    except Exception as err:
        print(err)
        return False

# Проверка, если ли поездка по маршруту
async def is_trip_with_route(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT id FROM trip WHERE route = (SELECT id FROM route WHERE name = %s)', (data['route'],))
            trip_id = cursor.fetchone()
            return trip_id
    except Exception as err:
        print(err)
        return False

# Проверка на доступное кол-во мест
# НУЖНО ВЕРНУТЬ МЕСТА НА МЕСТО В СЛУЧАЕ НЕОПЛАТЫ
async def seat_availability(state):
    try:
        async with state.proxy() as data:
            cursor.execute('UPDATE trip SET (available_seats, timestamp) = (available_seats - %s, %s) WHERE id = %s', (int(data['seat']), datetime.datetime.now(), data['trip_id']))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

async def restore_booked_seats(state):
    try:
        async with state.proxy() as data:
            cursor.execute('UPDATE trip SET available_seats = available_seats + %s WHERE id = %s', (int(data['seat']), data['trip_id']))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

async def create_ticket(state, payment_id):
    try:
        async with state.proxy() as data:
            cursor.execute('INSERT INTO ticket (payment_id, trip_id, pickup_point, booked_seats, otp) VALUES (%s, %s, (SELECT id from pickup_point WHERE name = %s), %s, %s)', (payment_id, data['trip_id'], data['geo'], data['seat'], data['otp']))
            connection.commit()
    except Exception as err:
        print(err)
        return False

# Приблизительное время подбора
async def calculate_raw_pickup_time(state):
    try:
        async with state.proxy() as data:
            # Время создания
            cursor.execute('SELECT creation_time FROM trip WHERE id = %s', (data['trip_id'],))
            trip_creation_time = cursor.fetchone()[0]
            # Время до остановки
            cursor.execute('SELECT time_to_pp FROM pickup_point WHERE name = %s', (data['geo'],))
            time_to_pp = cursor.fetchone()[0]
            aprox_time = ((trip_creation_time + config.TIME_OFFSET + timedelta(minutes = time_to_pp) + config.MAX_WAIT_TIME).strftime("%H:%M"))
            return aprox_time
    except Exception as err:
        print(err)
        return False