import psycopg2
import datetime

import database.crimgo_db_management as crimgo_db_management
import database.crimgo_db_crud as crimgo_db_crud

from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import config
from datetime import timedelta

def crimgo_db_start():
    global connection, cursor
    try:
        # Подключение к существующей базе данных
        connection = psycopg2.connect(user = config.DATABASE['username'],
                                      password = config.DATABASE['password'],
                                      host = config.DATABASE['host'],
                                      port = config.DATABASE['port'],
                                      dbname = config.DATABASE['database'])
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        # Курсор для выполнения операций с базой данных
        cursor = connection.cursor()
        if connection:
            print('Подключен к БД')
            crimgo_db_management.crimgo_check_tables(cursor, connection)

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)

# Регистрация водителя
async def create_driver(message, state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.insert_into_driver, (message.from_user.id, message.from_user.username, data['name'], message.contact.phone_number, datetime.datetime.now()))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

# Получение телефона водителя
async def get_driver_phone(message):
    try:
        cursor.execute(crimgo_db_crud.select_driver_phone, (message.text,))
        driver_phone = cursor.fetchone()
        return driver_phone
    except Exception as err:
        print(err)
        return False

# Проверка валидации водителя
async def is_driver_valid(message):
    try:
        cursor.execute(crimgo_db_crud.select_driver_validated, (message.from_user.id,))
        is_valid = cursor.fetchone()[0]
        return is_valid
    except Exception as err:
        print(err)
        return False

# Валидация водитеоя
async def validate_driver(driver_phone):
    try:
        cursor.execute(crimgo_db_crud.update_driver_set_validated, (driver_phone,))
        connection.commit()
        return True
    except Exception as err:
        print(err)
        return False

# Регистрация шаттла через админку
async def reg_shuttle(state):
    async with state.proxy() as data:
        cursor.execute(crimgo_db_crud.insert_into_shuttle, (data['name'], data['capacity'], datetime.datetime.now()))
        connection.commit()

# Проверка, существует ли пользователь в БД
async def is_exist(message):
    cursor.execute(crimgo_db_crud.select_user_id, (message.from_user.id,))
    pass_id = cursor.fetchone()
    if pass_id is None:
        return False
    else: 
        return True
        
# Создание пользователя в БД
async def create_user(message):
    cursor.execute(crimgo_db_crud.insert_into_passenger, (message.from_user.id, message.from_user.username, message.contact.phone_number, datetime.datetime.now()))
    connection.commit()

# Создание записи об успешном платеже
async def successful_payment(state):
    # Создаем запись о покупке
    async with state.proxy() as data:
        cursor.execute(crimgo_db_crud.insert_into_payment, (data['total_amount'], data['telegram_payment_charge_id'], data['provider_payment_charge_id'], data['pass_id'], data['payment_type'], datetime.datetime.now()))
        
        cursor.execute(crimgo_db_crud.udpate_passenger_increment_trip, (data['seat'], datetime.datetime.now(), data['pass_id']))
        connection.commit()

        # TODO
        cursor.execute('SELECT currval(pg_get_serial_sequence(\'payment\',\'id\'))')
        payment_id = cursor.fetchone()[0]
        return payment_id

# Проверка существует водитель в БД
async def is_driver_exist(message):
    try:
        cursor.execute(crimgo_db_crud.select_driver_id, (message.from_user.id,))
        driver_id = cursor.fetchone()
        return driver_id
    except Exception as err:
        print(err)
        return None

# Привязан ли шаттл к водителю
async def is_shuttle_binded(state):
    async with state.proxy() as data:
        try:
            cursor.execute(crimgo_db_crud.select_driver_id_from_shuttle, (data['shuttle_name'],))
            driver_id = cursor.fetchone()[0]
            return driver_id
        except Exception as err:
            print(err)
            return False

# Привзяка шаттла к водителю
async def bind_shuttle_to_driver(state, callback):
    # Ищем шаттл по имени
    async with state.proxy() as data:
        try:
            cursor.execute(crimgo_db_crud.update_driver_set_shift, (datetime.datetime.now(), callback.from_user.id))
            cursor.execute(crimgo_db_crud.update_shuttle_set_driver, (callback.from_user.id, datetime.datetime.now(), data['start_point'], data['driver_chat_id'], data['shuttle_name']))
            connection.commit()            
            return True
        except Exception as err:
            print(err)
            return False

