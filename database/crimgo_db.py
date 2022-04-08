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
    except (Exception, Error) as error:
        print("Ошибка при работе с create_driver", error)
        return False

# Получение телефона водителя
async def get_driver_phone(message):
    try:
        cursor.execute(crimgo_db_crud.select_driver_phone, (message.text,))
        driver_phone = cursor.fetchone()
        return driver_phone
    except (Exception, Error) as error:
        print("Ошибка при работе с get_driver_phone", error)
        return False

# Проверка валидации водителя
async def is_driver_valid(message):
    try:
        cursor.execute(crimgo_db_crud.select_driver_validated, (message.from_user.id,))
        is_valid = cursor.fetchone()[0]
        return is_valid
    except (Exception, Error) as error:
        print("Ошибка при работе с is_driver_valid", error)
        return False

# Валидация водитеоя
async def validate_driver(driver_phone):
    try:
        cursor.execute(crimgo_db_crud.update_driver_set_validated, (driver_phone,))
        connection.commit()
        return True
    except (Exception, Error) as error:
        print("Ошибка при работе с validate_driver", error)
        return False

# Регистрация шаттла через админку
async def reg_shuttle(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.insert_into_shuttle, (data['name'], data['capacity'], datetime.datetime.now()))
            connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с reg_shuttle", error)

# Проверка, существует ли пользователь в БД
async def is_exist(message):
    try:
        cursor.execute(crimgo_db_crud.select_user_id, (message.from_user.id,))
        pass_id = cursor.fetchone()
        if pass_id is None:
            return False
        else: 
            return True
    except (Exception, Error) as error:
        print("Ошибка при работе с is_exist", error)
        return False
        
# Создание пользователя в БД
async def create_user(message):
    try:
        cursor.execute(crimgo_db_crud.insert_into_passenger, (message.from_user.id, message.from_user.username, message.contact.phone_number, datetime.datetime.now()))
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с create_user", error)


# Создание записи об успешном платеже
async def successful_payment(state):
    # Создаем запись о покупке
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.insert_into_payment, (data['total_amount'], data['telegram_payment_charge_id'], data['provider_payment_charge_id'], data['pass_id'], data['payment_type'], datetime.datetime.now()))
            payment_id = cursor.fetchone()[0]

            cursor.execute(crimgo_db_crud.udpate_passenger_increment_trip, (data['seat'], datetime.datetime.now(), data['pass_id']))
            connection.commit()

            # TODO
            # cursor.execute('SELECT currval(pg_get_serial_sequence(\'payment\',\'id\'))')
            # payment_id = cursor.fetchone()[0]
            return payment_id
    except (Exception, Error) as error:
        print("Ошибка при работе с successful_payment", error)


# Проверка существует водитель в БД
async def is_driver_exist(message):
    try:
        cursor.execute(crimgo_db_crud.select_driver_id, (message.from_user.id,))
        driver_id = cursor.fetchone()
        return driver_id
    except (Exception, Error) as error:
        print("Ошибка при работе с is_driver_exist", error)
        return None

# Привязан ли шаттл к водителю
async def is_shuttle_binded(state):
    async with state.proxy() as data:
        try:
            cursor.execute(crimgo_db_crud.select_driver_id_from_shuttle, (data['shuttle_name'],))
            driver_id = cursor.fetchone()[0]
            return driver_id
        except (Exception, Error) as error:
            print("Ошибка при работе с is_shuttle_binded", error)
            return False

# Привзяка шаттла к водителю
async def bind_shuttle_to_driver(state, callback):
    # Ищем шаттл по имени
    async with state.proxy() as data:
        try:
            cursor.execute(crimgo_db_crud.update_driver_set_shift, (datetime.datetime.now(), callback.from_user.id))
            cursor.execute(crimgo_db_crud.update_shuttle_set_driver, (callback.from_user.id, datetime.datetime.now(), data['start_point'], data['route'], data['driver_chat_id'], data['shuttle_name']))
            connection.commit()            
            return True
        except (Exception, Error) as error:
            print("Ошибка при работе с bind_shuttle_to_driver", error)            
            return False

