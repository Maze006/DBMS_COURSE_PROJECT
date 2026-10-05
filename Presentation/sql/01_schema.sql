-- ============================================================================
-- Software License & Subscription Management System
-- 01_schema.sql : database, tables, constraints, business-rule triggers
-- Target: MySQL 8.0.16+ (CHECK constraints are enforced from 8.0.16)
-- WARNING: drops and recreates the database.
-- ============================================================================

DROP DATABASE IF EXISTS license_mgmt;
CREATE DATABASE license_mgmt CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE license_mgmt;

-- ----------------------------------------------------------------------------
-- Master data
-- ----------------------------------------------------------------------------
CREATE TABLE vendor (
  vendor_id      INT AUTO_INCREMENT PRIMARY KEY,
  name           VARCHAR(100) NOT NULL,
  contact_email  VARCHAR(150) NOT NULL,
  phone          VARCHAR(30),
  address        VARCHAR(255),
  CONSTRAINT uq_vendor_name  UNIQUE (name),
  CONSTRAINT chk_vendor_email CHECK (contact_email LIKE '_%@_%._%')
) ENGINE=InnoDB;

CREATE TABLE software_product (
  product_id   INT AUTO_INCREMENT PRIMARY KEY,
  vendor_id    INT NOT NULL,
  name         VARCHAR(100) NOT NULL,
  category     VARCHAR(50)  NOT NULL,
  description  VARCHAR(255),
  CONSTRAINT uq_product_vendor_name UNIQUE (vendor_id, name),
  CONSTRAINT fk_product_vendor FOREIGN KEY (vendor_id) REFERENCES vendor (vendor_id)
) ENGINE=InnoDB;

CREATE TABLE license_type (
  license_type_id    INT AUTO_INCREMENT PRIMARY KEY,
  product_id         INT NOT NULL,
  name               VARCHAR(60) NOT NULL,
  seats_per_license  INT NOT NULL DEFAULT 1,
  pricing_model      VARCHAR(20) NOT NULL,
  CONSTRAINT uq_ltype_product_name UNIQUE (product_id, name),
  CONSTRAINT fk_ltype_product FOREIGN KEY (product_id) REFERENCES software_product (product_id),
  CONSTRAINT chk_ltype_seats  CHECK (seats_per_license > 0),
  CONSTRAINT chk_ltype_model  CHECK (pricing_model IN ('Perpetual','Subscription','Concurrent','Per-User'))
) ENGINE=InnoDB;

CREATE TABLE department (
  department_id     INT AUTO_INCREMENT PRIMARY KEY,
  name              VARCHAR(80) NOT NULL,
  cost_center_code  VARCHAR(20) NOT NULL,
  CONSTRAINT uq_dept_name UNIQUE (name),
  CONSTRAINT uq_dept_cc   UNIQUE (cost_center_code)
) ENGINE=InnoDB;

CREATE TABLE app_user (
  user_id        INT AUTO_INCREMENT PRIMARY KEY,
  department_id  INT NOT NULL,
  name           VARCHAR(100) NOT NULL,
  email          VARCHAR(150) NOT NULL,
  role           VARCHAR(20)  NOT NULL DEFAULT 'Employee',
  CONSTRAINT uq_user_email UNIQUE (email),
  CONSTRAINT fk_user_dept FOREIGN KEY (department_id) REFERENCES department (department_id),
  CONSTRAINT chk_user_email CHECK (email LIKE '_%@_%._%'),
  CONSTRAINT chk_user_role CHECK (role IN ('Employee','Manager','Admin','LicenseManager','Compliance'))
) ENGINE=InnoDB;

