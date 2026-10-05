-- ============================================================================
-- 03_seed_data.sql : realistic sample data
-- All dates are relative to CURDATE(), so the "expiring soon", "expired" and
-- "active" cases stay valid whenever the demo is run.
-- Deliberate edge cases:
--   L4  expires in 25 days            L8/L9 expire in 12 days
--   L6  over-allocated (5 seats used, capacity cut to 4)
--   L7  expired but still has active allocations
--   L10, L12 fully utilized           L14  bought but never allocated (waste)
--   L17 revoked                       L5   cross-charged seat (HR user, Finance cost center)
-- Allocations go through the BR2-BR4 triggers, so the data is valid by construction;
-- the "gap" cases are produced afterwards by UPDATEs that simulate time passing.
-- ============================================================================
USE license_mgmt;

-- ---------------------------------------------------------------- vendors
INSERT INTO vendor (vendor_id, name, contact_email, phone, address) VALUES
 (1, 'Microsoft',  'enterprise@microsoft.example',  '+1-425-555-0101', 'One Microsoft Way, Redmond, WA'),
 (2, 'Adobe',      'sales@adobe.example',           '+1-408-555-0102', '345 Park Avenue, San Jose, CA'),
 (3, 'JetBrains',  'sales@jetbrains.example',       '+420-555-0103',   'Na Hrebenech II, Prague'),
 (4, 'Atlassian',  'licensing@atlassian.example',   '+61-2-5550-0104', '341 George Street, Sydney'),
 (5, 'Zoom',       'business@zoom.example',         '+1-888-555-0105', '55 Almaden Blvd, San Jose, CA'),
 (6, 'Oracle',     'licensing@oracle.example',      '+1-650-555-0106', '2300 Oracle Way, Austin, TX'),
 (7, 'Autodesk',   'sales@autodesk.example',        '+1-415-555-0107', '1 Market Street, San Francisco, CA'),
 (8, 'Salesforce', 'enterprise@salesforce.example', '+1-415-555-0108', '415 Mission Street, San Francisco, CA');

-- ---------------------------------------------------------------- products
INSERT INTO software_product (product_id, vendor_id, name, category, description) VALUES
 (1,  1, 'Microsoft 365 E3',            'Productivity',  'Office apps, Exchange, Teams, security'),
 (2,  1, 'Visual Studio',               'DevTools',      'IDE for .NET and C++ development'),
 (3,  1, 'Windows Server',              'Operating System', 'Server operating system'),
 (4,  2, 'Creative Cloud All Apps',     'Design',        'Photoshop, Illustrator, Premiere and more'),
 (5,  2, 'Acrobat Pro',                 'Productivity',  'PDF creation and editing'),
 (6,  3, 'IntelliJ IDEA Ultimate',      'DevTools',      'Java and Kotlin IDE'),
 (7,  3, 'PyCharm Professional',        'DevTools',      'Python IDE'),
 (8,  4, 'Jira Software',               'Collaboration', 'Issue and project tracking'),
 (9,  4, 'Confluence',                  'Collaboration', 'Team wiki and documentation'),
 (10, 5, 'Zoom Workplace',              'Communication', 'Video meetings and chat'),
 (11, 6, 'Oracle Database Enterprise',  'Database',      'Enterprise relational database'),
 (12, 7, 'AutoCAD',                     'Design',        '2D/3D CAD drafting'),
 (13, 8, 'Sales Cloud',                 'CRM',           'Customer relationship management');

-- ------------------------------------------------------------ license types
INSERT INTO license_type (license_type_id, product_id, name, seats_per_license, pricing_model) VALUES
 (1,  1,  'E3 Annual Subscription',          1,  'Subscription'),
 (2,  2,  'Enterprise Annual Subscription',  1,  'Subscription'),
 (3,  3,  'Standard Perpetual',              1,  'Perpetual'),
 (4,  4,  'All Apps Annual',                 1,  'Subscription'),
 (5,  5,  'Pro Annual',                      1,  'Subscription'),
 (6,  6,  'Ultimate Annual',                 1,  'Subscription'),
 (7,  7,  'Professional Annual',             1,  'Subscription'),
 (8,  8,  'Cloud Standard Monthly',          1,  'Subscription'),
 (9,  9,  'Cloud Standard Monthly',          1,  'Subscription'),
 (10, 10, 'Workplace Business Annual',       1,  'Subscription'),
 (11, 11, 'Processor Perpetual',             1,  'Perpetual'),
 (12, 12, 'Named User Annual',               1,  'Per-User'),
 (13, 13, 'Enterprise Annual',               1,  'Subscription'),
 (14, 12, 'Network Concurrent Perpetual',    1,  'Concurrent'),
 (15, 2,  'Professional Perpetual',          1,  'Perpetual'),
 (16, 8,  'Data Center 10-User Pack',        10, 'Subscription');

