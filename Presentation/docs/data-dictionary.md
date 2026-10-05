# Data Dictionary

Target DBMS: MySQL 8.0.16+ (InnoDB). Types: `INT AUTO_INCREMENT` keys, `VARCHAR(n)`, `DECIMAL(12,2)` money, `DATE`.
(`SERIAL` in the tables below means `INT AUTO_INCREMENT`; `NUMERIC` means `DECIMAL`.)
The one-active-seat rule is a UNIQUE index on `(license_id, active_user_key)` where `active_user_key` is a
stored generated column (`user_id` while status is Active, otherwise NULL), because MySQL has no partial indexes.
PK = primary key, FK = foreign key, UQ = unique, NN = NOT NULL.
Enforcement column: **C** = declarative constraint, **T** = trigger (cross-row / cross-table rule).

## vendor
Company that sells software.
| Column | Type | Constraints | Description |
|---|---|---|---|
| vendor_id | SERIAL | PK | Surrogate key |
| name | VARCHAR(100) | NN, UQ | Vendor name |
| contact_email | VARCHAR(150) | NN, CHECK contains '@' | Sales/support contact |
| phone | VARCHAR(30) | | Contact phone |
| address | VARCHAR(255) | | Postal address |

## software_product
| Column | Type | Constraints | Description |
|---|---|---|---|
| product_id | SERIAL | PK | |
| vendor_id | INT | NN, FK → vendor | Owning vendor |
| name | VARCHAR(100) | NN | Product name |
| category | VARCHAR(50) | NN | e.g. Productivity, Design, DevTools |
| description | VARCHAR(255) | | |
| | | UQ (vendor_id, name) | A vendor cannot list the same product twice |

## license_type
| Column | Type | Constraints | Description |
|---|---|---|---|
| license_type_id | SERIAL | PK | |
| product_id | INT | NN, FK → software_product | |
| name | VARCHAR(50) | NN | e.g. Perpetual, Annual Subscription, Concurrent, Named User |
| seats_per_license | INT | NN, DEFAULT 1, CHECK > 0 | Seats granted by one purchased unit |
| pricing_model | VARCHAR(20) | NN, CHECK IN ('Perpetual','Subscription','Concurrent','Per-User') | |
| | | UQ (product_id, name) | |

## purchase
A purchase order line for a quantity of one license type.
| Column | Type | Constraints | Description |
|---|---|---|---|
| purchase_id | SERIAL | PK | |
| license_type_id | INT | NN, FK → license_type | Vendor and product derived through this FK |
| quantity | INT | NN, CHECK > 0 | Units purchased |
| unit_cost | NUMERIC(12,2) | NN, CHECK >= 0 | Cost per unit |
| purchase_date | DATE | NN, DEFAULT CURRENT_DATE | |
| order_reference | VARCHAR(50) | UQ | PO/invoice number |

## license
The purchased pool of seats and its validity window.
| Column | Type | Constraints | Description |
|---|---|---|---|
| license_id | SERIAL | PK | |
| purchase_id | INT | NN, UQ, FK → purchase | 1:1 with purchase |
| license_key | VARCHAR(100) | NN, **UQ** | Unique license key (business rule) |
| quantity | INT | NN, CHECK > 0 | Seat capacity |
| start_date | DATE | NN | Validity start |
| end_date | DATE | NN, CHECK end_date > start_date | Validity end (perpetual licenses use a far-future date) |
| status | VARCHAR(10) | NN, DEFAULT 'Active', CHECK IN ('Active','Expired','Revoked') | Lifecycle state |

## subscription
Billing details for subscription-type licenses only.
| Column | Type | Constraints | Description |
|---|---|---|---|
| subscription_id | SERIAL | PK | |
| license_id | INT | NN, UQ, FK → license | 1:0..1 with license |
| billing_cycle | VARCHAR(10) | NN, CHECK IN ('Monthly','Quarterly','Annual') | |
| auto_renew | BOOLEAN | NN, DEFAULT FALSE | |
| cost_per_cycle | NUMERIC(12,2) | NN, CHECK > 0 | Amount charged each cycle |

## department
| Column | Type | Constraints | Description |
|---|---|---|---|
| department_id | SERIAL | PK | |
| name | VARCHAR(80) | NN, UQ | |
| cost_center_code | VARCHAR(20) | NN, UQ | Finance cost center |

