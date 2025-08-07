"""
title: Database Access
author: DUC
author_urls:
  - https://github.com/theducdev
description: A tool for reading database information and executing SQL queries, supporting multiple databases such as MySQL, PostgreSQL, SQLite, and Oracle. It provides functionalities for listing all tables, describing table schemas, and returning query results in CSV format. A versatile DB Agent for seamless database interactions.
required_open_webui_version: 0.5.4
requirements: pymysql, sqlalchemy, cx_Oracle, python-dotenv
version: 0.1.6
licence: MIT
"""

import os
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import re
from sqlalchemy import create_engine, text
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()


class Tools:
    class Valves(BaseModel):
        db_host: str = Field(
            default=os.getenv("DB_HOST"),
            description="The host of the database. Replace with your own host.",
        )
        db_user: str = Field(
            default=os.getenv("DB_USER"),
            description="The username for the database. Replace with your own username.",
        )
        db_password: str = Field(
            default=os.getenv("DB_PASSWORD"),
            description="The password for the database. Replace with your own password.",
        )
        db_name: str = Field(
            default=os.getenv("DB_NAME"),
            description="The name of the database. Replace with your own database name.",
        )
        db_port: int = Field(
            default=int(os.getenv("DB_PORT")),
            description="The port of the database. Replace with your own port.",
        )
        db_type: str = Field(
            default=os.getenv("DB_TYPE"),
            description="The type of the database (e.g., mysql, postgresql, sqlite, oracle).",
        )

    def __init__(self):
        """
        Initialize the Tools class with the credentials for the database.
        """
        print("Initializing database tool class")
        self.citation = True
        self.valves = Tools.Valves()

    def _get_engine(self) -> Engine:
        """
        Create and return a database engine using the current configuration.
        """
        if self.valves.db_type == "mysql":
            db_url = f"mysql+pymysql://{self.valves.db_user}:{self.valves.db_password}@{self.valves.db_host}:{self.valves.db_port}/{self.valves.db_name}"
        elif self.valves.db_type == "postgresql":
            db_url = f"postgresql://{self.valves.db_user}:{self.valves.db_password}@{self.valves.db_host}:{self.valves.db_port}/{self.valves.db_name}"
        elif self.valves.db_type == "sqlite":
            db_url = f"sqlite:///{self.valves.db_name}"
        elif self.valves.db_type == "oracle":
            db_url = f"oracle+cx_oracle://{self.valves.db_user}:{self.valves.db_password}@{self.valves.db_host}:{self.valves.db_port}/?service_name={self.valves.db_name}"
        else:
            raise ValueError(f"Unsupported database type: {self.valves.db_type}")

        return create_engine(db_url)

    def list_all_tables(self, db_name: str) -> str:
        """
        List all tables in the database.
        :param db_name: The name of the database.
        :return: A string containing the names of all tables.
        """
        print("Listing all tables in the database")
        engine = self._get_engine()  
        try:
            with engine.connect() as conn:
                if self.valves.db_type == "mysql":
                    result = conn.execute(text("SHOW TABLES;"))
                elif self.valves.db_type == "postgresql":
                    result = conn.execute(
                        text(
                            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                        )
                    )
                elif self.valves.db_type == "sqlite":
                    result = conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table';")
                    )
                elif self.valves.db_type == "oracle":
                    result = conn.execute(text("SELECT table_name FROM user_tables;"))
                else:
                    return "Unsupported database type."
                tables = [row[0] for row in result.fetchall()]
                if tables:
                    return (
                        "Here is a list of all the tables in the database:\n\n"
                        + "\n".join(tables)
                    )
                else:
                    return "No tables found."
        except SQLAlchemyError as e:
            return f"Error listing tables: {str(e)}"

    def get_table_indexes(self, db_name: str, table_name: str) -> str:
        """
        Get the indexes of a specific table in the database.
        :param db_name: The name of the database.
        :param table_name: The name of the table.
        :return: A string describing the indexes of the table.
        """
        print(f"Getting indexes for table: {table_name}")
        engine = self._get_engine()
        try:
            with engine.connect() as conn:
                if self.valves.db_type == "mysql":
                    query = text(
                        """
                        SHOW INDEX FROM :table_name;
                        """
                    )
                elif self.valves.db_type == "postgresql":
                    query = text(
                        """
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE tablename = :table_name;
                        """
                    )
                elif self.valves.db_type == "sqlite":
                    query = text(
                        """
                        PRAGMA index_list(:table_name);
                        """
                    )
                elif self.valves.db_type == "oracle":
                    query = text(
                        """
                        SELECT index_name, column_name
                        FROM user_ind_columns
                        WHERE table_name = :table_name;
                        """
                    )
                else:
                    return "Unsupported database type."
                result = conn.execute(query, {"table_name": table_name})
                indexes = result.fetchall()
                if not indexes:
                    return f"No indexes found for table: {table_name}"
                description = f"Indexes for table '{table_name}':\n"
                for index in indexes:
                    description += f"- {index[0]}: {index[1]}\n"
                return description
        except SQLAlchemyError as e:
            return f"Error getting indexes: {str(e)}"

    def table_data_schema(self, db_name: str, table_name: str) -> str:
        """
        Describe the schema of a specific table in the database, including column comments.
        :param db_name: The name of the database.
        :param table_name: The name of the table to describe.
        :return: A string describing the data schema of the table.
        """
        print(f"Describing table: {table_name}")
        engine = self._get_engine()  
        try:
            with engine.connect() as conn:
                if self.valves.db_type == "mysql":
                    query = text(
                        """
                        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA = :db_name AND TABLE_NAME = :table_name;
                    """
                    )
                elif self.valves.db_type == "postgresql":
                    query = text(
                        """
                        SELECT column_name, data_type, is_nullable, column_default, ''
                        FROM information_schema.columns
                        WHERE table_name = :table_name;
                    """
                    )
                elif self.valves.db_type == "sqlite":
                    query = text("PRAGMA table_info(:table_name);")
                elif self.valves.db_type == "oracle":
                    query = text(
                        """
                        SELECT column_name, data_type, nullable, data_default, comments
                        FROM user_tab_columns
                        LEFT JOIN user_col_comments
                        ON user_tab_columns.table_name = user_col_comments.table_name
                        AND user_tab_columns.column_name = user_col_comments.column_name
                        WHERE user_tab_columns.table_name = :table_name;
                    """
                    )
                else:
                    return "Unsupported database type."
                result = conn.execute(
                    query, {"db_name": db_name, "table_name": table_name}
                )
                columns = result.fetchall()
                if not columns:
                    return f"No such table: {table_name}"
                description = (
                    f"Table '{table_name}' in the database has the following columns:\n"
                )
                for column in columns:
                    if self.valves.db_type == "sqlite":
                        column_name, data_type, is_nullable, _, _, _ = column
                        column_comment = ""
                    elif self.valves.db_type == "oracle":
                        (
                            column_name,
                            data_type,
                            is_nullable,
                            data_default,
                            column_comment,
                        ) = column
                    else:
                        (
                            column_name,
                            data_type,
                            is_nullable,
                            column_key,
                            column_comment,
                        ) = column
                    description += f"- {column_name} ({data_type})"
                    if is_nullable == "YES" or is_nullable == "Y":
                        description += " [Nullable]"
                    if column_key == "PRI":
                        description += " [Primary Key]"
                    if column_comment:
                        description += f" [Comment: {column_comment}]"
                    description += "\n"
                return description
        except SQLAlchemyError as e:
            return f"Error describing table: {str(e)}"

    def analyze_customer_metrics(self, time_range: str = "last_30_days") -> str:
        """
        Phân tích toàn diện về khách hàng, bao gồm:
        - Thống kê khách theo care_priority (normal/high/urgent)
        - Tỷ lệ khách theo gender và độ tuổi
        - Top khách hàng có số buổi điều trị nhiều nhất
        - Khách hàng có debt cao nhất
        - Tỷ lệ khách theo trạng thái (active/inactive/banned)
        
        Args:
            time_range: Khoảng thời gian phân tích (default: "last_30_days")
                       Có thể là: "last_7_days", "last_30_days", "last_90_days", "last_365_days"
        
        Returns:
            String chứa kết quả phân tích dạng CSV
        """
        # Chuyển đổi time_range thành interval PostgreSQL
        time_intervals = {
            "last_7_days": "7 days",
            "last_30_days": "30 days",
            "last_90_days": "90 days",
            "last_365_days": "365 days"
        }
        interval = time_intervals.get(time_range, "30 days")
        
        query = """
        WITH customer_stats AS (
            SELECT 
                c.id,
                c.name,
                c.care_priority,
                c.gender,
                c.status,
                c.debt,
                COUNT(DISTINCT t.id) as treatment_count,
                DATE_PART('year', AGE(CURRENT_DATE, c.birth_date)) as age,
                COUNT(DISTINCT a.id) as appointment_count,
                SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_appointments
            FROM customers c
            LEFT JOIN treatments t ON c.id = t.customer_id
            LEFT JOIN appointments a ON c.id = a.customer_id
            WHERE c.created_at >= NOW() - INTERVAL :interval
            GROUP BY c.id, c.name, c.care_priority, c.gender, c.status, c.debt, c.birth_date
        ),
        age_groups AS (
            SELECT 
                CASE 
                    WHEN age < 18 THEN 'Under 18'
                    WHEN age BETWEEN 18 AND 25 THEN '18-25'
                    WHEN age BETWEEN 26 AND 35 THEN '26-35'
                    WHEN age BETWEEN 36 AND 50 THEN '36-50'
                    ELSE 'Over 50'
                END as age_group,
                COUNT(*) as count
            FROM customer_stats
            GROUP BY 
                CASE 
                    WHEN age < 18 THEN 'Under 18'
                    WHEN age BETWEEN 18 AND 25 THEN '18-25'
                    WHEN age BETWEEN 26 AND 35 THEN '26-35'
                    WHEN age BETWEEN 36 AND 50 THEN '36-50'
                    ELSE 'Over 50'
                END
        ),
        priority_stats AS (
            SELECT 
                care_priority,
                COUNT(*) as count,
                CAST(AVG(treatment_count) AS NUMERIC(10,2)) as avg_treatments,
                CAST(AVG(debt) AS NUMERIC(10,2)) as avg_debt
            FROM customer_stats
            GROUP BY care_priority
        ),
        gender_stats AS (
            SELECT 
                gender,
                COUNT(*) as count,
                CAST(AVG(age) AS NUMERIC(10,2)) as avg_age
            FROM customer_stats
            GROUP BY gender
        ),
        top_customers AS (
            SELECT 
                name,
                treatment_count,
                appointment_count,
                cancelled_appointments,
                debt,
                care_priority
            FROM customer_stats
            ORDER BY treatment_count DESC, debt DESC
            LIMIT 10
        )
        SELECT 
            'Priority Stats' as category,
            care_priority::text as metric,
            count::text as value,
            COALESCE(avg_treatments::text, '-') as additional_info1,
            COALESCE(avg_debt::text, '-') as additional_info2,
            '-' as additional_info3
        FROM priority_stats
        UNION ALL
        SELECT 
            'Age Stats' as category,
            age_group as metric,
            count::text as value,
            '-' as additional_info1,
            '-' as additional_info2,
            '-' as additional_info3
        FROM age_groups
        UNION ALL
        SELECT 
            'Gender Stats' as category,
            gender::text as metric,
            count::text as value,
            COALESCE(avg_age::text, '-') as additional_info1,
            '-' as additional_info2,
            '-' as additional_info3
        FROM gender_stats
        UNION ALL
        SELECT 
            'Top Customers' as category,
            name as metric,
            treatment_count::text as value,
            COALESCE(appointment_count::text, '0') as additional_info1,
            COALESCE(cancelled_appointments::text, '0') as additional_info2,
            COALESCE(debt::text, '0') as additional_info3
        FROM top_customers
        ORDER BY category, metric;
        """
        
        try:
            with self._get_engine().connect() as conn:
                result = conn.execute(text(query), {"interval": interval})
                rows = result.fetchall()
                
                if not rows:
                    return "Không có dữ liệu phân tích cho khoảng thời gian này."

                # Tạo header cho từng phần
                csv_data = "=== BÁO CÁO PHÂN TÍCH KHÁCH HÀNG ===\n"
                csv_data += f"Khoảng thời gian: {time_range}\n\n"
                
                current_category = None
                for row in rows:
                    if current_category != row[0]:
                        current_category = row[0]
                        if current_category == 'Priority Stats':
                            csv_data += "\n1. THỐNG KÊ THEO ĐỘ ƯU TIÊN\n"
                            csv_data += "Độ ưu tiên,Số lượng,Trung bình số liệu trình,Trung bình công nợ\n"
                        elif current_category == 'Age Stats':
                            csv_data += "\n2. THỐNG KÊ THEO ĐỘ TUỔI\n"
                            csv_data += "Nhóm tuổi,Số lượng\n"
                        elif current_category == 'Gender Stats':
                            csv_data += "\n3. THỐNG KÊ THEO GIỚI TÍNH\n"
                            csv_data += "Giới tính,Số lượng,Độ tuổi trung bình\n"
                        elif current_category == 'Top Customers':
                            csv_data += "\n4. TOP KHÁCH HÀNG\n"
                            csv_data += "Tên khách hàng,Số liệu trình,Số lần đặt hẹn,Số lần hủy hẹn,Công nợ\n"
                    
                    # Format dữ liệu theo từng category
                    if current_category == 'Priority Stats':
                        csv_data += f"{row[1]},{row[2]},{row[3]},{row[4]}\n"
                    elif current_category == 'Age Stats':
                        csv_data += f"{row[1]},{row[2]}\n"
                    elif current_category == 'Gender Stats':
                        csv_data += f"{row[1]},{row[2]},{row[3]}\n"
                    elif current_category == 'Top Customers':
                        csv_data += f"{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"
                
                return csv_data
                
        except SQLAlchemyError as e:
            return f"Lỗi khi phân tích dữ liệu khách hàng: {str(e)}"

    def track_treatment_progress(self, customer_identifier: str = None, treatment_id: str = None) -> str:
        """
        Theo dõi tiến trình điều trị của khách hàng.
        
        Args:
            customer_identifier: Tên hoặc số điện thoại của khách hàng
                               - Nếu là số điện thoại: có thể tìm một phần (ví dụ: "0909" sẽ tìm được "0909123456")
                               - Nếu là tên: không phân biệt hoa thường, có thể tìm một phần tên
            treatment_id: ID của liệu trình cụ thể (nếu muốn xem chi tiết 1 liệu trình)
            
        Returns:
            String chứa báo cáo tiến trình điều trị dạng CSV, bao gồm:
            - Thông tin tổng quan về các liệu trình
            - Chi tiết từng buổi điều trị
            - Hình ảnh trước/sau
            - Phản ứng và tình trạng da của khách
        """
        try:
            with self._get_engine().connect() as conn:
                # 1. Query thông minh để tìm khách hàng
                find_customer_query = """
                SELECT 
                    id as customer_id,
                    name as customer_name,
                    phone,
                    email,
                    care_priority::text
                FROM customers c
                WHERE 
                    CASE 
                        WHEN :identifier ~ '^[0-9]+$' 
                        THEN c.phone LIKE '%' || :identifier || '%'
                        ELSE LOWER(c.name) LIKE '%' || LOWER(:identifier) || '%'
                    END
                ORDER BY 
                    CASE 
                        WHEN c.phone = :identifier THEN 0
                        WHEN c.phone LIKE :identifier || '%' THEN 1
                        WHEN c.phone LIKE '%' || :identifier THEN 2
                        WHEN LOWER(c.name) = LOWER(:identifier) THEN 3
                        ELSE 4 
                    END,
                    c.created_at DESC
                LIMIT 1;
                """
                
                # 2. Query tổng quan các liệu trình
                treatments_query = """
                SELECT 
                    t.id as treatment_id,
                    t.treatment_name,
                    t.total_sessions,
                    t.current_session,
                    CAST((t.current_session::float / t.total_sessions * 100) AS NUMERIC(5,2)) as completion_percentage,
                    t.start_date::text,
                    COALESCE(t.end_date::text, 'Đang điều trị') as end_date,
                    CAST(t.price AS TEXT) as price,
                    t.status,
                    t.notes
                FROM treatments t
                WHERE t.customer_id = :customer_id
                """
                
                if treatment_id:
                    treatments_query += " AND t.id = :treatment_id"
                
                treatments_query += " ORDER BY t.start_date DESC;"
                
                # 3. Query chi tiết các buổi điều trị
                sessions_query = """
                WITH SessionImages AS (
                    SELECT 
                        session_id,
                        STRING_AGG(
                            CASE 
                                WHEN image_type = 'before' THEN image_url
                            END, 
                            ', '
                        ) as before_images,
                        STRING_AGG(
                            CASE 
                                WHEN image_type = 'after' THEN image_url
                            END, 
                            ', '
                        ) as after_images
                    FROM treatment_images
                    GROUP BY session_id
                )
                SELECT 
                    ts.session_number,
                    ts.session_date::text,
                    COALESCE(ts.products_used, '-') as products_used,
                    COALESCE(ts.skin_condition, '-') as skin_condition,
                    COALESCE(ts.reaction, '-') as reaction,
                    COALESCE(ts.next_appointment::text, '-') as next_appointment,
                    COALESCE(ts.notes, '-') as session_notes,
                    COALESCE(ts.products_sold, '-') as products_sold,
                    COALESCE(ts.after_sales_care, '-') as after_sales_care,
                    COALESCE(si.before_images, '-') as before_images,
                    COALESCE(si.after_images, '-') as after_images
                FROM treatment_sessions ts
                LEFT JOIN SessionImages si ON ts.id = si.session_id
                WHERE ts.treatment_id = :treatment_id
                ORDER BY ts.session_number;
                """
                
                # Thực hiện queries
                # Tìm khách hàng
                params = {"identifier": customer_identifier, "treatment_id": treatment_id}
                customer_result = conn.execute(text(find_customer_query), params).fetchone()
                
                if not customer_result:
                    return f"Không tìm thấy khách hàng với thông tin: {customer_identifier}. Vui lòng kiểm tra lại số điện thoại, email hoặc ID."
                
                # Cập nhật customer_id cho các query tiếp theo
                params["customer_id"] = customer_result.customer_id
                
                # Format kết quả
                report = "=== BÁO CÁO TIẾN TRÌNH ĐIỀU TRỊ ===\n\n"
                
                # Phần 1: Thông tin khách hàng
                report += "1. THÔNG TIN KHÁCH HÀNG\n"
                report += f"Tên khách hàng: {customer_result.customer_name}\n"
                report += f"Số điện thoại: {customer_result.phone}\n"
                report += f"Email: {customer_result.email}\n"
                report += f"Độ ưu tiên: {customer_result.care_priority}\n\n"
                
                # Phần 2: Tổng quan liệu trình
                treatments_result = conn.execute(text(treatments_query), params).fetchall()
                report += "2. TỔNG QUAN LIỆU TRÌNH\n"
                report += "ID liệu trình,Tên liệu trình,Tổng số buổi,Buổi hiện tại,Tiến độ (%),Ngày bắt đầu,Ngày kết thúc,Giá trị,Trạng thái,Ghi chú\n"
                
                for t in treatments_result:
                    report += f"{t.treatment_id},{t.treatment_name},{t.total_sessions},{t.current_session},"
                    report += f"{t.completion_percentage},{t.start_date},{t.end_date},{t.price},{t.status},"
                    report += f"{t.notes if t.notes else '-'}\n"
                
                # Phần 3: Chi tiết các buổi điều trị
                if treatment_id:
                    sessions_result = conn.execute(text(sessions_query), params).fetchall()
                    report += "\n3. CHI TIẾT CÁC BUỔI ĐIỀU TRỊ\n"
                    report += "Buổi số,Ngày điều trị,Sản phẩm sử dụng,Tình trạng da,Phản ứng,Lịch hẹn tiếp theo,"
                    report += "Ghi chú,Sản phẩm đã bán,Chăm sóc sau điều trị,Hình ảnh trước,Hình ảnh sau\n"
                    
                    for s in sessions_result:
                        report += f"{s.session_number},{s.session_date},{s.products_used},{s.skin_condition},"
                        report += f"{s.reaction},{s.next_appointment},{s.session_notes},{s.products_sold},"
                        report += f"{s.after_sales_care},{s.before_images},{s.after_images}\n"
                
                return report
                
        except SQLAlchemyError as e:
            return f"Lỗi khi theo dõi tiến trình điều trị: {str(e)}"

    def optimize_appointments(self, date_range: str = "today", staff_id: int = None) -> str:
        """
        Phân tích và tối ưu hóa lịch hẹn.
        
        Args:
            date_range: Khoảng thời gian phân tích:
                       - "today": Hôm nay
                       - "tomorrow": Ngày mai
                       - "this_week": Tuần này
                       - "next_week": Tuần sau
                       - "this_month": Tháng này
                       - "YYYY-MM-DD": Ngày cụ thể
            staff_id: ID của nhân viên cần phân tích (tùy chọn)
            
        Returns:
            String chứa báo cáo phân tích lịch hẹn dạng CSV
        """
        try:
            with self._get_engine().connect() as conn:
                # Xử lý date_range
                date_conditions = {
                    "today": "CURRENT_DATE",
                    "tomorrow": "CURRENT_DATE + INTERVAL '1 day'",
                    "this_week": "date_trunc('week', CURRENT_DATE)",
                    "next_week": "date_trunc('week', CURRENT_DATE + INTERVAL '1 week')",
                    "this_month": "date_trunc('month', CURRENT_DATE)"
                }
                
                if date_range in date_conditions:
                    date_condition = f"a.appointment_date >= {date_conditions[date_range]}"
                    if date_range in ["today", "tomorrow"]:
                        date_condition += f" AND a.appointment_date < {date_conditions[date_range]} + INTERVAL '1 day'"
                    elif date_range == "this_week":
                        date_condition += " AND a.appointment_date < date_trunc('week', CURRENT_DATE) + INTERVAL '1 week'"
                    elif date_range == "next_week":
                        date_condition += " AND a.appointment_date < date_trunc('week', CURRENT_DATE + INTERVAL '2 week')"
                    elif date_range == "this_month":
                        date_condition += " AND a.appointment_date < date_trunc('month', CURRENT_DATE) + INTERVAL '1 month'"
                else:
                    # Assume it's a specific date in YYYY-MM-DD format
                    date_condition = f"a.appointment_date = '{date_range}'"
                
                # 1. Tổng quan lịch hẹn
                overview_query = f"""
                WITH AppointmentStats AS (
                    SELECT 
                        a.appointment_date,
                        EXTRACT(DOW FROM a.appointment_date) as day_of_week,
                        EXTRACT(HOUR FROM a.appointment_time) as hour_of_day,
                        a.status,
                        c.care_priority,
                        u.id as staff_id,
                        u.full_name as staff_name,
                        COUNT(*) OVER (PARTITION BY a.appointment_date, EXTRACT(HOUR FROM a.appointment_time)) as appointments_per_hour,
                        COUNT(*) OVER (PARTITION BY a.appointment_date, u.id) as appointments_per_staff_day
                    FROM appointments a
                    JOIN customers c ON a.customer_id = c.id
                    JOIN users u ON a.created_by = u.id
                    WHERE {date_condition}
                    {f"AND u.id = {staff_id}" if staff_id else ""}
                )
                SELECT 
                    appointment_date::text,
                    CASE 
                        WHEN day_of_week = 0 THEN 'Chủ nhật'
                        WHEN day_of_week = 1 THEN 'Thứ hai'
                        WHEN day_of_week = 2 THEN 'Thứ ba'
                        WHEN day_of_week = 3 THEN 'Thứ tư'
                        WHEN day_of_week = 4 THEN 'Thứ năm'
                        WHEN day_of_week = 5 THEN 'Thứ sáu'
                        WHEN day_of_week = 6 THEN 'Thứ bảy'
                    END as day_name,
                    hour_of_day,
                    COUNT(*) as total_appointments,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN care_priority = 'urgent' THEN 1 ELSE 0 END) as vip_appointments,
                    ROUND(AVG(appointments_per_hour), 1) as avg_appointments_per_hour,
                    MAX(appointments_per_hour) as max_appointments_per_hour,
                    STRING_AGG(DISTINCT staff_name, ', ') as staff_names,
                    ROUND(AVG(appointments_per_staff_day), 1) as avg_appointments_per_staff
                FROM AppointmentStats
                GROUP BY appointment_date, day_of_week, hour_of_day
                ORDER BY appointment_date, hour_of_day;
                """
                
                # 2. Phân tích chi tiết theo nhân viên
                staff_query = f"""
                WITH StaffStats AS (
                    SELECT 
                        u.id as staff_id,
                        u.full_name as staff_name,
                        COUNT(*) as total_appointments,
                        COUNT(DISTINCT a.appointment_date) as working_days,
                        SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_appointments,
                        COUNT(DISTINCT c.id) as unique_customers,
                        SUM(CASE WHEN c.care_priority = 'urgent' THEN 1 ELSE 0 END) as vip_customers
                    FROM appointments a
                    JOIN users u ON a.created_by = u.id
                    JOIN customers c ON a.customer_id = c.id
                    WHERE {date_condition}
                    {f"AND u.id = {staff_id}" if staff_id else ""}
                    GROUP BY u.id, u.full_name
                )
                SELECT 
                    staff_name,
                    total_appointments,
                    working_days,
                    CAST(ROUND(total_appointments::numeric / NULLIF(working_days, 0), 1) AS TEXT) as avg_appointments_per_day,
                    cancelled_appointments,
                    CAST(ROUND(cancelled_appointments * 100.0 / NULLIF(total_appointments, 0), 1) AS TEXT) || '%' as cancellation_rate,
                    unique_customers,
                    vip_customers
                FROM StaffStats
                ORDER BY total_appointments DESC;
                """
                
                # 3. Phân tích khung giờ hot
                time_analysis_query = f"""
                WITH TimeStats AS (
                    SELECT 
                        EXTRACT(HOUR FROM a.appointment_time) as hour_of_day,
                        COUNT(*) as total_appointments,
                        SUM(CASE WHEN a.status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_appointments,
                        SUM(CASE WHEN a.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_appointments,
                        COUNT(DISTINCT a.customer_id) as unique_customers
                    FROM appointments a
                    WHERE {date_condition}
                    {f"AND a.created_by = {staff_id}" if staff_id else ""}
                    GROUP BY EXTRACT(HOUR FROM a.appointment_time)
                )
                SELECT 
                    hour_of_day,
                    total_appointments,
                    CAST(ROUND(confirmed_appointments * 100.0 / NULLIF(total_appointments, 0), 1) AS TEXT) || '%' as confirmation_rate,
                    CAST(ROUND(cancelled_appointments * 100.0 / NULLIF(total_appointments, 0), 1) AS TEXT) || '%' as cancellation_rate,
                    unique_customers,
                    CASE 
                        WHEN total_appointments > AVG(total_appointments) OVER () * 1.2 THEN 'Khung giờ cao điểm'
                        WHEN total_appointments < AVG(total_appointments) OVER () * 0.8 THEN 'Khung giờ thấp điểm'
                        ELSE 'Khung giờ bình thường'
                    END as time_slot_status
                FROM TimeStats
                ORDER BY total_appointments DESC;
                """
                
                # Thực hiện queries
                overview_result = conn.execute(text(overview_query)).fetchall()
                staff_result = conn.execute(text(staff_query)).fetchall()
                time_analysis_result = conn.execute(text(time_analysis_query)).fetchall()
                
                # Format kết quả
                report = f"=== BÁO CÁO PHÂN TÍCH LỊCH HẸN ===\nKhoảng thời gian: {date_range}\n\n"
                
                # Phần 1: Tổng quan theo ngày và giờ
                report += "1. TỔNG QUAN LỊCH HẸN THEO NGÀY VÀ GIỜ\n"
                report += "Ngày,Thứ,Giờ,Tổng số hẹn,Đã xác nhận,Đã hủy,Đang chờ,Khách VIP,TB hẹn/giờ,Tối đa hẹn/giờ,Nhân viên,TB hẹn/nhân viên\n"
                for row in overview_result:
                    report += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]},{row[7]},{row[8]},{row[9]},{row[10]},{row[11]}\n"
                
                # Phần 2: Phân tích theo nhân viên
                report += "\n2. PHÂN TÍCH THEO NHÂN VIÊN\n"
                report += "Nhân viên,Tổng số hẹn,Số ngày làm việc,TB hẹn/ngày,Số hẹn hủy,Tỷ lệ hủy,Số khách unique,Số khách VIP\n"
                for row in staff_result:
                    report += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]},{row[6]},{row[7]}\n"
                
                # Phần 3: Phân tích khung giờ
                report += "\n3. PHÂN TÍCH KHUNG GIỜ\n"
                report += "Giờ,Tổng số hẹn,Tỷ lệ xác nhận,Tỷ lệ hủy,Số khách unique,Trạng thái khung giờ\n"
                for row in time_analysis_result:
                    report += f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]},{row[5]}\n"
                
                # Thêm các đề xuất tối ưu
                report += "\n=== ĐỀ XUẤT TỐI ƯU ===\n"
                
                # Phân tích khung giờ cao điểm
                peak_hours = [row for row in time_analysis_result if row[5] == 'Khung giờ cao điểm']
                if peak_hours:
                    report += "1. Khung giờ cao điểm:\n"
                    for hour in peak_hours:
                        report += f"   - {hour[0]}h: {hour[1]} lịch hẹn, tỷ lệ hủy {hour[3]}\n"
                    report += "   Đề xuất: Tăng cường nhân viên trong các khung giờ này\n"
                
                # Phân tích tỷ lệ hủy hẹn
                high_cancel_staff = [row for row in staff_result if float(row[5].strip('%')) > 20]
                if high_cancel_staff:
                    report += "\n2. Nhân viên có tỷ lệ hủy hẹn cao (>20%):\n"
                    for staff in high_cancel_staff:
                        report += f"   - {staff[0]}: {staff[5]} tỷ lệ hủy\n"
                    report += "   Đề xuất: Kiểm tra nguyên nhân và cải thiện quy trình xác nhận lịch hẹn\n"
                
                # Đề xuất cân bằng tải
                workload_stats = [(row[0], float(row[3])) for row in staff_result if row[3] != '-']
                if workload_stats:
                    avg_workload = sum(load for _, load in workload_stats) / len(workload_stats)
                    overloaded_staff = [name for name, load in workload_stats if load > avg_workload * 1.2]
                    if overloaded_staff:
                        report += "\n3. Cân bằng tải:\n"
                        report += f"   - Nhân viên đang quá tải: {', '.join(overloaded_staff)}\n"
                        report += "   Đề xuất: Phân bổ lại lịch hẹn đều hơn giữa các nhân viên\n"
                
                return report
                
        except SQLAlchemyError as e:
            return f"Lỗi khi phân tích lịch hẹn: {str(e)}"

    def execute_read_query(self, query: str) -> str:
        """
        Execute a read query and return the result in CSV format.
        :param query: The SQL query to execute.
        :return: A string containing the result of the query in CSV format.
        """
        print(f"Executing query: {query}")
        normalized_query = query.strip().lower()
        if not re.match(
            r"^\s*(select|with|show|describe|desc|explain|use)\s", normalized_query
        ):
            return "Error: Only read-only queries (SELECT, WITH, SHOW, DESCRIBE, EXPLAIN, USE) are allowed. CREATE, DELETE, INSERT, UPDATE, DROP, and ALTER operations are not permitted."

        sensitive_keywords = [
            "insert",
            "update",
            "delete",
            "create",
            "drop",
            "alter",
            "truncate",
            "grant",
            "revoke",
            "replace",
        ]
        for keyword in sensitive_keywords:
            if re.search(rf"\b{keyword}\b", normalized_query):
                return f"Error: Query contains a sensitive keyword '{keyword}'. Only read operations are allowed."

        engine = self._get_engine()  
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                if not rows:
                    return "No data returned from query."

                column_names = result.keys()
                csv_data = f"Query executed successfully. Below is the actual result of the query {query} running against the database in CSV format:\n\n"
                csv_data += ",".join(column_names) + "\n"
                for row in rows:
                    csv_data += ",".join(map(str, row)) + "\n"
                return csv_data
        except SQLAlchemyError as e:
            return f"Error executing query: {str(e)}"
