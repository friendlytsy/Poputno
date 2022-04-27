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
    message_id bigint NULL,
    chat_id bigint NULL,
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
    finish_time timestamp without time zone NOT NULL,
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
    time_to_pp integer NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    price integer NOT NULL DEFAULT 0,
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
# Активный - active
# Использован по назначению - used
# Аннулирован пассажиром(отказался через бота) - refused
# Аннулирован водителем(не пришел на посадку) - canceled
create_table_ticket = '''CREATE TABLE IF NOT EXISTS public.ticket
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    payment_id integer NOT NULL,
    trip_id integer NOT NULL,
    pickup_point integer NOT NULL,
    drop_point integer NOT NULL,
    booked_seats integer NOT NULL,
    otp integer NOT NULL,
    raw_pickup_time timestamp without time zone NOT NULL,
    final_pickup_time timestamp without time zone NOT NULL,
    raw_drop_time timestamp without time zone NOT NULL,
    final_drop_time timestamp without time zone NOT NULL,
    status character varying COLLATE pg_catalog."default",
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

# -- Table: public.cancel_details
create_table_cancel_reason = '''CREATE TABLE IF NOT EXISTS public.cancel_details
(
    payment_id integer NOT NULL,
    trip_id bigint NOT NULL,
    pass_id bigint NOT NULL,
    cancel_reason character varying COLLATE pg_catalog."default" NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    CONSTRAINT cancel_details_pkey PRIMARY KEY (payment_id)
)

TABLESPACE pg_default;'''

alter_table_cancel_reason = '''ALTER TABLE IF EXISTS public.cancel_details OWNER to postgres;'''

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
insert_into_trip = '''INSERT INTO trip (shuttle_id, status, route, creation_time, available_seats, timestamp, start_time, finish_time) VALUES (%s, %s, (SELECT id FROM route WHERE name = %s), %s, ((SELECT capacity FROM shuttle WHERE id = %s) - %s), %s, %s, %s) RETURNING id'''

# Обновление времени поездки
update_trip_set_time_delta = '''UPDATE trip SET (start_time, finish_time) = (start_time + %s, finish_time + %s) WHERE id = %s'''

# Возвращает ИД шаттла на маршоуте, который стоит дольше всех
select_from_shuttle_order_by_timestamp = '''SELECT id FROM shuttle WHERE driver_id is not null AND current_position = (select min(id) from pickup_point where route_id = (SELECT id FROM route WHERE name = %s)) order by timestamp DESC'''

# Возвращает кол-во поездок которые назначены на шаттл
select_count_of_trip_by_shuttle_id = '''SELECT COUNT(*) FROM trip WHERE shuttle_id = %s AND status = \'awaiting_passengers\' OR status = \'scheduled\''''

# Возвращает ближайшие шаттлы на противополжном маршруте, не считаю начальную остановку
select_from_shuttle_opposite_route = '''SELECT id FROM shuttle WHERE driver_id is not null AND current_position between (select min(id)+1 from pickup_point where route_id = (SELECT id FROM route WHERE name = %s)) and (select max(id) from pickup_point where route_id = (SELECT id FROM route WHERE name = %s)) order by timestamp DESC'''

# Возвращает ИД поездок с статусом ждем пассажиров
select_trip_id_status_awaiting_pass = '''SELECT id FROM trip WHERE route = (SELECT id FROM route WHERE name = %s) AND available_seats > 0 and status = \'awaiting_passengers\' ORDER BY creation_time'''

# Возвращает ИД поедок с статусом ждем пассажиров и определенного кол-ва мест
# select_trip_id_status_awaiting_pass_with_specified_seats = '''SELECT id FROM trip WHERE route = (SELECT id FROM route WHERE name = %s) AND available_seats >= %s and status = \'awaiting_passengers\' ORDER BY creation_time DESC'''

# Возвращает ИД поедок с статусом ждем пассажиров и резервирует места если они есть
update_trip_and_reserve_seats_return_id = '''UPDATE trip SET available_seats = available_seats - %s WHERE id = (SELECT id FROM trip WHERE route = (SELECT id FROM route WHERE name = %s) AND available_seats >= %s and status = \'awaiting_passengers\' ORDER BY creation_time FETCH FIRST ROW ONLY) RETURNING id'''