## app_user
(Named `app_user` because `user` is reserved in PostgreSQL.)
| Column | Type | Constraints | Description |
|---|---|---|---|
| user_id | SERIAL | PK | |
| department_id | INT | NN, FK → department | Home department |
| name | VARCHAR(100) | NN | |
| email | VARCHAR(150) | NN, UQ | |
| role | VARCHAR(20) | NN, DEFAULT 'Employee', CHECK IN ('Employee','Manager','Admin','LicenseManager','Compliance') | Also drives app permissions |

## device
| Column | Type | Constraints | Description |
|---|---|---|---|
| device_id | SERIAL | PK | |
| department_id | INT | NN, FK → department | Owning department |
| asset_tag | VARCHAR(40) | NN, UQ | Inventory tag |
| device_type | VARCHAR(30) | NN | Laptop, Desktop, Server, VM |
| hostname | VARCHAR(80) | | |

## allocation
Assignment of one seat of a license to a user (optionally on a device).
| Column | Type | Constraints | Enforcement |
|---|---|---|---|
| allocation_id | SERIAL | PK | C |
| license_id | INT | NN, FK → license | C |
| user_id | INT | NN, FK → app_user | C |
| device_id | INT | FK → device (NULL for user-only licenses) | C |
| department_id | INT | NN, FK → department (department charged) | C |
| allocated_date | DATE | NN, DEFAULT CURRENT_DATE | C |
| expiry_date | DATE | NN | C |
| status | VARCHAR(10) | NN, DEFAULT 'Active', CHECK IN ('Active','Reclaimed','Expired') | C |
| | | CHECK (expiry_date > allocated_date) | C — valid allocation period |
| | | Active allocations of a license ≤ license.quantity | T — allocation within purchased quantity |
| | | License not Expired/Revoked and end_date ≥ today | T — no assignment of expired licenses |
| | | allocated_date ≥ license.start_date and expiry_date ≤ license.end_date | T — period inside license window |
| | | Partial UQ (license_id, user_id) WHERE status='Active' | C — one active seat per user per license |

## renewal
| Column | Type | Constraints | Description |
|---|---|---|---|
| renewal_id | SERIAL | PK | |
| license_id | INT | NN, FK → license | |
| renewal_date | DATE | NN, DEFAULT CURRENT_DATE | |
| previous_end_date | DATE | NN | End date before renewal |
| new_end_date | DATE | NN, CHECK new_end_date > previous_end_date | End date after renewal |
| renewal_cost | NUMERIC(12,2) | NN, **CHECK renewal_cost > 0** | Positive renewal value (business rule) |
| renewed_by | INT | FK → app_user | Who processed it |

## compliance_check
| Column | Type | Constraints | Description |
|---|---|---|---|
| check_id | SERIAL | PK | |
| license_id | INT | NN, FK → license | |
| check_date | DATE | NN, DEFAULT CURRENT_DATE | |
| check_type | VARCHAR(30) | NN, CHECK IN ('Over-allocation','Expired-in-use','Unused','Key-audit') | |
| result | VARCHAR(4) | NN, CHECK IN ('Pass','Fail') | |
| details | VARCHAR(255) | | Human-readable finding |

## Business rules to constraint mapping

| Business rule | Mechanism |
|---|---|
| Unique license keys | `license.license_key` UNIQUE NOT NULL |
| Allocation within purchased quantity | Trigger on `allocation` (count of Active rows vs `license.quantity`) |
| Valid allocation period | CHECK `expiry_date > allocated_date` plus trigger for license-window containment |
| No assignment of expired licenses | Trigger on `allocation` (license status and end_date) |
| Positive renewal values | CHECK `renewal_cost > 0` |

## Indexes planned (beyond PK/UQ indexes)

`license(end_date)`, `license(status)`, `allocation(license_id, status)`, `allocation(user_id)`,
`allocation(department_id)`, `software_product(vendor_id)`, `license_type(product_id)`,
`purchase(license_type_id)`, `purchase(purchase_date)`, `renewal(license_id)`,
`compliance_check(license_id, check_date)`, `app_user(department_id)`.