-- -------------------------------------------------------------- departments
INSERT INTO department (department_id, name, cost_center_code) VALUES
 (1, 'Engineering',    'CC-100'),
 (2, 'Sales',          'CC-200'),
 (3, 'Human Resources','CC-300'),
 (4, 'Finance',        'CC-400'),
 (5, 'IT Operations',  'CC-500'),
 (6, 'Marketing',      'CC-600');

-- -------------------------------------------------------------------- users
INSERT INTO app_user (user_id, department_id, name, email, role) VALUES
 (1,  1, 'Aarav Mehta',     'aarav.mehta@corp.example',     'Manager'),
 (2,  1, 'Isha Kapoor',     'isha.kapoor@corp.example',     'Employee'),
 (3,  1, 'Rohan Das',       'rohan.das@corp.example',       'Employee'),
 (4,  1, 'Priya Nair',      'priya.nair@corp.example',      'Employee'),
 (5,  1, 'Karan Malhotra',  'karan.malhotra@corp.example',  'Employee'),
 (6,  1, 'Sneha Iyer',      'sneha.iyer@corp.example',      'Employee'),
 (7,  1, 'Vikram Rao',      'vikram.rao@corp.example',      'Employee'),
 (8,  1, 'Ananya Bose',     'ananya.bose@corp.example',     'Employee'),
 (9,  1, 'Dev Sharma',      'dev.sharma@corp.example',      'Employee'),
 (10, 2, 'Meera Joshi',     'meera.joshi@corp.example',     'Manager'),
 (11, 2, 'Arjun Verma',     'arjun.verma@corp.example',     'Employee'),
 (12, 2, 'Pooja Reddy',     'pooja.reddy@corp.example',     'Employee'),
 (13, 2, 'Nikhil Gupta',    'nikhil.gupta@corp.example',    'Employee'),
 (14, 2, 'Tanya Singh',     'tanya.singh@corp.example',     'Employee'),
 (15, 3, 'Sunita Pillai',   'sunita.pillai@corp.example',   'Manager'),
 (16, 3, 'Rahul Menon',     'rahul.menon@corp.example',     'Employee'),
 (17, 3, 'Divya Chawla',    'divya.chawla@corp.example',    'Employee'),
 (18, 4, 'Anil Kulkarni',   'anil.kulkarni@corp.example',   'Manager'),
 (19, 4, 'Ritu Bansal',     'ritu.bansal@corp.example',     'Employee'),
 (20, 4, 'Sahil Arora',     'sahil.arora@corp.example',     'Employee'),
 (21, 4, 'Nisha Thakur',    'nisha.thakur@corp.example',    'Employee'),
 (22, 5, 'Harsh Vardhan',   'harsh.vardhan@corp.example',   'Admin'),
 (23, 5, 'Lakshmi Narayan', 'lakshmi.narayan@corp.example', 'LicenseManager'),
 (24, 5, 'Farhan Sheikh',   'farhan.sheikh@corp.example',   'Compliance'),
 (25, 5, 'Kavya Reddy',     'kavya.reddy@corp.example',     'Employee'),
 (26, 5, 'Manish Tiwari',   'manish.tiwari@corp.example',   'Employee'),
 (27, 6, 'Shreya Kohli',    'shreya.kohli@corp.example',    'Manager'),
 (28, 6, 'Aditya Jain',     'aditya.jain@corp.example',     'Employee'),
 (29, 6, 'Zoya Khan',       'zoya.khan@corp.example',       'Employee'),
 (30, 6, 'Neel Patel',      'neel.patel@corp.example',      'Employee');

