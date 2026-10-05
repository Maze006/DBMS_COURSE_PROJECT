-- ============================================================================
-- 04_queries.sql : query library (run after 01-03; run 05_views.sql for section F)
-- A basic retrieval   B joins   C aggregates   D nested queries   E window/analytic
-- F reports through the views   G cost analysis
-- ============================================================================
USE license_mgmt;

-- ============================ A. BASIC RETRIEVAL ============================
-- A1. Active licenses ordered by nearest expiry
SELECT license_id, license_key, quantity, end_date
  FROM license
 WHERE status = 'Active'
 ORDER BY end_date
 LIMIT 10;

-- A2. Licenses expiring in the next 30 days
SELECT license_id, license_key, end_date, DATEDIFF(end_date, CURDATE()) AS days_left
  FROM license
 WHERE status = 'Active'
   AND end_date BETWEEN CURDATE() AND CURDATE() + INTERVAL 30 DAY
 ORDER BY end_date;

-- A3. Search products by name fragment (the app's search box)
SELECT product_id, name, category
  FROM software_product
 WHERE name LIKE '%Cloud%' OR category = 'DevTools';

-- A4. Users in the IT department with an administrative role
SELECT u.user_id, u.name, u.role
  FROM app_user u
  JOIN department d ON d.department_id = u.department_id
 WHERE d.name = 'IT Operations' AND u.role IN ('Admin', 'LicenseManager', 'Compliance');

-- ================================ B. JOINS ==================================
-- B1. Full allocation listing: who holds which license, on which device, charged to whom
SELECT a.allocation_id, u.name AS holder, hd.name AS home_dept, cd.name AS charged_dept,
       p.name AS product, v.name AS vendor, dv.hostname AS device,
       a.allocated_date, a.expiry_date, a.status
  FROM allocation a
  JOIN app_user          u  ON u.user_id        = a.user_id
  JOIN department        hd ON hd.department_id = u.department_id
  JOIN department        cd ON cd.department_id = a.department_id
  JOIN license           l  ON l.license_id     = a.license_id
  JOIN purchase          pu ON pu.purchase_id   = l.purchase_id
  JOIN license_type      lt ON lt.license_type_id = pu.license_type_id
  JOIN software_product  p  ON p.product_id     = lt.product_id
  JOIN vendor            v  ON v.vendor_id      = p.vendor_id
  LEFT JOIN device       dv ON dv.device_id     = a.device_id
 WHERE a.status = 'Active'
 ORDER BY v.name, p.name, u.name;

-- B2. Cross-charged seats: charged department differs from the user's home department
SELECT u.name AS holder, hd.name AS home_dept, cd.name AS charged_dept, p.name AS product
  FROM allocation a
  JOIN app_user u        ON u.user_id = a.user_id
  JOIN department hd     ON hd.department_id = u.department_id
  JOIN department cd     ON cd.department_id = a.department_id
  JOIN license l         ON l.license_id = a.license_id
  JOIN purchase pu       ON pu.purchase_id = l.purchase_id
  JOIN license_type lt   ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
 WHERE a.status = 'Active' AND a.department_id <> u.department_id;

-- B3. LEFT JOIN: every license type with how many licenses were bought (including none)
SELECT lt.license_type_id, p.name AS product, lt.name AS license_type, COUNT(pu.purchase_id) AS purchases
  FROM license_type lt
  JOIN software_product p ON p.product_id = lt.product_id
  LEFT JOIN purchase pu   ON pu.license_type_id = lt.license_type_id
 GROUP BY lt.license_type_id, p.name, lt.name
 ORDER BY purchases, p.name;

-- B4. Devices with the licenses installed on them (INNER JOIN, device-bound seats only)
SELECT dv.hostname, dv.device_type, p.name AS product, u.name AS user_name
  FROM allocation a
  JOIN device dv          ON dv.device_id = a.device_id
  JOIN app_user u         ON u.user_id = a.user_id
  JOIN license l          ON l.license_id = a.license_id
  JOIN purchase pu        ON pu.purchase_id = l.purchase_id
  JOIN license_type lt    ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
 WHERE a.status = 'Active'
 ORDER BY dv.hostname;

-- B5. Renewal history with the person who processed it
SELECT l.license_key, p.name AS product, r.renewal_date, r.previous_end_date,
       r.new_end_date, r.renewal_cost, u.name AS renewed_by
  FROM renewal r
  JOIN license l          ON l.license_id = r.license_id
  JOIN purchase pu        ON pu.purchase_id = l.purchase_id
  JOIN license_type lt    ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
  LEFT JOIN app_user u    ON u.user_id = r.renewed_by
 ORDER BY r.renewal_date DESC;

-- ============================== C. AGGREGATES ===============================
-- C1. Seats allocated per license with utilization %
SELECT l.license_id, p.name AS product, l.quantity AS capacity,
       COUNT(a.allocation_id) AS active_seats,
       ROUND(100 * COUNT(a.allocation_id) / l.quantity, 1) AS utilization_pct
  FROM license l
  JOIN purchase pu        ON pu.purchase_id = l.purchase_id
  JOIN license_type lt    ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
  LEFT JOIN allocation a  ON a.license_id = l.license_id AND a.status = 'Active'
 GROUP BY l.license_id, p.name, l.quantity
 ORDER BY utilization_pct DESC;

-- C2. Purchase spend per vendor (HAVING filters vendors above 10,000)
SELECT v.name AS vendor, COUNT(*) AS purchases, SUM(pu.quantity * pu.unit_cost) AS spend
  FROM purchase pu
  JOIN license_type lt    ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
  JOIN vendor v           ON v.vendor_id = p.vendor_id
 GROUP BY v.vendor_id, v.name
HAVING SUM(pu.quantity * pu.unit_cost) > 10000
 ORDER BY spend DESC;

-- C3. Active seats per department and per status (history of the lifecycle)
SELECT d.name AS department, a.status, COUNT(*) AS allocations
  FROM allocation a
  JOIN department d ON d.department_id = a.department_id
 GROUP BY d.name, a.status
 ORDER BY d.name, a.status;

-- C4. Licenses by pricing model: count, total seats, min/avg/max unit cost
SELECT lt.pricing_model, COUNT(*) AS licenses, SUM(l.quantity) AS seats,
       MIN(pu.unit_cost) AS min_cost, ROUND(AVG(pu.unit_cost), 2) AS avg_cost, MAX(pu.unit_cost) AS max_cost
  FROM license l
  JOIN purchase pu     ON pu.purchase_id = l.purchase_id
  JOIN license_type lt ON lt.license_type_id = pu.license_type_id
 GROUP BY lt.pricing_model;

-- C5. Renewal cost per year
SELECT YEAR(renewal_date) AS yr, COUNT(*) AS renewals, SUM(renewal_cost) AS total_cost
  FROM renewal
 GROUP BY YEAR(renewal_date)
 ORDER BY yr;

-- ============================ D. NESTED QUERIES =============================
-- D1. Licenses with NO active allocation (unused spend) - NOT EXISTS
SELECT l.license_id, l.license_key, l.quantity
  FROM license l
 WHERE l.status = 'Active'
   AND NOT EXISTS (SELECT 1 FROM allocation a
                    WHERE a.license_id = l.license_id AND a.status = 'Active');

-- D2. Users holding more active licenses than the average user (scalar subquery)
SELECT u.user_id, u.name, COUNT(*) AS licenses_held
  FROM allocation a
  JOIN app_user u ON u.user_id = a.user_id
 WHERE a.status = 'Active'
 GROUP BY u.user_id, u.name
HAVING COUNT(*) > (SELECT AVG(c) FROM (SELECT COUNT(*) AS c FROM allocation
                                        WHERE status = 'Active' GROUP BY user_id) t)
 ORDER BY licenses_held DESC;

-- D3. Over-allocated licenses (correlated subquery in WHERE)
SELECT l.license_id, l.license_key, l.quantity
  FROM license l
 WHERE (SELECT COUNT(*) FROM allocation a
         WHERE a.license_id = l.license_id AND a.status = 'Active') > l.quantity;

-- D4. Expired licenses that still have active allocations (IN subquery)
SELECT license_id, license_key, end_date
  FROM license
 WHERE (status = 'Expired' OR end_date < CURDATE())
   AND license_id IN (SELECT license_id FROM allocation WHERE status = 'Active');

-- D5. Departments with above-average active seat count (subquery in HAVING)
SELECT d.name, COUNT(*) AS seats
  FROM allocation a
  JOIN department d ON d.department_id = a.department_id
 WHERE a.status = 'Active'
 GROUP BY d.department_id, d.name
HAVING COUNT(*) > (SELECT AVG(s) FROM (SELECT COUNT(*) AS s FROM allocation
                                        WHERE status = 'Active' GROUP BY department_id) x);

-- D6. Vendors none of whose products have been purchased (NOT IN)
SELECT vendor_id, name
  FROM vendor
 WHERE vendor_id NOT IN (SELECT p.vendor_id
                           FROM software_product p
                           JOIN license_type lt ON lt.product_id = p.product_id
                           JOIN purchase pu     ON pu.license_type_id = lt.license_type_id);

-- D7. The most expensive purchase per vendor (correlated subquery with MAX)
SELECT v.name AS vendor, p.name AS product, pu.quantity * pu.unit_cost AS cost
  FROM purchase pu
  JOIN license_type lt    ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
  JOIN vendor v           ON v.vendor_id = p.vendor_id
 WHERE pu.quantity * pu.unit_cost = (
         SELECT MAX(pu2.quantity * pu2.unit_cost)
           FROM purchase pu2
           JOIN license_type lt2    ON lt2.license_type_id = pu2.license_type_id
           JOIN software_product p2 ON p2.product_id = lt2.product_id
          WHERE p2.vendor_id = v.vendor_id);

-- D8. Licenses never renewed although they are subscriptions (EXISTS + NOT EXISTS)
SELECT l.license_id, l.license_key
  FROM license l
 WHERE EXISTS     (SELECT 1 FROM subscription s WHERE s.license_id = l.license_id)
   AND NOT EXISTS (SELECT 1 FROM renewal r      WHERE r.license_id = l.license_id);

-- ========================= E. WINDOW / ANALYTIC (MySQL 8) ===================
-- E1. Rank vendors by total purchase spend
SELECT v.name AS vendor, SUM(pu.quantity * pu.unit_cost) AS spend,
       RANK() OVER (ORDER BY SUM(pu.quantity * pu.unit_cost) DESC) AS spend_rank
  FROM purchase pu
  JOIN license_type lt    ON lt.license_type_id = pu.license_type_id
  JOIN software_product p ON p.product_id = lt.product_id
  JOIN vendor v           ON v.vendor_id = p.vendor_id
 GROUP BY v.vendor_id, v.name;

-- E2. Running total of purchase spend over time
SELECT purchase_date, quantity * unit_cost AS cost,
       SUM(quantity * unit_cost) OVER (ORDER BY purchase_date, purchase_id) AS running_total
  FROM purchase
 ORDER BY purchase_date, purchase_id;

-- ======================= F. REPORTS (through the views) =====================
-- F1. License expiry (expired + next 90 days)
SELECT * FROM vw_license_expiry ORDER BY days_remaining;

-- F2. Utilization, lowest first (waste) and over-allocated licenses show negative seats_available
SELECT license_id, vendor, product, capacity, active_allocated, seats_available, utilization_pct
  FROM vw_license_utilization
 WHERE status = 'Active'
 ORDER BY utilization_pct;

-- F3. Compliance gaps
SELECT * FROM vw_compliance_gaps ORDER BY gap_type, license_id;

-- F4. Renewal cost by year / vendor / product
SELECT * FROM vw_renewal_cost_summary ORDER BY renewal_year DESC, total_renewal_cost DESC;

-- F5. Department allocation
SELECT * FROM vw_department_allocation ORDER BY allocated_seat_cost DESC;

-- F6. Vendor portfolio
SELECT * FROM vw_vendor_portfolio ORDER BY total_spend DESC;

-- ============================ G. COST ANALYSIS ==============================
-- G1. Idle spend: cost of seats paid for but not allocated, per license (valid licenses only)
SELECT license_id, vendor, product, seats_available,
       ROUND(seats_available * cost_per_seat, 2) AS idle_cost
  FROM vw_license_utilization
 WHERE status = 'Active' AND end_date >= CURDATE() AND seats_available > 0
 ORDER BY idle_cost DESC;

-- G2. Total estimated cost of seats currently allocated vs. idle across the estate
SELECT ROUND(SUM(LEAST(active_allocated, capacity) * cost_per_seat), 2)                AS allocated_value,
       ROUND(SUM(GREATEST(seats_available, 0) * cost_per_seat), 2)                     AS idle_value
  FROM vw_license_utilization
 WHERE status = 'Active' AND end_date >= CURDATE();

-- G3. Subscription commitments renewing in the next 90 days (budget forecast)
SELECT e.license_id, e.product, e.end_date, e.auto_renew, s.billing_cycle, s.cost_per_cycle
  FROM vw_license_expiry e
  JOIN subscription s ON s.license_id = e.license_id
 WHERE e.days_remaining >= 0
 ORDER BY e.end_date;
