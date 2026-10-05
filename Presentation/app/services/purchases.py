import uuid

import db
import validators as v


def generate_key():
    h = uuid.uuid4().hex.upper()
    return "LIC-" + "-".join(h[i:i + 4] for i in range(0, 16, 4))


def record_purchase(license_type_id, quantity, unit_cost, purchase_date, order_reference,
                    license_key, start_date, end_date, billing_cycle=None, auto_renew=False,
                    cost_per_cycle=None):
    """Create purchase + license (+ subscription) atomically. Returns ids."""
    order_reference = v.clean(order_reference)
    license_key = v.clean(license_key)
    billing_cycle = v.clean(billing_cycle)
    v.validate_purchase(license_type_id, quantity, unit_cost, purchase_date, order_reference,
                        license_key, start_date, end_date, billing_cycle, cost_per_cycle)

    with db.transaction() as cur:
        cur.execute("SELECT seats_per_license FROM license_type WHERE license_type_id = %s",
                    (license_type_id,))
        lt = cur.fetchone()
        if not lt:
            raise db.AppError("That license type no longer exists.")

        cur.execute("""INSERT INTO purchase (license_type_id, quantity, unit_cost, purchase_date, order_reference)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (license_type_id, quantity, unit_cost, purchase_date, order_reference))
        purchase_id = cur.lastrowid

        key = license_key or generate_key()
        cur.execute("""INSERT INTO license (purchase_id, license_key, quantity, start_date, end_date)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (purchase_id, key, quantity * lt["seats_per_license"], start_date, end_date))
        license_id = cur.lastrowid

        if billing_cycle:
            cur.execute("""INSERT INTO subscription (license_id, billing_cycle, auto_renew, cost_per_cycle)
                           VALUES (%s, %s, %s, %s)""",
                        (license_id, billing_cycle, bool(auto_renew), cost_per_cycle))
    return {"purchase_id": purchase_id, "license_id": license_id, "license_key": key,
            "seats": quantity * lt["seats_per_license"]}


def list_purchases(search=None, vendor_id=None):
    sql = """SELECT pu.purchase_id, pu.order_reference, v.name AS vendor, p.name AS product,
                    lt.name AS license_type, pu.quantity, pu.unit_cost,
                    pu.quantity * pu.unit_cost AS total_cost, pu.purchase_date,
                    l.license_id, l.license_key
               FROM purchase pu
               JOIN license_type lt ON lt.license_type_id = pu.license_type_id
               JOIN software_product p ON p.product_id = lt.product_id
               JOIN vendor v ON v.vendor_id = p.vendor_id
               LEFT JOIN license l ON l.purchase_id = pu.purchase_id
              WHERE 1 = 1"""
    params = []
    if search:
        like = f"%{search}%"
        sql += " AND (p.name LIKE %s OR v.name LIKE %s OR pu.order_reference LIKE %s OR l.license_key LIKE %s)"
        params += [like] * 4
    if vendor_id:
        sql += " AND v.vendor_id = %s"
        params.append(vendor_id)
    return db.query(sql + " ORDER BY pu.purchase_date DESC, pu.purchase_id DESC", params)