-- ------------------------------------------------------------------ devices
INSERT INTO device (device_id, department_id, asset_tag, device_type, hostname) VALUES
 (1,  1, 'AST-0001', 'Laptop',  'eng-lt-001'),
 (2,  1, 'AST-0002', 'Laptop',  'eng-lt-002'),
 (3,  1, 'AST-0003', 'Laptop',  'eng-lt-003'),
 (4,  1, 'AST-0004', 'Laptop',  'eng-lt-004'),
 (5,  1, 'AST-0005', 'Desktop', 'eng-ws-005'),
 (6,  1, 'AST-0006', 'Desktop', 'eng-ws-006'),
 (7,  2, 'AST-0007', 'Laptop',  'sal-lt-007'),
 (8,  2, 'AST-0008', 'Laptop',  'sal-lt-008'),
 (9,  2, 'AST-0009', 'Laptop',  'sal-lt-009'),
 (10, 3, 'AST-0010', 'Laptop',  'hr-lt-010'),
 (11, 4, 'AST-0011', 'Laptop',  'fin-lt-011'),
 (12, 4, 'AST-0012', 'Desktop', 'fin-ws-012'),
 (13, 5, 'AST-0013', 'Server',  'it-srv-013'),
 (14, 5, 'AST-0014', 'Server',  'it-srv-014'),
 (15, 5, 'AST-0015', 'Server',  'it-db-015'),
 (16, 5, 'AST-0016', 'Server',  'it-db-016'),
 (17, 5, 'AST-0017', 'VM',      'it-vm-017'),
 (18, 6, 'AST-0018', 'Desktop', 'mkt-ws-018'),
 (19, 6, 'AST-0019', 'Desktop', 'mkt-ws-019'),
 (20, 6, 'AST-0020', 'Laptop',  'mkt-lt-020');

-- ---------------------------------------------------------------- purchases
-- purchase_id = license_id (1:1). unit_cost is the per-seat price for the term.
INSERT INTO purchase (purchase_id, license_type_id, quantity, unit_cost, purchase_date, order_reference) VALUES
 (1,  1,  12, 432.00,   CURDATE() - INTERVAL 605 DAY, 'PO-2026-001'),
 (2,  2,  6,  2999.00,  CURDATE() - INTERVAL 665 DAY, 'PO-2026-002'),
 (3,  3,  3,  972.00,   CURDATE() - INTERVAL 700 DAY, 'PO-2024-003'),
 (4,  4,  5,  659.88,   CURDATE() - INTERVAL 705 DAY, 'PO-2026-004'),
 (5,  5,  8,  239.88,   CURDATE() - INTERVAL 675 DAY, 'PO-2026-005'),
 (6,  6,  6,  599.00,   CURDATE() - INTERVAL 650 DAY, 'PO-2026-006'),
 (7,  7,  4,  249.00,   CURDATE() - INTERVAL 750 DAY, 'PO-2025-007'),
 (8,  8,  15, 97.80,    CURDATE() - INTERVAL 78 DAY,  'PO-2026-008'),
 (9,  9,  15, 61.92,    CURDATE() - INTERVAL 78 DAY,  'PO-2026-009'),
 (10, 10, 10, 240.00,   CURDATE() - INTERVAL 530 DAY, 'PO-2026-010'),
 (11, 11, 2,  47500.00, CURDATE() - INTERVAL 700 DAY, 'PO-2024-011'),
 (12, 12, 3,  2100.00,  CURDATE() - INTERVAL 100 DAY, 'PO-2026-012'),
 (13, 13, 8,  1800.00,  CURDATE() - INTERVAL 430 DAY, 'PO-2026-013'),
 (14, 14, 4,  4850.00,  CURDATE() - INTERVAL 500 DAY, 'PO-2025-014'),
 (15, 15, 5,  1199.00,  CURDATE() - INTERVAL 400 DAY, 'PO-2025-015'),
 (16, 16, 2,  3500.00,  CURDATE() - INTERVAL 685 DAY,  'PO-2026-016'),
 (17, 10, 5,  240.00,   CURDATE() - INTERVAL 90 DAY,  'PO-2026-017');

