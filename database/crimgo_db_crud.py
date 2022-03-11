##################################################
#               СОЗДАНИЕ ТАБЛИЦ БД               #
##################################################
# -- Table: public.driver
create_table_driver = '''CREATE TABLE IF NOT EXISTS public.driver
(
    phone character varying(50) COLLATE pg_catalog."default" NOT NULL,
    telegram_id bigint NOT NULL,
    telegram_name character varying(100) COLLATE pg_catalog."default",
    name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "timestamp" timestamp without time zone,
    on_shift boolean NOT NULL DEFAULT false,
    validated boolean NOT NULL DEFAULT false,
    CONSTRAINT telegram_id PRIMARY KEY (telegram_id)
)

TABLESPACE pg_default;'''

alter_table_driver_set_owner = '''ALTER TABLE IF EXISTS public.driver OWNER to postgres;'''

# -- Table: public.message
create_table_message = '''CREATE TABLE IF NOT EXISTS public.message
(
    trip_id bigint NOT NULL,
    text text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT message_pkey PRIMARY KEY (trip_id)
)

TABLESPACE pg_default;'''

alter_table_message_set_owner = '''ALTER TABLE IF EXISTS public.message OWNER to postgres;'''

#-- Table: public.passenger
create_table_passenger = '''CREATE TABLE IF NOT EXISTS public.passenger
(
    telegram_id bigint NOT NULL,
    phone character varying(50) COLLATE pg_catalog."default",
    "timestamp" timestamp without time zone NOT NULL,
    available_trips integer DEFAULT 0,
    telegram_name character varying(50) COLLATE pg_catalog."default",
    CONSTRAINT passenger_pkey PRIMARY KEY (telegram_id)
)

TABLESPACE pg_default;'''

alter_table_passenger_set_owner = '''ALTER TABLE IF EXISTS public.passenger OWNER to postgres;'''


#-- Table: public.trip
create_table_trip = '''CREATE TABLE IF NOT EXISTS public.trip
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    shuttle_id integer NOT NULL,
    status character varying(20) COLLATE pg_catalog."default" NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    route integer NOT NULL,
    creation_time timestamp without time zone NOT NULL,
    available_seats integer NOT NULL,
    start_time timestamp without time zone NOT NULL,
    CONSTRAINT path_pkey PRIMARY KEY (id),
    CONSTRAINT path_ref_route_fk FOREIGN KEY (route)
        REFERENCES public.route (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT shuttle_ref_shuttle_id_fk FOREIGN KEY (shuttle_id)
        REFERENCES public.shuttle (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT seats_nonnegative CHECK (available_seats >= 0)
)

TABLESPACE pg_default;'''

alter_table_trip_set_owner = '''ALTER TABLE IF EXISTS public.trip OWNER to postgres;'''


# -- Table: public.payment
create_table_payment = '''CREATE TABLE IF NOT EXISTS public.payment
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    total_amount double precision NOT NULL,
    telegram_payment_charge_id character varying(100) COLLATE pg_catalog."default",
    provider_payment_charge_id character varying(100) COLLATE pg_catalog."default",
    pass_id bigint NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    payment_type character varying(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT payment_pkey PRIMARY KEY (id),
    CONSTRAINT payment_ref_pass_fk FOREIGN KEY (pass_id)
        REFERENCES public.passenger (telegram_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;'''

alter_table_payment_set_owner = '''ALTER TABLE IF EXISTS public.payment OWNER to postgres;'''


# -- Table: public.pickup_point
create_table_pickup_point = '''
CREATE TABLE IF NOT EXISTS public.pickup_point
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    name character varying(20) COLLATE pg_catalog."default" NOT NULL,
    route_id integer NOT NULL,
    time_to_pp integer,
    CONSTRAINT pickup_point_pkey PRIMARY KEY (id),
    CONSTRAINT pp_ref_rout_fk FOREIGN KEY (route_id)
        REFERENCES public.route (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;'''