# Проверяем находится ли водитель в смене 
async def is_on_shift(message):    
    try:
        cursor.execute(crimgo_db_crud.select_driver_shift, (message.from_user.id,))
        on_shift = cursor.fetchone()[0]
        return on_shift
    except (Exception, Error) as error:
        print("Ошибка при работе с is_on_shift", error)
        return False

# Завершение смены
async def stop_driver_shift(message):
    try:
        cursor.execute(crimgo_db_crud.update_shuttle_remove_driver, (datetime.datetime.now(),))
        cursor.execute(crimgo_db_crud.update_driver_remove_shift, (datetime.datetime.now(),))
    except (Exception, Error) as error:
        print("Ошибка при работе с stop_driver_shift", error)

# Создание поездки
async def create_trip(state):
    try:
        async with state.proxy() as data:
            # создание рейса и привязка шаттла, бросит исключение из-за "null value in column "shuttle_id" violates not-null constraint"
            # Поиск шаттла на начальной остановке маршрута, сортировка по времени простоя
            cursor.execute(crimgo_db_crud.select_from_shuttle_order_by_timestamp, (data['route'], ))
            shuttle_id = cursor.fetchone()

            # Поиск ближайшего шаттла на противополжном маршруте, не считаю начальную остановку
            if shuttle_id is None:
                cursor.execute(crimgo_db_crud.select_from_shuttle_opposite_route, (data['opposite'], data['opposite']))
                shuttle_id = cursor.fetchone()
            # Поиск шаттла на противополжной начальной остановке
            if shuttle_id is None:
                cursor.execute(crimgo_db_crud.select_from_shuttle_order_by_timestamp, (data['opposite'], ))
                shuttle_id = cursor.fetchone()
            cursor.execute(crimgo_db_crud.insert_into_trip, (shuttle_id[0] ,'awaiting_passengers', data['route'],  datetime.datetime.now(), shuttle_id,datetime.datetime.now(), datetime.datetime.now() + config.MAX_WAIT_TIME, datetime.datetime.now() + config.MAX_WAIT_TIME + config.TRVL_TIME))
            trip_id = cursor.fetchone()[0]
            connection.commit()
            return trip_id
    except (Exception, Error) as error:
        print("Ошибка при работе с create_trip", error)
        return False

# Обнлвление времени
async def update_trip_set_time_delta(state, ADD_DELTA_TIME):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.update_trip_set_time_delta, (ADD_DELTA_TIME, ADD_DELTA_TIME, data['trip_id']))
            connection.commit()
            return True
    except (Exception, Error) as error:
        print("Ошибка при работе с update_trip_set_time_delta", error)
        return False    

# Проверка, если ли поездка по маршруту
async def is_trip_with_route(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_trip_id_status_awaiting_pass, (data['route'],))
            trip_id = cursor.fetchone()
            return trip_id
    except (Exception, Error) as error:
        print("Ошибка при работе с is_trip_with_route", error)
        return False

# Проверка на доступное кол-во мест
# НУЖНО ВЕРНУТЬ МЕСТА НА МЕСТО В СЛУЧАЕ НЕОПЛАТЫ
async def seat_availability(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.update_trip_decrement_seats, (int(data['seat']), datetime.datetime.now(), data['trip_id']))
            connection.commit()
            return True
    except (Exception, Error) as error:
        print("Ошибка при работе с seat_availability", error)
        return False

async def restore_booked_seats(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.update_trip_restore_seats, (int(data['seat']), data['trip_id']))
            connection.commit()
            return True
    except (Exception, Error) as error:
        print("Ошибка при работе с restore_booked_seats", error)
        return False