-- ----------------------------------------------------------------- licenses
-- quantity = purchase.quantity * license_type.seats_per_license
-- L7 is inserted valid and expired afterwards (see below); L17 is revoked.
INSERT INTO license (license_id, purchase_id, license_key, quantity, start_date, end_date, status) VALUES
 (1,  1,  'M365-E3-7F2A-91C4-0001',  12, CURDATE() - INTERVAL 605 DAY, CURDATE() + INTERVAL 125 DAY, 'Active'),
 (2,  2,  'VSENT-3B91-AA02-5D17-0002', 6, CURDATE() - INTERVAL 665 DAY, CURDATE() + INTERVAL 65 DAY,  'Active'),
 (3,  3,  'WINSRV-91C0-4E2B-7A33-0003', 3, CURDATE() - INTERVAL 700 DAY, '2099-12-31',                 'Active'),
 (4,  4,  'CCALL-5E10-77B4-C2D8-0004', 5, CURDATE() - INTERVAL 705 DAY, CURDATE() + INTERVAL 25 DAY,  'Active'),
 (5,  5,  'ACRPRO-A7F3-1190-6B2C-0005', 8, CURDATE() - INTERVAL 675 DAY, CURDATE() + INTERVAL 55 DAY,  'Active'),
 (6,  6,  'IDEAU-C4D2-08E6-93F1-0006', 6, CURDATE() - INTERVAL 650 DAY, CURDATE() + INTERVAL 80 DAY,  'Active'),
 (7,  7,  'PYCHP-2B6E-F451-0D9A-0007', 4, CURDATE() - INTERVAL 750 DAY, CURDATE() + INTERVAL 30 DAY,  'Active'),
 (8,  8,  'JIRA-CLD-4412-90AB-0008',  15, CURDATE() - INTERVAL 78 DAY,  CURDATE() + INTERVAL 12 DAY,  'Active'),
 (9,  9,  'CONF-CLD-8820-17CD-0009',  15, CURDATE() - INTERVAL 78 DAY,  CURDATE() + INTERVAL 12 DAY,  'Active'),
 (10, 10, 'ZOOM-BIZ-3391-AF20-0010',  10, CURDATE() - INTERVAL 530 DAY, CURDATE() + INTERVAL 200 DAY, 'Active'),
 (11, 11, 'ORADB-EE-0F11-8C3D-0011',   2, CURDATE() - INTERVAL 700 DAY, '2099-12-31',                 'Active'),
 (12, 12, 'ACAD-NU-6D55-21B8-0012',    3, CURDATE() - INTERVAL 100 DAY, CURDATE() + INTERVAL 150 DAY, 'Active'),
 (13, 13, 'SFDC-SC-9A04-E5F7-0013',    8, CURDATE() - INTERVAL 430 DAY, CURDATE() + INTERVAL 300 DAY, 'Active'),
 (14, 14, 'ACAD-NET-5C77-B310-0014',   4, CURDATE() - INTERVAL 500 DAY, '2099-12-31',                 'Active'),
 (15, 15, 'VSPRO-PERP-2E48-D09C-0015', 5, CURDATE() - INTERVAL 400 DAY, '2099-12-31',                 'Active'),
 (16, 16, 'JIRA-DC-7710-A4E2-0016',   20, CURDATE() - INTERVAL 685 DAY,  CURDATE() + INTERVAL 45 DAY,  'Active'),
 (17, 17, 'ZOOM-BIZ-1105-CC90-0017',   5, CURDATE() - INTERVAL 90 DAY,  CURDATE() + INTERVAL 275 DAY, 'Revoked');

-- ------------------------------------------------------------ subscriptions
INSERT INTO subscription (license_id, billing_cycle, auto_renew, cost_per_cycle) VALUES
 (1,  'Annual',  TRUE,  5443.20),
 (2,  'Annual',  FALSE, 18893.70),
 (4,  'Annual',  FALSE, 3464.37),
 (5,  'Annual',  TRUE,  2014.99),
 (6,  'Annual',  TRUE,  3773.70),
 (7,  'Annual',  FALSE, 1045.80),
 (8,  'Monthly', TRUE,  128.36),
 (9,  'Monthly', TRUE,  81.27),
 (10, 'Annual',  TRUE,  2520.00),
 (13, 'Annual',  TRUE,  15120.00),
 (16, 'Annual',  FALSE, 7350.00),
 (17, 'Annual',  FALSE, 1200.00);

-- -------------------------------------------------------------- allocations
-- User-only licenses: department charged = user's home department.
-- L1 Microsoft 365 (9 active + 1 reclaimed)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 1, user_id, NULL, department_id, CURDATE() - INTERVAL 200 DAY, CURDATE() + INTERVAL 125 DAY
  FROM app_user WHERE user_id IN (1,2,3,5,10,11,15,18,22);

-- L2 Visual Studio Enterprise (4, with devices)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date) VALUES
 (2, 1, 1, 1, CURDATE() - INTERVAL 280 DAY, CURDATE() + INTERVAL 65 DAY),
 (2, 2, 2, 1, CURDATE() - INTERVAL 280 DAY, CURDATE() + INTERVAL 65 DAY),
 (2, 3, 3, 1, CURDATE() - INTERVAL 280 DAY, CURDATE() + INTERVAL 65 DAY),
 (2, 4, 4, 1, CURDATE() - INTERVAL 280 DAY, CURDATE() + INTERVAL 65 DAY);

