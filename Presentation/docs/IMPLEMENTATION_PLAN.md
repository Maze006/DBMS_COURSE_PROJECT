# Software License & Subscription Management System — Implementation Plan

## 0. Project Snapshot
- **Course project:** Project 40 — DBMS
- **Goal:** Centralized system to track vendors, software products, licenses, subscriptions, allocations to departments/users/devices, purchases, renewals, and compliance.
- **Stack:** PostgreSQL (recommended over MySQL for CHECK constraints, views, window functions) + Python (Streamlit or Tkinter/PyQt, or Flask) for the front end.
- **Timeline assumption:** 4–5 week build, organized into 8 phases below. Adjust dates to your actual deadlines.

---

## 1. Problem Identification, Scope, Objectives

### 1.1 Problem
Organizations buy licenses/subscriptions for many software products across departments. Without a central system: licenses expire unnoticed, seats get over-allocated beyond purchased quantity, expired licenses stay assigned, renewal costs aren't tracked, and there's no compliance visibility (allocated vs. purchased vs. actually installed).

### 1.2 Scope
In scope:
- Master data: vendors, software products, license types, departments, users, devices
- Transactional data: purchases, licenses (keys), subscriptions, allocations, renewals
- Compliance checks (a log/report of over-allocation or expiry violations)
- Reporting: expiry, utilization, compliance gaps, renewal cost, department allocation, vendor portfolio
- A CRUD front-end app for day-to-day operations

Out of scope:
- Actual software deployment/installation automation
- Payment processing / invoicing integration
- SSO/user authentication federation (a simple login for the app itself is enough)

### 1.3 Objectives
1. Design a normalized (3NF) relational schema modeling the domain correctly.
2. Enforce business rules via DB constraints, not just app code.
3. Provide realistic sample data and a query library covering joins, subqueries, aggregates, views.
4. Build a working Python front end for the operational workflows.
5. Demonstrate integrity, indexing, transactions, and basic testing.

### 1.4 User Roles
| Role | Responsibilities |
|---|---|
| **Admin** | Manage vendors/products/license types/departments/users/devices; full access |
| **License Manager** | Record purchases, allocate/reclaim licenses, process renewals |
| **Compliance Officer** | Run compliance checks, view reports, flag violations |
| **Department Viewer** (optional/stretch) | Read-only view of their department's allocations |

### 1.5 Functional Requirements
- FR1: Record a purchase (vendor, product, license type, quantity, cost, date) → generates license record(s)/pool
- FR2: Allocate a license/seat to a user+device within a department, within purchased quantity, within valid dates
- FR3: Prevent allocation of expired or fully-utilized licenses
- FR4: Reclaim (deallocate) a license from a user/device
- FR5: Renew a subscription/license (extend end date, log renewal cost — must be positive)
- FR6: Monitor expiring licenses (e.g., within 30/60/90 days)
- FR7: Run compliance checks (allocated > purchased, expired-but-allocated, unassigned wasted seats)
- FR8: Generate reports: expiry, utilization %, compliance gaps, renewal cost trends, department cost allocation, vendor portfolio summary
- FR9: Search/filter across licenses, vendors, products, departments
- FR10: Input validation + error handling in the app layer, backed by DB constraints

---

## 2. Conceptual Design (ER Model)

### 2.1 Entities & Key Attributes

