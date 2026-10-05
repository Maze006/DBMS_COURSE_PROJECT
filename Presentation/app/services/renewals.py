import db
import validators as v


def renew_license(license_id, new_end_date, cost, renewed_by, renewal_date=None):
    """Extend a license and log the renewal in one transaction."""
    v.validate_renewal(license_id, new_end_date, cost)
    with db.transaction() as cur:
        cur.execute("SELECT end_date, status FROM license WHERE license_id = %s FOR UPDATE", (license_id,))
        lic = cur.fetchone()
        if not lic:
            raise db.AppError("That license no longer exists.")
        if lic["status"] == "Revoked":
            raise db.AppError("A revoked license can't be renewed. Change its status first.")
        if new_end_date <= lic["end_date"]:
            raise db.AppError(f"The new end date must be after the current end date ({lic['end_date']}).")
        cur.execute("""INSERT INTO renewal (license_id, renewal_date, previous_end_date, new_end_date,
                                            renewal_cost, renewed_by)
                       VALUES (%s, COALESCE(%s, CURDATE()), %s, %s, %s, %s)""",
                    (license_id, renewal_date, lic["end_date"], new_end_date, cost, renewed_by))
        renewal_id = cur.lastrowid
        cur.execute("UPDATE license SET end_date = %s, status = 'Active' WHERE license_id = %s",
                    (new_end_date, license_id))
        return renewal_id


def list_renewals(license_id=None):
    sql = """SELECT r.renewal_id, r.license_id, l.license_key, p.name AS product, r.renewal_date,
                    r.previous_end_date, r.new_end_date, r.renewal_cost, u.name AS renewed_by
               FROM renewal r
               JOIN license l ON l.license_id = r.license_id
               JOIN purchase pu ON pu.purchase_id = l.purchase_id
               JOIN license_type lt ON lt.license_type_id = pu.license_type_id
               JOIN software_product p ON p.product_id = lt.product_id
               LEFT JOIN app_user u ON u.user_id = r.renewed_by"""
    params = []
    if license_id:
        sql += " WHERE r.license_id = %s"
        params.append(license_id)
    return db.query(sql + " ORDER BY r.renewal_date DESC, r.renewal_id DESC", params)
