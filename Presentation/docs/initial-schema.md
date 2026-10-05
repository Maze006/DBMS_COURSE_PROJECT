# Initial Relational Schema (Pre-Normalization Pass)

This is the first-pass table list derived directly from the ER model, before the 3NF
decomposition documented in `normalization.md`. It exists to show the anomalies a naive
design would have, and to justify the final table boundaries.

## 1. Naive flat design (what a first attempt often looks like)

A common first instinct is to fold related data into fewer, wider tables. Example —
a single `PURCHASE_RECORD` table:

```
PURCHASE_RECORD (
  purchase_id, purchase_date, quantity, unit_cost,
  vendor_id, vendor_name, vendor_email,                -- vendor fields repeated per purchase
  product_id, product_name, product_category,          -- product fields repeated per purchase
  license_type_id, license_type_name,
  license_key_1, license_key_2, license_key_3, ...      -- repeating group: unknown # of keys
  allocated_user_1, allocated_user_2, ...                -- repeating group: unknown # of allocations
)
```

Problems:
- **Repeating groups** (`license_key_1..n`, `allocated_user_1..n`) — violates 1NF; number of
  licenses/allocations per purchase is unbounded and unknown in advance.
- **Redundant vendor/product attributes** copied into every purchase row — update anomaly
  (renaming a vendor requires updating every purchase row) and insertion anomaly (can't
  record a vendor before a purchase exists).
- **Mixed grain**: the table mixes purchase-level facts, vendor-level facts, product-level
  facts, and allocation-level facts in one row — a classic sign the design needs decomposition.

## 2. First decomposition (1NF)

Split repeating groups into their own tables, one row per fact:

- `VENDOR(vendor_id, name, contact_email, phone, address)`
- `SOFTWARE_PRODUCT(product_id, vendor_id, name, category, description)`
- `LICENSE_TYPE(license_type_id, product_id, name, seats_per_license, pricing_model)`
- `PURCHASE(purchase_id, vendor_id, product_id, license_type_id, quantity, unit_cost, total_cost, purchase_date, order_reference)`
- `LICENSE(license_id, purchase_id, license_key, quantity, start_date, end_date, status)`
- `SUBSCRIPTION(subscription_id, license_id, billing_cycle, subscription_start, subscription_end, auto_renew, cost_per_cycle)`
- `DEPARTMENT(department_id, name, cost_center_code)`
- `APP_USER(user_id, name, email, department_id, role)`
- `DEVICE(device_id, department_id, asset_tag, device_type, hostname)`
- `ALLOCATION(allocation_id, license_id, user_id, device_id, department_id, allocated_date, expiry_date, status)`
- `RENEWAL(renewal_id, license_id, renewal_date, previous_end_date, new_end_date, renewal_cost, renewed_by)`
- `COMPLIANCE_CHECK(check_id, license_id, check_date, check_type, result, details)`

This removes repeating groups (each license key / allocation is now its own row) but still
needs a 2NF/3NF pass — e.g. at this stage some early drafts leave `vendor_name` sitting on
`PURCHASE` "for convenience," which is a transitive dependency through `product_id → vendor_id`
that must be removed. That check, table by table, is carried out in `normalization.md`.

## 3. Known repeating-group / redundancy risks to watch for in this domain

| Risk | Where it would appear naively | Resolution |
|---|---|---|
| Multiple license keys per purchase | `PURCHASE.license_key_1..n` | Own `LICENSE` table, FK to `PURCHASE` |
| Multiple allocations per license | `LICENSE.allocated_user_1..n` | Own `ALLOCATION` table, FK to `LICENSE` |
| Vendor name duplicated per product/purchase | `SOFTWARE_PRODUCT.vendor_name`, `PURCHASE.vendor_name` | Store only `vendor_id` FK, join to `VENDOR` for the name |
| Department name duplicated per user/device/allocation | `APP_USER.department_name` | Store only `department_id` FK |
| Renewal history flattened onto `LICENSE` (`renewal_1_date, renewal_2_date, ...`) | `LICENSE` table | Own `RENEWAL` table, FK to `LICENSE`, one row per renewal event |
| Compliance results flattened onto `LICENSE` (`last_check_result`) | `LICENSE` table | Own `COMPLIANCE_CHECK` table, one row per check event, preserves history |

## 4. Primary keys and relationships (as carried into the schema)

| Table | Primary Key | References (FK →) |
|---|---|---|
| VENDOR | vendor_id | — |
| SOFTWARE_PRODUCT | product_id | VENDOR |
| LICENSE_TYPE | license_type_id | SOFTWARE_PRODUCT |
| PURCHASE | purchase_id | VENDOR, SOFTWARE_PRODUCT, LICENSE_TYPE |
| LICENSE | license_id | PURCHASE |
| SUBSCRIPTION | subscription_id | LICENSE |
| DEPARTMENT | department_id | — |
| APP_USER | user_id | DEPARTMENT |
| DEVICE | device_id | DEPARTMENT |
| ALLOCATION | allocation_id | LICENSE, APP_USER, DEVICE (nullable), DEPARTMENT |
| RENEWAL | renewal_id | LICENSE |
| COMPLIANCE_CHECK | check_id | LICENSE |

Note: this is the *first-draft* list. The normalization pass found `PURCHASE` carrying redundant
`vendor_id`/`product_id`/`total_cost`, `SUBSCRIPTION` duplicating license dates, and `RENEWAL.renewed_by`
as free text; the corrected final tables are in `normalization.md` section 5.

This table list is the input to the normalization pass in `normalization.md`, which verifies
each table against 1NF/2NF/3NF and documents the functional dependencies formally.

See also: [er-diagram.svg](er-diagram.svg), [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
