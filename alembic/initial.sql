--
-- PostgreSQL database dump
--

-- Dumped from database version 17.6 (Debian 17.6-1.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: currency; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.currency AS ENUM (
    'USD',
    'CLP'
);


--
-- Name: expensecategory; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.expensecategory AS ENUM (
    'GENERAL',
    'FOOD',
    'EDUCATION',
    'TRANSPORT',
    'SERVICES',
    'TRANSFERS',
    'CLOTHING',
    'ENTERTAINMENT',
    'SPORTS',
    'LOAN',
    'ATM_WITHDRAWAL',
    'INVESTMENTS',
    'HOUSING',
    'EXTERNAL_FOOD',
    'RECREATION',
    'ONLINE',
    'COMMISSIONS',
    'TRAVEL',
    'HEALTH',
    'FAMILY',
    'LAUNDRY',
    'BOOKS',
    'PURIFIED_WATER'
);


SET default_tablespace = '';

SET default_table_access_method = heap;


--
-- Name: expense; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expense (
    id integer NOT NULL,
    commerce character varying NOT NULL,
    amount double precision NOT NULL,
    currency public.currency NOT NULL,
    category public.expensecategory NOT NULL,
    date timestamp without time zone NOT NULL,
    description character varying
);


--
-- Name: expense_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.expense_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: expense_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.expense_id_seq OWNED BY public.expense.id;


--
-- Name: transference; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transference (
    id integer NOT NULL,
    recipient character varying NOT NULL,
    amount double precision NOT NULL,
    currency public.currency NOT NULL,
    category public.expensecategory NOT NULL,
    date timestamp without time zone NOT NULL,
    description character varying
);


--
-- Name: transference_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transference_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transference_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transference_id_seq OWNED BY public.transference.id;


--
-- Name: expense id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense ALTER COLUMN id SET DEFAULT nextval('public.expense_id_seq'::regclass);


--
-- Name: transference id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transference ALTER COLUMN id SET DEFAULT nextval('public.transference_id_seq'::regclass);


--
-- Name: expense expense_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expense
    ADD CONSTRAINT expense_pkey PRIMARY KEY (id);


--
-- Name: transference transference_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transference
    ADD CONSTRAINT transference_pkey PRIMARY KEY (id);


--
-- Name: ix_expense_commerce; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_expense_commerce ON public.expense USING btree (commerce);


--
-- Name: ix_transference_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_transference_recipient ON public.transference USING btree (recipient);


--
-- PostgreSQL database dump complete
--

