# SUB MAG: Project Report

**Project 40: Design and Implementation of a Database Management System for Software License and Subscription Management System**

Course: Database Management Systems (DBMS), Semester 3 · Academic year 2026–27
Faculty: [Faculty Name]

| Name | Roll number |
|---|---|
| Shreyash Singh | [Roll number] |
| [Member 2 name] | [Roll number] |
| [Member 3 name] | [Roll number] |

## What is in this folder

| File / folder | Content |
|---|---|
| `PROJECT_REPORT.docx` | The full project report (Word) |
| `PROJECT_REPORT.md` | The same report in Markdown (source) |
| `images/` | ER diagram and application screenshots used in the report |

The report follows the required structure: cover page, abstract, introduction and problem statement, objectives and scope, software and hardware requirements, ER diagram, relational schema and normalization, data dictionary, SQL commands, queries with outputs, UI design and screenshots, implementation details, testing, conclusion and future enhancements, references, contribution of each member, and appendix.

## About the project

SUB MAG is a software license and subscription management system. It centralizes vendors, products, license types, purchases, licenses, subscriptions, departments, users, devices, allocations, renewals and compliance checks in a normalized (3NF) MySQL database. The key business rules (unique license keys, allocation within purchased quantity, valid allocation period, no assignment of expired licenses, positive renewal values) are enforced inside the database. A Python and Streamlit web application provides purchase recording, allocation, reclaim, expiry monitoring, renewal, compliance checking, cost analysis and reporting.

## Where the code is

The complete codebase (application, SQL scripts and design documents) is in the [`Presentation`](../Presentation) folder of this repository:

| Path | Content |
|---|---|
| `Presentation/app/` | Streamlit application |
| `Presentation/sql/` | Schema, indexes, sample data, queries, views and procedures |
| `Presentation/docs/` | Requirements, ER diagram, normalization and data dictionary |

To run the system, load the SQL scripts in the order given in the report (Section 12.5), create `Presentation/app/.env` from `.env.example`, then run `streamlit run main.py` from `Presentation/app`.

## Converting the Markdown report to Word

From this folder (so the image paths resolve):

```bash
pandoc PROJECT_REPORT.md -o PROJECT_REPORT.docx --toc --toc-depth=2
```