alter_table_pickup_point_set_owner = '''ALTER TABLE IF EXISTS public.pickup_point OWNER to postgres;'''


# -- Table: public.route
create_table_route = '''CREATE TABLE IF NOT EXISTS public.route
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    name character varying(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT route_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;'''

alter_table_route_set_owner = '''ALTER TABLE IF EXISTS public.route OWNER to postgres;'''


# -- Table: public.shuttle
create_table_shuttle = '''CREATE TABLE IF NOT EXISTS public.shuttle
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    capacity integer NOT NULL,
    driver_id bigint,
    current_position integer,
    "timestamp" timestamp without time zone NOT NULL,
    driver_chat_id bigint,
    driver_message_id bigint,
    CONSTRAINT shuttle_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;'''

alter_table_shuttle_set_owner = '''ALTER TABLE IF EXISTS public.shuttle OWNER to postgres;'''


# -- Table: public.ticket
create_table_ticket = '''CREATE TABLE IF NOT EXISTS public.ticket
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    payment_id integer NOT NULL,
    trip_id integer NOT NULL,
    pickup_point integer NOT NULL,
    booked_seats integer NOT NULL,
    otp integer NOT NULL,
    raw_pickup_time timestamp without time zone NOT NULL,
    final_pickup_time timestamp without time zone NOT NULL,
    use boolean NOT NULL DEFAULT false,
    CONSTRAINT ticket_pkey PRIMARY KEY (id),
    CONSTRAINT ticket_ref_payment_fk FOREIGN KEY (payment_id)
        REFERENCES public.payment (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT ticket_ref_pp_fk FOREIGN KEY (pickup_point)
        REFERENCES public.pickup_point (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT ticket_ref_trip_fk FOREIGN KEY (trip_id)
        REFERENCES public.trip (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;'''

alter_table_ticket_set_owner = '''ALTER TABLE IF EXISTS public.ticket OWNER to postgres;'''

##################################################
#                   SQL ЗАПРОСЫ                  #
##################################################

# Создание записи водителя
insert_into_driver = '''INSERT INTO driver (telegram_id, telegram_name, name, phone, timestamp) VALUES (%s, %s, %s, %s, %s)'''

# Получение телефона водителя
select_driver_phone = '''SELECT phone FROM driver WHERE phone = %s'''

# Проверка поля validated водителя
select_driver_validated = '''SELECT validated FROM driver WHERE telegram_id = %s'''

# Обновления поля validated
update_driver_set_validated = '''UPDATE driver SET validated = TRUE WHERE phone = %s'''

# Создание записи шатла
insert_into_shuttle = '''INSERT INTO shuttle (name, capacity, timestamp) VALUES (%s, %s, %s)'''

# Возвращает ИД пользователя
select_user_id = '''SELECT telegram_id from passenger where telegram_id = %s'''

# Создание записи пользователя
insert_into_passenger = '''INSERT INTO passenger (telegram_id, telegram_name, phone, timestamp) VALUES (%s, %s, %s, %s)'''

# Создание записи оплаты
insert_into_payment = '''INSERT INTO payment (total_amount, telegram_payment_charge_id, provider_payment_charge_id, pass_id, payment_type, timestamp) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id'''

# Обновление кол-ва поездок пассажира
udpate_passenger_increment_trip = '''UPDATE passenger SET (available_trips, timestamp) = (available_trips + %s, %s) WHERE telegram_id = %s'''

# Возвращает ИД водителя
select_driver_id = '''SELECT telegram_id from driver where telegram_id = %s'''

# Возвращает ИД водителя из таблицы shuttle
select_driver_id_from_shuttle = '''SELECT driver_id FROM shuttle WHERE name = %s'''

# Обновляет поле on_shift
update_driver_set_shift = '''UPDATE driver SET (on_shift, timestamp) = (TRUE, %s) WHERE telegram_id = %s'''

