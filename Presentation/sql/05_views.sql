-- ============================================================================
-- 05_views.sql : reporting views
--   vw_license_utilization   (base view: capacity vs. active seats per license)
--   vw_license_expiry        report: license expiry
--   vw_compliance_gaps       report: compliance gaps
--   vw_renewal_cost_summary  report: renewal cost
--   vw_department_allocation report: department allocation
--   vw_vendor_portfolio      report: vendor portfolio
-- Views hide the 4-table join (license -> purchase -> license_type -> product -> vendor).
-- ============================================================================
USE license_mgmt;

-- ---------------------------------------------------------------------------
-- Base view: one row per license with vendor/product, capacity, usage and cost
-- seats_available is negative when a license is over-allocated.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_license_utilization AS
SELECT l.license_id,
       l.license_key,
       v.vendor_id,
       v.name                                   AS vendor,
       p.product_id,
       p.name                                   AS product,
       lt.name                                  AS license_type,
       lt.pricing_model,
       l.status,
       l.start_date,
       l.end_date,
       l.quantity                               AS capacity,
       COALESCE(a.active_cnt, 0)                AS active_allocated,
       l.quantity - COALESCE(a.active_cnt, 0)   AS seats_available,
       ROUND(100 * COALESCE(a.active_cnt, 0) / l.quantity, 1) AS utilization_pct,
       ROUND(pu.unit_cost / lt.seats_per_license, 2)          AS cost_per_seat,
       pu.quantity * pu.unit_cost               AS purchase_cost
  FROM license l
  JOIN purchase         pu ON pu.purchase_id     = l.purchase_id
  JOIN license_type     lt ON lt.license_type_id = pu.license_type_id
  JOIN software_product p  ON p.product_id       = lt.product_id
  JOIN vendor           v  ON v.vendor_id        = p.vendor_id
  LEFT JOIN (SELECT license_id, COUNT(*) AS active_cnt
               FROM allocation
              WHERE status = 'Active'
              GROUP BY license_id) a ON a.license_id = l.license_id;

-- ---------------------------------------------------------------------------
-- Report: license expiry (expired + expiring within 90 days, revoked excluded)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_license_expiry AS
SELECT u.license_id,
       u.license_key,
       u.vendor,
       u.product,
       u.end_date,
       DATEDIFF(u.end_date, CURDATE())  AS days_remaining,
       CASE
         WHEN u.end_date < CURDATE()                         THEN 'Expired'
         WHEN u.end_date <= CURDATE() + INTERVAL 30 DAY      THEN '0-30 days'
         WHEN u.end_date <= CURDATE() + INTERVAL 60 DAY      THEN '31-60 days'
         ELSE                                                     '61-90 days'
       END                              AS expiry_bucket,
       u.active_allocated,
       COALESCE(s.auto_renew, FALSE)    AS auto_renew
  FROM vw_license_utilization u
  LEFT JOIN subscription s ON s.license_id = u.license_id
 WHERE u.status <> 'Revoked'
   AND u.end_date <= CURDATE() + INTERVAL 90 DAY;

-- ---------------------------------------------------------------------------
-- Report: compliance gaps
--   Over-allocation : more active seats than capacity
--   Expired-in-use  : license expired but seats still allocated
--   Revoked-in-use  : license revoked but seats still allocated
--   Unused          : valid license with zero allocations (cost_at_risk = idle spend)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_compliance_gaps AS
SELECT license_id, license_key, vendor, product,
       'Over-allocation' AS gap_type, capacity, active_allocated,
       CONCAT(active_allocated - capacity, ' seat(s) over purchased quantity') AS detail,
       CAST(0 AS DECIMAL(12,2)) AS cost_at_risk
  FROM vw_license_utilization
 WHERE active_allocated > capacity
UNION ALL
SELECT license_id, license_key, vendor, product,
       'Expired-in-use', capacity, active_allocated,
       CONCAT('Expired on ', end_date, ' with ', active_allocated, ' active allocation(s)'),
       CAST(0 AS DECIMAL(12,2))
  FROM vw_license_utilization
 WHERE status <> 'Revoked' AND (status = 'Expired' OR end_date < CURDATE()) AND active_allocated > 0
