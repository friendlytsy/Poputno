from telnetlib import EC
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
            cursor.execute('INSERT INTO driver (telegram_id, telegram_name, name, phone, timestamp) VALUES (%s, %s, %s, %s, %s)', (message.from_user.id, message.from_user.username, data['name'], message.contact.phone_number, datetime.datetime.now()))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

# Получение телефона водителя
async def get_driver_phone(message):
    try:
        cursor.execute('SELECT phone FROM driver WHERE phone = %s', (message.text,))
        driver_phone = cursor.fetchone()
        return driver_phone
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

# Валидация водитеоя
async def validate_driver(driver_phone):
    try:
        cursor.execute('UPDATE driver SET validated = TRUE WHERE phone = %s', (driver_phone,))
        connection.commit()
        return True
    except Exception as err:
        print(err)
        return False

# Регистрация шаттла через админку
async def reg_shuttle(state):
    async with state.proxy() as data:
        cursor.execute('INSERT INTO shuttle (name, capacity, timestamp) VALUES (%s, %s, %s)', (data['name'], data['capacity'], datetime.datetime.now()))
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
async def is_shuttle_binded(state):
    async with state.proxy() as data:
        try:
            cursor.execute('SELECT driver_id FROM shuttle WHERE name = %s', (data['shuttle_name'],))
            driver_id = cursor.fetchone()[0]
            return driver_id
        except Exception as err:
            print(err)
            return False

# Привзяка шаттла к водителю
async def bind_shuttle_to_driver(state, callback):
    # Ищем шаттл по имени
    async with state.proxy() as data:
        # try:
        cursor.execute('UPDATE driver SET (on_shift, timestamp) = (TRUE, %s) WHERE telegram_id = %s', (datetime.datetime.now(), callback.from_user.id))
        cursor.execute('UPDATE shuttle SET (driver_id, timestamp, current_position, driver_chat_id) = (%s, %s, (SELECT id FROM pickup_point WHERE name = %s), %s) WHERE name = %s', (callback.from_user.id, datetime.datetime.now(), data['start_point'], data['driver_chat_id'], data['shuttle_name']))
        connection.commit()            
            # return True
        # except Exception as err:
            # print(err)
            # return False

# Проверяем находится ли водитель в смене 
async def is_on_shift(message):    
    try:
        cursor.execute('SELECT on_shift FROM driver where telegram_id = %s', (message.from_user.id,))
        on_shift = cursor.fetchone()[0]
        return on_shift
    except Exception as err:
        print(err)
        return False

# Завершение смены
async def stop_driver_shift(message):
    try:
        cursor.execute('UPDATE shuttle SET (driver_id, current_position, driver_chat_id , timestamp) = (null, null, null, %s)', (datetime.datetime.now(),))
        cursor.execute('UPDATE driver SET (on_shift, timestamp) = (false, %s)', (datetime.datetime.now(),))
    except Exception as err:
        print(err)

# Создание поездки
async def create_trip(state):
    try:
        async with state.proxy() as data:
            # создание рейса и привязка шаттла, бросит исключение из-за "null value in column "shuttle_id" violates not-null constraint"
            # TODO выбор шатла из нескольких
            cursor.execute('INSERT INTO trip (shuttle_id, status, route, creation_time, available_seats, timestamp, start_time) VALUES ((SELECT id FROM shuttle WHERE driver_id IS NOT NULL), %s, (SELECT id FROM route WHERE name = %s), %s, (SELECT capacity FROM shuttle WHERE driver_id IS NOT NULL), %s, %s) RETURNING id', ('awaiting_passengers', data['route'],  datetime.datetime.now(), datetime.datetime.now(), datetime.datetime.now() + config.MAX_WAIT_TIME))
            trip_id = cursor.fetchone()[0]
            connection.commit()
            return trip_id
    except Exception as err:
        print(err)
        return False

# Проверка, если ли поездка по маршруту
async def is_trip_with_route(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT id FROM trip WHERE route = (SELECT id FROM route WHERE name = %s) AND available_seats > 0 and status = \'awaiting_passengers\'', (data['route'],))
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
            # Время создания
            cursor.execute('SELECT creation_time FROM trip WHERE id = %s', (data['trip_id'],))
            trip_creation_time = cursor.fetchone()[0]
            
            # Время до остановки
            cursor.execute('SELECT time_to_pp FROM pickup_point WHERE name = %s', (data['geo'],))
            time_to_pp = cursor.fetchone()[0]

            cursor.execute('INSERT INTO ticket (payment_id, trip_id, pickup_point, booked_seats, otp, raw_pickup_time, final_pickup_time) VALUES (%s, %s, (SELECT id from pickup_point WHERE name = %s), %s, %s, %s, %s)',\
                 (int(payment_id), data['trip_id'], data['geo'], data['seat'], data['otp'], (datetime.datetime.now() + config.MAX_WAIT_TIME + timedelta(minutes = time_to_pp)), ((datetime.datetime.now() + config.MAX_WAIT_TIME + timedelta(minutes = time_to_pp)))))
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