# Обновляет поле driver_id, timestamp, current_position, driver_chat_id
update_shuttle_set_driver = '''UPDATE shuttle SET (driver_id, timestamp, current_position, driver_chat_id) = (%s, %s, (SELECT id FROM pickup_point WHERE name = %s AND route_id = %s), %s) WHERE name = %s'''

# Возвращает статус смены
select_driver_shift = '''SELECT on_shift FROM driver where telegram_id = %s'''

# Обновляет поле driver_id, timestamp, current_position, driver_chat_id
update_shuttle_remove_driver = '''UPDATE shuttle SET (driver_id, current_position, driver_chat_id, driver_message_id, timestamp) = (null, null, null, null, %s)'''

# Обновляет поле on_shift
update_driver_remove_shift = '''UPDATE driver SET (on_shift, timestamp) = (false, %s)'''

# Создание записи поездки
insert_into_trip = '''INSERT INTO trip (shuttle_id, status, route, creation_time, available_seats, timestamp, start_time) VALUES ((SELECT id FROM shuttle WHERE driver_id IS NOT NULL), %s, (SELECT id FROM route WHERE name = %s), %s, (SELECT capacity FROM shuttle WHERE driver_id IS NOT NULL), %s, %s) RETURNING id'''

# Возвращает ИД поедок с статусом ждем пассажиров
select_trip_id_status_awaiting_pass = '''SELECT id FROM trip WHERE route = (SELECT id FROM route WHERE name = %s) AND available_seats > 0 and status = \'awaiting_passengers\''''

# Вычет заказанных мест из поездки
update_trip_decrement_seats = '''UPDATE trip SET (available_seats, timestamp) = (available_seats - %s, %s) WHERE id = %s'''

# Возврат мест если клиент отменил заказ
update_trip_restore_seats = '''UPDATE trip SET available_seats = available_seats + %s WHERE id = %s'''

# Возвращает время создания поездки
select_trip_creation_time = '''SELECT creation_time FROM trip WHERE id = %s'''

# Возвращает время до остановки 
select_time_to_pp = '''SELECT time_to_pp FROM pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)'''

# Создание записи билета
insert_into_ticket = '''INSERT INTO ticket (payment_id, trip_id, pickup_point, booked_seats, otp, raw_pickup_time, final_pickup_time) VALUES (%s, %s, (SELECT id from pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)), %s, %s, %s, %s) RETURNING id'''

# Возвращает детали поездки, t.id, r.name, t.start_time
select_trip_available = '''SELECT t.id, r.name, t.creation_time FROM trip AS t, route AS r WHERE t.shuttle_id = (SELECT id FROM shuttle WHERE name = %s) AND t.status = \'scheduled\' AND t.route = r.id'''

select_trip_details = '''SELECT t.id, r.name, t.start_time FROM trip AS t, route as r WHERE t.id = %s and r.id = t.route'''

# Возвращает вместимость шаттла
select_capacity = '''SELECT capacity FROM shuttle WHERE id = (SELECT shuttle_id FROM trip WHERE id = %s)'''

# Возвращает кол-во доступных мест
select_available_seats = '''SELECT available_seats FROM trip WHERE id = %s'''

# Возвращает билеты поездки отсортированные по времени
select_ticket_order_by_raw_pickup_time = '''SELECT raw_pickup_time FROM ticket WHERE trip_id = %s ORDER BY raw_pickup_time'''

# Обновление финального времени подбора пассажиров
update_ticket_set_final_time = '''UPDATE ticket SET final_pickup_time = final_pickup_time - %s WHERE trip_id = %s'''

# Обновление статуса поездки
update_trip_set_status_scheduled = '''UPDATE trip SET status = \'scheduled\', start_time = start_time - %s WHERE id = %s'''

# Возвращает чат ИД 
select_driver_chat_id = '''SELECT s.driver_chat_id, s.driver_message_id FROM trip AS t, shuttle AS s WHERE t.id = %s AND t.shuttle_id = s.id'''