# Вычет заказанных мест из поездки
update_trip_decrement_seats = '''UPDATE trip SET (available_seats, timestamp) = (available_seats - %s, %s) WHERE id = %s'''

# Возврат мест если клиент отменил заказ
update_trip_restore_seats = '''UPDATE trip SET available_seats = available_seats + %s WHERE id = %s'''

# Возвращает время создания поездки
select_trip_start_time = '''SELECT start_time FROM trip WHERE id = %s'''

# Возвращает время до остановки 
select_time_to_pp = '''SELECT time_to_pp FROM pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)'''

# Создание записи билета
insert_into_ticket = '''INSERT INTO ticket (payment_id, trip_id, pickup_point, booked_seats, otp, raw_pickup_time, final_pickup_time, drop_point, status, raw_drop_time, final_drop_time) 
                        VALUES (%s, %s, (SELECT id from pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)), %s, %s, %s, %s, (SELECT id from pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)), \'active\', %s, %s) RETURNING id'''

# Возвращает детали поездки, t.id, r.name, t.start_time
select_trip_available = '''SELECT t.id, r.name, t.creation_time FROM trip AS t, route AS r WHERE t.shuttle_id = (SELECT id FROM shuttle WHERE name = %s) AND t.status = \'scheduled\' AND t.route = r.id'''

# Возвращает поездки по видителю
select_trip_available_by_driver = '''SELECT t.id, r.name, t.start_time FROM trip AS t, route AS r WHERE t.status = \'scheduled\' OR t.status = \'awaiting_passengers\' AND t.route = %s AND t.shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s) AND t.route = r.id ORDER BY t.start_time'''

# Возвращает позицию шаттла по ИД водителя 
select_shuttle_position = '''SELECT current_position FROM shuttle WHERE driver_id = %s'''

# Возвращает поездку по ИД
select_trip_details = '''SELECT t.id, r.name, t.start_time, t.finish_time FROM trip AS t, route as r WHERE t.id = %s and r.id = t.route'''

# Возвращает вместимость шаттла
select_capacity = '''SELECT capacity FROM shuttle WHERE id = (SELECT shuttle_id FROM trip WHERE id = %s)'''

# Возвращает кол-во доступных мест
select_available_seats = '''SELECT available_seats FROM trip WHERE id = %s'''

# Возвращает билеты поездки отсортированные по времени
select_ticket_order_by_raw_pickup_time = '''SELECT raw_pickup_time FROM ticket WHERE trip_id = %s ORDER BY raw_pickup_time'''

# Обновление финального времени подбора пассажиров
update_ticket_set_final_time = '''UPDATE ticket SET final_pickup_time = final_pickup_time - %s, final_drop_time = final_drop_time - %s WHERE trip_id = %s'''

# Обновление статуса поездки
update_trip_set_status_scheduled = '''UPDATE trip SET status = \'scheduled\', start_time = start_time - %s, finish_time = finish_time - %s WHERE id = %s'''

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

# Возвращает билеты по видителю
select_tickets_by_driver_dp = '''SELECT p.name, booked_seats, final_drop_time, p.id, pm.payment_type, pm.total_amount 
                                FROM ticket AS t, pickup_point AS p, payment as pm 
                                WHERE t.drop_point = p.id AND payment_id = pm.id AND trip_id = (SELECT id 
                                                                            FROM trip 
                                                                            WHERE status = \'started\' AND shuttle_id = (SELECT id 
                                                                                                                            FROM shuttle 
                                                                                                                            WHERE driver_id = %s)) 
                                ORDER BY final_drop_time'''

# Возвращает билеты по позиции шаттла и водителю
select_tickets_by_shuttle_position = '''SELECT otp FROM ticket WHERE pickup_point = %s AND status = \'active\' AND trip_id = (SELECT id 
                                                                            FROM trip 
                                                                            WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle 
                                                                                                                            WHERE driver_id = %s))'''

select_tickets_by_shuttle_position_with_refused = '''SELECT otp FROM ticket WHERE status = \'refused\' AND pickup_point = %s AND trip_id = (SELECT id 
                                                                            FROM trip 
                                                                            WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle 
                                                                                                                            WHERE driver_id = %s))'''

