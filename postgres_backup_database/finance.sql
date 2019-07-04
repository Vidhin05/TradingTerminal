toc.dat                                                                                             0000600 0004000 0002000 00000017743 13507510031 0014446 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        PGDMP       %                    w            tradingterminal    11.3    11.3     �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                       false         �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                       false         �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                       false         �           1262    33065    tradingterminal    DATABASE     �   CREATE DATABASE tradingterminal WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';
    DROP DATABASE tradingterminal;
             vidhin    false         �            1259    33109    option_post    TABLE     �  CREATE TABLE public.option_post (
    option_id integer NOT NULL,
    writer_id integer NOT NULL,
    holder_id integer NOT NULL,
    stock_symbol text NOT NULL,
    option_type text NOT NULL,
    option_price real NOT NULL,
    strike_price real NOT NULL,
    num_of_shares integer NOT NULL,
    transaction_date text NOT NULL,
    is_available text DEFAULT 'Yes'::text NOT NULL,
    expiry_date text NOT NULL
);
    DROP TABLE public.option_post;
       public         postgres    false         �            1259    33150    option_transaction    TABLE     �  CREATE TABLE public.option_transaction (
    option_id integer NOT NULL,
    writer_id integer NOT NULL,
    holder_id integer NOT NULL,
    stock_symbol text NOT NULL,
    option_type text NOT NULL,
    option_price real NOT NULL,
    strike_price real NOT NULL,
    num_of_shares integer NOT NULL,
    transaction_date text NOT NULL,
    is_available text DEFAULT 'Yes'::text NOT NULL,
    expiry_date text NOT NULL
);
 &   DROP TABLE public.option_transaction;
       public         postgres    false         �            1259    33169    transactions    TABLE     �   CREATE TABLE public.transactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    symbol text NOT NULL,
    price real NOT NULL,
    quantity integer NOT NULL,
    transaction_date text NOT NULL
);
     DROP TABLE public.transactions;
       public         postgres    false         �            1259    33167    transactions_id_seq    SEQUENCE     |   CREATE SEQUENCE public.transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.transactions_id_seq;
       public       postgres    false    200         �           0    0    transactions_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;
            public       postgres    false    199         �            1259    33066    users    TABLE     �   CREATE TABLE public.users (
    id integer NOT NULL,
    username text NOT NULL,
    hash text NOT NULL,
    cash real DEFAULT 10000 NOT NULL,
    assets real DEFAULT 0 NOT NULL,
    last_update_time text NOT NULL
);
    DROP TABLE public.users;
       public         postgres    false                    2604    33172    transactions id    DEFAULT     r   ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);
 >   ALTER TABLE public.transactions ALTER COLUMN id DROP DEFAULT;
       public       postgres    false    199    200    200         �          0    33109    option_post 
   TABLE DATA               �   COPY public.option_post (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM stdin;
    public       postgres    false    197       3211.dat �          0    33150    option_transaction 
   TABLE DATA               �   COPY public.option_transaction (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM stdin;
    public       postgres    false    198       3212.dat �          0    33169    transactions 
   TABLE DATA               ^   COPY public.transactions (id, user_id, symbol, price, quantity, transaction_date) FROM stdin;
    public       postgres    false    200       3214.dat �          0    33066    users 
   TABLE DATA               S   COPY public.users (id, username, hash, cash, assets, last_update_time) FROM stdin;
    public       postgres    false    196       3210.dat �           0    0    transactions_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.transactions_id_seq', 52, true);
            public       postgres    false    199         	           2606    33117    option_post option_post_pkey 
   CONSTRAINT     a   ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT option_post_pkey PRIMARY KEY (option_id);
 F   ALTER TABLE ONLY public.option_post DROP CONSTRAINT option_post_pkey;
       public         postgres    false    197                    2606    33177    transactions transactions_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.transactions DROP CONSTRAINT transactions_pkey;
       public         postgres    false    200                    2606    33075    users users_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public         postgres    false    196                    1259    33133    fki_holder_if    INDEX     J   CREATE INDEX fki_holder_if ON public.option_post USING btree (holder_id);
 !   DROP INDEX public.fki_holder_if;
       public         postgres    false    197                    1259    33149    fki_writer_id    INDEX     J   CREATE INDEX fki_writer_id ON public.option_post USING btree (writer_id);
 !   DROP INDEX public.fki_writer_id;
       public         postgres    false    197                    2606    33134    option_post holder_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT holder_id FOREIGN KEY (holder_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 ?   ALTER TABLE ONLY public.option_post DROP CONSTRAINT holder_id;
       public       postgres    false    3077    196    197                    2606    33157    option_transaction holder_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_transaction
    ADD CONSTRAINT holder_id FOREIGN KEY (holder_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 F   ALTER TABLE ONLY public.option_transaction DROP CONSTRAINT holder_id;
       public       postgres    false    3077    198    196                    2606    33178    transactions user_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 >   ALTER TABLE ONLY public.transactions DROP CONSTRAINT user_id;
       public       postgres    false    3077    196    200                    2606    33144    option_post writer_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT writer_id FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 ?   ALTER TABLE ONLY public.option_post DROP CONSTRAINT writer_id;
       public       postgres    false    197    196    3077                    2606    33162    option_transaction writer_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_transaction
    ADD CONSTRAINT writer_id FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 F   ALTER TABLE ONLY public.option_transaction DROP CONSTRAINT writer_id;
       public       postgres    false    196    198    3077                                     3211.dat                                                                                            0000600 0004000 0002000 00000001300 13507510031 0014225 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        4	4	4	GOOG	CALL	4	60	1	Fri Jun 21 23:15:23 2019	Yes	Sat Jul 20 23:15:23 2019
7	2	2	GOOGL	PUT	1	60	5	Fri Jun 21 23:15:26 2019	Yes	Sat Jul 20 23:15:23 2019
8	5	5	AAPL	PUT	3	90	4	Fri Jun 21 23:15:27 2019	Yes	Sat Jul 20 23:15:23 2019
9	4	4	IBB	CALL	5	100	5	Fri Jun 21 23:15:28 2019	Yes	Sat Jul 20 23:15:23 2019
11	5	5	AAPL	CALL	3	50	3	Fri Jun 21 23:15:30 2019	Yes	Sat Jul 20 23:15:23 2019
13	3	2	AAPL	PUT	3	30	3	Sat Jun 22 00:07:49 2019	Yes	Sat Jul 20 23:15:23 2019
15	1	1	AAPL	PUT	1	40	5	Fri Jun 21 23:15:34 2019	Yes	Sat Jul 20 23:15:23 2019
17	3	3	GOOGL	PUT	1	60	5	Fri Jun 21 23:15:36 2019	Yes	Sat Jul 20 23:15:23 2019
21	2	2	GOOGL	CALL	10	1000	3	Sat Jun 22 00:09:30 2019	Yes	Sat Jul 20 23:15:23 2019
\.


                                                                                                                                                                                                                                                                                                                                3212.dat                                                                                            0000600 0004000 0002000 00000002065 13507510031 0014237 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        3	3	4	AAPL	PUT	1	30	3	Sun Jun 23 23:21:27 2019	Yes	Sun Jun 23 23:21:27 2019
2	2	4	GOOG	PUT	2	40	2	Fri Jun 21 23:21:31 2019	Yes	Sun Jun 23 23:21:27 2019
5	1	4	AAPL	PUT	1	40	5	Fri Jun 21 23:21:35 2019	Yes	Sun Jun 23 23:21:27 2019
6	5	3	IBB	CALL	6	40	5	Fri Jun 21 23:22:08 2019	No	Sun Jun 23 23:21:27 2019
10	1	3	IBB	CALL	2	200	6	Fri Jun 21 23:22:15 2019	Yes	Sun Jun 23 23:21:27 2019
13	3	2	AAPL	PUT	1	30	3	Fri Jun 21 23:23:55 2019	No	Sun Jun 23 23:21:27 2019
12	2	1	GOOG	PUT	2	40	2	Fri Jun 21 23:25:00 2019	Yes	Sun Jun 23 23:21:27 2019
18	4	1	AAPL	PUT	3	90	4	Fri Jun 21 23:25:08 2019	Yes	Sun Jun 23 23:21:27 2019
20	3	5	IBB	CALL	2	200	6	Fri Jun 21 23:26:15 2019	Yes	Sun Jun 23 23:21:27 2019
1	4	3	AAPL	CALL	3	50	3	Fri Jun 21 23:22:03 2019	No	Sun Jun 23 23:21:27 2019
19	5	2	IBB	CALL	5	100	5	Fri Jun 21 23:23:45 2019	No	Sun Jun 23 23:21:27 2019
16	2	5	IBB	CALL	6	40	5	Fri Jun 21 23:26:23 2019	No	Sun Jun 23 23:21:27 2019
14	4	2	GOOG	CALL	4	60	1	Fri Jun 21 23:23:36 2019	No	Sun Jun 23 23:21:27 2019
14	4	2	GOOG	CALL	6	60	1	Sat Jun 22 00:08:58 2019	No	Sun Jun 23 23:21:27 2019
\.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                           3214.dat                                                                                            0000600 0004000 0002000 00000004621 13507510031 0014241 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1	1	AAPL	135.720001	100	Sun Feb 19 17:13:10 2019
2	4	AAPL	135.720001	50	Sun Feb 19 17:15:23 2019
3	4	AAPL	135.720001	1	Sun Feb 19 17:16:54 2019
4	1	AAPL	136.460007	12	Tue Feb 21 09:32:13 2019
5	1	MU	23.6650009	1000	Tue Feb 21 09:48:52 2019
6	1	MU	23.7399998	100	Tue Feb 21 13:07:38 2019
7	1	DIA	207.410004	112	Fri Feb 24 10:22:15 2019
8	1	CAC	42.3199997	946	Wed Feb 22 14:07:33 2019
9	1	AAPL	137.029999	-15	Wed Feb 22 14:08:41 2019
10	1	BABA	104.300003	50	Wed Feb 22 14:04:18 2019
11	1	DIS	109.660004	125	Fri Feb 24 10:22:36 2019
12	1	EEM	38.5200005	814	Fri Feb 24 10:22:44 2019
13	1	EFA	60.4000015	75	Fri Feb 24 10:22:58 2019
14	1	GXC	80.7200012	125	Fri Feb 24 10:23:14 2019
15	1	IBB	288.154999	233	Fri Feb 24 10:23:47 2019
16	1	IJH	172.899994	332	Fri Feb 24 10:23:57 2019
17	1	IVW	130.149902	167	Fri Feb 24 10:24:08 2019
18	1	IWD	116.5	306	Fri Feb 24 10:24:38 2019
19	1	IWM	138.5	33	Fri Feb 24 10:24:49 2019
20	1	IWV	140.230194	301	Fri Feb 24 10:25:17 2019
21	1	IWV	140.240005	301	Fri Feb 24 10:25:31 2019
22	1	IWV	140.240005	-301	Fri Feb 24 10:25:52 2019
23	1	NFLX	143.080002	71	Fri Feb 24 10:26:03 2019
24	1	MU	23.0599995	21	Fri Feb 24 10:26:27 2019
25	1	QQQ	129.735001	437	Fri Feb 24 10:26:37 2019
26	1	STGXX	1	201	Fri Feb 24 10:26:50 2019
27	1	VT	64.6999969	825	Fri Feb 24 10:27:08 2019
28	1	AAPL	135.815002	97	Fri Feb 24 10:32:50 2019
29	1	BABA	102.230003	48	Fri Feb 24 10:33:25 2019
30	1	IWS	83.9605026	75	Fri Feb 24 10:34:32 2019
31	2	AAPL	194.190002	10	Thu Jun 13 11:28:51 2019
32	2	AAPL	194.190002	5	Thu Jun 13 11:36:16 2019
33	2	AAPL	194.190002	-4	Thu Jun 13 11:36:27 2019
34	2	AAPL	195.5	5	Thu Jun 13 22:20:17 2019
35	2	MSFT	132.399994	5	Fri Jun 14 20:10:36 2019
36	2	GOOG	1082.41003	3	Fri Jun 14 20:10:47 2019
37	5	IBB	104.07	8	Fri Jun 14 20:12:03 2019
38	2	GOOGL	1088.88	2	Fri Jun 14 21:26:03 2019
39	4	GOOG	1116.91003	1	Fri Jun 21 23:11:21 2019
40	3	IBB	108.669998	5	Fri Jun 21 23:22:24 2019
41	3	NFLX	369.850006	4	Fri Jun 21 23:22:44 2019
42	3	GOOG	1117.07996	4	Fri Jun 21 23:22:57 2019
43	4	AAPL	204.410004	3	Fri Jul  5 02:08:37 2019
44	4	AAPL	204.410004	-3	Fri Jul  5 02:08:37 2019
45	3	AAPL	50	3	Fri Jul  5 02:08:37 2019
46	5	IBB	110.93	5	Fri Jul  5 02:08:38 2019
47	5	IBB	110.93	-5	Fri Jul  5 02:08:38 2019
48	2	IBB	100	5	Fri Jul  5 02:08:38 2019
49	5	IBB	40	5	Fri Jul  5 02:08:39 2019
50	4	GOOG	1121.57996	1	Fri Jul  5 02:08:39 2019
51	4	GOOG	1121.57996	-1	Fri Jul  5 02:08:39 2019
52	2	GOOG	60	1	Fri Jul  5 02:08:39 2019
\.


                                                                                                               3210.dat                                                                                            0000600 0004000 0002000 00000001234 13507510031 0014232 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        4	Parth	$5$rounds=535000$xiMmm4dDqC8OfnY5$Rj3Q5QCEJUltKW88FRZ2YRhXBvBnatoPqrBcDNJNRM6	239.217056	11319.9404	Fri Jul  5 05:03:36 2019
1	Ben	$5$rounds=535000$ATinCGX97s5AhND7$7vRkSmBTYiz92FvzpMIa7qesQOTqzjhld0DonWzayc/	10043.4443	626861.125	Fri Jul  5 05:03:36 2019
5	Emily	$5$rounds=535000$0JMC0SYuMk2mb/mJ$Lzi19bI3UplSZD1lL0aJ9K9N4bVt4Mq3Yf4bQhF/nDA	8456.54688	869.280029	Fri Jul  5 05:03:36 2019
2	Vidhin	$5$rounds=535000$g.XeQ0CUU1ldY2B6$5b/Z8.RxJu3ggY0iFfVT1xJxPmnzZlV5xKqHGL1AH02	243.12207	11244.8096	Fri Jul  5 05:03:36 2019
3	admin	$5$rounds=535000$lbxQjj4JjXrgnYiB$OhX1CXC0WqfRW0Bjfm9nT.umiCjOCFQdNDVlbxf4Mv7	3369.69482	7181.08008	Fri Jul  5 05:03:36 2019
\.


                                                                                                                                                                                                                                                                                                                                                                    restore.sql                                                                                         0000600 0004000 0002000 00000016503 13507510031 0015364 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        --
-- NOTE:
--
-- File paths need to be edited. Search for $$PATH$$ and
-- replace it with the path to the directory containing
-- the extracted data files.
--
--
-- PostgreSQL database dump
--

-- Dumped from database version 11.3
-- Dumped by pg_dump version 11.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE tradingterminal;
--
-- Name: tradingterminal; Type: DATABASE; Schema: -; Owner: vidhin
--

CREATE DATABASE tradingterminal WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';


ALTER DATABASE tradingterminal OWNER TO vidhin;

\connect tradingterminal

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: option_post; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.option_post (
    option_id integer NOT NULL,
    writer_id integer NOT NULL,
    holder_id integer NOT NULL,
    stock_symbol text NOT NULL,
    option_type text NOT NULL,
    option_price real NOT NULL,
    strike_price real NOT NULL,
    num_of_shares integer NOT NULL,
    transaction_date text NOT NULL,
    is_available text DEFAULT 'Yes'::text NOT NULL,
    expiry_date text NOT NULL
);


ALTER TABLE public.option_post OWNER TO postgres;

--
-- Name: option_transaction; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.option_transaction (
    option_id integer NOT NULL,
    writer_id integer NOT NULL,
    holder_id integer NOT NULL,
    stock_symbol text NOT NULL,
    option_type text NOT NULL,
    option_price real NOT NULL,
    strike_price real NOT NULL,
    num_of_shares integer NOT NULL,
    transaction_date text NOT NULL,
    is_available text DEFAULT 'Yes'::text NOT NULL,
    expiry_date text NOT NULL
);


ALTER TABLE public.option_transaction OWNER TO postgres;

--
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    symbol text NOT NULL,
    price real NOT NULL,
    quantity integer NOT NULL,
    transaction_date text NOT NULL
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.transactions_id_seq OWNER TO postgres;

--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username text NOT NULL,
    hash text NOT NULL,
    cash real DEFAULT 10000 NOT NULL,
    assets real DEFAULT 0 NOT NULL,
    last_update_time text NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);


--
-- Data for Name: option_post; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.option_post (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM stdin;
\.
COPY public.option_post (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM '$$PATH$$/3211.dat';

--
-- Data for Name: option_transaction; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.option_transaction (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM stdin;
\.
COPY public.option_transaction (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM '$$PATH$$/3212.dat';

--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transactions (id, user_id, symbol, price, quantity, transaction_date) FROM stdin;
\.
COPY public.transactions (id, user_id, symbol, price, quantity, transaction_date) FROM '$$PATH$$/3214.dat';

--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, hash, cash, assets, last_update_time) FROM stdin;
\.
COPY public.users (id, username, hash, cash, assets, last_update_time) FROM '$$PATH$$/3210.dat';

--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transactions_id_seq', 52, true);


--
-- Name: option_post option_post_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT option_post_pkey PRIMARY KEY (option_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: fki_holder_if; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_holder_if ON public.option_post USING btree (holder_id);


--
-- Name: fki_writer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX fki_writer_id ON public.option_post USING btree (writer_id);


--
-- Name: option_post holder_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT holder_id FOREIGN KEY (holder_id) REFERENCES public.users(id) ON UPDATE CASCADE;


--
-- Name: option_transaction holder_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.option_transaction
    ADD CONSTRAINT holder_id FOREIGN KEY (holder_id) REFERENCES public.users(id) ON UPDATE CASCADE;


--
-- Name: transactions user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE;


--
-- Name: option_post writer_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT writer_id FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE;


--
-- Name: option_transaction writer_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.option_transaction
    ADD CONSTRAINT writer_id FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE;


--
-- PostgreSQL database dump complete
--

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             