"""Generic CRUD for the six master-data tables.

Table and column names come only from the MASTER spec below (never from user input),
so building identifiers into SQL is safe; all values are bound as parameters.
"""
import db
import validators as v
from services import lookups


def _f(name, label, kind="text", required=True, max_len=255, options=None):
    return {"name": name, "label": label, "kind": kind, "required": required,
            "max": max_len, "options": options}


ROLES = ["Employee", "Manager", "Admin", "LicenseManager", "Compliance"]
PRICING = ["Perpetual", "Subscription", "Concurrent", "Per-User"]

MASTER = {
    "Vendors": {
        "table": "vendor", "pk": "vendor_id",
        "list_sql": "SELECT vendor_id, name, contact_email, phone, address FROM vendor ORDER BY name",
        "fields": [_f("name", "Name", max_len=100), _f("contact_email", "Contact email", "email", max_len=150),
                   _f("phone", "Phone", required=False, max_len=30),
                   _f("address", "Address", required=False)],
    },
    "Products": {
        "table": "software_product", "pk": "product_id",
        "list_sql": """SELECT p.product_id, p.name, v.name AS vendor, p.category, p.description
                         FROM software_product p JOIN vendor v ON v.vendor_id = p.vendor_id
                        ORDER BY v.name, p.name""",
        "fields": [_f("vendor_id", "Vendor", "select", options=lookups.vendors),
                   _f("name", "Name", max_len=100), _f("category", "Category", max_len=50),
                   _f("description", "Description", required=False)],
    },
    "License types": {
        "table": "license_type", "pk": "license_type_id",
        "list_sql": """SELECT lt.license_type_id, p.name AS product, lt.name, lt.seats_per_license, lt.pricing_model
                         FROM license_type lt JOIN software_product p ON p.product_id = lt.product_id
                        ORDER BY p.name, lt.name""",
        "fields": [_f("product_id", "Product", "select", options=lookups.products),
                   _f("name", "Name", max_len=60), _f("seats_per_license", "Seats per license", "int"),
                   _f("pricing_model", "Pricing model", "choice", options=lambda: PRICING)],
    },
    "Departments": {
        "table": "department", "pk": "department_id",
        "list_sql": "SELECT department_id, name, cost_center_code FROM department ORDER BY name",
        "fields": [_f("name", "Name", max_len=80), _f("cost_center_code", "Cost center code", max_len=20)],
    },
    "Users": {
        "table": "app_user", "pk": "user_id",
        "list_sql": """SELECT u.user_id, u.name, u.email, d.name AS department, u.role
                         FROM app_user u JOIN department d ON d.department_id = u.department_id
                        ORDER BY u.name""",
        "fields": [_f("name", "Name", max_len=100), _f("email", "Email", "email", max_len=150),
                   _f("department_id", "Department", "select", options=lookups.departments),
                   _f("role", "Role", "choice", options=lambda: ROLES)],
    },
    "Devices": {
        "table": "device", "pk": "device_id",
        "list_sql": """SELECT dv.device_id, dv.asset_tag, dv.hostname, dv.device_type, d.name AS department
                         FROM device dv JOIN department d ON d.department_id = dv.department_id
                        ORDER BY dv.asset_tag""",
        "fields": [_f("asset_tag", "Asset tag", max_len=40), _f("device_type", "Device type", max_len=30),
                   _f("hostname", "Hostname", required=False, max_len=80),
                   _f("department_id", "Department", "select", options=lookups.departments)],
    },
}


def list_rows(entity, text=None):
    rows = db.query(MASTER[entity]["list_sql"])
    if text:
        t = text.lower()
        rows = [r for r in rows if any(t in str(x).lower() for x in r.values())]
    return rows


def get_row(entity, row_id):
    m = MASTER[entity]
    cols = ", ".join(f["name"] for f in m["fields"])
    return db.query_one(f"SELECT {cols} FROM {m['table']} WHERE {m['pk']} = %s", (row_id,))


def _prepare(entity, values):
    spec = MASTER[entity]["fields"]
    values = {k: (v.clean(x) if isinstance(x, str) else x) for k, x in values.items()}
    v.validate_fields(values, spec)
    return spec, values


def insert_row(entity, values):
    spec, values = _prepare(entity, values)
    m = MASTER[entity]
    cols = [f["name"] for f in spec]
    with db.transaction() as cur:
        cur.execute(f"INSERT INTO {m['table']} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                    [values.get(c) for c in cols])
        return cur.lastrowid


def update_row(entity, row_id, values):
    spec, values = _prepare(entity, values)
    m = MASTER[entity]
    sets = ", ".join(f"{f['name']} = %s" for f in spec)
    with db.transaction() as cur:
        cur.execute(f"UPDATE {m['table']} SET {sets} WHERE {m['pk']} = %s",
                    [values.get(f["name"]) for f in spec] + [row_id])


def delete_row(entity, row_id):
    m = MASTER[entity]
    with db.transaction() as cur:
        cur.execute(f"DELETE FROM {m['table']} WHERE {m['pk']} = %s", (row_id,))
        if cur.rowcount == 0:
            raise db.AppError("That record no longer exists.")