# Возвращает маршурт ИД по водителю
select_route_id_by_driver = '''SELECT route FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Создание записи в сообщениях
insert_into_message = '''INSERT INTO message (trip_id, text) VALUES (%s, %s) ON CONFLICT (trip_id) DO UPDATE SET text = %s'''

# Возвращает сообщения по ИД поездки
select_message_by_trip = '''SELECT * FROM message WHERE trip_id = %s'''

# Возвращает статус поездки по BL
select_status_from_trip = '''SELECT status FROM trip WHERE id = %s'''

# Возвращает билеты по поездке
select_tickets_by_trip = '''SELECT p.name, booked_seats, final_pickup_time FROM ticket AS t, pickup_point AS p WHERE t.pickup_point = p.id AND trip_id = %s ORDER BY final_pickup_time'''

select_drop_points_by_trip = '''SELECT p.name, booked_seats, final_drop_time FROM ticket AS t, pickup_point AS p WHERE t.drop_point = p.id AND trip_id = %s ORDER BY final_drop_time'''

# Возвращает время начала поездки
select_start_time_from_trip = '''SELECT start_time FROM trip WHERE id = %s'''

# Возвращает время начала поездки
select_finish_time_from_trip = '''SELECT finish_time FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Возвращает текущую позицию шаттла
select_current_possition_from_shuttle = '''SELECT current_position FROM shuttle WHERE driver_id = %s'''

# Возвращает список остановок в поездке
select_pickup_point_from_ticket = '''SELECT pickup_point FROM ticket WHERE trip_id = (SELECT id FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) ORDER BY final_pickup_time'''

# Обновляет позицию шаттла
update_shutlle_set_position = '''UPDATE shuttle SET current_position = %s WHERE driver_id = %s'''

# Обновление статуса параметром
update_trip_set_status = '''UPDATE trip SET status = %s WHERE status = %s AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Обновление статуса параметром через trip_id
update_trip_set_status_by_id = '''UPDATE trip SET status = %s WHERE id = %s AND status = \'awaiting_passengers\' OR status = \'scheduled\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Возвращает p.pass_id, t.booked_seats
select_pass_seat = '''SELECT p.pass_id, t.booked_seats FROM payment AS p, ticket AS t WHERE p.id = (SELECT payment_id FROM ticket WHERE status = \'active\' AND otp = %s AND trip_id = (SELECT id FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s))) AND p.id = t.payment_id'''

# Обновляет статус билета
update_ticket_status = '''UPDATE ticket SET status = \'used\' WHERE status = \'active\' AND pickup_point = %s AND trip_id = (SELECT id FROM trip where status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) AND booked_seats = %s AND otp = %s'''

# Обновляет статус билета, статус cancel
update_ticket_status_set_cancel = '''UPDATE ticket SET status = \'cancel\' WHERE status = \'active\' AND pickup_point = %s AND trip_id = (SELECT id FROM trip where status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) AND booked_seats = %s AND otp = %s'''

# Обновляет кол-во поездок у пассажира
update_passenger_decrease_trip = '''UPDATE passenger SET available_trips = available_trips - %s WHERE telegram_id = %s'''

# Возвращает булево значение по имени шаттла
select_shuttle_name_and_status = '''SELECT EXISTS (SELECT name FROM shuttle where name = %s AND driver_id IS NULL)'''

# Возвращает время из билета 
select_ticket_dp_time = '''SELECT final_drop_time FROM ticket WHERE id = %s'''