-- L3 Windows Server perpetual (2, on servers)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date) VALUES
 (3, 22, 13, 5, CURDATE() - INTERVAL 600 DAY, CURDATE() + INTERVAL 365 DAY),
 (3, 23, 14, 5, CURDATE() - INTERVAL 600 DAY, CURDATE() + INTERVAL 365 DAY);

-- L4 Creative Cloud (4, expiring in 25 days)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 4, user_id, NULL, department_id, CURDATE() - INTERVAL 300 DAY, CURDATE() + INTERVAL 25 DAY
  FROM app_user WHERE user_id IN (27,28,29,30);

-- L5 Acrobat Pro (5 own-department + 1 cross-charged: HR user billed to Finance)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 5, user_id, NULL, department_id, CURDATE() - INTERVAL 180 DAY, CURDATE() + INTERVAL 55 DAY
  FROM app_user WHERE user_id IN (10,11,12,15,18);
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date) VALUES
 (5, 16, NULL, 4, CURDATE() - INTERVAL 180 DAY, CURDATE() + INTERVAL 55 DAY);

-- L6 IntelliJ (5 active; capacity is cut to 4 below -> over-allocation gap)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 6, user_id, NULL, department_id, CURDATE() - INTERVAL 140 DAY, CURDATE() + INTERVAL 80 DAY
  FROM app_user WHERE user_id IN (1,2,3,4,5);

-- L7 PyCharm (3 active; license is expired below -> expired-in-use gap)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 7, user_id, NULL, department_id, CURDATE() - INTERVAL 300 DAY, CURDATE() + INTERVAL 30 DAY
  FROM app_user WHERE user_id IN (6,7,8);

-- L8 Jira and L9 Confluence (8 each, expiring in 12 days)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 8, user_id, NULL, department_id, CURDATE() - INTERVAL 25 DAY, CURDATE() + INTERVAL 12 DAY
  FROM app_user WHERE user_id IN (1,2,3,4,6,7,8,9);
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 9, user_id, NULL, department_id, CURDATE() - INTERVAL 25 DAY, CURDATE() + INTERVAL 12 DAY
  FROM app_user WHERE user_id IN (1,2,3,10,11,15,18,27);

-- L10 Zoom (10 of 10: fully utilized)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 10, user_id, NULL, department_id, CURDATE() - INTERVAL 150 DAY, CURDATE() + INTERVAL 200 DAY
  FROM app_user WHERE user_id IN (10,11,12,13,14,15,16,18,27,28);

-- L11 Oracle DB (1 of 2)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date) VALUES
 (11, 24, 15, 5, CURDATE() - INTERVAL 500 DAY, CURDATE() + INTERVAL 365 DAY);

-- L12 AutoCAD named user (3 of 3: fully utilized)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date) VALUES
 (12, 5,  5,  1, CURDATE() - INTERVAL 90 DAY, CURDATE() + INTERVAL 150 DAY),
 (12, 6,  6,  1, CURDATE() - INTERVAL 90 DAY, CURDATE() + INTERVAL 150 DAY),
 (12, 29, 19, 6, CURDATE() - INTERVAL 90 DAY, CURDATE() + INTERVAL 150 DAY);

-- L13 Salesforce (5)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 13, user_id, NULL, department_id, CURDATE() - INTERVAL 100 DAY, CURDATE() + INTERVAL 300 DAY
  FROM app_user WHERE user_id IN (10,11,12,13,14);

-- L14 AutoCAD concurrent: intentionally NO allocations (paid but unused)

-- L15 Visual Studio Professional perpetual (2)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date) VALUES
 (15, 5, 5, 1, CURDATE() - INTERVAL 200 DAY, CURDATE() + INTERVAL 365 DAY),
 (15, 6, 6, 1, CURDATE() - INTERVAL 200 DAY, CURDATE() + INTERVAL 365 DAY);

-- L16 Jira Data Center pack (5 of 20)
INSERT INTO allocation (license_id, user_id, device_id, department_id, allocated_date, expiry_date)
SELECT 16, user_id, NULL, department_id, CURDATE() - INTERVAL 40 DAY, CURDATE() + INTERVAL 45 DAY
  FROM app_user WHERE user_id IN (22,23,24,25,26);