- **Vendor** (vendor_id PK, name, contact_email, phone, address)
- **SoftwareProduct** (product_id PK, vendor_id FK, name, category, description)
- **LicenseType** (license_type_id PK, product_id FK, name [e.g. Perpetual/Subscription/Concurrent/Named-User], seats_per_license, pricing_model)
- **Purchase** (purchase_id PK, vendor_id FK, product_id FK, license_type_id FK, quantity, unit_cost, total_cost, purchase_date, order_reference)
- **License** (license_id PK, purchase_id FK, license_key UNIQUE, quantity (seats in this license pool), start_date, end_date, status [Active/Expired/Revoked])
- **Subscription** (subscription_id PK, license_id FK, billing_cycle [Monthly/Annual], subscription_start, subscription_end, auto_renew BOOLEAN, cost_per_cycle)
- **Department** (department_id PK, name, cost_center_code)
- **AppUser** (user_id PK, name, email UNIQUE, department_id FK, role)
- **Device** (device_id PK, department_id FK, asset_tag UNIQUE, device_type, hostname)
- **Allocation** (allocation_id PK, license_id FK, user_id FK, device_id FK NULLABLE, department_id FK, allocated_date, expiry_date, status [Active/Reclaimed/Expired])
- **Renewal** (renewal_id PK, license_id FK or subscription_id FK, renewal_date, previous_end_date, new_end_date, renewal_cost, renewed_by)
- **ComplianceCheck** (check_id PK, license_id FK, check_date, check_type, result [Pass/Fail], details)

### 2.2 Key Relationships
- Vendor 1—N SoftwareProduct
- SoftwareProduct 1—N LicenseType
- Vendor/Product/LicenseType 1—N Purchase
- Purchase 1—N License (a purchase can be split into license batches; simplest: 1 purchase → 1 license pool, keep 1:1 or 1:N depending on your design choice — recommend 1 Purchase → 1 License for simplicity, N licenses only if batching needed)
- License 1—0/1 Subscription (only subscription-type licenses have a subscription row) OR License 1—N Subscription (for renewing billing cycles) — recommend 1—N so each billing cycle can be tracked, OR fold subscription behavior into Renewal and keep Subscription 1:1 with License. **Decision: License 1—0..1 Subscription** (subscription is subscription-specific metadata for that license).
- License 1—N Allocation
- Department 1—N AppUser, 1—N Device, 1—N Allocation
- AppUser 1—N Allocation
- Device 1—N Allocation (nullable if license is user-only, not device-bound)
- License 1—N Renewal
- License 1—N ComplianceCheck

### 2.3 ER Diagram
Deliverable: draw in draw.io / Lucidchart / MySQL Workbench / pgModeler. Suggested crow's-foot notation. (See `docs/er-diagram.png` — produce this separately as an image; I can generate a text/SVG version on request.)

---

## 3. Initial Relational Schema (Unnormalized → 1NF/2NF pass)

Start by listing raw tables mirroring entities above, note repeating groups (e.g. if a purchase naively stored multiple license keys in one column — split into License rows), and partial/transitive dependencies (e.g., vendor_name stored redundantly on Purchase — remove, rely on FK to Vendor). Document this analysis in `docs/normalization.md`:
- Show original flat "Purchase+License+Allocation" table, identify FDs, decompose.

---

## 4. Normalization to 3NF

