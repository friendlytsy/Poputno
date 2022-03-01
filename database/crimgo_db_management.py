import psycopg2
from psycopg2 import Error

import database.crimgo_db_crud as crimgo_db_crud

def crimgo_check_tables(cursor, connection):
    print('Проверяем наличие таблиц, создаем если не существует')
    try:
    # -- Table: public.driver
        cursor.execute(crimgo_db_crud.create_table_driver)
        cursor.execute(crimgo_db_crud.alter_table_driver_set_owner)
    
    # -- Table: public.message
        cursor.execute(crimgo_db_crud.create_table_message)
        cursor.execute(crimgo_db_crud.alter_table_message_set_owner)    
        
    #-- Table: public.passenger
        cursor.execute(crimgo_db_crud.create_table_passenger)
        cursor.execute(crimgo_db_crud.alter_table_passenger_set_owner)    
        
    # -- Table: public.route
        cursor.execute(crimgo_db_crud.create_table_route)
        cursor.execute(crimgo_db_crud.alter_table_route_set_owner)

    # -- Table: public.shuttle    
        cursor.execute(crimgo_db_crud.create_table_shuttle)
        cursor.execute(crimgo_db_crud.alter_table_shuttle_set_owner)

    # -- Table: public.pickup_point
        cursor.execute(crimgo_db_crud.create_table_pickup_point)
        cursor.execute(crimgo_db_crud.alter_table_pickup_point_set_owner)

    #-- Table: public.trip
        cursor.execute(crimgo_db_crud.create_table_trip)
        cursor.execute(crimgo_db_crud.alter_table_trip_set_owner)

    # -- Table: public.payment
        cursor.execute(crimgo_db_crud.create_table_payment)
        cursor.execute(crimgo_db_crud.alter_table_payment_set_owner)
    
    # -- Table: public.ticket
        cursor.execute(crimgo_db_crud.create_table_ticket)
        cursor.execute(crimgo_db_crud.alter_table_ticket_set_owner)

        connection.commit()
        print('Готово')
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)