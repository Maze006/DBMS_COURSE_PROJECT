"""Option lists for dropdowns."""
from db import query


def _pairs(sql, params=None):
    return [(r["id"], r["label"]) for r in query(sql, params)]


def vendors():
    return _pairs("SELECT vendor_id AS id, name AS label FROM vendor ORDER BY name")


def products():
    return _pairs("""SELECT p.product_id AS id, CONCAT(p.name, ' (', v.name, ')') AS label
                       FROM software_product p JOIN vendor v ON v.vendor_id = p.vendor_id
                      ORDER BY p.name""")


def license_types():
    return query("""SELECT lt.license_type_id AS id,
                           CONCAT(p.name, ' - ', lt.name, ' (', v.name, ')') AS label,
                           lt.seats_per_license, lt.pricing_model
                      FROM license_type lt
                      JOIN software_product p ON p.product_id = lt.product_id
                      JOIN vendor v ON v.vendor_id = p.vendor_id
                     ORDER BY p.name, lt.name""")


def departments():
    return _pairs("SELECT department_id AS id, name AS label FROM department ORDER BY name")


def users():
    return query("""SELECT u.user_id AS id, CONCAT(u.name, ' (', d.name, ')') AS label,
                           u.name, u.role, u.department_id
                      FROM app_user u JOIN department d ON d.department_id = u.department_id
                     ORDER BY u.name""")


def devices():
    return _pairs("""SELECT device_id AS id, CONCAT(hostname, ' [', asset_tag, ']') AS label
                       FROM device ORDER BY hostname""")


def licenses(only_valid=False, include_revoked=True):
    where = []
    if only_valid:
        where.append("status = 'Active' AND end_date >= CURDATE()")
    if not include_revoked:
        where.append("status <> 'Revoked'")
    clause = ("WHERE " + " AND ".join(where)) if where else ""
    return query(f"""SELECT license_id AS id,
                            CONCAT('#', license_id, ' ', product, ' - ', license_key,
                                   ' (', seats_available, ' free, ends ', end_date, ')') AS label,
                            end_date, start_date, status, seats_available, capacity
                       FROM vw_license_utilization {clause}
                      ORDER BY product, license_id""")
