PGDMP     )                    w            tradingterminal    11.5    11.5 *    �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                       false            �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                       false            �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                       false            �           1262    33338    tradingterminal    DATABASE     �   CREATE DATABASE tradingterminal WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';
    DROP DATABASE tradingterminal;
             vidhin    false            �            1259    33339    option_post    TABLE     �  CREATE TABLE public.option_post (
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
       public         vidhin    false            �            1259    33346    option_post_option_id_seq    SEQUENCE     �   CREATE SEQUENCE public.option_post_option_id_seq
    START WITH 22
    INCREMENT BY 1
    MINVALUE 22
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.option_post_option_id_seq;
       public       vidhin    false    196            �           0    0    option_post_option_id_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.option_post_option_id_seq OWNED BY public.option_post.option_id;
            public       vidhin    false    197            �            1259    33348    option_transaction    TABLE     �  CREATE TABLE public.option_transaction (
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
       public         vidhin    false            �            1259    33429 
   order_book    TABLE     �   CREATE TABLE public.order_book (
    order_id integer NOT NULL,
    writer_id integer NOT NULL,
    stock_symbol text NOT NULL,
    price real NOT NULL,
    shares integer NOT NULL,
    buy_sell text NOT NULL,
    order_time text NOT NULL
);
    DROP TABLE public.order_book;
       public         vidhin    false            �            1259    33427    order_book_order_id_seq    SEQUENCE     �   CREATE SEQUENCE public.order_book_order_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.order_book_order_id_seq;
       public       vidhin    false    204            �           0    0    order_book_order_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.order_book_order_id_seq OWNED BY public.order_book.order_id;
            public       vidhin    false    203            �            1259    33355    transactions    TABLE     �   CREATE TABLE public.transactions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    symbol text NOT NULL,
    price real NOT NULL,
    quantity integer NOT NULL,
    transaction_date text NOT NULL
);
     DROP TABLE public.transactions;
       public         vidhin    false            �            1259    33361    transactions_id_seq    SEQUENCE     |   CREATE SEQUENCE public.transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 *   DROP SEQUENCE public.transactions_id_seq;
       public       vidhin    false    199            �           0    0    transactions_id_seq    SEQUENCE OWNED BY     K   ALTER SEQUENCE public.transactions_id_seq OWNED BY public.transactions.id;
            public       vidhin    false    200            �            1259    33363    users    TABLE       CREATE TABLE public.users (
    id integer NOT NULL,
    username text NOT NULL,
    hash text NOT NULL,
    cash real DEFAULT 10000 NOT NULL,
    assets real DEFAULT 0 NOT NULL,
    last_update_time text DEFAULT 'Fri Jul  5 14:29:31 2019'::text NOT NULL
);
    DROP TABLE public.users;
       public         vidhin    false            �            1259    33372    users_id_seq    SEQUENCE     u   CREATE SEQUENCE public.users_id_seq
    START WITH 5
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 #   DROP SEQUENCE public.users_id_seq;
       public       vidhin    false    201            �           0    0    users_id_seq    SEQUENCE OWNED BY     =   ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;
            public       vidhin    false    202                       2604    33374    option_post option_id    DEFAULT     ~   ALTER TABLE ONLY public.option_post ALTER COLUMN option_id SET DEFAULT nextval('public.option_post_option_id_seq'::regclass);
 D   ALTER TABLE public.option_post ALTER COLUMN option_id DROP DEFAULT;
       public       vidhin    false    197    196                       2604    33432    order_book order_id    DEFAULT     z   ALTER TABLE ONLY public.order_book ALTER COLUMN order_id SET DEFAULT nextval('public.order_book_order_id_seq'::regclass);
 B   ALTER TABLE public.order_book ALTER COLUMN order_id DROP DEFAULT;
       public       vidhin    false    203    204    204                       2604    33375    transactions id    DEFAULT     r   ALTER TABLE ONLY public.transactions ALTER COLUMN id SET DEFAULT nextval('public.transactions_id_seq'::regclass);
 >   ALTER TABLE public.transactions ALTER COLUMN id DROP DEFAULT;
       public       vidhin    false    200    199                       2604    33376    users id    DEFAULT     d   ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);
 7   ALTER TABLE public.users ALTER COLUMN id DROP DEFAULT;
       public       vidhin    false    202    201            �          0    33339    option_post 
   TABLE DATA               �   COPY public.option_post (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM stdin;
    public       vidhin    false    196   2       �          0    33348    option_transaction 
   TABLE DATA               �   COPY public.option_transaction (option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, transaction_date, is_available, expiry_date) FROM stdin;
    public       vidhin    false    198   &3       �          0    33429 
   order_book 
   TABLE DATA               l   COPY public.order_book (order_id, writer_id, stock_symbol, price, shares, buy_sell, order_time) FROM stdin;
    public       vidhin    false    204   @4       �          0    33355    transactions 
   TABLE DATA               ^   COPY public.transactions (id, user_id, symbol, price, quantity, transaction_date) FROM stdin;
    public       vidhin    false    199   ]4       �          0    33363    users 
   TABLE DATA               S   COPY public.users (id, username, hash, cash, assets, last_update_time) FROM stdin;
    public       vidhin    false    201   �7       �           0    0    option_post_option_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.option_post_option_id_seq', 22, true);
            public       vidhin    false    197            �           0    0    order_book_order_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.order_book_order_id_seq', 10, true);
            public       vidhin    false    203            �           0    0    transactions_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.transactions_id_seq', 53, true);
            public       vidhin    false    200            �           0    0    users_id_seq    SEQUENCE SET     :   SELECT pg_catalog.setval('public.users_id_seq', 7, true);
            public       vidhin    false    202                       2606    33378    option_post option_post_pkey 
   CONSTRAINT     a   ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT option_post_pkey PRIMARY KEY (option_id);
 F   ALTER TABLE ONLY public.option_post DROP CONSTRAINT option_post_pkey;
       public         vidhin    false    196                       2606    33380    transactions transactions_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);
 H   ALTER TABLE ONLY public.transactions DROP CONSTRAINT transactions_pkey;
       public         vidhin    false    199                       2606    33382    users users_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public         vidhin    false    201                       1259    33383    fki_holder_if    INDEX     J   CREATE INDEX fki_holder_if ON public.option_post USING btree (holder_id);
 !   DROP INDEX public.fki_holder_if;
       public         vidhin    false    196                       1259    33384    fki_writer_id    INDEX     J   CREATE INDEX fki_writer_id ON public.option_post USING btree (writer_id);
 !   DROP INDEX public.fki_writer_id;
       public         vidhin    false    196                       1259    33441    order_book_order_id_uindex    INDEX     \   CREATE UNIQUE INDEX order_book_order_id_uindex ON public.order_book USING btree (order_id);
 .   DROP INDEX public.order_book_order_id_uindex;
       public         vidhin    false    204                       2606    33385    option_post holder_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT holder_id FOREIGN KEY (holder_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 ?   ALTER TABLE ONLY public.option_post DROP CONSTRAINT holder_id;
       public       vidhin    false    201    196    3098                       2606    33390    option_transaction holder_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_transaction
    ADD CONSTRAINT holder_id FOREIGN KEY (holder_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 F   ALTER TABLE ONLY public.option_transaction DROP CONSTRAINT holder_id;
       public       vidhin    false    3098    201    198            !           2606    33436 !   order_book order_book_users_id_fk    FK CONSTRAINT     �   ALTER TABLE ONLY public.order_book
    ADD CONSTRAINT order_book_users_id_fk FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE ON DELETE RESTRICT;
 K   ALTER TABLE ONLY public.order_book DROP CONSTRAINT order_book_users_id_fk;
       public       vidhin    false    3098    204    201                        2606    33395    transactions user_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 >   ALTER TABLE ONLY public.transactions DROP CONSTRAINT user_id;
       public       vidhin    false    201    199    3098                       2606    33400    option_post writer_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_post
    ADD CONSTRAINT writer_id FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 ?   ALTER TABLE ONLY public.option_post DROP CONSTRAINT writer_id;
       public       vidhin    false    3098    196    201                       2606    33405    option_transaction writer_id    FK CONSTRAINT     �   ALTER TABLE ONLY public.option_transaction
    ADD CONSTRAINT writer_id FOREIGN KEY (writer_id) REFERENCES public.users(id) ON UPDATE CASCADE;
 F   ALTER TABLE ONLY public.option_transaction DROP CONSTRAINT writer_id;
       public       vidhin    false    198    3098    201            �   �   x����J1���S���$�lr�
em�A�Ń� ]P���Z��\6d���#.����p��=�0���7�>PrH$I[�ϯ_p?�q=� ����pV���rш�GLܣ%�ɑ��a<�oy��kg +p^c���c~�
7��f��}�+�2��������V��A-�b:�bg��gI�塬bY��X<a��!9�г��@Kc�CV���dY��r��\a��㌷˥��r�&�j��U�4��ݣ~      �   
  x����J�@�ϝ��H�d�dnY�E	���A�����ߚ�d���@&3�U#����8��ង��r�~koq��J*I/[e������FI���������l���&V��?��
+��`E�4����j�&��,M����y�p�haadf+�x�IvL����a�,����{��-�sF��aE�L:��̑� ]�(CQx%NK]p�"Pa�1�GX�)��9�:��-�0����;=��2#�<�5���O^	�,�.���
���      �      x������ � �      �   ]  x�}V�N$G<_�?0�|իo��g^���x�H�d�`��wfWU3��n���Ȍ�(С��{p��' t�N������ӈ<"Xn�ɊV�0W<o�q	�c�
�=�KTxrH���6�	(#�*�����o���]L=,��@g|�?y����B9W�~�}:�A�b�U��9��W�ˀ0��	������	yF��\��^�~T<(S�&�|��<�1�Ò�G�J@P���v��ų*��/2b� qj���3�-PX���H	�??:�>�_\FY�Y�l���E�bx՟6>�"�����ehA[�t���������=�!� ����_&�ن*�ye������� ���bZ̉F0��/�t��!��}��L�G-��.��v\0A�
xb��
׃YM8�%A&�6	���hM�m2�Ő�����U)�!+�\Z�m�I��`��6��[0w���t�e��^�>��	���|����07J��Uf���E�ф���z���*��4��ղ���3�|\#�av����y�4��\f_"�fV�º;m��6EE<�i���?߇/����#i�5u�ׄ��s��mx���dM�v�|���O���	��d5�=�g��a���섷��߮%*����{�0Ӕ��x��g�K�\�(�w"/�4�$�V��jg���K4^n0}����2	������R��Tf�5c�g%,�6��ơ§��X|�g+:Y�{�
)���g"�&o�{�����=[}�C��M�%���]#h�TB���c7��gr	m�'�g���̫ㆫ5K�)۰����6��x�
7�k�{�ja�c�7Rg=���M=A��$�b���������%�9      �   3  x�}�ˮ�0�q}�=`�mi���xCQAQ1g"r���{{f+i����� �D!��h��ȕE+]���nsu��ǓgW�sO�.k���$��ߊC��C� f���@�2���0ۦ��^�/D�0�F�����8{�D@����m���07�e#��%�̶'eK�|�W���Ĭ$7$�M��>L�s	ǈ�#�5b�� ��oy\G?%�v�"��e6��|h��4��P���$��35��b��U9C��9�g�B��U�(��u@(BF��O�ƻ���f��@�4��
v"Y��Ɔ�Ջc��];:�O���ۦ��g}e�lS�P"%�9�����qſ��U<^,�9���@�቉vk4����x�w�5�M^t�lO�E5�.�hq��B��[�	��BI�d��z����0Ѣ�[͞/^�`,C��y[c;�Y���Fv�fZ�{�ʥ����KzW!Q�3J�ׅ� �m��ZIB��x�n�
�舴�Uh���9/vb��Z��&V�������O �]E�N8)�|F���?����     