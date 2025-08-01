-- 1. Tạo các ENUM type trước
CREATE TYPE message_type AS ENUM ('sms', 'email', 'zalo');
CREATE TYPE gender AS ENUM ('male', 'female', 'other');
CREATE TYPE customer_status AS ENUM ('active', 'inactive', 'banned');
CREATE TYPE customer_care_priority AS ENUM ('normal', 'high', 'urgent');
CREATE TYPE user_role AS ENUM ('staff', 'manager', 'admin');

CREATE SEQUENCE users_id_seq START 1;


-- 2. Tạo các bảng theo thứ tự hợp lý

CREATE TABLE public.customer_tags (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  color character varying NOT NULL DEFAULT '#000000'::character varying,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT customer_tags_pkey PRIMARY KEY (id)
);

CREATE TABLE public.customers (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  phone character varying,
  email character varying,
  gender gender,
  birth_date date,
  address text,
  face_image_url text,
  face_image_path text,
  notes text,
  status customer_status DEFAULT 'active',
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  tag_id uuid,
  debt bigint DEFAULT 0 CHECK (debt >= 0),
  uid_zalo character varying,
  care_priority customer_care_priority NOT NULL DEFAULT 'normal',
  CONSTRAINT customers_pkey PRIMARY KEY (id),
  CONSTRAINT customers_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.customer_tags(id)
);

CREATE TABLE public.users (
  id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
  username character varying NOT NULL UNIQUE,
  password_hash character varying NOT NULL,
  full_name character varying NOT NULL,
  role user_role NOT NULL DEFAULT 'staff',
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);

CREATE TABLE public.appointments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  customer_id uuid,
  appointment_date date NOT NULL,
  appointment_time time without time zone NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status = ANY (ARRAY['pending', 'confirmed', 'cancelled'])),
  notes text,
  created_at timestamp with time zone NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamp with time zone NOT NULL DEFAULT timezone('utc', now()),
  created_by integer,
  CONSTRAINT appointments_pkey PRIMARY KEY (id),
  CONSTRAINT appointments_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id),
  CONSTRAINT appointments_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id)
);

CREATE TABLE public.customer_messages (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  customer_id uuid NOT NULL,
  message_type message_type NOT NULL,
  message_content text NOT NULL,
  sent_at timestamp with time zone DEFAULT now(),
  sent_by integer NOT NULL,
  delivery_status character varying NOT NULL DEFAULT 'pending',
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT customer_messages_pkey PRIMARY KEY (id),
  CONSTRAINT customer_messages_sent_by_fkey FOREIGN KEY (sent_by) REFERENCES public.users(id),
  CONSTRAINT customer_messages_customer_fk FOREIGN KEY (customer_id) REFERENCES public.customers(id)
);

CREATE TABLE public.products (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  notes text,
  status character varying DEFAULT 'active',
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT products_pkey PRIMARY KEY (id)
);

CREATE TABLE public.treatment_packages (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name character varying NOT NULL,
  description text,
  total_sessions integer NOT NULL,
  price numeric NOT NULL,
  status character varying DEFAULT 'active',
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT treatment_packages_pkey PRIMARY KEY (id)
);

CREATE TABLE public.treatments (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  customer_id uuid,
  treatment_name character varying NOT NULL,
  total_sessions integer NOT NULL,
  current_session integer DEFAULT 0 CHECK (current_session >= 0),
  start_date date NOT NULL,
  end_date date,
  price numeric,
  status character varying DEFAULT 'active',
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT treatments_pkey PRIMARY KEY (id),
  CONSTRAINT treatments_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(id)
);

CREATE TABLE public.treatment_sessions (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  treatment_id uuid,
  session_number integer NOT NULL,
  session_date date NOT NULL,
  products_used text,
  skin_condition text,
  reaction text,
  next_appointment date,
  notes text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  products_sold text,
  after_sales_care text,
  CONSTRAINT treatment_sessions_pkey PRIMARY KEY (id),
  CONSTRAINT treatment_sessions_treatment_id_fkey FOREIGN KEY (treatment_id) REFERENCES public.treatments(id)
);

CREATE TABLE public.treatment_images (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  session_id uuid,
  image_type character varying NOT NULL,
  image_url text NOT NULL,
  storage_path text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  file_type text NOT NULL DEFAULT 'image' CHECK (file_type = ANY (ARRAY['image', 'video'])),
  CONSTRAINT treatment_images_pkey PRIMARY KEY (id),
  CONSTRAINT treatment_images_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.treatment_sessions(id)
);