async def create_ticket(state, payment_id):
    try:
        async with state.proxy() as data:
            # ИД маршрута
            cursor.execute(crimgo_db_crud.select_route_by_trip_id, (data['trip_id'], ))
            route = cursor.fetchone()[0]
            if route  == 1:
                # Время до остановки
                cursor.execute(crimgo_db_crud.select_time_to_pp, (data['pickup_point'], data['route']))
                time_to_pp = cursor.fetchone()[0]

                # Время высадки, берется из поездки
                cursor.execute(crimgo_db_crud.select_trip_drop_time, (data['trip_id'], ))
                trip_drop_time = cursor.fetchone()[0]

                # Время начала рейса, берется из поездки
                cursor.execute(crimgo_db_crud.select_trip_start_time, (data['trip_id'], ))
                trip_start_time = cursor.fetchone()[0]
                # Используется время pickup point
                cursor.execute(crimgo_db_crud.insert_into_ticket ,(int(payment_id), data['trip_id'], data['pickup_point'], data['route'], data['seat'], data['otp'], (trip_start_time + timedelta(minutes = time_to_pp)), (trip_start_time + timedelta(minutes = time_to_pp)), data['drop_point'], data['route'], trip_drop_time, trip_drop_time))

            if route == 2:
                # Время до остановки
                cursor.execute(crimgo_db_crud.select_time_to_pp, (data['drop_point'], data['route']))
                time_to_dp = cursor.fetchone()[0]

                # Время высадки, берется из поездки
                #cursor.execute(crimgo_db_crud.select_trip_drop_time, (data['trip_id'], ))
                #trip_drop_time = cursor.fetchone()[0]

                # Время начала рейса, берется из поездки
                cursor.execute(crimgo_db_crud.select_trip_start_time, (data['trip_id'], ))
                trip_start_time = cursor.fetchone()[0]
                # Используется время drop point
                cursor.execute(crimgo_db_crud.insert_into_ticket ,(int(payment_id), data['trip_id'], data['pickup_point'], data['route'], data['seat'], data['otp'], trip_start_time, trip_start_time, data['drop_point'], data['route'], (trip_start_time + timedelta(minutes = time_to_dp)), (trip_start_time + timedelta(minutes = time_to_dp))))
            
            ticket_id = cursor.fetchone()[0]
            connection.commit()
            return ticket_id
    except (Exception, Error) as error:
        print("Ошибка при работе с create_ticket", error)
        return False

# Приблизительное время подбора
async def calculate_raw_pickup_time(state):
    try:
        async with state.proxy() as data:
            # Время создания
            cursor.execute(crimgo_db_crud.select_trip_start_time, (data['trip_id'],))
            trip_start_time = cursor.fetchone()[0]
            if data['route'] == 'К морю':
                # Время до остановки
                cursor.execute(crimgo_db_crud.select_time_to_pp, (data['pickup_point'], data['route']))
                time_to_pp = cursor.fetchone()[0]
                aprox_time = ((trip_start_time + config.TIME_OFFSET + timedelta(minutes = time_to_pp)).strftime("%H:%M"))
            if data['route'] == 'От моря':
                aprox_time = ((trip_start_time + config.TIME_OFFSET).strftime("%H:%M"))
            return aprox_time
    except (Exception, Error) as error:
        print("Ошибка при работе с calculate_raw_pickup_time", error)
        return False

# Проверка доступных поездок и назначение водителю
async def check_available_trip(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_trip_available, (data['shuttle_name'],))
            trip_details = cursor.fetchone()
            return trip_details
    except (Exception, Error) as error:
        print("Ошибка при работе с check_available_trip", error)
        return False

# Проверка доступных поездок после выполенния маршрута
async def check_available_trip_after_trip(driver_id):
    try:
        cursor.execute(crimgo_db_crud.select_trip_available_by_driver, (driver_id,))
        trip_details = cursor.fetchone()
        return trip_details
    except (Exception, Error) as error:
        print("Ошибка при работе с check_available_trip_after_trip", error)
        return False


