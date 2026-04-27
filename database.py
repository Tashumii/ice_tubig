import pymysql
import hashlib
from pymysql.constants import CLIENT
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

class DatabaseError(Exception):
    """General database exception for the IceTubig system."""
    pass

class DatabaseManager:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host="localhost",
                user="root",
                password="",
                database="ice_tubig",
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
        if getattr(self, "conn", None):
            try:
                self.conn.close()
            finally:
                self.conn = None

    def __del__(self):
        self.close()

    def _raise_error(self, message, exc=None):
        if exc is None:
            raise DatabaseError(message)
        raise DatabaseError(f"{message}: {exc}") from exc

    def _ensure_connection_alive(self):
        if getattr(self, "conn", None) is None:
            self._raise_error("Database connection is closed")
        try:
            self.conn.ping(reconnect=True)
        except pymysql.MySQLError as exc:
            self._raise_error("Database connection unavailable", exc)

    def _execute_query(self, sql, params=None, commit=False, fetchone=False, fetchall=False):
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
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
        except pymysql.MySQLError as exc:
            if ignore_error_codes and exc.args and exc.args[0] in ignore_error_codes:
                return
            raise

    def _call_procedure(self, procedure_name, args=None, fetchone=False, fetchall=False):
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
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _ensure_schema(self):
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
                shift_end_time TIME NOT NULL DEFAULT '17:00:00'
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
        ]

        for statement in schema_statements:
            self._execute_safe_schema(statement)

        # Seed default roles
        self._execute_safe_schema(
            "INSERT IGNORE INTO roles (role_id, role_name, description) VALUES (1, 'admin', 'System administrator with full access'), (2, 'staff', 'Staff member with limited access')"
        )

        # Seed default admin user
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
        return self._execute_query(
            "SELECT stock_id, time_added, product_name, kg, freeze_duration_hours, status, price "
            "FROM ice_stocks WHERE status != 'SOLD' ORDER BY time_added DESC",
            fetchall=True,
        )

    def fetch_sales_history(self):
        query = """
            SELECT s.sale_id, s.stock_id, DATE_FORMAT(i.time_added, '%b %d, %Y %h:%i %p'),
                   DATE_FORMAT(s.sale_time, '%b %d, %Y %h:%i %p'),
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
        try:
            result = self._execute_query("SELECT theme FROM system_settings WHERE id = 1", fetchone=True)
            return result[0] if (result and result[0]) else "light"
        except DatabaseError:
            return "light"

    def update_theme_setting(self, theme):
        self._execute_query(
            "INSERT INTO system_settings (id, theme) VALUES (1, %s) "
            "ON DUPLICATE KEY UPDATE theme = VALUES(theme)",
            (theme,),
            commit=True,
        )

    def fetch_shift_schedule(self):
        result = self._execute_query(
            "SELECT shift_start_time, shift_end_time FROM system_settings WHERE id = 1",
            fetchone=True,
        )
        if not result:
            return ("08:00:00", "17:00:00")
        return result

    def update_shift_schedule(self, shift_start_time: str, shift_end_time: str):
        self._execute_query(
            "INSERT INTO system_settings (id, shift_start_time, shift_end_time) VALUES (1, %s, %s) "
            "ON DUPLICATE KEY UPDATE shift_start_time = VALUES(shift_start_time), shift_end_time = VALUES(shift_end_time)",
            (shift_start_time, shift_end_time),
            commit=True,
        )

    def clock_in_user(self, user_id: int):
        query = """
            INSERT INTO employee_shift_logs (
                user_id, shift_date, expected_in, expected_out, actual_in, attendance_status
            )
            VALUES (
                %s,
                CURRENT_DATE(),
                (SELECT shift_start_time FROM system_settings WHERE id = 1),
                (SELECT shift_end_time FROM system_settings WHERE id = 1),
                NOW(),
                CASE
                    WHEN TIME(NOW()) <= (SELECT shift_start_time FROM system_settings WHERE id = 1)
                    THEN 'ON_TIME'
                    ELSE 'LATE'
                END
            )
            ON DUPLICATE KEY UPDATE
                actual_in = COALESCE(actual_in, VALUES(actual_in)),
                expected_in = VALUES(expected_in),
                expected_out = VALUES(expected_out),
                attendance_status = CASE
                    WHEN actual_in IS NULL AND TIME(NOW()) <= (SELECT shift_start_time FROM system_settings WHERE id = 1) THEN 'ON_TIME'
                    WHEN actual_in IS NULL THEN 'LATE'
                    ELSE attendance_status
                END
        """
        self._execute_query(query, (user_id,), commit=True)

    def clock_out_user(self, user_id: int):
        query = """
            INSERT INTO employee_shift_logs (
                user_id, shift_date, expected_in, expected_out, actual_out, attendance_status
            )
            VALUES (
                %s,
                CURRENT_DATE(),
                (SELECT shift_start_time FROM system_settings WHERE id = 1),
                (SELECT shift_end_time FROM system_settings WHERE id = 1),
                NOW(),
                'COMPLETED'
            )
            ON DUPLICATE KEY UPDATE
                actual_out = NOW(),
                attendance_status = 'COMPLETED'
        """
        self._execute_query(query, (user_id,), commit=True)

    def fetch_shift_logs(self, user_id: int | None = None):
        query = """
            SELECT
                l.log_id,
                u.username,
                l.shift_date,
                DATE_FORMAT(l.expected_in, '%%H:%%i') AS expected_in,
                DATE_FORMAT(l.expected_out, '%%H:%%i') AS expected_out,
                DATE_FORMAT(l.actual_in, '%%Y-%%m-%%d %%H:%%i') AS actual_in,
                DATE_FORMAT(l.actual_out, '%%Y-%%m-%%d %%H:%%i') AS actual_out,
                l.attendance_status
            FROM employee_shift_logs l
            INNER JOIN users u ON u.user_id = l.user_id
        """
        params = ()
        if user_id is not None:
            query += " WHERE l.user_id = %s"
            params = (user_id,)
        query += " ORDER BY l.shift_date DESC, l.updated_at DESC"
        return self._execute_query(query, params if params else None, fetchall=True) or []

    def fetch_available_product_types(self):
        query = """
        SELECT MIN(s.stock_id), s.kg, s.freeze_duration_hours, s.price
        FROM ice_stocks s
        WHERE s.status = 'AVAILABLE'
        GROUP BY s.kg, s.freeze_duration_hours, s.price
        """
        return self._execute_query(query, fetchall=True)

    def fetch_activity_event_count(self):
        result = self._execute_query("SELECT COUNT(*) FROM ice_activity_log", fetchone=True)
        return int(result[0]) if result else 0

    def refresh_stock_availability(self):
        if self.procedure_mode:
            try:
                self._call_procedure("sp_refresh_ice_availability")
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
        if not isinstance(stock_id, int) or stock_id < 1:
            raise DatabaseError("Invalid stock identifier")

        if self.procedure_mode:
            try:
                self._call_procedure("sp_sell_stock", (stock_id, sold_by_user_id))
                return
            except DatabaseError:
                self.procedure_mode = False

        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM ice_stocks WHERE stock_id = %s",
                    (stock_id,),
                )
                record = cursor.fetchone()
                if not record:
                    raise DatabaseError("Stock not found")
                if record[0] != 'AVAILABLE':
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
        except pymysql.MySQLError as exc:
            self.conn.rollback()
            self._raise_error("Failed to sell ice stock", exc)

    # ==================== AUTHENTICATION METHODS ====================
    def authenticate_user(self, username: str, password: str) -> Optional[Tuple]:
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
                
                return user
        except pymysql.MySQLError as exc:
            self._raise_error("Authentication failed", exc)

    def get_user_by_username(self, username: str) -> Optional[Tuple]:
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
        try:
            self._execute_query(
                "UPDATE users SET is_active = %s WHERE user_id = %s",
                (1 if is_active else 0, user_id),
                commit=True,
            )
        except DatabaseError as exc:
            self._raise_error("Failed to update user status", exc)

    def update_user_password(self, user_id: int, new_password: str) -> None:
        try:
            password_hash = self._hash_password(new_password)
            self._execute_query(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (password_hash, user_id),
                commit=True,
            )
        except DatabaseError as exc:
            self._raise_error("Failed to reset user password", exc)

    # ==================== REPORTING METHODS ====================
    def fetch_revenue_summary(self) -> Dict[str, float]:
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
        """Search stocks by product name."""
        try:
            self._ensure_connection_alive()
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM ice_stocks WHERE product_name LIKE %s",
                    (f"%{product_name}%",),
                )
                return cursor.fetchall()
        except pymysql.MySQLError as exc:
            self._raise_error("Failed to search stocks", exc)

    def filter_sales_by_price_range(self, min_price: float, max_price: float) -> List[Tuple]:
        """Filter sales within price range."""
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
        """Filter sales within date range."""
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