UNION ALL
SELECT license_id, license_key, vendor, product,
       'Revoked-in-use', capacity, active_allocated,
       CONCAT('Revoked license with ', active_allocated, ' active allocation(s)'),
       CAST(0 AS DECIMAL(12,2))
  FROM vw_license_utilization
 WHERE status = 'Revoked' AND active_allocated > 0
UNION ALL
SELECT license_id, license_key, vendor, product,
       'Unused', capacity, active_allocated,
       CONCAT('0 of ', capacity, ' seats allocated'),
       CAST(purchase_cost AS DECIMAL(12,2))
  FROM vw_license_utilization
 WHERE status = 'Active' AND end_date >= CURDATE() AND active_allocated = 0;

-- ---------------------------------------------------------------------------
-- Report: renewal cost by year, vendor and product
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_renewal_cost_summary AS
SELECT YEAR(r.renewal_date)        AS renewal_year,
       v.name                      AS vendor,
       p.name                      AS product,
       COUNT(*)                    AS renewals,
       SUM(r.renewal_cost)         AS total_renewal_cost,
       ROUND(AVG(r.renewal_cost), 2) AS avg_renewal_cost
  FROM renewal r
  JOIN license          l  ON l.license_id       = r.license_id
  JOIN purchase         pu ON pu.purchase_id     = l.purchase_id
  JOIN license_type     lt ON lt.license_type_id = pu.license_type_id
  JOIN software_product p  ON p.product_id       = lt.product_id
  JOIN vendor           v  ON v.vendor_id        = p.vendor_id
 GROUP BY YEAR(r.renewal_date), v.vendor_id, v.name, p.product_id, p.name;

-- ---------------------------------------------------------------------------
-- Report: department allocation (active seats and the cost charged to each department)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_department_allocation AS
SELECT d.department_id,
       d.name                              AS department,
       d.cost_center_code,
       COUNT(a.allocation_id)              AS active_seats,
       COUNT(DISTINCT a.license_id)        AS licenses_in_use,
       COALESCE(SUM(u.cost_per_seat), 0)   AS allocated_seat_cost,
       ROUND(100 * COALESCE(SUM(u.cost_per_seat), 0)
             / NULLIF(SUM(COALESCE(SUM(u.cost_per_seat), 0)) OVER (), 0), 1) AS cost_share_pct
  FROM department d
  LEFT JOIN allocation a ON a.department_id = d.department_id AND a.status = 'Active'
  LEFT JOIN vw_license_utilization u ON u.license_id = a.license_id
 GROUP BY d.department_id, d.name, d.cost_center_code;

-- ---------------------------------------------------------------------------
-- Report: vendor portfolio
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_vendor_portfolio AS
SELECT v.vendor_id,
       v.name                                   AS vendor,
       (SELECT COUNT(*) FROM software_product sp WHERE sp.vendor_id = v.vendor_id) AS products,
       COALESCE(u.licenses, 0)                  AS licenses,
       COALESCE(u.total_seats, 0)               AS total_seats,
       COALESCE(u.seats_allocated, 0)           AS seats_allocated,
       COALESCE(u.purchase_spend, 0)            AS purchase_spend,
       COALESCE(rn.renewal_spend, 0)            AS renewal_spend,
       COALESCE(u.purchase_spend, 0) + COALESCE(rn.renewal_spend, 0) AS total_spend
  FROM vendor v
  LEFT JOIN (SELECT vendor_id,
                    COUNT(*)              AS licenses,
                    SUM(capacity)         AS total_seats,
                    SUM(active_allocated) AS seats_allocated,
                    SUM(purchase_cost)    AS purchase_spend
               FROM vw_license_utilization
              GROUP BY vendor_id) u ON u.vendor_id = v.vendor_id
  LEFT JOIN (SELECT p.vendor_id, SUM(r.renewal_cost) AS renewal_spend
               FROM renewal r
               JOIN license          l  ON l.license_id       = r.license_id
               JOIN purchase         pu ON pu.purchase_id     = l.purchase_id
               JOIN license_type     lt ON lt.license_type_id = pu.license_type_id
               JOIN software_product p  ON p.product_id       = lt.product_id
              GROUP BY p.vendor_id) rn ON rn.vendor_id = v.vendor_id;