# Детали поездки
async def trip_details(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_trip_details, (data['trip_id'],))
            trip_details = cursor.fetchone()
            return trip_details
    except (Exception, Error) as error:
        print("Ошибка при работе с trip_details", error)
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
            # если наполняемость больше 80%
            if (( (shuttle_capacity - trip_available_seats) / shuttle_capacity)*100 > 80):
                soonest_pp_time = ''
                # нужно обновить время подбора пассажиров
                if data['route'] == 'К морю':
                    cursor.execute(crimgo_db_crud.select_ticket_order_by_raw_pickup_time, (data['trip_id'],))
                    soonest_pp_time = cursor.fetchone()[0]
                     # берем ближайшее время и вычисляем время к билжайшему пассажиру
                    time_offset = soonest_pp_time - datetime.datetime.now()

                if data['route'] == 'От моря': 
                    cursor.execute(crimgo_db_crud.select_trip_start_time, (data['trip_id'],))
                    soonest_pp_time = cursor.fetchone()[0]
                    # берем время создания поездки
                    time_offset = soonest_pp_time - datetime.datetime.now()
                
                # Если в запасе есть 10 минут, меняем время старта и прибытия    
                if (time_offset > config.MIN_WAIT_TIME):
                    # Меняю время подбора для пассажиров
                    new_time = time_offset - config.MIN_WAIT_TIME

                    cursor.execute(crimgo_db_crud.update_ticket_set_final_time, (new_time, new_time, data['trip_id']))
                    # Меняем время начала и статус рейса
                    cursor.execute(crimgo_db_crud.update_trip_set_status_scheduled, (new_time, new_time, data['trip_id']))
                    connection.commit()

    except (Exception, Error) as error:
        print("Ошибка при работе с trip_status_review", error)
        return False

# Получить ID драйвера
async def get_driver_chat_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_driver_chat_id, (data['trip_id'],))
            driver_id = cursor.fetchone()
            return driver_id
    except (Exception, Error) as error:
        print("Ошибка при работе с get_driver_chat_id", error)
        return False

# Получить соббщение по поездке
async def get_message_text_trip_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_message_by_trip_id, (data['trip_id'],))
            text = cursor.fetchone()[0]
            return text
    except (Exception, Error) as error:
        print("Ошибка при работе с get_message_text_trip_id", error)
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
    except (Exception, Error) as error:
        print("Ошибка при работе с is_first_ticket", error)
        return False

async def set_shuttle_message_id(message_id, state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.update_shuttle_set_driver_message_id, (message_id, data['trip_id']))
            connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с set_shuttle_message_id", error)

async def get_dict_of_tickets_by_driver(from_user_id):
    try:
        cursor.execute(crimgo_db_crud.select_tickets_by_driver, (from_user_id,))
        tickets = cursor.fetchall()
        return tickets
    except (Exception, Error) as error:
        print("Ошибка при работе с get_dict_of_tickets_by_driver", error)
        return False

async def get_dict_of_tickets_by_driver_drop_point(from_user_id):
    try:
        cursor.execute(crimgo_db_crud.select_tickets_by_driver_dp, (from_user_id,))
        tickets = cursor.fetchall()
        return tickets
    except (Exception, Error) as error:
        print("Ошибка при работе с get_dict_of_tickets_by_driver_drop_point", error)
        return False

async def route_id_by_trip(from_user_id):
    try:
        cursor.execute(crimgo_db_crud.select_route_id_by_driver, (from_user_id,))
        route_id = cursor.fetchone()[0]
        return route_id
    except (Exception, Error) as error:
        print("Ошибка при работе с route_id_by_trip", error)
        return False

async def get_dict_of_tickets_by_shuttle_position(from_user_id, shuttle_position):
    try:
        cursor.execute(crimgo_db_crud.select_tickets_by_shuttle_position, (shuttle_position, from_user_id))
        pp_tickets = cursor.fetchone()[0]
        return pp_tickets
    except (Exception, Error) as error:
        print("Ошибка при работе с get_dict_of_tickets_by_shuttle_position", error)
        return False

async def save_message_id_and_text(state, text):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.insert_into_message, (data['trip_id'], text, text))
            connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с save_message_id_and_text", error)

async def get_message_id_and_text(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_message_by_trip, (data['trip_id'],))
            message_and_text = cursor.fetchone()[1]
            return message_and_text
    except (Exception, Error) as error:
        print("Ошибка при работе с get_message_id_and_text", error)