# Возвращает кол-во билетов в поездке
select_count_id_from_ticket = '''SELECT COUNT(id) FROM ticket WHERE trip_id = %s'''

# Обновление driver_message_id
update_shuttle_set_driver_message_id = '''UPDATE shuttle SET driver_message_id = %s WHERE id = (SELECT shuttle_id FROM trip WHERE id = %s)'''

# Возвращает билеты по видителю
select_tickets_by_driver = '''SELECT p.name, booked_seats, final_pickup_time, p.id, pm.payment_type, pm.total_amount 
                                FROM ticket AS t, pickup_point AS p, payment as pm 
                                WHERE t.pickup_point = p.id AND payment_id = pm.id AND trip_id = (SELECT id 
                                                                            FROM trip 
                                                                            WHERE status = \'started\' AND shuttle_id = (SELECT id 
                                                                                                                            FROM shuttle 
                                                                                                                            WHERE driver_id = %s)) 
                                ORDER BY final_pickup_time'''

# Создание записи в сообщениях
insert_into_message = '''INSERT INTO message (trip_id, text) VALUES (%s, %s) ON CONFLICT (trip_id) DO UPDATE SET text = %s'''

# Возвращает сообщения по ИД поездки
select_message_by_trip = '''SELECT * FROM message WHERE trip_id = %s'''

# Возвращает статус поездки по BL
select_status_from_trip = '''SELECT status FROM trip WHERE id = %s'''

# Возвращает билеты по поездке
select_tickets_by_trip = '''SELECT p.name, booked_seats, final_pickup_time FROM ticket AS t, pickup_point AS p WHERE t.pickup_point = p.id AND trip_id = %s ORDER BY final_pickup_time'''

# Возвращает время начала поездки
select_start_time_from_trip = '''SELECT start_time FROM trip WHERE id = %s'''

# Возвращает текущую позицию шаттла
select_current_possition_from_shuttle = '''SELECT current_position FROM shuttle WHERE driver_id = %s'''

# Возвращает список остановок в поездке
select_pickup_point_from_ticket = '''SELECT pickup_point FROM ticket WHERE trip_id = (SELECT id FROM trip where status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) ORDER BY final_pickup_time'''

# Обновляет позицию шаттла
update_shutlle_set_position = '''UPDATE shuttle SET current_position = %s WHERE driver_id = %s'''

# Обновление статуса параметром
update_trip_set_status = '''UPDATE trip SET status = %s WHERE status = %s AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Возвращает p.pass_id, t.booked_seats
select_pass_seat = '''SELECT p.pass_id, t.booked_seats FROM payment AS p, ticket AS t WHERE p.id = (SELECT payment_id FROM ticket WHERE use = False AND otp = %s AND trip_id = (SELECT id FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s))) AND p.id = t.payment_id'''

# Обновляет статус билета
update_ticket_status = '''UPDATE ticket SET use = True WHERE use = False AND pickup_point = %s AND trip_id = (SELECT id FROM trip where status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) AND booked_seats = %s AND otp = %s'''

# Обновляет кол-во поездок у пассажира
update_passenger_decrease_trip = '''UPDATE passenger SET available_trips = available_trips - %s WHERE telegram_id = %s'''

# Возвращает булево значение по имени шаттла
select_shuttle_name_and_status = '''SELECT EXISTS (SELECT name FROM shuttle where name = %s AND driver_id IS NULL)'''

# Возвращает время из билета 
select_ticket_pp_time = '''SELECT final_pickup_time FROM ticket WHERE id = %s'''

# Возвращает ИД маршрута
select_route_from_trip = '''SELECT route FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Возвращает имя шаттла
select_shuttle_name_by_driver = '''SELECT name FROM shuttle WHERE driver_id = %s'''

# Устанавливает позицию шаттла по имени точки
update_shutlle_set_position_where_pp_name = '''UPDATE shuttle SET current_position = (SELECT id FROM pickup_point WHERE name = %s and route_id = %s)'''