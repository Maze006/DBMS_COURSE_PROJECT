-- ============================================================================
-- 06_procedures.sql : stored procedures used by the application
--   sp_expire_overdue      expiry sweep: mark lapsed licenses/allocations as Expired
--   sp_run_compliance_check evaluate every license and store each result
-- Run after 05_views.sql.
-- ============================================================================
USE license_mgmt;

DROP PROCEDURE IF EXISTS sp_expire_overdue;
DROP PROCEDURE IF EXISTS sp_run_compliance_check;

DELIMITER $$

-- Marks Active licenses past their end date as Expired, then marks Active allocations
-- as Expired when their own expiry date passed or their license is no longer valid.
-- Revoked licenses are left alone: their allocations show up as compliance gaps instead.
CREATE PROCEDURE sp_expire_overdue(OUT p_licenses INT, OUT p_allocations INT)
BEGIN
  UPDATE license
     SET status = 'Expired'
   WHERE status = 'Active' AND end_date < CURDATE();
  SET p_licenses = ROW_COUNT();

  UPDATE allocation a
  JOIN license l ON l.license_id = a.license_id
     SET a.status = 'Expired'
   WHERE a.status = 'Active'
     AND (a.expiry_date < CURDATE() OR l.status = 'Expired');
  SET p_allocations = ROW_COUNT();
END$$

-- One row per license per check type. Re-running on the same day replaces that day's
-- results; Key-audit rows are manual and never touched.
CREATE PROCEDURE sp_run_compliance_check()
BEGIN
  DELETE FROM compliance_check
   WHERE check_date = CURDATE()
     AND check_type IN ('Over-allocation', 'Expired-in-use', 'Unused');

  INSERT INTO compliance_check (license_id, check_date, check_type, result, details)
  SELECT license_id, CURDATE(), 'Over-allocation',
         IF(active_allocated > capacity, 'Fail', 'Pass'),
         CONCAT('Allocated ', active_allocated, ' of ', capacity, ' seats')
    FROM vw_license_utilization
   WHERE status <> 'Revoked';

  INSERT INTO compliance_check (license_id, check_date, check_type, result, details)
  SELECT license_id, CURDATE(), 'Expired-in-use',
         IF((status IN ('Expired', 'Revoked') OR end_date < CURDATE()) AND active_allocated > 0, 'Fail', 'Pass'),
         IF((status IN ('Expired', 'Revoked') OR end_date < CURDATE()) AND active_allocated > 0,
            CONCAT(status, ' license with ', active_allocated, ' active allocation(s)'),
            'No active allocations on an invalid license')
    FROM vw_license_utilization;

  INSERT INTO compliance_check (license_id, check_date, check_type, result, details)
  SELECT license_id, CURDATE(), 'Unused',
         IF(active_allocated = 0, 'Fail', 'Pass'),
         IF(active_allocated = 0,
            CONCAT('0 of ', capacity, ' seats allocated; license is idle'),
            CONCAT(active_allocated, ' of ', capacity, ' seats in use'))
    FROM vw_license_utilization
   WHERE status = 'Active' AND end_date >= CURDATE();
END$$

DELIMITER ;
