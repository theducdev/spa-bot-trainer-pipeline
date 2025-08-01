-- USERS
INSERT INTO public.users (username, password_hash, full_name, role, is_active)
VALUES
('admin', 'hashed_pw_1', 'Admin User', 'admin', true),
('staff1', 'hashed_pw_2', 'Staff One', 'staff', true),
('staff2', 'hashed_pw_3', 'Staff Two', 'staff', true);

-- CUSTOMER TAGS
INSERT INTO public.customer_tags (id, name, color)
VALUES
(gen_random_uuid(), 'VIP', '#FFD700'),
(gen_random_uuid(), 'New', '#00BFFF');

-- CUSTOMERS
INSERT INTO public.customers (id, name, phone, email, gender, birth_date, address, face_image_url, status, tag_id, care_priority)
VALUES
(gen_random_uuid(), 'Nguyen Van A', '0909123456', 'a@example.com', 'male', '1990-01-01', 'Hanoi', 'http://example.com/a.jpg', 'active',
 (SELECT id FROM public.customer_tags LIMIT 1), 'high'),
(gen_random_uuid(), 'Tran Thi B', '0909987654', 'b@example.com', 'female', '1995-05-05', 'HCM', NULL, 'inactive',
 (SELECT id FROM public.customer_tags OFFSET 1 LIMIT 1), 'normal');

-- PRODUCTS
INSERT INTO public.products (id, name, notes)
VALUES
(gen_random_uuid(), 'Serum A', 'Dưỡng ẩm cao'),
(gen_random_uuid(), 'Toner B', 'Làm sạch da');

-- TREATMENTS
INSERT INTO public.treatments (id, customer_id, treatment_name, total_sessions, current_session, start_date, price)
VALUES
(gen_random_uuid(), (SELECT id FROM public.customers LIMIT 1), 'Liệu trình trẻ hóa', 5, 1, '2025-08-01', 5000000),
(gen_random_uuid(), (SELECT id FROM public.customers OFFSET 1 LIMIT 1), 'Liệu trình trị mụn', 3, 0, '2025-08-02', 3000000);

-- TREATMENT SESSIONS
INSERT INTO public.treatment_sessions (id, treatment_id, session_number, session_date)
VALUES
(uuid_generate_v4(), (SELECT id FROM public.treatments LIMIT 1), 1, '2025-08-01'),
(uuid_generate_v4(), (SELECT id FROM public.treatments OFFSET 1 LIMIT 1), 1, '2025-08-02');

-- TREATMENT IMAGES
INSERT INTO public.treatment_images (id, session_id, image_type, image_url, storage_path, file_type)
VALUES
(uuid_generate_v4(), (SELECT id FROM public.treatment_sessions LIMIT 1), 'before', 'http://img.com/before1.jpg', '/storage/before1.jpg', 'image'),
(uuid_generate_v4(), (SELECT id FROM public.treatment_sessions LIMIT 1), 'after', 'http://img.com/after1.jpg', '/storage/after1.jpg', 'image');

-- TREATMENT PACKAGES
INSERT INTO public.treatment_packages (id, name, description, total_sessions, price)
VALUES
(gen_random_uuid(), 'Gói trẻ hóa da', 'Bao gồm 5 buổi chăm sóc', 5, 5000000),
(gen_random_uuid(), 'Gói trị mụn', 'Chăm sóc da mụn 3 buổi', 3, 3000000);

-- APPOINTMENTS
INSERT INTO public.appointments (id, customer_id, appointment_date, appointment_time, status, created_by)
VALUES
(gen_random_uuid(), (SELECT id FROM public.customers LIMIT 1), '2025-08-03', '10:00:00', 'confirmed', 1),
(gen_random_uuid(), (SELECT id FROM public.customers OFFSET 1 LIMIT 1), '2025-08-04', '14:00:00', 'pending', 2);

-- CUSTOMER MESSAGES
INSERT INTO public.customer_messages (id, customer_id, message_type, message_content, sent_by)
VALUES
(gen_random_uuid(), (SELECT id FROM public.customers LIMIT 1), 'zalo', 'Xin chào quý khách!', 1),
(gen_random_uuid(), (SELECT id FROM public.customers OFFSET 1 LIMIT 1), 'sms', 'Hẹn gặp lại!', 2);
