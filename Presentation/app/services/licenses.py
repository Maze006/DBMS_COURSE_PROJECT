import db
import validators as v


def search_licenses(text=None, vendor_id=None, status=None, expiring_within=None):
    sql = """SELECT license_id, license_key, vendor, product, license_type, status,
                    start_date, end_date, capacity, active_allocated, seats_available,
                    utilization_pct, DATEDIFF(end_date, CURDATE()) AS days_remaining
               FROM vw_license_utilization WHERE 1 = 1"""
    params = []
    if text:
        like = f"%{text}%"
        sql += " AND (license_key LIKE %s OR product LIKE %s OR vendor LIKE %s)"
        params += [like] * 3
    if vendor_id:
        sql += " AND vendor_id = %s"
        params.append(vendor_id)
    if status:
        sql += " AND status = %s"
        params.append(status)
    if expiring_within is not None:
        sql += " AND end_date <= CURDATE() + INTERVAL %s DAY"
        params.append(int(expiring_within))
    return db.query(sql + " ORDER BY end_date, license_id", params)


def get_license(license_id):
    return db.query_one("SELECT * FROM license WHERE license_id = %s", (license_id,))


def update_license(license_id, license_key, quantity, start_date, end_date, status):
    license_key = v.clean(license_key)
    v.validate_license_update(license_key, quantity, start_date, end_date, status)
    with db.transaction() as cur:
        cur.execute("SELECT 1 FROM license WHERE license_id = %s FOR UPDATE", (license_id,))
        if not cur.fetchone():
            raise db.AppError("That license no longer exists.")
        cur.execute("""UPDATE license SET license_key = %s, quantity = %s, start_date = %s,
                              end_date = %s, status = %s WHERE license_id = %s""",
                    (license_key, quantity, start_date, end_date, status, license_id))


def delete_license(license_id):
    """Delete a license and its purchase/subscription, only if nothing else depends on it."""
    with db.transaction() as cur:
        cur.execute("SELECT purchase_id FROM license WHERE license_id = %s FOR UPDATE", (license_id,))
        row = cur.fetchone()
        if not row:
            raise db.AppError("That license no longer exists.")
        cur.execute("""SELECT (SELECT COUNT(*) FROM allocation WHERE license_id = %s) AS allocations,
                              (SELECT COUNT(*) FROM renewal WHERE license_id = %s) AS renewals,
                              (SELECT COUNT(*) FROM compliance_check WHERE license_id = %s) AS checks""",
                    (license_id,) * 3)
        c = cur.fetchone()
        if c["allocations"] or c["renewals"] or c["checks"]:
            raise db.AppError(
                f"Can't delete: this license has {c['allocations']} allocation(s), "
                f"{c['renewals']} renewal(s) and {c['checks']} compliance check(s). "
                "Revoke it instead to keep the history.")
        cur.execute("DELETE FROM subscription WHERE license_id = %s", (license_id,))
        cur.execute("DELETE FROM license WHERE license_id = %s", (license_id,))
        cur.execute("DELETE FROM purchase WHERE purchase_id = %s", (row["purchase_id"],))