async def trip_status(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_status_from_trip, (data['trip_id'], ))
            status = cursor.fetchone()[0]
            return status
    except (Exception, Error) as error:
        print("Ошибка при работе с trip_status", error)
        return False

async def get_dict_of_tickets_by_trip(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_tickets_by_trip, (data['trip_id'],))
            tickets = cursor.fetchall()
            return tickets
    except (Exception, Error) as error:
        print("Ошибка при работе с get_dict_of_tickets_by_trip", error)
        return False

async def get_dict_of_drop_points_by_trip(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_drop_points_by_trip, (data['trip_id'],))
            tickets = cursor.fetchall()
            return tickets
    except (Exception, Error) as error:
        print("Ошибка при работе с get_dict_of_drop_points_by_trip", error)
        return False

async def get_trip_start_time_by_id(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_start_time_from_trip, (data['trip_id'],))
            start_time = cursor.fetchone()[0]
            return start_time
    except (Exception, Error) as error:
        print("Ошибка при работе с get_trip_start_time_by_id", error)
        return False

async def get_shuttle_position(callback):
    try:
        cursor.execute(crimgo_db_crud.select_current_possition_from_shuttle, (callback.from_user.id,))
        current_position = cursor.fetchone()[0]
        return current_position
    except (Exception, Error) as error:
        print("Ошибка при работе с get_shuttle_position", error)

async def set_shuttle_position(callback, route_id_by_trip):
    try:
        if route_id_by_trip == 1:
            # Берем список точек посадки
            cursor.execute(crimgo_db_crud.select_pickup_point_from_ticket, (callback.from_user.id, ))
        if route_id_by_trip == 2:
            # Берем точки высадки
            cursor.execute(crimgo_db_crud.select_drop_point_from_ticket, (callback.from_user.id, ))
        # pickup_point_list = cursor.fetchall()
        pickup_point_list = [item[0] for item in cursor.fetchall()]

        # Позиция шаттла
        cursor.execute(crimgo_db_crud.select_current_possition_from_shuttle, (callback.from_user.id,))
        shuttle_possition = cursor.fetchone()
        if (shuttle_possition[0] == 1 and pickup_point_list[0] != 1) or (shuttle_possition[0] == 9 and pickup_point_list[0] != 9):
            cursor.execute(crimgo_db_crud.update_shutlle_set_position, (pickup_point_list[0], callback.from_user.id))
            connection.commit()
        else:
            index = pickup_point_list.index(shuttle_possition[0])
            # TODO ПОТЕНЦИАЛЬНАЯ ОШИБКА
            counter = pickup_point_list.count(pickup_point_list[index])
            cursor.execute(crimgo_db_crud.update_shutlle_set_position, (pickup_point_list[index + counter], callback.from_user.id))
            connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с set_shuttle_position", error) 

    # Если шаттл на начальной точке, меняем позицию на первую из pickup_point_list
    # if shuttle_possition[0] == 1:
    #     cursor.execute('UPDATE shuttle SET current_position = %s WHERE driver_id = %s', (pickup_point_list[0][0], callback.from_user.id))
    #     connection.commit()
    # # В противном случае, ищем индекс входжения позиции шатла в pickup_point_list и меняем позицию на индекс вхождения + 1
    # else:
    #     index = pickup_point_list.index(shuttle_possition)
    #     cursor.execute('UPDATE shuttle SET current_position = %s WHERE driver_id = %s', (pickup_point_list[index +1][0], callback.from_user.id))
    #     connection.commit()
    
async def set_trip_status(callback, from_status, to_status):
    try:
        cursor.execute(crimgo_db_crud.update_trip_set_status, (to_status, from_status, callback.from_user.id))
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с set_trip_status", error) 