# Проверяем находится ли водитель в смене 
async def is_on_shift(message):    
    try:
        cursor.execute(crimgo_db_crud.select_driver_shift, (message.from_user.id,))
        on_shift = cursor.fetchone()[0]
        return on_shift
    except Exception as err:
        print(err)
        return False

# Завершение смены
async def stop_driver_shift(message):
    try:
        cursor.execute(crimgo_db_crud.update_shuttle_remove_driver, (datetime.datetime.now(),))
        cursor.execute(crimgo_db_crud.update_driver_remove_shift, (datetime.datetime.now(),))
    except Exception as err:
        print(err)

# Создание поездки
async def create_trip(state):
    try:
        async with state.proxy() as data:
            # создание рейса и привязка шаттла, бросит исключение из-за "null value in column "shuttle_id" violates not-null constraint"
            # TODO выбор шатла из нескольких
            cursor.execute(crimgo_db_crud.insert_into_trip, ('awaiting_passengers', data['route'],  datetime.datetime.now(), datetime.datetime.now(), datetime.datetime.now() + config.MAX_WAIT_TIME))
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
            cursor.execute(crimgo_db_crud.select_trip_id_status_awaiting_pass, (data['route'],))
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
            cursor.execute(crimgo_db_crud.update_trip_decrement_seats, (int(data['seat']), datetime.datetime.now(), data['trip_id']))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

async def restore_booked_seats(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.update_trip_restore_seats, (int(data['seat']), data['trip_id']))
            connection.commit()
            return True
    except Exception as err:
        print(err)
        return False

async def create_ticket(state, payment_id):
    try:
        async with state.proxy() as data:
            # # Время создания
            # cursor.execute(crimgo_db_crud.select_trip_creation_time, (data['trip_id'],))
            # trip_creation_time = cursor.fetchone()[0]
            
            # Время до остановки
            cursor.execute(crimgo_db_crud.select_time_to_pp, (data['geo'],))
            time_to_pp = cursor.fetchone()[0]

            cursor.execute(crimgo_db_crud.insert_into_ticket ,(int(payment_id), data['trip_id'], data['geo'], data['seat'], data['otp'], (datetime.datetime.now() + config.MAX_WAIT_TIME + timedelta(minutes = time_to_pp)), ((datetime.datetime.now() + config.MAX_WAIT_TIME + timedelta(minutes = time_to_pp)))))
            connection.commit()
    except Exception as err:
        print(err)
        return False

# Приблизительное время подбора
async def calculate_raw_pickup_time(state):
    try:
        async with state.proxy() as data:
            # Время создания
            cursor.execute(crimgo_db_crud.select_trip_creation_time, (data['trip_id'],))
            trip_creation_time = cursor.fetchone()[0]
            # Время до остановки
            cursor.execute(crimgo_db_crud.select_time_to_pp, (data['geo'],))
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
            cursor.execute('', (data['shuttle_name'],))
            trip_details = cursor.fetchone()
            return trip_details
    except Exception as err:
        print(err)
        return False

# Детали поездки
async def trip_details(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_trip_details, (data['trip_id'],))
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
            cursor.execute(crimgo_db_crud.select_capacity, (data['trip_id'],))
            shuttle_capacity = cursor.fetchone()[0]
            
            # Проверка оставшегося кол-ва мест
            cursor.execute(crimgo_db_crud.select_available_seats, (data['trip_id'],))
            trip_available_seats = cursor.fetchone()[0]
            # если наполняемость больше 50%
            if (( (shuttle_capacity - trip_available_seats) / shuttle_capacity)*100 > 50):
                # нужно обновить время подбора пассажиров
                cursor.execute(crimgo_db_crud.select_ticket_order_by_raw_pickup_time, (data['trip_id'],))
                # берем ближайшее время и вычисляем время к билжайшему пассажиру
                soonest_pp_time = cursor.fetchone()[0]
                time_offset = soonest_pp_time - datetime.datetime.now()
                if (time_offset > config.MIN_WAIT_TIME):
                    # Меняю время подбора для пассажиров
                    new_time = time_offset - config.MIN_WAIT_TIME
                    cursor.execute(crimgo_db_crud.update_ticket_set_final_time, (new_time, data['trip_id']))
                    # Меняем время начала и статус рейса
                    cursor.execute(crimgo_db_crud.update_trip_set_status_scheduled, (new_time, data['trip_id']))
                    connection.commit()

    except Exception as err:
        print(err)
        return False

