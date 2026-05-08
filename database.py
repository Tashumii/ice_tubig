import pymysql
import hashlib
import os
from pymysql.constants import CLIENT
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from utils import humanize_status

class DatabaseError(Exception):
    """General database exception for the IceTubig system."""
    pass

class DatabaseManager:
    def __init__(self):
        # Initializes object
        try:
            self.conn = pymysql.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "ice_tubig"),
                charset="utf8mb4",
                client_flag=CLIENT.MULTI_STATEMENTS,
                connect_timeout=5,
                read_timeout=10,
                write_timeout=10,
            )
        except pymysql.MySQLError as exc:
            raise DatabaseError(f"Failed to connect to database: {exc}") from exc

        self.procedure_mode = True
        self._ensure_schema()

    def close(self):
        # Close data
        if getattr(self, "conn", None):
            try:
                self.conn.close()
            finally:
                self.conn = None

    def __del__(self):
        # Del data
        self.close()

    def _raise_error(self, message, exc=None):
        # Raise error
        if exc is None:
            raise DatabaseError(message)
        raise DatabaseError(f"{message}: {exc}") from exc

    def _ensure_connection_alive(self):
        # Ensure alive
        if getattr(self, "conn", None) is None:
            self._raise_error("Database connection is closed")
        try:
            self.conn.ping(reconnect=True)
        except pymysql.MySQLError as exc:
            self._raise_error("Database connection unavailable", exc)

    def _execute_query(self, sql, params=None, commit=False, fetchone=False, fetchall=False):
        # Execute query
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
                if commit:
                    self.conn.commit()
                if fetchone:
                    return cursor.fetchone()
                if fetchall:
                    return cursor.fetchall()
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Database execution error", exc)

    def _execute_safe_schema(self, sql, params=None, ignore_error_codes=None):
        # Execute schema
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
        except pymysql.MySQLError as exc:
            if ignore_error_codes and exc.args and exc.args[0] in ignore_error_codes:
                return
            raise

    def _call_procedure(self, procedure_name, args=None, fetchone=False, fetchall=False):
        # Call procedure
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.callproc(procedure_name, args or ())
                if fetchone:
                    return cursor.fetchone()
                if fetchall:
                    return cursor.fetchall()
                return None
        except pymysql.MySQLError as exc:
            self._raise_error(f"Database procedure error '{procedure_name}'", exc)

    @staticmethod
    def _hash_password(password: str) -> str:
        # Hash password
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _ensure_schema(self):
        # Ensure schema
        schema_statements = [
            """
            CREATE TABLE IF NOT EXISTS roles (
                role_id INT AUTO_INCREMENT PRIMARY KEY,
                role_name VARCHAR(50) UNIQUE NOT NULL,
                description VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                shift_start_time TIME NULL,
                shift_end_time TIME NULL,
                night_shift_start_time TIME NULL,
                night_shift_end_time TIME NULL,
                INDEX (username)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INT NOT NULL,
                role_id INT NOT NULL,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                id INT PRIMARY KEY DEFAULT 1,
                freeze_duration_hours INT NOT NULL DEFAULT 3,
                theme VARCHAR(20) NOT NULL DEFAULT 'light',
                shift_start_time TIME NOT NULL DEFAULT '08:00:00',
                shift_end_time TIME NOT NULL DEFAULT '17:00:00',
                night_shift_start_time TIME NULL,
                night_shift_end_time TIME NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ice_stocks (
                stock_id INT AUTO_INCREMENT PRIMARY KEY,
                time_added DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD') DEFAULT 'NOT_AVAILABLE',
                product_name VARCHAR(80) DEFAULT 'Ice',
                kg DECIMAL(5,2) DEFAULT 1.0,
                freeze_duration_hours INT DEFAULT 3,
                price DECIMAL(10,2) DEFAULT 5.00
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ice_sales (
                sale_id INT AUTO_INCREMENT PRIMARY KEY,
                stock_id INT NOT NULL,
                sale_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                price DECIMAL(10,2) NOT NULL,
                sold_by_user_id INT NULL,
                FOREIGN KEY (stock_id) REFERENCES ice_stocks(stock_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ice_activity_log (
                event_id INT AUTO_INCREMENT PRIMARY KEY,
                stock_id INT,
                event_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                event_type ENUM('ADDED', 'AVAILABLE', 'SOLD', 'SALE', 'CONFIG') NOT NULL,
                old_status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD') NULL,
                new_status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD') NULL,
                product_name VARCHAR(80) NULL,
                kg DECIMAL(5,2) DEFAULT 1.0,
                price DECIMAL(10,2) DEFAULT 5.00,
                freeze_duration_hours INT DEFAULT 3,
                details TEXT NULL,
                INDEX (stock_id),
                INDEX (event_type)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employee_shift_logs (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                shift_date DATE NOT NULL,
                expected_in TIME NOT NULL,
                expected_out TIME NOT NULL,
                actual_in DATETIME NULL,
                actual_out DATETIME NULL,
                attendance_status VARCHAR(20) NOT NULL DEFAULT 'OFFSITE',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_user_shift (user_id, shift_date),
                INDEX idx_shift_date (shift_date),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS announcements (
                announcement_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                created_by_user_id INT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                deleted_at DATETIME NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_created_at (created_at),
                INDEX idx_is_active (is_active),
                INDEX idx_deleted_at (deleted_at)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS announcement_recipients (
                announcement_id INT NOT NULL,
                user_id INT NOT NULL,
                is_read TINYINT(1) NOT NULL DEFAULT 0,
                read_at DATETIME NULL,
                PRIMARY KEY (announcement_id, user_id),
                FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_user_unread (user_id, is_read)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS admin_notifications (
                notification_id INT AUTO_INCREMENT PRIMARY KEY,
                event_type VARCHAR(40) NOT NULL,
                user_id INT NULL,
                title VARCHAR(160) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(20) NOT NULL DEFAULT 'info',
                is_read TINYINT(1) NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                INDEX idx_admin_notifications_created (created_at),
                INDEX idx_admin_notifications_unread (is_read, created_at),
                INDEX idx_admin_notifications_event (event_type)
            )
            """,
        ]

        for statement in schema_statements:
            self._execute_safe_schema(statement)

       
        self._execute_safe_schema(
            "INSERT IGNORE INTO roles (role_id, role_name, description) VALUES (1, 'admin', 'System administrator with full access'), (2, 'staff', 'Staff member with limited access')"
        )


        admin_password_hash = self._hash_password("admin123")
        self._execute_safe_schema(
            "INSERT IGNORE INTO users (user_id, username, password_hash) VALUES (1, %s, %s)",
            params=('admin', admin_password_hash),
        )

        # Assign admin role to admin user
        self._execute_safe_schema(
            "INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (1, 1)"
        )

        self._execute_safe_schema(
            "INSERT IGNORE INTO system_settings (id, freeze_duration_hours, theme) VALUES (1, 3, 'light')"
        )

        self._execute_safe_schema(
            "ALTER TABLE ice_stocks ADD COLUMN product_name VARCHAR(80) DEFAULT 'Ice'",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE ice_activity_log ADD COLUMN product_name VARCHAR(80) NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE ice_sales ADD COLUMN sold_by_user_id INT NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE ice_sales ADD INDEX idx_ice_sales_sold_by_user_id (sold_by_user_id)",
            ignore_error_codes=(1061,),
        )
        self._execute_safe_schema(
            "ALTER TABLE users ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE system_settings ADD COLUMN shift_start_time TIME NOT NULL DEFAULT '08:00:00'",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE system_settings ADD COLUMN shift_end_time TIME NOT NULL DEFAULT '17:00:00'",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE users ADD COLUMN shift_start_time TIME NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE users ADD COLUMN shift_end_time TIME NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE users ADD COLUMN night_shift_start_time TIME NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE users ADD COLUMN night_shift_end_time TIME NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE system_settings ADD COLUMN night_shift_start_time TIME NULL",
            ignore_error_codes=(1060,),
        )
        self._execute_safe_schema(
            "ALTER TABLE system_settings ADD COLUMN night_shift_end_time TIME NULL",
            ignore_error_codes=(1060,),
        )

        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SET GLOBAL event_scheduler = ON")
        except pymysql.MySQLError:
            pass

        object_statements = [
            """
            DROP EVENT IF EXISTS evt_update_ice_availability;
            CREATE EVENT evt_update_ice_availability
            ON SCHEDULE EVERY 1 MINUTE
            DO
                UPDATE ice_stocks
                SET status = 'AVAILABLE'
                WHERE status = 'NOT_AVAILABLE'
                AND TIMESTAMPDIFF(HOUR, time_added, NOW()) >= (
                    SELECT freeze_duration_hours FROM system_settings WHERE id = 1
                );
            """,
            """
            DROP VIEW IF EXISTS vw_stock_availability;
            CREATE VIEW vw_stock_availability AS
            SELECT
                stock_id,
                product_name,
                kg,
                price,
                freeze_duration_hours,
                status,
                time_added,
                CASE
                    WHEN status = 'NOT_AVAILABLE' THEN
                        TIMESTAMPDIFF(
                            MINUTE,
                            NOW(),
                            DATE_ADD(time_added, INTERVAL freeze_duration_hours HOUR)
                        )
                    ELSE 0
                END AS minutes_until_available,
                CASE
                    WHEN status = 'NOT_AVAILABLE' THEN
                        DATE_ADD(time_added, INTERVAL freeze_duration_hours HOUR)
                    ELSE time_added
                END AS available_at
            FROM ice_stocks;
            """,
            """
            DROP VIEW IF EXISTS vw_sales_with_stock;
            CREATE VIEW vw_sales_with_stock AS
            SELECT
                s.sale_id,
                s.stock_id,
                i.product_name,
                i.kg,
                i.price AS stock_price,
                s.price AS sale_price,
                s.sale_time,
                u.user_id AS sold_by_user_id,
                u.username AS sold_by_username
            FROM ice_sales s
            JOIN ice_stocks i ON s.stock_id = i.stock_id
            LEFT JOIN users u ON u.user_id = s.sold_by_user_id;
            """,
            """
            DROP VIEW IF EXISTS vw_daily_sales_summary;
            CREATE VIEW vw_daily_sales_summary AS
            SELECT
                DATE(sale_time) AS sale_date,
                COUNT(*) AS sale_count,
                COALESCE(SUM(price), 0) AS total_revenue,
                COALESCE(AVG(price), 0) AS average_price
            FROM ice_sales
            GROUP BY DATE(sale_time)
            ORDER BY sale_date DESC;
            """,
            """
            DROP VIEW IF EXISTS vw_shift_attendance;
            CREATE VIEW vw_shift_attendance AS
            SELECT
                l.log_id,
                l.user_id,
                u.username,
                l.shift_date,
                TIME_FORMAT(l.expected_in, '%H:%i') AS expected_in,
                TIME_FORMAT(l.expected_out, '%H:%i') AS expected_out,
                DATE_FORMAT(l.actual_in, '%Y-%m-%d %H:%i') AS actual_in,
                DATE_FORMAT(l.actual_out, '%Y-%m-%d %H:%i') AS actual_out,
                l.attendance_status,
                l.created_at,
                l.updated_at
            FROM employee_shift_logs l
            JOIN users u ON u.user_id = l.user_id;
            """,
            """
            DROP VIEW IF EXISTS vw_available_products;
            CREATE VIEW vw_available_products AS
            SELECT
                product_name,
                kg,
                price,
                COUNT(*) AS available_count
            FROM ice_stocks
            WHERE status = 'AVAILABLE'
            GROUP BY product_name, kg, price;
            """,
            """
            DROP VIEW IF EXISTS vw_activity_log_summary;
            CREATE VIEW vw_activity_log_summary AS
            SELECT
                event_type,
                COUNT(*) AS events_count,
                MIN(event_time) AS first_event,
                MAX(event_time) AS latest_event
            FROM ice_activity_log
            GROUP BY event_type;
            """,
            """
            DROP PROCEDURE IF EXISTS sp_add_ice_stock;
            CREATE PROCEDURE sp_add_ice_stock(
                IN p_qty INT,
                IN p_product_name VARCHAR(80),
                IN p_kg DECIMAL(5,2),
                IN p_freeze_duration_hours INT,
                IN p_price DECIMAL(10,2),
                IN p_instant BOOLEAN
            )
            BEGIN
                DECLARE counter INT DEFAULT 0;
                DECLARE target_status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD');
                SET target_status = IF(p_instant OR p_freeze_duration_hours = 0, 'AVAILABLE', 'NOT_AVAILABLE');
                WHILE counter < p_qty DO
                    INSERT INTO ice_stocks (status, product_name, kg, freeze_duration_hours, price)
                    VALUES (target_status, p_product_name, p_kg, IF(p_instant, 0, p_freeze_duration_hours), p_price);
                    SET counter = counter + 1;
                END WHILE;
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS sp_sell_stock;
            CREATE PROCEDURE sp_sell_stock(IN p_stock_id INT, IN p_sold_by_user_id INT)
            BEGIN
                DECLARE v_status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD');
                DECLARE EXIT HANDLER FOR NOT FOUND SET v_status = NULL;
                SELECT status INTO v_status FROM ice_stocks WHERE stock_id = p_stock_id;
                IF v_status IS NULL THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock not found';
                ELSEIF v_status != 'AVAILABLE' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock not available for sale';
                ELSE
                    INSERT INTO ice_sales (stock_id, price, sold_by_user_id)
                    SELECT stock_id, price, p_sold_by_user_id FROM ice_stocks WHERE stock_id = p_stock_id;
                    UPDATE ice_stocks SET status = 'SOLD' WHERE stock_id = p_stock_id;
                END IF;
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS sp_refresh_ice_availability;
            CREATE PROCEDURE sp_refresh_ice_availability()
            BEGIN
                UPDATE ice_stocks
                SET status = 'AVAILABLE'
                WHERE status = 'NOT_AVAILABLE'
                AND TIMESTAMPDIFF(HOUR, time_added, NOW()) >= (
                    SELECT freeze_duration_hours FROM system_settings WHERE id = 1
                );
            END;
            """,
            """
            DROP PROCEDURE IF EXISTS sp_get_dashboard_summary;
            CREATE PROCEDURE sp_get_dashboard_summary()
            BEGIN
                SELECT
                    COALESCE(SUM(status = 'AVAILABLE'), 0) AS available_count,
                    COALESCE(SUM(status = 'NOT_AVAILABLE'), 0) AS freezing_count,
                    (SELECT COUNT(*) FROM ice_sales) AS sold_count,
                    (SELECT COUNT(*) FROM ice_activity_log) AS activity_count
                FROM ice_stocks;
            END;
            """,
            """
            DROP TRIGGER IF EXISTS trg_before_insert_ice_stocks;
            CREATE TRIGGER trg_before_insert_ice_stocks
            BEFORE INSERT ON ice_stocks
            FOR EACH ROW
            BEGIN
                IF NEW.freeze_duration_hours = 0 THEN
                    SET NEW.status = 'AVAILABLE';
                ELSE
                    SET NEW.status = 'NOT_AVAILABLE';
                END IF;
            END;
            """,
            """
            DROP TRIGGER IF EXISTS trg_after_insert_ice_stocks;
            CREATE TRIGGER trg_after_insert_ice_stocks
            AFTER INSERT ON ice_stocks
            FOR EACH ROW
            BEGIN
                INSERT INTO ice_activity_log (
                    stock_id, event_type, new_status, product_name, kg, price, freeze_duration_hours, details
                ) VALUES (
                    NEW.stock_id, 'ADDED', NEW.status, NEW.product_name, NEW.kg, NEW.price, NEW.freeze_duration_hours,
                    CONCAT('New stock added with status ', NEW.status)
                );
            END;
            """,
            """
            DROP TRIGGER IF EXISTS trg_after_update_ice_stocks;
            CREATE TRIGGER trg_after_update_ice_stocks
            AFTER UPDATE ON ice_stocks
            FOR EACH ROW
            BEGIN
                INSERT INTO ice_activity_log (
                    stock_id, event_type, old_status, new_status, product_name, kg, price, freeze_duration_hours, details
                ) VALUES (
                    NEW.stock_id,
                    CASE
                        WHEN NEW.status = 'SOLD' THEN 'SOLD'
                        WHEN NEW.status = 'AVAILABLE' THEN 'AVAILABLE'
                        ELSE 'CONFIG'
                    END,
                    OLD.status,
                    NEW.status,
                    NEW.product_name,
                    NEW.kg,
                    NEW.price,
                    NEW.freeze_duration_hours,
                    CONCAT('Stock status changed from ', OLD.status, ' to ', NEW.status)
                );
            END;
            """,
            """
            DROP TRIGGER IF EXISTS trg_after_ice_sale;
            CREATE TRIGGER trg_after_ice_sale
            AFTER INSERT ON ice_sales
            FOR EACH ROW
            BEGIN
                INSERT INTO ice_activity_log (
                    stock_id, event_type, old_status, new_status, product_name, price, details
                ) VALUES (
                    NEW.stock_id, 'SALE', 'AVAILABLE', 'SOLD',
                    (SELECT product_name FROM ice_stocks WHERE stock_id = NEW.stock_id),
                    NEW.price,
                    CONCAT('Sale recorded for stock ', NEW.stock_id)
                );
            END;
            """,
        ]

        for statement in object_statements:
            try:
                self._execute_safe_schema(statement)
            except pymysql.MySQLError:
                if "CREATE PROCEDURE" in statement:
                    self.procedure_mode = False
                    continue
                continue

        self.conn.commit()

    def fetch_active_stocks(self):
        # Fetchs stocks
        return self._execute_query(
            "SELECT stock_id, time_added, product_name, kg, freeze_duration_hours, status, price "
            "FROM ice_stocks WHERE status != 'SOLD' ORDER BY time_added DESC",
            fetchall=True,
        )

    def fetch_sales_history(self):
        # Fetchs history
        query = """
        SELECT s.sale_id, s.stock_id, DATE_FORMAT(i.time_added, '%%b %%d, %%Y %%h:%%i %%p'),
               DATE_FORMAT(s.sale_time, '%%b %%d, %%Y %%h:%%i %%p'),
               i.product_name,
               s.price,
               i.kg,
               s.sold_by_user_id,
               COALESCE(u.username, 'Unassigned') AS sold_by_username,
               CASE
                   WHEN HOUR(s.sale_time) BETWEEN 6 AND 13 THEN 'Morning Shift'
                   WHEN HOUR(s.sale_time) BETWEEN 14 AND 21 THEN 'Afternoon Shift'
                   ELSE 'Night Shift'
               END AS shift_name
        FROM ice_sales s
        INNER JOIN ice_stocks i ON s.stock_id = i.stock_id
        LEFT JOIN users u ON u.user_id = s.sold_by_user_id
        ORDER BY s.sale_time DESC
    """
        return self._execute_query(query, fetchall=True)

    def fetch_employee_sales_summary(self):
        # Fetchs summary
        query = """
            SELECT
                COALESCE(u.username, 'Unassigned') AS username,
                CASE
                    WHEN HOUR(s.sale_time) BETWEEN 6 AND 13 THEN 'Morning Shift'
                    WHEN HOUR(s.sale_time) BETWEEN 14 AND 21 THEN 'Afternoon Shift'
                    ELSE 'Night Shift'
                END AS shift_name,
                COUNT(*) AS sales_count,
                COALESCE(SUM(s.price), 0) AS total_revenue
            FROM ice_sales s
            LEFT JOIN users u ON u.user_id = s.sold_by_user_id
            GROUP BY COALESCE(u.username, 'Unassigned'), shift_name
            ORDER BY total_revenue DESC, sales_count DESC
        """
        return self._execute_query(query, fetchall=True) or []

    def fetch_sales_comparison_summary(self):
        # Fetchs summary
        result = self._execute_query(
            "SELECT "
            "COALESCE((SELECT SUM(price) FROM ice_sales WHERE YEAR(sale_time) = YEAR(CURRENT_DATE()) AND MONTH(sale_time) = MONTH(CURRENT_DATE())), 0), "
            "COALESCE((SELECT SUM(price) FROM ice_sales WHERE YEAR(sale_time) = YEAR(CURRENT_DATE() - INTERVAL 1 MONTH) AND MONTH(sale_time) = MONTH(CURRENT_DATE() - INTERVAL 1 MONTH)), 0), "
            "COALESCE((SELECT SUM(price) FROM ice_sales WHERE YEAR(sale_time) = YEAR(CURRENT_DATE())), 0), "
            "COALESCE((SELECT SUM(price) FROM ice_sales WHERE YEAR(sale_time) = YEAR(CURRENT_DATE()) - 1), 0)"
            ,
            fetchone=True,
        )
        return result or (0, 0, 0, 0)

    def fetch_revenue_by_month(self, months=12):
        # Fetchs month
        return self._execute_query(
            "SELECT DATE_FORMAT(sale_time, '%%Y-%%m'), COALESCE(SUM(price), 0) "
            "FROM ice_sales "
            "WHERE sale_time >= DATE_SUB(CURRENT_DATE(), INTERVAL %s MONTH) "
            "GROUP BY DATE_FORMAT(sale_time, '%%Y-%%m') "
            "ORDER BY DATE_FORMAT(sale_time, '%%Y-%%m')",
            (months,),
            fetchall=True,
        ) or []

    def fetch_revenue_by_year(self, years=5):
        # Fetchs year
        return self._execute_query(
            "SELECT YEAR(sale_time), COALESCE(SUM(price), 0) "
            "FROM ice_sales "
            "WHERE sale_time >= DATE_SUB(CURRENT_DATE(), INTERVAL %s YEAR) "
            "GROUP BY YEAR(sale_time) "
            "ORDER BY YEAR(sale_time)",
            (years,),
            fetchall=True,
        ) or []

    def fetch_theme_setting(self):
        # Fetchs setting
        try:
            result = self._execute_query("SELECT theme FROM system_settings WHERE id = 1", fetchone=True)
            return result[0] if (result and result[0]) else "light"
        except DatabaseError:
            return "light"

    def update_theme_setting(self, theme):
        # Updates setting
        self._execute_query(
            "INSERT INTO system_settings (id, theme) VALUES (1, %s) "
            "ON DUPLICATE KEY UPDATE theme = VALUES(theme)",
            (theme,),
            commit=True,
        )

    def fetch_shift_schedule(self):
        # Fetchs schedule
        result = self._execute_query(
            "SELECT shift_start_time, shift_end_time, night_shift_start_time, night_shift_end_time FROM system_settings WHERE id = 1",
            fetchone=True,
        )
        if not result:
            return ("08:00:00", "17:00:00", None, None)
        return result

    def update_shift_schedule(self, shift_start_time: str, shift_end_time: str, night_shift_start_time: str = None, night_shift_end_time: str = None):
        # Updates schedule
        self._execute_query(
            "INSERT INTO system_settings (id, shift_start_time, shift_end_time, night_shift_start_time, night_shift_end_time) VALUES (1, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE shift_start_time = VALUES(shift_start_time), shift_end_time = VALUES(shift_end_time), "
            "night_shift_start_time = VALUES(night_shift_start_time), night_shift_end_time = VALUES(night_shift_end_time)",
            (shift_start_time, shift_end_time, night_shift_start_time, night_shift_end_time),
            commit=True,
        )

    def _ensure_default_shift_settings(self):
        # Ensure settings
        self._execute_query(
            "INSERT IGNORE INTO system_settings (id, shift_start_time, shift_end_time, night_shift_start_time, night_shift_end_time) VALUES (1, '08:00:00', '17:00:00', NULL, NULL)",
            commit=True,
        )

    def _fetch_username(self, user_id: int) -> str:
        # Fetchs username
        row = self._execute_query(
            "SELECT username FROM users WHERE user_id = %s",
            (user_id,),
            fetchone=True,
        )
        return str(row[0]) if row and row[0] else f"User #{user_id}"

    def _fetch_today_shift_state(self, user_id: int):
        # Use the view which has proper formatting applied
        return self._execute_query(
            """
            SELECT
                log_id,
                username,
                expected_in,
                expected_out,
                actual_in,
                actual_out,
                attendance_status
            FROM vw_shift_attendance
            WHERE user_id = %s AND shift_date = CURRENT_DATE()
            """,
            (user_id,),
            fetchone=True,
        )

    def _create_admin_notification(
        self,
        event_type: str,
        user_id: Optional[int],
        title: str,
        message: str,
        severity: str = "info",
    ):
        # Creates notification
        try:
            self._execute_query(
                """
                INSERT INTO admin_notifications (event_type, user_id, title, message, severity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(event_type or "SYSTEM")[:40],
                    user_id,
                    str(title or "System Notice")[:160],
                    str(message or ""),
                    str(severity or "info")[:20],
                ),
                commit=True,
            )
        except DatabaseError:
            pass

    def fetch_admin_notifications(self, limit: int = 20, unread_only: bool = False):
        # Fetchs notifications
        try:
            clean_limit = max(1, min(int(limit or 20), 100))
        except (TypeError, ValueError):
            clean_limit = 20

        query = """
            SELECT
                n.notification_id,
                n.event_type,
                COALESCE(u.username, 'System') AS username,
                n.title,
                n.message,
                n.severity,
                n.is_read,
                DATE_FORMAT(n.created_at, '%%Y-%%m-%%d %%H:%%i') AS created_at
            FROM admin_notifications n
            LEFT JOIN users u ON u.user_id = n.user_id
        """
        params = []
        if unread_only:
            query += " WHERE n.is_read = 0"
        query += " ORDER BY n.created_at DESC LIMIT %s"
        params.append(clean_limit)
        return self._execute_query(query, tuple(params), fetchall=True) or []

    def count_unread_admin_notifications(self) -> int:
        # Count notifications
        result = self._execute_query(
            "SELECT COUNT(*) FROM admin_notifications WHERE is_read = 0",
            fetchone=True,
        )
        return int(result[0] or 0) if result else 0

    def mark_admin_notifications_read(self) -> None:
        # Mark read
        self._execute_query(
            "UPDATE admin_notifications SET is_read = 1 WHERE is_read = 0",
            commit=True,
        )

    def clock_in_user(self, user_id: int):
        # Clock user
        self._ensure_default_shift_settings()
        username = self._fetch_username(user_id)
        existing = self._fetch_today_shift_state(user_id)

        if existing and existing[4] and not existing[5]:
            self._create_admin_notification(
                "ALREADY_ON_SITE",
                user_id,
                "Duplicate On Site Attempt",
                f"{username} tried to clock in again while already On Site.",
                "warning",
            )
            raise DatabaseError("You are already On Site for today's shift.")
        if existing and existing[5]:
            self._create_admin_notification(
                "ALREADY_TIMED_OUT",
                user_id,
                "Clock In Blocked",
                f"{username} tried to clock in after already timing out today.",
                "warning",
            )
            raise DatabaseError("You already timed out today. Ask admin to adjust your shift if this is a mistake.")

        query = """
        INSERT INTO employee_shift_logs (
            user_id, shift_date, expected_in, expected_out, actual_in, attendance_status
        )
        SELECT
            %s,
            CURRENT_DATE(),
            COALESCE(u.shift_start_time, s.shift_start_time),
            COALESCE(u.shift_end_time, s.shift_end_time),
            NOW(),
            CASE
                WHEN TIME(NOW()) <= COALESCE(u.shift_start_time, s.shift_start_time) THEN 'ON_TIME'
                ELSE 'LATE'
            END
        FROM users u
        CROSS JOIN system_settings s
        WHERE u.user_id = %s AND s.id = 1
        ON DUPLICATE KEY UPDATE
            actual_in = CASE
                WHEN actual_in IS NULL THEN NOW()
                ELSE actual_in
            END,
            attendance_status = CASE
                WHEN actual_in IS NULL AND TIME(NOW()) <= expected_in THEN 'ON_TIME'
                WHEN actual_in IS NULL THEN 'LATE'
                ELSE attendance_status
            END
    """
        self._execute_query(query, (user_id, user_id), commit=True)
        state = self._fetch_today_shift_state(user_id)
        if state:
            status = str(state[6] or "")
            late = status == "LATE"
            self._create_admin_notification(
                "LATE_CLOCK_IN" if late else "CLOCK_IN",
                user_id,
                "Late Clock In" if late else "Staff On Site",
                f"{username} clocked in at {state[4] or 'Not recorded'} (expected {state[2] or 'Not recorded'}). Status: {humanize_status(status or 'ON_TIME')}.",
                "warning" if late else "success",
            )

    def clock_out_user(self, user_id: int):
        # Clock user
        self._ensure_default_shift_settings()
        username = self._fetch_username(user_id)
        existing = self._fetch_today_shift_state(user_id)

        if not existing or not existing[4]:
            self._create_admin_notification(
                "TIME_OUT_WITHOUT_CLOCK_IN",
                user_id,
                "Time Out Blocked",
                f"{username} tried to time out without being On Site first.",
                "warning",
            )
            raise DatabaseError("You must clock in before timing out.")
        if existing[5]:
            self._create_admin_notification(
                "ALREADY_TIMED_OUT",
                user_id,
                "Duplicate Time Out Attempt",
                f"{username} tried to time out again after {existing[5]}.",
                "warning",
            )
            raise DatabaseError("You already timed out today.")

        query = """
            UPDATE employee_shift_logs
            SET
                actual_out = NOW(),
                attendance_status = CASE
                    WHEN TIME(NOW()) < expected_out AND attendance_status = 'LATE' THEN 'LATE_EARLY_OUT'
                    WHEN TIME(NOW()) < expected_out THEN 'EARLY_OUT'
                    WHEN attendance_status = 'LATE' THEN 'LATE_COMPLETED'
                    ELSE 'COMPLETED'
                END
            WHERE user_id = %s AND shift_date = CURRENT_DATE()
        """
        self._execute_query(query, (user_id,), commit=True)
        state = self._fetch_today_shift_state(user_id)
        if state:
            status = str(state[6] or "")
            early = "EARLY_OUT" in status
            self._create_admin_notification(
                "EARLY_TIME_OUT" if early else "CLOCK_OUT",
                user_id,
                "Early Time Out" if early else "Staff Time Out",
                f"{username} timed out at {state[5] or 'Not recorded'} (expected {state[3] or 'Not recorded'}). Status: {humanize_status(status or 'COMPLETED')}.",
                "warning" if early else "success",
            )

    def fetch_shift_logs(self, user_id: Optional[int] = None):
        # Use the view which already has formatting applied
        query = """
            SELECT
                log_id,
                username,
                shift_date,
                expected_in,
                expected_out,
                actual_in,
                actual_out,
                attendance_status
            FROM vw_shift_attendance
        """
        params = ()
        if user_id is not None:
            query += " WHERE user_id = %s"
            params = (user_id,)
        query += " ORDER BY shift_date DESC, updated_at DESC"
        return self._execute_query(query, params if params else None, fetchall=True) or []

    def fetch_available_product_types(self):
        # Fetchs types
        query = """
        SELECT MIN(s.stock_id), s.kg, s.freeze_duration_hours, s.price
        FROM ice_stocks s
        WHERE s.status = 'AVAILABLE'
        GROUP BY s.kg, s.freeze_duration_hours, s.price
        """
        return self._execute_query(query, fetchall=True)

    def fetch_activity_event_count(self):
        # Fetchs count
        result = self._execute_query("SELECT COUNT(*) FROM ice_activity_log", fetchone=True)
        return int(result[0]) if result else 0

    def refresh_stock_availability(self):
        # Refreshes availability
        if self.procedure_mode:
            try:
                self._call_procedure("sp_refresh_ice_availability")
                self.conn.commit()
                return
            except DatabaseError:
                self.procedure_mode = False

        self._execute_query(
            "UPDATE ice_stocks "
            "SET status = 'AVAILABLE' "
            "WHERE status = 'NOT_AVAILABLE' "
            "AND TIMESTAMPDIFF(HOUR, time_added, NOW()) >= "
            "(SELECT freeze_duration_hours FROM system_settings WHERE id = 1)",
            commit=True,
        )

    def fetch_dashboard_summary(self):
        # Fetchs summary
        if self.procedure_mode:
            try:
                result = self._call_procedure("sp_get_dashboard_summary", fetchone=True)
                if result:
                    return result
            except DatabaseError:
                self.procedure_mode = False

        result = self._execute_query(
            "SELECT "
            "COALESCE(SUM(status = 'AVAILABLE'), 0), "
            "COALESCE(SUM(status = 'NOT_AVAILABLE'), 0), "
            "(SELECT COUNT(*) FROM ice_sales), "
            "(SELECT COUNT(*) FROM ice_activity_log) "
            "FROM ice_stocks",
            fetchone=True,
        )
        return result or (0, 0, 0, 0)

    def add_ice_stock_via_procedure(self, quantity=1, product_name='Ice', weight_kg=25.0, freeze_duration_hours=3, price=35.00, instant=False):
        # Adds procedure
        if quantity < 1:
            raise DatabaseError("Quantity must be at least 1")
        if not isinstance(product_name, str) or not product_name.strip():
            raise DatabaseError("Product name is required")
        if weight_kg <= 0:
            raise DatabaseError("Weight must be greater than 0")
        if price < 0:
            raise DatabaseError("Price cannot be negative")

        duration_value = 0 if instant else freeze_duration_hours

        if self.procedure_mode:
            try:
                self._call_procedure(
                    "sp_add_ice_stock",
                    (quantity, product_name.strip(), weight_kg, duration_value, price, int(bool(instant))),
                )
                self.conn.commit()
                return
            except DatabaseError:
                self.procedure_mode = False

        status = 'AVAILABLE' if instant or duration_value == 0 else 'NOT_AVAILABLE'

        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                for _ in range(quantity):
                    cursor.execute(
                        "INSERT INTO ice_stocks (status, product_name, kg, freeze_duration_hours, price) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (status, product_name.strip(), weight_kg, duration_value, price),
                    )
            self.conn.commit()
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Failed to add ice stock", exc)

    def sell_stock_via_procedure(self, stock_id, sold_by_user_id=None):
        # Sell procedure
        if not isinstance(stock_id, int) or stock_id < 1:
            raise DatabaseError("Invalid stock identifier")
        if sold_by_user_id is not None and (not isinstance(sold_by_user_id, int) or sold_by_user_id < 1):
            raise DatabaseError("Invalid seller identifier")

        stock = self._execute_query(
            "SELECT product_name, kg, price, status FROM ice_stocks WHERE stock_id = %s",
            (stock_id,),
            fetchone=True,
        )
        if not stock:
            raise DatabaseError("Stock not found")

        product_name = str(stock[0] or "Ice")
        kg = float(stock[1] or 0.0)
        price = float(stock[2] or 0.0)
        status = str(stock[3] or "")

        seller_name = "Staff member"
        if sold_by_user_id is not None:
            seller_name = self._fetch_username(sold_by_user_id)

        if status != 'AVAILABLE':
            if sold_by_user_id is not None:
                self._create_admin_notification(
                    "SALE_BLOCKED",
                    sold_by_user_id,
                    "Sale Blocked",
                    f"{seller_name} tried to sell stock #{stock_id}, but it is {humanize_status(status)}.",
                    "warning",
                )
            raise DatabaseError("Stock not available for sale")

        if sold_by_user_id is not None:
            shift_state = self._fetch_today_shift_state(sold_by_user_id)
            if not shift_state or not shift_state[4]:
                self._create_admin_notification(
                    "SALE_BLOCKED",
                    sold_by_user_id,
                    "Sale Blocked",
                    f"{seller_name} tried to sell {product_name}, but they are not On Site.",
                    "warning",
                )
                raise DatabaseError("You must be On Site before selling stock.")
            if shift_state[5]:
                self._create_admin_notification(
                    "SALE_BLOCKED",
                    sold_by_user_id,
                    "Sale Blocked",
                    f"{seller_name} tried to sell {product_name} after timing out at {shift_state[5]}.",
                    "warning",
                )
                raise DatabaseError("You already timed out. You cannot sell after Time Out.")

        if self.procedure_mode:
            try:
                self._call_procedure("sp_sell_stock", (stock_id, sold_by_user_id))
                self.conn.commit()
                self._create_admin_notification(
                    "SALE_RECORDED",
                    sold_by_user_id,
                    "Sale Recorded",
                    f"{seller_name} sold {product_name} ({kg:g} kg) for ₱ {price:,.2f}. Stock #{stock_id} is now Sold.",
                    "success",
                )
                return
            except DatabaseError:
                self.procedure_mode = False

        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM ice_stocks WHERE stock_id = %s FOR UPDATE",
                    (stock_id,),
                )
                current_stock = cursor.fetchone()
                if not current_stock:
                    raise DatabaseError("Stock not found")
                if current_stock[0] != 'AVAILABLE':
                    raise DatabaseError("Stock not available for sale")

                cursor.execute(
                    "INSERT INTO ice_sales (stock_id, price, sold_by_user_id) "
                    "SELECT stock_id, price, %s FROM ice_stocks WHERE stock_id = %s",
                    (sold_by_user_id, stock_id),
                )
                cursor.execute(
                    "UPDATE ice_stocks SET status = 'SOLD' WHERE stock_id = %s",
                    (stock_id,),
                )
            self.conn.commit()
            self._create_admin_notification(
                "SALE_RECORDED",
                sold_by_user_id,
                "Sale Recorded",
                f"{seller_name} sold {product_name} ({kg:g} kg) for ₱ {price:,.2f}. Stock #{stock_id} is now Sold.",
                "success",
            )
        except DatabaseError:
            self.conn.rollback()
            raise
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Failed to sell ice stock", exc)

    
    def authenticate_user(self, username: str, password: str) -> Optional[Tuple]:
        # Authenticate user
        """Authenticate user and return full user row (user_id, username, password_hash, created_at) or None."""
        try:
            self._ensure_connection_alive()
            password_hash = self._hash_password(password)
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id, username, password_hash, created_at FROM users WHERE username = %s AND password_hash = %s AND is_active = 1",
                    (username, password_hash),
                )
                user = cursor.fetchone()
                if not user:
                    return None
                
                if user[1] != username:
                    return None
                    
                return user
        except pymysql.MySQLError as exc:
            self._raise_error("Authentication failed", exc)

    def get_user_by_username(self, username: str) -> Optional[Tuple]:
        # Gets username
        """Get user by username. Returns full user row (user_id, username, password_hash, created_at) or None."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id, username, password_hash, created_at FROM users WHERE username = %s",
                    (username,),
                )
                user = cursor.fetchone()
                if not user:
                    return None
                
                return user
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to get user", exc)

    def get_user_roles(self, user_id: int) -> List[str]:
        # Gets roles
        """Get roles for a user."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT r.role_name FROM user_roles ur JOIN roles r ON ur.role_id = r.role_id WHERE ur.user_id = %s",
                    (user_id,),
                )
                return [row[0] for row in cursor.fetchall()]
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to get user roles", exc)

    def fetch_users_with_roles(self) -> List[Tuple]:
        # Fetchs roles
        """Get all users with aggregated role names and active flag."""
        query = """
            SELECT
                u.user_id,
                u.username,
                u.created_at,
                u.is_active,
                COALESCE(GROUP_CONCAT(r.role_name ORDER BY r.role_name SEPARATOR ', '), '') AS roles
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.user_id
            LEFT JOIN roles r ON r.role_id = ur.role_id
            GROUP BY u.user_id, u.username, u.created_at, u.is_active
            ORDER BY u.created_at DESC
        """
        return self._execute_query(query, fetchall=True) or []

    def create_user_with_role(self, username: str, password: str, role_name: str) -> int:
        # Creates role
        """Create a user and assign a role. Returns new user_id."""
        normalized_role = (role_name or "").strip().lower()
        if normalized_role not in ("admin", "staff"):
            raise DatabaseError("Invalid role. Allowed roles: admin, staff")

        try:
            self._ensure_connection_alive()
            password_hash = self._hash_password(password)
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    raise DatabaseError("Username already exists")

                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (username, password_hash),
                )
                new_user_id = cursor.lastrowid

                cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (normalized_role,))
                role_row = cursor.fetchone()
                if not role_row:
                    raise DatabaseError("Role not found")

                cursor.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (new_user_id, role_row[0]),
                )
            self.conn.commit()
            return int(new_user_id)
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Failed to create user account", exc)

    def set_user_active(self, user_id: int, is_active: bool) -> None:
        # Sets active
        try:
            self._execute_query(
                "UPDATE users SET is_active = %s WHERE user_id = %s",
                (1 if is_active else 0, user_id),
                commit=True,
            )
        except DatabaseError as exc:
            self._raise_error("Failed to update user status", exc)

    def update_user_password(self, user_id: int, new_password: str) -> None:
        # Updates password
        try:
            password_hash = self._hash_password(new_password)
            self._execute_query(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (password_hash, user_id),
                commit=True,
            )
        except DatabaseError as exc:
            self._raise_error("Failed to reset user password", exc)

    #REPORTING METHODS
    def fetch_revenue_summary(self) -> Dict[str, float]:
        # Fetchs summary
        """Get revenue summary: total, this_month, this_year."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                # Total revenue
                cursor.execute("SELECT COALESCE(SUM(price), 0) FROM ice_sales")
                total = cursor.fetchone()[0]
                
                # This month revenue
                cursor.execute(
                    "SELECT COALESCE(SUM(price), 0) FROM ice_sales WHERE MONTH(sale_time) = MONTH(NOW()) AND YEAR(sale_time) = YEAR(NOW())"
                )
                this_month = cursor.fetchone()[0]
                
                # This year revenue
                cursor.execute(
                    "SELECT COALESCE(SUM(price), 0) FROM ice_sales WHERE YEAR(sale_time) = YEAR(NOW())"
                )
                this_year = cursor.fetchone()[0]
                
                return {
                    "total": float(total),
                    "this_month": float(this_month),
                    "this_year": float(this_year),
                }
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to fetch revenue summary", exc)

    def fetch_stock_status_breakdown(self) -> Dict[str, int]:
        # Fetchs breakdown
        """Get count of stocks by status."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT status, COUNT(*) FROM ice_stocks GROUP BY status"
                )
                results = cursor.fetchall()
                breakdown = {"available": 0, "freezing": 0, "sold": 0, "total": 0}
                
                for status, count in results:
                    if status == "AVAILABLE":
                        breakdown["available"] = count
                    elif status == "NOT_AVAILABLE":
                        breakdown["freezing"] = count
                    elif status == "SOLD":
                        breakdown["sold"] = count
                    breakdown["total"] += count
                
                return breakdown
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to fetch stock status breakdown", exc)

    def fetch_top_products(self, limit: int = 10) -> List[Dict]:
        # Fetchs products
        """Get top selling products."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT s.product_name, COUNT(*) as sale_count, COALESCE(SUM(sl.price), 0) as total_revenue "
                    "FROM ice_stocks s LEFT JOIN ice_sales sl ON s.stock_id = sl.stock_id "
                    "GROUP BY s.product_name ORDER BY sale_count DESC LIMIT %s",
                    (limit,),
                )
                results = cursor.fetchall()
                return [
                    {
                        "product_name": row[0],
                        "sale_count": row[1],
                        "total_revenue": float(row[2]),
                    }
                    for row in results
                ]
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to fetch top products", exc)

    def fetch_sales_by_date_range(self, start_date: str = None, end_date: str = None, limit: int = 30) -> List[Dict]:
        # Fetchs range
        """Get daily sales summary."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                query = (
                    "SELECT DATE(sale_time) as sale_date, COUNT(*) as quantity, COALESCE(SUM(price), 0) as amount "
                    "FROM ice_sales "
                )
                params = []

                if start_date and end_date:
                    query += "WHERE DATE(sale_time) BETWEEN %s AND %s "
                    params.extend([start_date, end_date])
                elif start_date:
                    query += "WHERE DATE(sale_time) >= %s "
                    params.append(start_date)
                elif end_date:
                    query += "WHERE DATE(sale_time) <= %s "
                    params.append(end_date)
                else:
                    # Default to rolling time window when dates are not supplied.
                    query += "WHERE sale_time >= DATE_SUB(NOW(), INTERVAL %s DAY) "
                    params.append(limit)

                query += "GROUP BY DATE(sale_time) ORDER BY sale_date DESC"
                cursor.execute(query, tuple(params))
                results = cursor.fetchall()
                return [
                    {
                        "date": str(row[0]),
                        "quantity": row[1],
                        "amount": float(row[2]),
                    }
                    for row in results
                ]
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to fetch sales by date range", exc)

    # ==================== SEARCH/FILTER METHODS ====================
    def search_stocks_by_product(self, product_name: str) -> List[Tuple]:
        # Search product
        """Search stocks by product name."""
        if not product_name or not isinstance(product_name, str):
            return []
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM ice_stocks WHERE product_name LIKE %s",
                    (f"%{product_name[:80]}%",)
                )
                return cursor.fetchall()
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to search stocks", exc)

    def filter_sales_by_price_range(self, min_price: float, max_price: float) -> List[Tuple]:
        # Filter range
        """Filter sales within price range."""
        if not isinstance(min_price, (int, float)) or not isinstance(max_price, (int, float)):
            raise DatabaseError("Price range must be numeric")
        if min_price < 0 or max_price < 0:
            raise DatabaseError("Price cannot be negative")
        if min_price > max_price:
            raise DatabaseError("Minimum price cannot exceed maximum price")
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM ice_sales WHERE price >= %s AND price <= %s ORDER BY sale_time DESC",
                    (min_price, max_price),
                )
                return cursor.fetchall()
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to filter sales by price", exc)

    def filter_sales_by_date(self, start_date: str, end_date: str) -> List[Tuple]:
        # Filter date
        """Filter sales within date range."""
        if not start_date or not end_date:
            raise DatabaseError("Start and end dates are required")
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM ice_sales WHERE DATE(sale_time) >= %s AND DATE(sale_time) <= %s ORDER BY sale_time DESC",
                    (start_date, end_date),
                )
                return cursor.fetchall()
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to filter sales by date", exc)

    # ==================== ANNOUNCEMENT METHODS ====================
    def create_announcement(self, title: str, message: str, created_by_user_id: int, recipient_user_ids: List[int]) -> int:
        # Creates announcement
        """Create announcement and assign recipients. Returns announcement_id."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO announcements (title, message, created_by_user_id) VALUES (%s, %s, %s)",
                    (title, message, created_by_user_id),
                )
                announcement_id = cursor.lastrowid
                
                if recipient_user_ids:
                    cursor.executemany(
                        "INSERT INTO announcement_recipients (announcement_id, user_id) VALUES (%s, %s)",
                        [(announcement_id, uid) for uid in recipient_user_ids],
                    )
            self.conn.commit()
            return int(announcement_id)
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Failed to create announcement", exc)

    def fetch_announcements_for_user(self, user_id: int) -> List[Tuple]:
        # Fetchs user
        """Get all active (non-deleted) announcements for a specific user."""
        query = """
            SELECT
                a.announcement_id,
                a.title,
                a.message,
                a.created_at,
                u.username AS created_by,
                ar.is_read,
                ar.read_at,
                a.deleted_at
            FROM announcements a
            JOIN users u ON u.user_id = a.created_by_user_id
            JOIN announcement_recipients ar ON ar.announcement_id = a.announcement_id
            WHERE ar.user_id = %s AND a.is_active = 1 AND a.deleted_at IS NULL
            ORDER BY a.created_at DESC
        """
        return self._execute_query(query, (user_id,), fetchall=True) or []

    def fetch_all_announcements(self) -> List[Tuple]:
        # Fetchs announcements
        """Get all active (non-deleted) announcements (admin view)."""
        query = """
            SELECT
                a.announcement_id,
                a.title,
                a.message,
                a.created_at,
                u.username AS created_by,
                a.is_active,
                COUNT(ar.user_id) AS recipient_count,
                SUM(ar.is_read) AS read_count,
                a.deleted_at
            FROM announcements a
            JOIN users u ON u.user_id = a.created_by_user_id
            LEFT JOIN announcement_recipients ar ON ar.announcement_id = a.announcement_id
            WHERE a.deleted_at IS NULL
            GROUP BY a.announcement_id, a.title, a.message, a.created_at, u.username, a.is_active, a.deleted_at
            ORDER BY a.created_at DESC
        """
        return self._execute_query(query, fetchall=True) or []

    def mark_announcement_as_read(self, announcement_id: int, user_id: int) -> None:
        # Mark read
        """Mark announcement as read for a user."""
        self._execute_query(
            "UPDATE announcement_recipients SET is_read = 1, read_at = NOW() WHERE announcement_id = %s AND user_id = %s",
            (announcement_id, user_id),
            commit=True,
        )

    def delete_announcement(self, announcement_id: int) -> None:
        # Deletes announcement
        """Soft delete announcement by setting deleted_at to current timestamp."""
        self._execute_query(
            "UPDATE announcements SET deleted_at = NOW() WHERE announcement_id = %s",
            (announcement_id,),
            commit=True,
        )

    def soft_delete_announcement(self, announcement_id: int) -> None:
        # Soft announcement
        """Soft delete announcement by setting deleted_at to current timestamp."""
        self._execute_query(
            "UPDATE announcements SET deleted_at = NOW() WHERE announcement_id = %s",
            (announcement_id,),
            commit=True,
        )

    def restore_announcement(self, announcement_id: int) -> None:
        # Restore announcement
        """Restore a soft-deleted announcement by setting deleted_at to NULL."""
        self._execute_query(
            "UPDATE announcements SET deleted_at = NULL WHERE announcement_id = %s",
            (announcement_id,),
            commit=True,
        )

    def permanently_delete_announcement(self, announcement_id: int) -> None:
        # Permanently announcement
        """Permanently delete an announcement and its associated recipients."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM announcement_recipients WHERE announcement_id = %s", (announcement_id,))
                cursor.execute("DELETE FROM announcements WHERE announcement_id = %s", (announcement_id,))
            self.conn.commit()
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Failed to permanently delete announcement", exc)

    def fetch_deleted_announcements(self) -> List[Tuple]:
        # Fetchs announcements
        """Get all soft-deleted announcements (admin view)."""
        query = """
            SELECT
                a.announcement_id,
                a.title,
                a.message,
                a.created_at,
                u.username AS created_by,
                a.is_active,
                COUNT(ar.user_id) AS recipient_count,
                SUM(ar.is_read) AS read_count,
                a.deleted_at
            FROM announcements a
            JOIN users u ON u.user_id = a.created_by_user_id
            LEFT JOIN announcement_recipients ar ON ar.announcement_id = a.announcement_id
            WHERE a.deleted_at IS NOT NULL
            GROUP BY a.announcement_id, a.title, a.message, a.created_at, u.username, a.is_active, a.deleted_at
            ORDER BY a.deleted_at DESC
        """
        return self._execute_query(query, fetchall=True) or []

    def fetch_staff_users(self) -> List[Tuple]:
        # Fetchs users
        """Get all staff users (non-admin users)."""
        query = """
            SELECT DISTINCT u.user_id, u.username
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.user_id
            JOIN roles r ON r.role_id = ur.role_id
            WHERE r.role_name = 'staff' AND u.is_active = 1
            ORDER BY u.username
        """
        return self._execute_query(query, fetchall=True) or []

    def fetch_user_shift_schedule(self, user_id: int):
        # Fetchs schedule
        """Get shift schedule for a specific user. Returns (shift_start, shift_end, night_start, night_end) or all None if using global."""
        result = self._execute_query(
            "SELECT shift_start_time, shift_end_time, night_shift_start_time, night_shift_end_time FROM users WHERE user_id = %s",
            (user_id,),
            fetchone=True,
        )
        if not result:
            return (None, None, None, None)
        return result

    def update_user_shift_schedule(self, user_id: int, shift_start_time: str = None, shift_end_time: str = None, 
                                   night_shift_start_time: str = None, night_shift_end_time: str = None):
        # Updates schedule
        """Update shift schedule for a specific user. Pass None to clear/use global shifts."""
        self._execute_query(
            "UPDATE users SET shift_start_time = %s, shift_end_time = %s, night_shift_start_time = %s, night_shift_end_time = %s WHERE user_id = %s",
            (shift_start_time, shift_end_time, night_shift_start_time, night_shift_end_time, user_id),
            commit=True,
        )

    def fetch_all_staff_with_shifts(self) -> List[Tuple]:
        # Fetchs shifts
        """Get all staff users with their shift times (for admin view)."""
        query = """
            SELECT DISTINCT u.user_id, u.username, u.shift_start_time, u.shift_end_time, 
                   u.night_shift_start_time, u.night_shift_end_time
            FROM users u
            JOIN user_roles ur ON ur.user_id = u.user_id
            JOIN roles r ON r.role_id = ur.role_id
            WHERE r.role_name = 'staff' AND u.is_active = 1
            ORDER BY u.username
        """
        return self._execute_query(query, fetchall=True) or []


    def fetch_stock_availability_details(self) -> List[Tuple]:
        # Fetchs details
        """Get stock availability with minutes until available (uses vw_stock_availability)."""
        query = "SELECT * FROM vw_stock_availability ORDER BY minutes_until_available ASC"
        return self._execute_query(query, fetchall=True) or []

    def fetch_sales_with_stock_details(self) -> List[Tuple]:
        # Fetchs details
        """Get sales data with stock and seller info (uses vw_sales_with_stock)."""
        query = "SELECT * FROM vw_sales_with_stock ORDER BY sale_time DESC"
        return self._execute_query(query, fetchall=True) or []

    def fetch_daily_sales_summary(self, days: int = 30) -> List[Tuple]:
        # Fetchs summary
        """Get daily sales summary for reporting (uses vw_daily_sales_summary)."""
        query = """
            SELECT * FROM vw_daily_sales_summary
            WHERE sale_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY sale_date DESC
        """
        return self._execute_query(query, (days,), fetchall=True) or []

    def fetch_available_products_inventory(self) -> List[Tuple]:
        # Fetchs inventory
        """Get inventory of available products (uses vw_available_products)."""
        query = "SELECT * FROM vw_available_products ORDER BY available_count DESC, product_name ASC"
        return self._execute_query(query, fetchall=True) or []

    def fetch_activity_log_summary_by_type(self) -> List[Tuple]:
        # Fetchs type
        """Get activity log summary grouped by event type (uses vw_activity_log_summary)."""
        query = "SELECT * FROM vw_activity_log_summary ORDER BY events_count DESC"
        return self._execute_query(query, fetchall=True) or []