async def verify_pass_code(message, code):
    # Позиция шаттла
    try:
        cursor.execute(crimgo_db_crud.select_current_possition_from_shuttle, (message.from_user.id,))
        shuttle_position = cursor.fetchone()[0]
        # Ищем пас ID и забронированые места
        cursor.execute(crimgo_db_crud.select_pass_seat, (code, message.from_user.id))
        pass_id_seats = cursor.fetchone()
        # Гасим билет и отнимаем поедку
        cursor.execute(crimgo_db_crud.update_ticket_status, (shuttle_position, message.from_user.id, pass_id_seats[1], code))
        if cursor.rowcount == 1:
            cursor.execute(crimgo_db_crud.update_passenger_decrease_trip, (pass_id_seats[1], pass_id_seats[0]))
            if cursor.rowcount == 1:
                connection.commit()
                return True
        return False
    except (Exception, Error) as error:
        print("Ошибка при работе с verify_pass_code", error) 

# Проверка существует ли шаттл
async def check_shuttle_name_and_status(name):
    try:
        cursor.execute(crimgo_db_crud.select_shuttle_name_and_status, (name,))
        shuttle_exists = cursor.fetchone()[0]
        return shuttle_exists
    except (Exception, Error) as error:
        print("Ошибка при работе с check_shuttle_name_and_status", error) 

# Время подбора пасажира в билете
async def ticket_dp_time(ticket_id):
    try:
        cursor.execute(crimgo_db_crud.select_ticket_dp_time, (ticket_id,))
        dp_time = cursor.fetchone()[0]
        return dp_time
    except (Exception, Error) as error:
        print("Ошибка при работе с ticket_pp_time", error) 

# ИД маршрута из поездки
async def get_route(callback):
    try:
        cursor.execute(crimgo_db_crud.select_route_from_trip, (callback.from_user.id, ))
        route_id = cursor.fetchone()[0]
        return route_id
    except (Exception, Error) as error:
        print("Ошибка при работе с get_route", error) 

# Имя шаттла по ИД водителя
async def get_shuttle_name_by_driver(callback):
    try:
        cursor.execute(crimgo_db_crud.select_shuttle_name_by_driver, (callback.from_user.id, ))
        shuttle_name = cursor.fetchone()[0]
        return shuttle_name
    except (Exception, Error) as error:
        print("Ошибка при работе с get_shuttle_name_by_driver", error) 

async def set_shuttle_position_by_pp_name(new_position_name, route):
    try:
        cursor.execute(crimgo_db_crud.update_shutlle_set_position_where_pp_name, (new_position_name, route))
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с set_shuttle_position_by_pp_name", error)   

async def get_ending_station_by_route(route):
    try:
        cursor.execute(crimgo_db_crud.select_ending_station, (route, ))
        ending_station = cursor.fetchone()[0]
        return ending_station
    except (Exception, Error) as error:
        print("Ошибка при работе с get_ending_station_by_route", error)  

async def get_trip_finish_time(from_user_id):
    try:
        cursor.execute(crimgo_db_crud.select_finish_time_from_trip, (from_user_id, ))
        trip_finish_time = cursor.fetchone()[0]
        return trip_finish_time
    except (Exception, Error) as error:
        print("Ошибка при работе с get_trip_finish_time", error)

async def get_pp_location(pp_name, route_name):
    try:
        cursor.execute(crimgo_db_crud.select_pp_location_by_route, (pp_name, route_name))
        pp_location = cursor.fetchone()
        return pp_location
    except (Exception, Error) as error:
        print("Ошибка при работе с get_pp_location", error) 

async def save_pass_message_id(from_user_id, msg_id, chat_id):
    try:
        cursor.execute(crimgo_db_crud.update_passenger_set_msg_chat_id, (msg_id, chat_id, from_user_id))
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с save_pass_message_id", error)     

async def get_pass_trip_details(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_trip_pass_details, (data['trip_id'], ))
            pass_trip_details = cursor.fetchall()
            return pass_trip_details
    except (Exception, Error) as error:
        print("Ошибка при работе с get_pass_trip_details", error)

async def is_push_needed(state):
    try:
        async with state.proxy() as data:
            cursor.execute(crimgo_db_crud.select_trip_status, (data['trip_id'],))
            trip_status = cursor.fetchone()[0]
            if trip_status == 'awaiting_passengers' or 'scheduled':
                return True
            else: return False
    except (Exception, Error) as error:
        print("Ошибка при работе с is_push_needed", error)