# Возвращает ИД маршрута
select_route_from_trip = '''SELECT route FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Возвращает имя шаттла
select_shuttle_name_by_driver = '''SELECT name FROM shuttle WHERE driver_id = %s'''

# Устанавливает позицию шаттла по имени точки
update_shutlle_set_position_where_pp_name = '''UPDATE shuttle SET current_position = (SELECT id FROM pickup_point WHERE name = %s and route_id = %s)'''

# Возвращает имя и время до конечной остановки по марщруту
select_ending_station = '''SELECT name FROM pickup_point WHERE route_id = %s ORDER BY time_to_pp DESC'''

# Возвращает ширину и долготу остановки по маршруту
select_pp_location_by_route = '''SELECT latitude, longitude FROM pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)'''

# Обновляет ИД чата и сообщения
update_passenger_set_msg_chat_id = '''UPDATE passenger SET message_id = %s, chat_id = %s WHERE telegram_id = %s'''

# Возвращает инфу по билетам для пуша пользователю 
#select_trip_pass_details = '''SELECT p.chat_id, p.message_id, t.final_pickup_time, pp.name, t.otp FROM ticket AS t, passenger AS p, pickup_point AS pp WHERE trip_id = %s AND t.status = 'active' AND t.pickup_point = pp.id'''
select_trip_pass_details = '''SELECT pay.pass_id, p.message_id, t.final_pickup_time, pp.name, t.otp, pay.id from ticket AS t, pickup_point AS pp, payment AS pay, passenger AS p WHERE trip_id = %s AND t.pickup_point = pp.id AND t.payment_id = pay.id AND pay.pass_id = p.telegram_id'''

# Возвращает время высадки
select_trip_drop_time = '''SELECT finish_time FROM trip WHERE status = \'awaiting_passengers\' AND id = %s'''

# Возвращает время начала поездки
select_trip_start_time = '''SELECT start_time FROM trip WHERE status = \'awaiting_passengers\' AND id = %s'''

# Возвращает ИД маршрута по поездке
select_route_by_trip_id = '''SELECT route FROM trip WHERE id = %s'''

# Возвращает точки высадки
select_drop_point_from_ticket = '''SELECT drop_point FROM ticket WHERE trip_id = (SELECT id FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)) ORDER BY final_drop_time'''

# Возвращает статус поездки
select_trip_status = '''SELECT t.status FROM trip AS t, shuttle AS s, pickup_point AS p WHERE t.id = %s and s.current_position = (select min(id) from pickup_point WHERE route_id = t.route)'''

# Возвращает сообщение для пуша 
select_message_by_trip_id = '''SELECT text FROM message WHERE trip_id = %s'''

# Возвращает стоимость одного места
select_price_from_pp = '''SELECT price FROM pickup_point WHERE name = %s AND route_id = (SELECT id FROM route WHERE name = %s)'''

# Возвращает стоимость поездки
select_total_amount = '''SELECT total_amount FROM payment WHERE id = %s'''

# Возвращает кол-во водителей в смене
select_count_from_driver_where_on_shift = '''SELECT COUNT(*) FROM driver WHERE on_shift = true'''

# Возвращает имя водителя по ID поездки
select_name_from_driver = '''SELECT name FROM driver WHERE telegram_id = (SELECT driver_id FROM shuttle WHERE id = (SELECT shuttle_id FROM trip WHERE id = %s))'''

# Возвращает точку высадки
select_drop_point_from_pp = '''SELECT name FROM pickup_point WHERE id = (SELECT drop_point FROM ticket WHERE trip_id = %s and id = %s)'''

# Возвращает тотал 
select_total_amount_from_payment_by_trip_id = '''SELECT total_amount FROM payment WHERE id = (SELECT payment_id FROM ticket WHERE trip_id = %s and id = %s)'''

# Возвращает true/false если назначены поездки
select_is_assigned_on_driver = '''SELECT EXISTS (SELECT FROM trip WHERE status = \'scheduled\' or status = \'awaiting_passengers\' AND shuttle_id = (SELECT id from shuttle where driver_id = %s))'''

# Возвращает ИД водителя по поездке
select_driver_id_from_trip = '''SELECT s.driver_id FROM shuttle AS s, trip AS t WHERE t.id = %s AND t.shuttle_id = s.id'''

# Возвращает ИД поездки по водителю
select_id_from_trip_by_driver = '''SELECT id FROM trip WHERE status = \'started\' AND shuttle_id = (SELECT id FROM shuttle WHERE driver_id = %s)'''

# Возвращает ИД поездки по пассажиру
select_trip_id_by_payment_id = '''SELECT trip_id FROM ticket WHERE status = \'active\' AND payment_id = %s'''

# Вставка причины отказа
insert_into_cancel_details = '''INSERT INTO cancel_details (trip_id, pass_id, payment_id, cancel_reason, timestamp) VALUES (%s, %s, %s, %s, %s)'''

# Обновление статуса билета
update_ticket_set_refused = '''UPDATE ticket SET status = \'refused\' WHERE trip_id = %s AND status = \'active\' AND payment_id =  %s'''