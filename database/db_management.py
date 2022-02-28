# --
# -- PostgreSQL database dump
# --

# -- Dumped from database version 12.9 (Ubuntu 12.9-0ubuntu0.20.04.1)
# -- Dumped by pg_dump version 14.1

# -- Started on 2022-02-28 17:56:58 MSK

# SET statement_timeout = 0;
# SET lock_timeout = 0;
# SET idle_in_transaction_session_timeout = 0;
# SET client_encoding = 'UTF8';
# SET standard_conforming_strings = on;
# SELECT pg_catalog.set_config('search_path', '', false);
# SET check_function_bodies = false;
# SET xmloption = content;
# SET client_min_messages = warning;
# SET row_security = off;

# SET default_tablespace = '';

# SET default_table_access_method = heap;

# --
# -- TOC entry 203 (class 1259 OID 16525)
# -- Name: driver; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_driver = '''CREATE TABLE public.driver (
    phone character(50) NOT NULL,
    telegram_id bigint NOT NULL,
    telegram_name character(100),
    name character(100) NOT NULL,
    "timestamp" timestamp without time zone,
    on_shift boolean DEFAULT false NOT NULL,
    validated boolean DEFAULT false NOT NULL
);'''

alter_table_driver = '''ALTER TABLE public.driver OWNER TO postgres;'''

# --
# -- TOC entry 216 (class 1259 OID 16708)
# -- Name: message; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_message = '''CREATE TABLE public.message (
    trip_id bigint NOT NULL,
    text text NOT NULL
);'''

alter_table_message = '''ALTER TABLE public.message OWNER TO postgres;'''

# --
# -- TOC entry 202 (class 1259 OID 16502)
# -- Name: passenger; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_passenger = '''
CREATE TABLE public.passenger (
    telegram_id bigint NOT NULL,
    phone character(50),
    "timestamp" timestamp without time zone NOT NULL,
    available_trips integer DEFAULT 0,
    telegram_name character(50)
);'''

alter_table_passenger = '''ALTER TABLE public.passenger OWNER TO postgres;'''

# --
# -- TOC entry 207 (class 1259 OID 16594)
# -- Name: trip; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_trip = '''
CREATE TABLE public.trip (
    id integer NOT NULL,
    shuttle_id integer NOT NULL,
    status character varying(20) NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    route integer NOT NULL,
    creation_time timestamp without time zone NOT NULL,
    available_seats integer NOT NULL,
    start_time timestamp without time zone NOT NULL
);'''

alter_table_trip = '''ALTER TABLE public.trip OWNER TO postgres;'''

# --
# -- TOC entry 206 (class 1259 OID 16592)
# -- Name: path_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
# --

alter_table_trip_set_path_id_seq = '''
ALTER TABLE public.trip ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.path_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);'''


# --
# -- TOC entry 215 (class 1259 OID 16690)
# -- Name: payment; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_payment = '''
CREATE TABLE public.payment (
    id integer NOT NULL,
    total_amount double precision NOT NULL,
    telegram_payment_charge_id character(100),
    provider_payment_charge_id character(100),
    pass_id bigint NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    payment_type character(10) NOT NULL
);'''

alter_table_payment = '''ALTER TABLE public.payment OWNER TO postgres;'''

# --
# -- TOC entry 214 (class 1259 OID 16688)
# -- Name: payment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
# --

alter_table_payment_set_payment_id_seq = '''
ALTER TABLE public.payment ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.payment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);'''


# --
# -- TOC entry 211 (class 1259 OID 16656)
# -- Name: pickup_point; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_pickup_point = '''
CREATE TABLE public.pickup_point (
    id integer NOT NULL,
    name character varying(20) NOT NULL,
    route_id integer NOT NULL,
    time_to_pp integer
);'''

alter_table_pickup_point = '''ALTER TABLE public.pickup_point OWNER TO postgres;'''

# --
# -- TOC entry 210 (class 1259 OID 16654)
# -- Name: pickup_point_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
# --

alter_table_pickup_point_set_pickup_point_id_seq = '''
ALTER TABLE public.pickup_point ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.pickup_point_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);'''


# --
# -- TOC entry 209 (class 1259 OID 16626)
# -- Name: route; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_route = '''
CREATE TABLE public.route (
    id integer NOT NULL,
    name character(10) NOT NULL
);'''

alter_table_route = '''ALTER TABLE public.route OWNER TO postgres;'''

# --
# -- TOC entry 208 (class 1259 OID 16624)
# -- Name: route_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
# --

alter_table_route_route_id_seq = '''
ALTER TABLE public.route ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.route_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);'''

# --
# -- TOC entry 205 (class 1259 OID 16586)
# -- Name: shuttle; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_shuttle = '''
CREATE TABLE public.shuttle (
    id integer NOT NULL,
    name character(50) NOT NULL,
    capacity integer NOT NULL,
    driver_id bigint,
    current_position integer,
    "timestamp" timestamp without time zone NOT NULL,
    driver_chat_id bigint,
    driver_message_id bigint
);'''

alter_table_shuttle_set_owner = '''ALTER TABLE public.shuttle OWNER TO postgres;'''

# --
# -- TOC entry 204 (class 1259 OID 16584)
# -- Name: shuttle_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
# --

alter_table_shuttle_set_shuttle_id_seq = '''
ALTER TABLE public.shuttle ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.shuttle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);'''


# --
# -- TOC entry 212 (class 1259 OID 16666)
# -- Name: ticket; Type: TABLE; Schema: public; Owner: postgres
# --

create_table_ticket = '''
CREATE TABLE public.ticket (
    id integer NOT NULL,
    payment_id integer NOT NULL,
    trip_id integer NOT NULL,
    pickup_point integer NOT NULL,
    booked_seats integer NOT NULL,
    otp integer NOT NULL,
    raw_pickup_time timestamp without time zone NOT NULL,
    final_pickup_time timestamp without time zone NOT NULL,
    use boolean DEFAULT false NOT NULL
);'''

alter_table_ticket_set_owner = '''ALTER TABLE public.ticket OWNER TO postgres;'''

# --
# -- TOC entry 213 (class 1259 OID 16686)
# -- Name: ticket_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
# --

alter_table_ticket_set_ticket_id_seq = '''
ALTER TABLE public.ticket ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ticket_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);'''


# --
# -- TOC entry 2862 (class 2606 OID 16712)
# -- Name: message message_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --
alter_table_message_set_constraint_message_pkey = '''
ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (trip_id);'''


# --
# -- TOC entry 2846 (class 2606 OID 16564)
# -- Name: passenger passenger_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_passenger_set_constraint_passenger_pkey = '''
ALTER TABLE ONLY public.passenger
    ADD CONSTRAINT passenger_pkey PRIMARY KEY (telegram_id);'''


# --
# -- TOC entry 2852 (class 2606 OID 16598)
# -- Name: trip path_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_trip_set_constraint_path_pkey = '''
ALTER TABLE ONLY public.trip
    ADD CONSTRAINT path_pkey PRIMARY KEY (id);'''

# --
# -- TOC entry 2860 (class 2606 OID 16694)
# -- Name: payment payment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_payment_set_constraint_payment_pkey = '''
ALTER TABLE ONLY public.payment
    ADD CONSTRAINT payment_pkey PRIMARY KEY (id);'''


# --
# -- TOC entry 2856 (class 2606 OID 16660)
# -- Name: pickup_point pickup_point_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_pickup_point_set_constraint_pickup_point_pkey = '''
ALTER TABLE ONLY public.pickup_point
    ADD CONSTRAINT pickup_point_pkey PRIMARY KEY (id);'''


# --
# -- TOC entry 2854 (class 2606 OID 16630)
# -- Name: route route_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_route_set_constraint_route_pkey = '''
ALTER TABLE ONLY public.route
    ADD CONSTRAINT route_pkey PRIMARY KEY (id);'''


# --
# -- TOC entry 2843 (class 2606 OID 16653)
# -- Name: trip seats_nonnegative; Type: CHECK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_trip_set_constraint_seats_nonnegative = '''
ALTER TABLE public.trip
    ADD CONSTRAINT seats_nonnegative CHECK ((available_seats >= 0)) NOT VALID;'''


# --
# -- TOC entry 2850 (class 2606 OID 16590)
# -- Name: shuttle shuttle_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_shuttle_set_constraint_shuttle_pkey = '''
ALTER TABLE ONLY public.shuttle
    ADD CONSTRAINT shuttle_pkey PRIMARY KEY (id);'''

# --
# -- TOC entry 2848 (class 2606 OID 16649)
# -- Name: driver telegram_id; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_driver_set_constraint_telegram_id_pkey = '''
ALTER TABLE ONLY public.driver
    ADD CONSTRAINT telegram_id_pkey PRIMARY KEY (telegram_id);'''

# --
# -- TOC entry 2858 (class 2606 OID 16670)
# -- Name: ticket ticket_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_ticket_set_constraint_ticket_pkey = '''
ALTER TABLE ONLY public.ticket
    ADD CONSTRAINT ticket_pkey PRIMARY KEY (id);'''

# --
# -- TOC entry 2864 (class 2606 OID 16631)
# -- Name: trip path_ref_route_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_trip_set_constraint_route_ref_route_fk = '''
ALTER TABLE ONLY public.trip
    ADD CONSTRAINT route_ref_route_fk FOREIGN KEY (route) REFERENCES public.route(id) NOT VALID;'''

# --
# -- TOC entry 2869 (class 2606 OID 16695)
# -- Name: payment payment_ref_pass_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_payment_set_constraint_payment_ref_pass_fk = '''
ALTER TABLE ONLY public.payment
    ADD CONSTRAINT payment_ref_pass_fk FOREIGN KEY (pass_id) REFERENCES public.passenger(telegram_id);'''

# --
# -- TOC entry 2865 (class 2606 OID 16661)
# -- Name: pickup_point pp_ref_rout_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_pickup_point_set_constraint_pp_ref_rout_fk = '''
ALTER TABLE ONLY public.pickup_point
    ADD CONSTRAINT pp_ref_rout_fk FOREIGN KEY (route_id) REFERENCES public.route(id);'''


# --
# -- TOC entry 2863 (class 2606 OID 16738)
# -- Name: trip shuttle_ref_shuttle_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_trip_set_constraint_shuttle_ref_shuttle_id_fk = '''
ALTER TABLE ONLY public.trip
    ADD CONSTRAINT shuttle_ref_shuttle_id_fk FOREIGN KEY (shuttle_id) REFERENCES public.shuttle(id) NOT VALID;'''

# --
# -- TOC entry 2868 (class 2606 OID 16733)
# -- Name: ticket ticket_ref_payment_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_ticket_set_constraint_ticket_ref_payment_fk = '''
ALTER TABLE ONLY public.ticket
    ADD CONSTRAINT ticket_ref_payment_fk FOREIGN KEY (payment_id) REFERENCES public.payment(id) NOT VALID;'''

# --
# -- TOC entry 2866 (class 2606 OID 16681)
# -- Name: ticket ticket_ref_pp_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_ticket_set_constraint_ticket_ref_pp_fk = '''
ALTER TABLE ONLY public.ticket
    ADD CONSTRAINT ticket_ref_pp_fk FOREIGN KEY (pickup_point) REFERENCES public.pickup_point(id) NOT VALID;'''

# --
# -- TOC entry 2867 (class 2606 OID 16676)
# -- Name: ticket ticket_ref_trip_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
# --

alter_table_ticket_set_constraint_ticket_ref_trip_fk = '''
ALTER TABLE ONLY public.ticket
    ADD CONSTRAINT ticket_ref_trip_fk FOREIGN KEY (trip_id) REFERENCES public.trip(id) NOT VALID;'''


# -- Completed on 2022-02-28 17:56:58 MSK

# --
# -- PostgreSQL database dump complete
# --