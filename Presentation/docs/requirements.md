# Requirements — Software License & Subscription Management System

## 1. Problem Identification
Organizations buy many licensed products and subscriptions and use them across departments.
Without centralized control:
- licenses and subscriptions expire unnoticed;
- seats are over-allocated beyond what was purchased (audit and legal risk);
- expired licenses stay assigned to users and devices;
- renewal costs and department spend are not visible;
- paid seats sit unused while other teams run short.

A relational database with enforced business rules, plus a small application on top of it, gives one
source of truth for what was bought, what is assigned, what is expiring and what it costs.

## 2. Scope
**In scope**
- Master data: vendors, software products, license types, departments, users, devices.
- Transactions: purchases, licenses (keys and seat pools), subscriptions, allocations, renewals,
  compliance checks.
- Reports: license expiry, utilization, compliance gaps, renewal cost, department allocation,
  vendor portfolio.
- A Python front end for purchase recording, allocation, expiry monitoring, renewal, reclaim,
  compliance checking, cost analysis and reporting.

**Out of scope**
- Automated software installation or deployment, or detection of installed software on devices.
- Payment processing and invoicing integration.
- Enterprise single sign-on (the app uses a simple role selection or login).

## 3. Objectives
1. Model the domain as an ER design and normalize it to 3NF.
2. Enforce the business rules inside the database, not only in the application.
3. Provide realistic sample data and a query set covering joins, aggregates, subqueries and views.
4. Provide an application that demonstrates CRUD, search, validation, reports and error handling.
5. Demonstrate transaction awareness, indexing and systematic testing.

## 4. Users and Roles
| Role | Needs |
|---|---|
| Administrator | Maintain vendors, products, license types, departments, users, devices |
| License Manager | Record purchases, allocate and reclaim licenses, process renewals, monitor expiry |
| Compliance Officer | Run compliance checks, review gaps and utilization, produce reports |
| Finance / Department Head (read-only) | View renewal cost, department allocation and vendor portfolio reports |

## 5. Functional Requirements
| ID | Requirement |
|---|---|
| FR1 | Maintain CRUD for vendors, software products, license types, departments, users and devices |
| FR2 | Record a purchase (license type, quantity, unit cost, date, order reference) and create the corresponding license with a unique key and validity window |
| FR3 | Optionally attach subscription billing details (cycle, auto-renew, cost per cycle) to a license |
| FR4 | Allocate a license seat to a user, optionally on a device, charged to a department, for a valid period |
| FR5 | Reject allocation when the license is expired or revoked, fully utilized, or the period falls outside the license validity |
| FR6 | Reclaim an allocation, freeing the seat for reuse and keeping the history |
| FR7 | Renew a license: extend its end date and record the renewal with a positive cost |
| FR8 | Expiry monitoring: list licenses expiring within 30, 60 or 90 days, and already expired ones |
| FR9 | Compliance checking: detect over-allocation, expired licenses still in use and unused paid seats; store each check result |
| FR10 | Cost analysis: spend per vendor, per department and per product; renewal cost per period |
| FR11 | Reports: license expiry, utilization, compliance gaps, renewal cost, department allocation, vendor portfolio, with CSV export |
| FR12 | Search and filter licenses, allocations, users and products |
| FR13 | Validate all input and show clear messages for rule violations |

## 6. Business Rules
| ID | Rule | Enforced by |
|---|---|---|
| BR1 | License keys are unique | UNIQUE constraint |
| BR2 | Active allocations of a license never exceed its purchased quantity | Trigger |
| BR3 | An allocation has a valid period (end after start, inside the license window) | CHECK + trigger |
| BR4 | Expired or revoked licenses cannot be assigned | Trigger |
| BR5 | Renewal cost is positive | CHECK |
| BR6 | A user holds at most one active seat per license | Partial unique index |

## 7. Non-Functional Requirements
- **Integrity:** PK, FK, UNIQUE, NOT NULL, CHECK and DEFAULT constraints on all tables.
- **Transactions:** multi-step operations (purchase + license, renewal + end-date update) are atomic.
- **Performance:** indexes on frequently searched attributes (expiry date, status, foreign keys).
- **Usability:** form validation, confirmation before reclaim, readable error messages.
- **Testability:** every business rule has at least one passing and one failing test case.

## 8. Assumptions
- One purchase creates one license (a seat pool); batching is a future extension.
- Perpetual licenses use a far-future end date.
- A license seat is held by one user (optionally on one device) at a time.
- Currency is a single unit; no exchange rates.

## 9. Deliverable Traceability
| Brief deliverable | Document / artifact |
|---|---|
| Problem, scope, objectives, users, FRs | this file |
| ER diagram | `er-diagram.svg` |
| Initial relational schema | `initial-schema.md` |
| 3NF design, FDs, data dictionary | `normalization.md`, `data-dictionary.md` |
| DDL with constraints | `sql/01_schema.sql` (next) |
| Sample data, queries, views | `sql/03_seed_data.sql`, `sql/04_queries.sql`, `sql/05_views.sql` |
| Application | `app/` |
| Testing | `docs/test-plan.md` |