# Получить ID драйвера
async def get_driver_chat_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_driver_chat_id, (data['trip_id'],))
            driver_id = cursor.fetchone()
            return driver_id
    except Exception as err:
        print(err)
        return False

# is_first_ticket
async def is_first_ticket(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_count_id_from_ticket, (data['trip_id'],))
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
            cursor.execute(crimgo_db_crud.update_shuttle_set_driver_message_id, (message_id, data['trip_id']))
            connection.commit()
    except Exception as err:
        print(err)

async def get_dict_of_tickets_by_driver(from_user_id):
    try:
        cursor.execute(crimgo_db_crud.select_tickets_by_driver, (from_user_id,))
        tickets = cursor.fetchall()
        return tickets
    except Exception as err:
        print(err)
        return False

async def save_message_id_and_text(state, text):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.insert_into_message, (data['trip_id'], text, text))
            connection.commit()
    except Exception as err:
        print(err)

async def get_message_id_and_text(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_message_by_trip, (data['trip_id'],))
            message_and_text = cursor.fetchone()[1]
            return message_and_text
    except Exception as err:
        print(err)

async def trip_status(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_status_from_trip, (data['trip_id']))
            status = cursor.fetchone()[0]
            return status
    except Exception as err:
        print(err)
        return False

async def get_dict_of_tickets_by_trip(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_tickets_by_trip, (data['trip_id'],))
            tickets = cursor.fetchall()
            return tickets
    except Exception as err:
        print(err)
        return False

async def get_trip_start_time_by_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_start_time_from_trip, (data['trip_id'],))
            start_time = cursor.fetchone()[0]
            return start_time
    except Exception as err:
        print(err)
        return False

async def get_shuttle_position(callback):
    try:
        cursor.execute(crimgo_db_crud.select_current_possition_from_shuttle, (callback.from_user.id,))
        current_position = cursor.fetchone()[0]
        return current_position
    except Exception as err:
        print(err)

async def set_shuttle_position(callback):
    # Берем список точек посадки
    cursor.execute(crimgo_db_crud.select_pickup_point_from_ticket, (callback.from_user.id, ))
    # pickup_point_list = cursor.fetchall()
    pickup_point_list = [item[0] for item in cursor.fetchall()]

    # Позиция шаттла
    cursor.execute(crimgo_db_crud.select_current_possition_from_shuttle, (callback.from_user.id,))
    shuttle_possition = cursor.fetchone()
    if shuttle_possition[0] == 1:
        index = pickup_point_list.index(shuttle_possition[0])
        cursor.execute(crimgo_db_crud.update_shutlle_set_position, (pickup_point_list[index +1], callback.from_user.id))
        connection.commit()
        
    # Если шаттл на начальной точке, меняем позицию на первую из pickup_point_list
    # if shuttle_possition[0] == 1:
    #     cursor.execute('UPDATE shuttle SET current_position = %s WHERE driver_id = %s', (pickup_point_list[0][0], callback.from_user.id))
    #     connection.commit()
    # # В противном случае, ищем индекс входжения позиции шатла в pickup_point_list и меняем позицию на индекс вхождения + 1
    # else:
    #     index = pickup_point_list.index(shuttle_possition)
    #     cursor.execute('UPDATE shuttle SET current_position = %s WHERE driver_id = %s', (pickup_point_list[index +1][0], callback.from_user.id))
    #     connection.commit()
    
async def set_trip_status(callback, status):
    try:
        cursor.execute(crimgo_db_crud.update_trip_set_status, (status, callback.from_user.id))
        connection.commit()
    except Exception as err:
        print(err)

async def verify_pass_code(message, code):
    # Позиция шаттла
    cursor.execute(crimgo_db_crud.select_current_possition_from_shuttle, (message.from_user.id,))
    shuttle_position = cursor.fetchone()[0]
    # Ищем пас ID и забронированые места
    cursor.execute(crimgo_db_crud.select_pass_seat, (code, message.from_user.id))
    pass_id_seats = cursor.fetchone()
    # Гасим билет и отнимаем поедку
    cursor.execute(crimgo_db_crud.update_ticket_status, (shuttle_position, message.from_user.id, pass_id_seats[1], code))
    if cursor.rowcount == 1:
        cursor.execute(crimgo_db_crud.update_passenger_decrease_seat, (pass_id_seats[1], pass_id_seats[0]))
        if cursor.rowcount == 1:
            connection.commit()
            return True
    # connection.rollback()
    return False
