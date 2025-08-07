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
