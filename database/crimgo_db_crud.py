# -- Table: public.driver
create_table_driver = '''CREATE TABLE IF NOT EXISTS public.driver
(
    phone character(50) COLLATE pg_catalog."default" NOT NULL,
    telegram_id bigint NOT NULL,
    telegram_name character(100) COLLATE pg_catalog."default",
    name character(100) COLLATE pg_catalog."default" NOT NULL,
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
    phone character(50) COLLATE pg_catalog."default",
    "timestamp" timestamp without time zone NOT NULL,
    available_trips integer DEFAULT 0,
    telegram_name character(50) COLLATE pg_catalog."default",
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
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT shuttle_ref_shuttle_id_fk FOREIGN KEY (shuttle_id)
        REFERENCES public.shuttle (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT seats_nonnegative CHECK (available_seats >= 0) NOT VALID
)

TABLESPACE pg_default;'''

alter_table_trip_set_owner = '''ALTER TABLE IF EXISTS public.trip OWNER to postgres;'''


# -- Table: public.payment
create_table_payment = '''CREATE TABLE IF NOT EXISTS public.payment
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    total_amount double precision NOT NULL,
    telegram_payment_charge_id character(100) COLLATE pg_catalog."default",
    provider_payment_charge_id character(100) COLLATE pg_catalog."default",
    pass_id bigint NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    payment_type character(10) COLLATE pg_catalog."default" NOT NULL,
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
    name character(10) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT route_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;'''

alter_table_route_set_owner = '''ALTER TABLE IF EXISTS public.route OWNER to postgres;'''


# -- Table: public.shuttle
create_table_shuttle = '''CREATE TABLE IF NOT EXISTS public.shuttle
(
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
    name character(50) COLLATE pg_catalog."default" NOT NULL,
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
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT ticket_ref_pp_fk FOREIGN KEY (pickup_point)
        REFERENCES public.pickup_point (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT ticket_ref_trip_fk FOREIGN KEY (trip_id)
        REFERENCES public.trip (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;'''

alter_table_ticket_set_owner = '''ALTER TABLE IF EXISTS public.ticket OWNER to postgres;'''