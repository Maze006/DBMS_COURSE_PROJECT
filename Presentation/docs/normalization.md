# Normalization to 3NF

Input: the first-pass table set in `initial-schema.md`. Output: the final 12-table design
(unchanged table count; several columns removed or re-pointed).

## 1. Normal-form rules applied

- **1NF** – atomic values, no repeating groups, every table has a primary key.
- **2NF** – 1NF + no non-key attribute depends on only part of a composite key.
- **3NF** – 2NF + no non-key attribute depends on another non-key attribute (no transitive dependency).

All tables use a single-column surrogate primary key, so partial dependencies cannot occur:
**2NF holds automatically**. The real work is the 3NF (transitive dependency) check below.

## 2. Functional dependencies per table

Notation: `A → B` means A determines B. Only the PK-level dependencies are listed unless
a non-key dependency is called out.

| Table | Functional dependencies |
|---|---|
| vendor | vendor_id → name, contact_email, phone, address |
| software_product | product_id → vendor_id, name, category, description |
| license_type | license_type_id → product_id, name, seats_per_license, pricing_model |
| purchase | purchase_id → license_type_id, quantity, unit_cost, purchase_date, order_reference |
| license | license_id → purchase_id, license_key, quantity, start_date, end_date, status; also license_key → license_id (candidate key) |
| subscription | subscription_id → license_id, billing_cycle, auto_renew, cost_per_cycle; license_id → subscription_id (1:0..1) |
| department | department_id → name, cost_center_code; cost_center_code → department_id (candidate key) |
| app_user | user_id → name, email, department_id, role; email → user_id (candidate key) |
| device | device_id → department_id, asset_tag, device_type, hostname; asset_tag → device_id (candidate key) |
| allocation | allocation_id → license_id, user_id, device_id, department_id, allocated_date, expiry_date, status |
| renewal | renewal_id → license_id, renewal_date, previous_end_date, new_end_date, renewal_cost, renewed_by |
| compliance_check | check_id → license_id, check_date, check_type, result, details |

Every determinant above is a key (primary or candidate), which is exactly the BCNF condition,
so the final design is in **BCNF**, which is stronger than 3NF.

## 3. Violations found in the first draft and how they were fixed

| # | Problem in first draft | Dependency | Normal form broken | Fix |
|---|---|---|---|---|
| 1 | `purchase.vendor_id` stored alongside `product_id` | license_type_id → product_id → vendor_id, so vendor_id depends on purchase only transitively | 3NF | Removed `vendor_id` from purchase. Vendor is reached via license_type → software_product → vendor |
| 2 | `purchase.product_id` stored alongside `license_type_id` | license_type_id → product_id (license_type already holds product_id) | 3NF | Removed `product_id` from purchase |
| 3 | `purchase.total_cost` | total_cost = quantity × unit_cost (derived from non-key attributes) | 3NF | Removed. Computed in queries and views |
| 4 | `subscription.subscription_start` / `subscription_end` duplicate `license.start_date` / `end_date` for the same license | license_id → start/end (via license) | 3NF (redundant, update-anomaly prone) | Removed from subscription; the license validity window is the single source of truth |
| 5 | `renewal.renewed_by` as free text (name) | name depends on a user, not on the renewal | 3NF | Replaced with `renewed_by` FK → app_user.user_id |
| 6 | Vendor/department names copied onto child tables | child_id → parent_id → parent_name | 3NF | Child tables keep only the FK |
| 7 | Repeating `license_key_1..n`, `allocated_user_1..n`, `renewal_1..n` | — | 1NF | Own tables: license, allocation, renewal |

## 4. Deliberate design decisions (not violations)

**allocation.department_id vs app_user.department_id.**
It looks like `allocation.user_id → app_user.department_id` makes `allocation.department_id`
transitive. It is not, because the two attributes mean different things:
`app_user.department_id` is the user's *home* department, while `allocation.department_id` is the
department *charged* for the seat (cost center), which can differ (shared tools, cross-charging,
a user on loan). Since `user_id` does not determine the charged department, no dependency exists
and the column is legitimately part of the allocation fact. The same reasoning holds for
`device.department_id` (owning department).

**license.quantity.**
Seat capacity of a license. With one purchase producing one license, it equals
`purchase.quantity × license_type.seats_per_license`. It is kept as a stored attribute (rather than
derived) because the allocation trigger needs a fast capacity check and because a license can later be
split or adjusted independently of the purchase. The dependency spans tables, so it is not a 3NF
violation within `license`. The trigger and the sample data keep the two consistent.

**license.status.**
`Active` / `Expired` / `Revoked`. `Expired` is derivable from `end_date`, but `Revoked` is not, and
the status is needed as an explicit lifecycle state. Views compute effective expiry from `end_date`,
and the allocation trigger checks both.

**Purchase → License is 1:1.**
Each purchase creates one license record (a pool of seats). Batching a purchase into several
licenses is a possible extension and would only require relaxing the unique FK.

## 5. Final table set (3NF/BCNF)

```
vendor(vendor_id PK, name, contact_email, phone, address)
software_product(product_id PK, vendor_id FK, name, category, description)
license_type(license_type_id PK, product_id FK, name, seats_per_license, pricing_model)
purchase(purchase_id PK, license_type_id FK, quantity, unit_cost, purchase_date, order_reference)
license(license_id PK, purchase_id FK UNIQUE, license_key UNIQUE, quantity, start_date, end_date, status)
subscription(subscription_id PK, license_id FK UNIQUE, billing_cycle, auto_renew, cost_per_cycle)
department(department_id PK, name, cost_center_code UNIQUE)
app_user(user_id PK, department_id FK, name, email UNIQUE, role)
device(device_id PK, department_id FK, asset_tag UNIQUE, device_type, hostname)
allocation(allocation_id PK, license_id FK, user_id FK, device_id FK NULL, department_id FK,
           allocated_date, expiry_date, status)
renewal(renewal_id PK, license_id FK, renewal_date, previous_end_date, new_end_date,
        renewal_cost, renewed_by FK)
compliance_check(check_id PK, license_id FK, check_date, check_type, result, details)
```

Vendor information for a purchase is obtained with
`purchase → license_type → software_product → vendor` (three joins). This is the price of
removing the redundancy, and the `vw_vendor_portfolio` and related views hide it from report users.