### 4.1 Functional Dependencies (sample)
- `product_id → vendor_id` (redundant if vendor is derivable via product; keep FK on product only, don't duplicate vendor_id on Purchase)
- `license_id → purchase_id, license_key, start_date, end_date, status`
- `allocation_id → license_id, user_id, device_id, department_id, allocated_date, expiry_date`
- `user_id → department_id`  (so department_id should NOT be duplicated on Allocation if derivable — but keep it denormalized-with-justification OR derive via join; for reporting convenience many designs keep department_id on Allocation as it can differ from user's home department for cross-charging — document this decision explicitly as an intentional controlled redundancy, not a 3NF violation, since it's a valid FK relationship representing "allocated to this department" not transitively dependent solely on user)

### 4.2 Result
All tables in 3NF: every non-key attribute depends on the whole key, and only the key. Document each table's PK, FKs, and confirm no transitive dependencies remain. Put this as a table in `docs/data-dictionary.md`.

### 4.3 Data Dictionary
For each table: column name, data type, constraints, description. (Template provided in `docs/data-dictionary.md`.)

---

## 5. DDL Design — Tables & Constraints

File: `sql/01_schema.sql`

Key constraints to implement:
- `license.license_key` → `UNIQUE NOT NULL`
- `purchase.quantity`, `license.quantity` → `CHECK (quantity > 0)`
- Allocation within purchased quantity → enforce via **trigger** (COUNT(active allocations for license) <= license.quantity) since plain CHECK can't aggregate across rows
- Valid allocation period → `CHECK (expiry_date > allocated_date)` and `CHECK (allocated_date >= license.start_date)` (trigger, cross-table)
- No assignment of expired licenses → trigger: reject INSERT into allocation if `license.end_date < CURRENT_DATE` or `license.status = 'Expired'`
- Positive renewal cost → `CHECK (renewal_cost > 0)`
- `email` UNIQUE on AppUser; `asset_tag` UNIQUE on Device
- Sensible `DEFAULT`s: `status DEFAULT 'Active'`, `allocated_date DEFAULT CURRENT_DATE`, `auto_renew DEFAULT FALSE`
- `NOT NULL` on all required FKs and business-critical fields

### 5.1 Triggers (PostgreSQL example)
```sql
CREATE OR REPLACE FUNCTION check_allocation_rules() RETURNS TRIGGER AS $$
DECLARE
  lic RECORD;
  active_count INT;
BEGIN
  SELECT * INTO lic FROM license WHERE license_id = NEW.license_id;

  IF lic.status = 'Expired' OR lic.end_date < CURRENT_DATE THEN
    RAISE EXCEPTION 'Cannot allocate an expired license (license_id=%)', NEW.license_id;
  END IF;

  IF NEW.allocated_date < lic.start_date OR NEW.expiry_date > lic.end_date THEN
    RAISE EXCEPTION 'Allocation period outside license validity window';
  END IF;

  SELECT COUNT(*) INTO active_count FROM allocation
    WHERE license_id = NEW.license_id AND status = 'Active';
  IF active_count >= lic.quantity THEN
    RAISE EXCEPTION 'Allocation exceeds purchased quantity for license_id=%', NEW.license_id;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_allocation
BEFORE INSERT ON allocation
FOR EACH ROW EXECUTE FUNCTION check_allocation_rules();
```

### 5.2 Indexes
File: `sql/02_indexes.sql`
- `idx_license_enddate ON license(end_date)` — expiry queries
- `idx_allocation_license ON allocation(license_id)`
- `idx_allocation_user ON allocation(user_id)`
- `idx_purchase_vendor ON purchase(vendor_id)`
- `idx_product_vendor ON software_product(vendor_id)`
- Unique indexes auto-created by UNIQUE constraints (license_key, email, asset_tag)

---

## 6. Sample Data

File: `sql/03_seed_data.sql`
- 5–8 vendors (Microsoft, Adobe, JetBrains, Atlassian, Slack, Zoom, AWS, Oracle)
- 10–15 software products across vendors
- License types per product (Perpetual, Subscription-Annual, Subscription-Monthly, Concurrent)
- 5–6 departments (Engineering, Sales, HR, Finance, IT, Marketing)
- 30–50 users distributed across departments
- 20–30 devices
- 15–25 purchases with varying dates (include some near-expiry and some expired for testing)
- Licenses tied to purchases (include a few deliberately expired, one deliberately at full utilization)
- 40–60 allocations (mix active/reclaimed/expired)
- Renewal history rows
- A few compliance check log entries

---

## 7. SQL Query Library

File: `sql/04_queries.sql` — organize by category:

1. **Basic retrieval / filters**: all active licenses, licenses expiring in 30 days
2. **Joins**: license + product + vendor + department for a full allocation view
3. **Aggregates**: total spend per vendor, seat utilization % per license (`allocated/quantity`), renewal cost by year
4. **Nested/subqueries**: departments exceeding X% utilization; licenses with zero allocations (unused, cost-waste); users with more allocations than average
5. **Views** (file `sql/05_views.sql`):
   - `vw_license_expiry` — licenses expiring in next 30/60/90 days
   - `vw_utilization` — per license: purchased qty, allocated qty, % utilized
   - `vw_compliance_gaps` — over-allocated or expired-but-active-allocation cases
   - `vw_renewal_cost_summary` — renewal cost by product/year
   - `vw_department_allocation` — cost & seat count per department
   - `vw_vendor_portfolio` — products, total licenses, total spend per vendor

---

## 8. Transactions

Wrap multi-step operations in explicit transactions in the app layer:
- **Purchase recording**: insert Purchase → insert License row(s) → commit/rollback together
- **Renewal**: update license.end_date + insert Renewal row atomically
- **Reclaim**: update allocation.status='Reclaimed' — simple but still wrap for consistency
Use `BEGIN; ... COMMIT;` / `ROLLBACK` on exception in Python (`psycopg2`/`SQLAlchemy` handles this via `with conn.begin():`).

---

## 9. Front-End Application (Python)

**Recommended:** Streamlit (fast to build, good for a DB CRUD demo) or Tkinter (classic desktop CRUD if instructor expects a GUI app) — pick Streamlit unless your course specifically wants a desktop GUI.

### 9.1 Structure
```
app/
  db.py          # connection pooling, config from .env
  models.py      # optional: dataclasses / SQLAlchemy models
  services/
    purchases.py     # record_purchase()
    allocations.py    # allocate_license(), reclaim_license()
    renewals.py       # renew_license()
    compliance.py      # run_compliance_check()
    reports.py         # wraps the SQL views
  main.py         # Streamlit entrypoint with pages/tabs
  validators.py   # input validation helpers
```

### 9.2 Screens / Pages
1. Dashboard — KPI cards (total licenses, expiring soon, compliance issues, total spend)
2. Purchases — form to record a purchase; list/search existing purchases
3. Licenses — list with filters (status, product, vendor); expiry monitor
4. Allocations — allocate seat (dropdowns: license, user, device), reclaim button per row
5. Renewals — renew form (pulls current license, computes new end date), history table
6. Compliance — run check button, shows violations table
7. Reports — tabs for each of the 6 report views, with export-to-CSV

### 9.3 Validation & Error Handling
- App-level: required fields, positive numbers, date ranges, dropdown-only FKs (no free text for FK fields)
- Catch DB exceptions (trigger RAISE EXCEPTION messages) and surface as friendly UI error messages
- Confirm destructive actions (reclaim) with a confirmation dialog

---

## 10. Testing Plan

File: `docs/test-plan.md`
- **Constraint tests**: attempt duplicate license_key → expect failure; attempt negative quantity → expect failure
- **Business rule tests**: allocate beyond quantity → expect trigger exception; allocate against expired license → expect exception; allocate with expiry_date before allocated_date → expect exception
- **Functional tests**: full workflow purchase → license → allocate → renew → reclaim
- **Report correctness**: manually compute utilization % for one license and compare to view output
- **App tests**: form validation rejects bad input; error messages surface correctly

---

## 11. Suggested Build Order / Milestones

1. **Week 1:** Requirements doc, ER diagram, initial schema sketch (Sections 1–2)
2. **Week 2:** Normalization + data dictionary; finalize DDL with constraints/triggers/indexes (Sections 3–5)
3. **Week 3:** Seed data + query library + views (Sections 6–7); start transactions design (Section 8)
4. **Week 4:** Build Python app CRUD screens + reports (Section 9)
5. **Week 5:** Testing, polish, final demo prep, report writeup (Sections 10, deliverables packaging)

---

## 12. Deliverables Checklist Mapping
- [ ] Problem/scope/objectives/roles/FRs → `docs/requirements.md`
- [ ] ER diagram → `docs/er-diagram.png` (+ description)
- [ ] Initial schema → `docs/initial-schema.md`
- [ ] 3NF design + FDs + data dictionary → `docs/normalization.md`, `docs/data-dictionary.md`
- [ ] DDL with constraints → `sql/01_schema.sql`, `sql/02_indexes.sql`
- [ ] Sample data + queries + views → `sql/03_seed_data.sql`, `sql/04_queries.sql`, `sql/05_views.sql`
- [ ] Prototype demo → running Postgres + populated DB
- [ ] Python app → `app/` folder
- [ ] Final demo: CRUD, search, validation, reports, error handling — walk through each app screen live
