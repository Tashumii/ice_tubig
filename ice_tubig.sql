CREATE DATABASE IF NOT EXISTS ice_tubig;
USE ice_tubig;

-- 1. Table for Settings (Configurable freezing time)
CREATE TABLE IF NOT EXISTS system_settings (
    id INT PRIMARY KEY DEFAULT 1,
    freeze_duration_hours INT NOT NULL DEFAULT 3,
    theme VARCHAR(20) NOT NULL DEFAULT 'light'
);

-- Insert default setting (3 hours)
INSERT IGNORE INTO system_settings (id, freeze_duration_hours, theme) VALUES (1, 3, 'light');

-- 2. Table for Ice Stocks
CREATE TABLE IF NOT EXISTS ice_stocks (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    time_added DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD') DEFAULT 'NOT_AVAILABLE',
    product_name VARCHAR(80) DEFAULT 'Ice',
    kg DECIMAL(5,2) DEFAULT 1.0,
    freeze_duration_hours INT DEFAULT 3,
    price DECIMAL(10,2) DEFAULT 5.00
);

-- 3. Table for Sales
CREATE TABLE IF NOT EXISTS ice_sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT NOT NULL,
    sale_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (stock_id) REFERENCES ice_stocks(stock_id)
);

-- 4. Activity log for trigger-driven insights
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
);

-- 5. ADBMS Automation: MySQL EVENT that checks and updates status automatically
-- Make sure the event scheduler is enabled in your MySQL configuration
SET GLOBAL event_scheduler = ON;

CREATE EVENT IF NOT EXISTS evt_update_ice_availability
ON SCHEDULE EVERY 1 MINUTE
DO
    UPDATE ice_stocks 
    SET status = 'AVAILABLE' 
    WHERE status = 'NOT_AVAILABLE' 
    AND TIMESTAMPDIFF(HOUR, time_added, NOW()) >= (
        SELECT freeze_duration_hours FROM system_settings WHERE id = 1
    );

-- 6. Stored procedures are supported when the database allows them.
--    The application can still work using direct SQL if procedures are unavailable.

DELIMITER $$
DROP PROCEDURE IF EXISTS sp_add_ice_stock$$
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
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error adding ice stock. Transaction rolled back.';
    END;

    START TRANSACTION;
    SET target_status = IF(p_instant OR p_freeze_duration_hours = 0, 'AVAILABLE', 'NOT_AVAILABLE');
    WHILE counter < p_qty DO
        INSERT INTO ice_stocks (status, product_name, kg, freeze_duration_hours, price)
        VALUES (target_status, p_product_name, p_kg, IF(p_instant, 0, p_freeze_duration_hours), p_price);
        SET counter = counter + 1;
    END WHILE;
    COMMIT;
END$$

DROP PROCEDURE IF EXISTS sp_sell_stock$$
CREATE PROCEDURE sp_sell_stock(IN p_stock_id INT)
BEGIN
    DECLARE v_status ENUM('NOT_AVAILABLE', 'AVAILABLE', 'SOLD');
    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error processing sale. Transaction rolled back.';
    END;

    START TRANSACTION;
    SELECT status INTO v_status FROM ice_stocks WHERE stock_id = p_stock_id FOR UPDATE;
    
    IF v_status IS NULL THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock not found';
    ELSEIF v_status != 'AVAILABLE' THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock not available for sale';
    ELSE
        INSERT INTO ice_sales (stock_id, price)
        SELECT stock_id, price FROM ice_stocks WHERE stock_id = p_stock_id;
        
        UPDATE ice_stocks SET status = 'SOLD' WHERE stock_id = p_stock_id;
        COMMIT;
    END IF;
END$$

DROP PROCEDURE IF EXISTS sp_refresh_ice_availability$$
CREATE PROCEDURE sp_refresh_ice_availability()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION 
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error refreshing availability. Transaction rolled back.';
    END;

    START TRANSACTION;
    UPDATE ice_stocks
    SET status = 'AVAILABLE'
    WHERE status = 'NOT_AVAILABLE'
    AND TIMESTAMPDIFF(HOUR, time_added, NOW()) >= (
        SELECT freeze_duration_hours FROM system_settings WHERE id = 1
    );
    COMMIT;
END$$

DROP PROCEDURE IF EXISTS sp_get_dashboard_summary$$
CREATE PROCEDURE sp_get_dashboard_summary()
BEGIN
    SELECT
        COALESCE(SUM(status = 'AVAILABLE'), 0) AS available_count,
        COALESCE(SUM(status = 'NOT_AVAILABLE'), 0) AS freezing_count,
        (SELECT COUNT(*) FROM ice_sales) AS sold_count,
        (SELECT COUNT(*) FROM ice_activity_log) AS activity_count
    FROM ice_stocks;
END$$

-- 7. Triggers for automatic stock state and event logging
DROP TRIGGER IF EXISTS trg_before_insert_ice_stocks$$
CREATE TRIGGER trg_before_insert_ice_stocks
BEFORE INSERT ON ice_stocks
FOR EACH ROW
BEGIN
    IF NEW.freeze_duration_hours = 0 THEN
        SET NEW.status = 'AVAILABLE';
    ELSE
        SET NEW.status = 'NOT_AVAILABLE';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_after_insert_ice_stocks$$
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
END$$

DROP TRIGGER IF EXISTS trg_after_update_ice_stocks$$
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
END$$

DROP TRIGGER IF EXISTS trg_after_ice_sale$$
CREATE TRIGGER trg_after_ice_sale
AFTER INSERT ON ice_sales
FOR EACH ROW
BEGIN
    UPDATE ice_stocks SET status = 'SOLD' WHERE stock_id = NEW.stock_id;
    INSERT INTO ice_activity_log (
        stock_id, event_type, old_status, new_status, product_name, price, details
    ) VALUES (
        NEW.stock_id, 'SALE', 'AVAILABLE', 'SOLD',
        (SELECT product_name FROM ice_stocks WHERE stock_id = NEW.stock_id),
        NEW.price,
        CONCAT('Sale recorded for stock ', NEW.stock_id)
    );
END$$
DELIMITER ;

