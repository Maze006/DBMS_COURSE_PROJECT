-- ============================================================================
-- 02_indexes.sql : indexes on frequently searched / filtered / joined attributes
-- InnoDB already indexes every FK column and every UNIQUE constraint
-- (license_key, email, asset_tag, order_reference, ...), so only the extra
-- access paths are created here.
-- ============================================================================
USE license_mgmt;

-- Expiry monitoring: WHERE end_date BETWEEN ... / status = 'Active'
CREATE INDEX idx_license_end_status  ON license (end_date, status);

-- Utilization / seat counting used by the allocation trigger and reports
CREATE INDEX idx_alloc_license_status ON allocation (license_id, status);

-- Allocation listings per department / user with status filter
CREATE INDEX idx_alloc_dept_status    ON allocation (department_id, status);
CREATE INDEX idx_alloc_expiry         ON allocation (expiry_date);

-- Cost analysis by period
CREATE INDEX idx_purchase_date        ON purchase (purchase_date);
CREATE INDEX idx_renewal_date         ON renewal (renewal_date);

-- Compliance history for a license, newest first
CREATE INDEX idx_check_license_date   ON compliance_check (license_id, check_date);

-- Search boxes in the app (name lookups)
CREATE INDEX idx_user_name            ON app_user (name);
CREATE INDEX idx_product_name         ON software_product (name);
CREATE INDEX idx_device_hostname      ON device (hostname);