-- ------------------------------------------------ history / lifecycle changes
-- Reclaimed seats (user left the project)
UPDATE allocation SET status = 'Reclaimed' WHERE license_id = 1  AND user_id = 5;
UPDATE allocation SET status = 'Reclaimed' WHERE license_id = 13 AND user_id = 14;
UPDATE allocation SET status = 'Reclaimed' WHERE license_id = 8  AND user_id = 9;

-- Simulate time passing: PyCharm license lapsed, allocations were never cleaned up
UPDATE license SET end_date = CURDATE() - INTERVAL 20 DAY, status = 'Expired' WHERE license_id = 7;

-- Simulate a vendor true-down: IntelliJ capacity reduced below current usage
UPDATE license SET quantity = 4 WHERE license_id = 6;

-- ----------------------------------------------------------------- renewals
-- Renewals happen on the term anniversary, after the original purchase.
-- Latest new_end_date = current license end_date.
INSERT INTO renewal (license_id, renewal_date, previous_end_date, new_end_date, renewal_cost, renewed_by) VALUES
 (1,  CURDATE() - INTERVAL 245 DAY, CURDATE() - INTERVAL 240 DAY, CURDATE() + INTERVAL 125 DAY, 5443.20,  23),
 (2,  CURDATE() - INTERVAL 305 DAY, CURDATE() - INTERVAL 300 DAY, CURDATE() + INTERVAL 65 DAY,  18893.70, 23),
 (4,  CURDATE() - INTERVAL 345 DAY, CURDATE() - INTERVAL 340 DAY, CURDATE() + INTERVAL 25 DAY,  3464.37,  23),
 (5,  CURDATE() - INTERVAL 315 DAY, CURDATE() - INTERVAL 310 DAY, CURDATE() + INTERVAL 55 DAY,  2014.99,  23),
 (6,  CURDATE() - INTERVAL 290 DAY, CURDATE() - INTERVAL 285 DAY, CURDATE() + INTERVAL 80 DAY,  3773.70,  22),
 (7,  CURDATE() - INTERVAL 390 DAY, CURDATE() - INTERVAL 385 DAY, CURDATE() - INTERVAL 20 DAY,  1045.80,  22),
 (8,  CURDATE() - INTERVAL 23 DAY,  CURDATE() - INTERVAL 18 DAY,  CURDATE() + INTERVAL 12 DAY,  128.36,   23),
 (9,  CURDATE() - INTERVAL 23 DAY,  CURDATE() - INTERVAL 18 DAY,  CURDATE() + INTERVAL 12 DAY,  81.27,    23),
 (10, CURDATE() - INTERVAL 170 DAY, CURDATE() - INTERVAL 165 DAY, CURDATE() + INTERVAL 200 DAY, 2520.00,  23),
 (13, CURDATE() - INTERVAL 70 DAY,  CURDATE() - INTERVAL 65 DAY,  CURDATE() + INTERVAL 300 DAY, 15120.00, 22),
 (16, CURDATE() - INTERVAL 325 DAY, CURDATE() - INTERVAL 320 DAY, CURDATE() + INTERVAL 45 DAY,  7350.00,  23);

-- --------------------------------------------------------- compliance checks
INSERT INTO compliance_check (license_id, check_date, check_type, result, details) VALUES
 (1,  CURDATE() - INTERVAL 30 DAY, 'Over-allocation', 'Pass', 'Allocated 9 of 12 seats'),
 (2,  CURDATE() - INTERVAL 30 DAY, 'Over-allocation', 'Pass', 'Allocated 4 of 6 seats'),
 (6,  CURDATE() - INTERVAL 7 DAY,  'Over-allocation', 'Fail', 'Allocated 5 seats but capacity is 4'),
 (7,  CURDATE() - INTERVAL 7 DAY,  'Expired-in-use',  'Fail', 'License expired 20 days ago; 3 active allocations remain'),
 (14, CURDATE() - INTERVAL 7 DAY,  'Unused',          'Fail', '0 of 4 seats allocated; license paid but idle'),
 (10, CURDATE() - INTERVAL 7 DAY,  'Over-allocation', 'Pass', 'Allocated 10 of 10 seats (fully utilized)'),
 (3,  CURDATE() - INTERVAL 90 DAY, 'Key-audit',       'Pass', 'Key verified with vendor portal'),
 (11, CURDATE() - INTERVAL 90 DAY, 'Key-audit',       'Pass', 'Key verified with vendor portal');