# Проверка доступных поездок и назначение водителю
async def check_available_trip(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT t.id, r.name, t.creation_time FROM trip AS t, route AS r WHERE t.shuttle_id = (SELECT id FROM shuttle WHERE name = %s) AND t.status = \'scheduled\' AND t.route = r.id', (data['shuttle_name'],))
            trip_details = cursor.fetchone()
            return trip_details
    except Exception as err:
        print(err)
        return False

# Детали поездки
async def trip_details(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT t.id, r.name, t.start_time FROM trip AS t, route as r WHERE t.id = %s and r.id = t.route', (data['trip_id'],))
            trip_details = cursor.fetchone()
            return trip_details
    except Exception as err:
        print(err)
        return False

# Обновление статуса trip, перерасчет времени
async def trip_status_review(state):
    try:
        async with state.proxy() as data:
            # Поиск вместительности шаттла
            cursor.execute('SELECT capacity FROM shuttle WHERE id = (SELECT shuttle_id FROM trip WHERE id = %s)', (data['trip_id'],))
            shuttle_capacity = cursor.fetchone()[0]
            
            # Проверка оставшегося кол-ва мест
            cursor.execute('SELECT available_seats FROM trip WHERE id = %s', (data['trip_id'],))
            trip_available_seats = cursor.fetchone()[0]
            # если наполняемость больше 50%
            if (( (shuttle_capacity - trip_available_seats) / shuttle_capacity)*100 > 50):
                # нужно обновить время подбора пассажиров
                cursor.execute('SELECT raw_pickup_time FROM ticket WHERE trip_id = %s ORDER BY raw_pickup_time', (data['trip_id'],))
                # берем ближайшее время и вычисляем время к билжайшему пассажиру
                soonest_pp_time = cursor.fetchone()[0]
                time_offset = soonest_pp_time - datetime.datetime.now()
                if (time_offset > config.MIN_WAIT_TIME):
                    # Меняю время подбора для пассажиров
                    new_time = time_offset - config.MIN_WAIT_TIME
                    cursor.execute('UPDATE ticket SET final_pickup_time = final_pickup_time - %s WHERE trip_id = %s', (new_time, data['trip_id']))
                    # Меняем время начала и статус рейса
                    cursor.execute('UPDATE trip SET status = \'scheduled\', start_time = start_time - %s WHERE id = %s', (new_time, data['trip_id']))
                    connection.commit()

    except Exception as err:
        print(err)
        return False

# Получить ID драйвера
async def get_driver_chat_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT s.driver_chat_id, s.driver_message_id FROM trip AS t, shuttle AS s WHERE t.id = %s AND t.shuttle_id = s.id', (data['trip_id'],))
            driver_id = cursor.fetchone()
            return driver_id
    except Exception as err:
        print(err)
        return False

# is_first_ticket
async def is_first_ticket(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT COUNT(id) FROM ticket WHERE trip_id = %s', (data['trip_id'],))
            ids = cursor.fetchone()[0]
            if ids == 1:
                return True
            else :
                return False
    except Exception as err:
        print(err)
        return False

async def set_shuttle_message_id(message_id, state):
    try:
        async with state.proxy() as data:
            cursor.execute('UPDATE shuttle SET driver_message_id = %s WHERE id = (SELECT shuttle_id FROM trip WHERE id = %s)', (message_id, data['trip_id']))
            connection.commit()
    except Exception as err:
        print(err)

async def get_dict_of_tickets_by_driver(from_user_id):
    try:
        cursor.execute('SELECT p.name, booked_seats, final_pickup_time FROM ticket AS t, pickup_point AS p WHERE t.pickup_point = p.id AND trip_id = (SELECT id FROM trip WHERE shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) ORDER BY final_pickup_time', (from_user_id,))
        tickets = cursor.fetchall()
        return tickets
    except Exception as err:
        print(err)
        return False

async def save_message_id_and_text(state, text):
    try:
        async with state.proxy() as data:
            cursor.execute('INSERT INTO message (trip_id, text) VALUES (%s, %s) ON CONFLICT (trip_id) DO UPDATE SET text = %s', (data['trip_id'], text, text))
            connection.commit()
    except Exception as err:
        print(err)

async def get_message_id_and_text(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT * FROM message WHERE trip_id = %s', (data['trip_id'],))
            message_and_text = cursor.fetchone()[1]
            return message_and_text
    except Exception as err:
        print(err)

async def trip_status(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT status FROM trip WHERE id = %s', (data['trip_id']))
            status = cursor.fetchone()[0]
            return status
    except Exception as err:
        print(err)
        return False

async def get_dict_of_tickets_by_trip(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT p.name, booked_seats, final_pickup_time FROM ticket AS t, pickup_point AS p WHERE t.pickup_point = p.id AND trip_id = %s ORDER BY final_pickup_time', (data['trip_id'],))
            tickets = cursor.fetchall()
            return tickets
    except Exception as err:
        print(err)
        return False

async def get_trip_start_time_by_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute('SELECT start_time FROM trip WHERE id = %s', (data['trip_id'],))
            start_time = cursor.fetchone()[0]
            return start_time
    except Exception as err:
        print(err)
        return False