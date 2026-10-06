# SUB MAG: Software License & Subscription Management System

A database-driven system that keeps track of every software license and subscription an organization owns: who bought it, who uses it, when it expires and what it costs. It stops licenses from being over-allocated or used after they expire.

Built for **Database Management Systems (Semester 3), Project 40**.

![Demo](Presentation/demo/demo.gif)

▶ [Watch the full demo video (MP4)](Presentation/demo/demo.mp4)

## The problem

When licenses live in spreadsheets, they expire unnoticed, seats get handed out beyond what was bought, and nobody knows what the company really spends. SUB MAG puts everything in one normalized database and enforces the rules **inside the database**, so the data stays correct no matter what.

## What it does

- Record purchases and issue license keys
- Allocate seats to users and devices, and reclaim them
- Monitor expiring and expired licenses
- Renew licenses and log renewal costs
- Run compliance checks (over-allocated, expired-but-in-use, unused)
- Analyse cost by vendor, department and idle seats
- Six reports with CSV download
- Role-based access: Admin, License manager, Compliance, Manager, Employee

## Rules enforced by the database

| Rule | How |
|---|---|
| License keys are unique | `UNIQUE` constraint |
| Allocation never exceeds purchased quantity | Trigger |
| Allocation period must be valid | `CHECK` + trigger |
| Expired or revoked licenses cannot be assigned | Trigger |
| Renewal cost must be positive | `CHECK` constraint |

## Screenshots

| | |
|---|---|
| ![Dashboard](Report/images/09_dashboard.jpg) | ![Rule error](Report/images/14_allocate_rule_error.jpg) |
| Dashboard | A business rule stopping an over-allocation |
| ![Home](Report/images/06_home_cards_admin.jpg) | ![ER diagram](Report/images/er_diagram.png) |
| Role-based Home page | ER diagram |

## Tech stack

MySQL 8.0 (tables, constraints, triggers, views, stored procedures) · Python 3 · Streamlit · Three.js (animated intro)

## Run it

1. Load the database scripts into MySQL, from `Presentation/sql`, in this order: `01_schema.sql`, `02_indexes.sql`, `03_seed_data.sql`, `05_views.sql`, `06_procedures.sql`

   ```bash
   mysql -u root -p < 01_schema.sql
   ```

2. Set up the app, from `Presentation/app`:

   ```bash
   cp .env.example .env
   ```

   Open `.env` and put your MySQL password in it, then:

   ```bash
   pip install -r requirements.txt
   ```

   ```bash
   streamlit run main.py
   ```

3. Open http://localhost:8501. Scroll through the intro, then pick a user from **Signed in as** in the sidebar.

## Repository

```text
├── Report/          project report (Word + Markdown), images, README
└── Presentation/
    ├── app/         Streamlit application
    ├── sql/         schema, indexes, sample data, queries, views, procedures
    ├── docs/        requirements, ER diagram, normalization, data dictionary
    └── demo/        demo video (MP4) and GIF
```

## Team

| Name | Roll number |
|---|---|
| Shreyash Singh | 25WU0101130 |
| Shivam Singh | 25WU0101129 |
| Sambhaji Dungahu | 25WU0101120 |
| Rama Sudeshna | 25WU0101104 |

Faculty: Dr. Kiran Mayee Adavala