CREATE TABLE device (
  device_id      INT AUTO_INCREMENT PRIMARY KEY,
  department_id  INT NOT NULL,
  asset_tag      VARCHAR(40) NOT NULL,
  device_type    VARCHAR(30) NOT NULL,
  hostname       VARCHAR(80),
  CONSTRAINT uq_device_tag UNIQUE (asset_tag),
  CONSTRAINT fk_device_dept FOREIGN KEY (department_id) REFERENCES department (department_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- Commercial and license lifecycle
-- ----------------------------------------------------------------------------
CREATE TABLE purchase (
  purchase_id      INT AUTO_INCREMENT PRIMARY KEY,
  license_type_id  INT NOT NULL,
  quantity         INT NOT NULL,
  unit_cost        DECIMAL(12,2) NOT NULL,
  purchase_date    DATE NOT NULL DEFAULT (CURDATE()),
  order_reference  VARCHAR(50),
  CONSTRAINT uq_purchase_order UNIQUE (order_reference),
  CONSTRAINT fk_purchase_ltype FOREIGN KEY (license_type_id) REFERENCES license_type (license_type_id),
  CONSTRAINT chk_purchase_qty  CHECK (quantity > 0),
  CONSTRAINT chk_purchase_cost CHECK (unit_cost >= 0)
) ENGINE=InnoDB;

CREATE TABLE license (
  license_id   INT AUTO_INCREMENT PRIMARY KEY,
  purchase_id  INT NOT NULL,
  license_key  VARCHAR(100) NOT NULL,
  quantity     INT NOT NULL,
  start_date   DATE NOT NULL,
  end_date     DATE NOT NULL,
  status       VARCHAR(10) NOT NULL DEFAULT 'Active',
  CONSTRAINT uq_license_key      UNIQUE (license_key),                 -- BR1
  CONSTRAINT uq_license_purchase UNIQUE (purchase_id),
  CONSTRAINT fk_license_purchase FOREIGN KEY (purchase_id) REFERENCES purchase (purchase_id),
  CONSTRAINT chk_license_qty    CHECK (quantity > 0),
  CONSTRAINT chk_license_dates  CHECK (end_date > start_date),
  CONSTRAINT chk_license_status CHECK (status IN ('Active','Expired','Revoked'))
) ENGINE=InnoDB;

CREATE TABLE subscription (
  subscription_id  INT AUTO_INCREMENT PRIMARY KEY,
  license_id       INT NOT NULL,
  billing_cycle    VARCHAR(10) NOT NULL,
  auto_renew       BOOLEAN NOT NULL DEFAULT FALSE,
  cost_per_cycle   DECIMAL(12,2) NOT NULL,
  CONSTRAINT uq_subscription_license UNIQUE (license_id),
  CONSTRAINT fk_subscription_license FOREIGN KEY (license_id) REFERENCES license (license_id),
  CONSTRAINT chk_sub_cycle CHECK (billing_cycle IN ('Monthly','Quarterly','Annual')),
  CONSTRAINT chk_sub_cost  CHECK (cost_per_cycle > 0)
) ENGINE=InnoDB;

CREATE TABLE allocation (
  allocation_id   INT AUTO_INCREMENT PRIMARY KEY,
  license_id      INT NOT NULL,
  user_id         INT NOT NULL,
  device_id       INT NULL,
  department_id   INT NOT NULL,                       -- department charged
  allocated_date  DATE NOT NULL DEFAULT (CURDATE()),
  expiry_date     DATE NOT NULL,
  status          VARCHAR(10) NOT NULL DEFAULT 'Active',
  -- BR6: one active seat per user per license (MySQL has no partial unique index)
  active_user_key INT GENERATED ALWAYS AS (IF(status = 'Active', user_id, NULL)) STORED,
  CONSTRAINT uq_active_seat UNIQUE (license_id, active_user_key),
  CONSTRAINT fk_alloc_license FOREIGN KEY (license_id)    REFERENCES license (license_id),
  CONSTRAINT fk_alloc_user    FOREIGN KEY (user_id)       REFERENCES app_user (user_id),
  CONSTRAINT fk_alloc_device  FOREIGN KEY (device_id)     REFERENCES device (device_id),
  CONSTRAINT fk_alloc_dept    FOREIGN KEY (department_id) REFERENCES department (department_id),
  CONSTRAINT chk_alloc_period CHECK (expiry_date > allocated_date),                -- BR3 (part 1)
  CONSTRAINT chk_alloc_status CHECK (status IN ('Active','Reclaimed','Expired'))
) ENGINE=InnoDB;

CREATE TABLE renewal (
  renewal_id         INT AUTO_INCREMENT PRIMARY KEY,
  license_id         INT NOT NULL,
  renewal_date       DATE NOT NULL DEFAULT (CURDATE()),
  previous_end_date  DATE NOT NULL,
  new_end_date       DATE NOT NULL,
  renewal_cost       DECIMAL(12,2) NOT NULL,
  renewed_by         INT NULL,
  CONSTRAINT fk_renewal_license FOREIGN KEY (license_id) REFERENCES license (license_id),
  CONSTRAINT fk_renewal_user    FOREIGN KEY (renewed_by) REFERENCES app_user (user_id),
  CONSTRAINT chk_renewal_cost  CHECK (renewal_cost > 0),                            -- BR5
  CONSTRAINT chk_renewal_dates CHECK (new_end_date > previous_end_date)
) ENGINE=InnoDB;

CREATE TABLE compliance_check (
  check_id    INT AUTO_INCREMENT PRIMARY KEY,
  license_id  INT NOT NULL,
  check_date  DATE NOT NULL DEFAULT (CURDATE()),
  check_type  VARCHAR(30) NOT NULL,
  result      VARCHAR(4)  NOT NULL,
  details     VARCHAR(255),
  CONSTRAINT fk_check_license FOREIGN KEY (license_id) REFERENCES license (license_id),
  CONSTRAINT chk_check_type   CHECK (check_type IN ('Over-allocation','Expired-in-use','Unused','Key-audit')),
  CONSTRAINT chk_check_result CHECK (result IN ('Pass','Fail'))
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- Business-rule triggers (cross-row / cross-table rules a CHECK cannot express)
--   BR2 allocation within purchased quantity
--   BR3 allocation period inside the license validity window
--   BR4 no assignment of expired / revoked licenses
-- The license row is locked (FOR UPDATE) so two concurrent allocations cannot
-- both take the last seat.
-- ----------------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER trg_allocation_bi
BEFORE INSERT ON allocation
FOR EACH ROW
BEGIN
  DECLARE v_qty    INT;
  DECLARE v_start  DATE;
  DECLARE v_end    DATE;
  DECLARE v_status VARCHAR(10);
  DECLARE v_used   INT;

  IF NEW.status = 'Active' THEN
    SELECT quantity, start_date, end_date, status
      INTO v_qty, v_start, v_end, v_status
      FROM license WHERE license_id = NEW.license_id FOR UPDATE;

    IF v_status <> 'Active' OR v_end < CURDATE() THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot allocate an expired or revoked license';
    END IF;

    IF NEW.allocated_date < v_start OR NEW.expiry_date > v_end THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Allocation period must lie within the license validity window';
    END IF;

    SELECT COUNT(*) INTO v_used FROM allocation
     WHERE license_id = NEW.license_id AND status = 'Active';
    IF v_used >= v_qty THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Allocation exceeds purchased quantity for this license';
    END IF;
  END IF;
END$$

CREATE TRIGGER trg_allocation_bu
BEFORE UPDATE ON allocation
FOR EACH ROW
BEGIN
  DECLARE v_qty    INT;
  DECLARE v_start  DATE;
  DECLARE v_end    DATE;
  DECLARE v_status VARCHAR(10);
  DECLARE v_used   INT;

  -- validate only when a row becomes (or is changed while) Active
  IF NEW.status = 'Active' AND (OLD.status <> 'Active'
        OR NEW.license_id <> OLD.license_id
        OR NEW.allocated_date <> OLD.allocated_date
        OR NEW.expiry_date <> OLD.expiry_date) THEN

    SELECT quantity, start_date, end_date, status
      INTO v_qty, v_start, v_end, v_status
      FROM license WHERE license_id = NEW.license_id FOR UPDATE;

    IF v_status <> 'Active' OR v_end < CURDATE() THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot allocate an expired or revoked license';
    END IF;

    IF NEW.allocated_date < v_start OR NEW.expiry_date > v_end THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Allocation period must lie within the license validity window';
    END IF;

    SELECT COUNT(*) INTO v_used FROM allocation
     WHERE license_id = NEW.license_id AND status = 'Active'
       AND allocation_id <> NEW.allocation_id;
    IF v_used >= v_qty THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Allocation exceeds purchased quantity for this license';
    END IF;
  END IF;
END$$

DELIMITER ;
