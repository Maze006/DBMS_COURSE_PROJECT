import db
import validators as v


def allocate(license_id, user_id, device_id, department_id, allocated_date, expiry_date):
    v.validate_allocation(license_id, user_id, department_id, allocated_date, expiry_date)
    with db.transaction() as cur:
        cur.execute("""INSERT INTO allocation (license_id, user_id, device_id, department_id,
                                               allocated_date, expiry_date)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (license_id, user_id, device_id, department_id, allocated_date, expiry_date))
        return cur.lastrowid


def reclaim(allocation_id):
    with db.transaction() as cur:
        cur.execute("SELECT status FROM allocation WHERE allocation_id = %s FOR UPDATE", (allocation_id,))
        row = cur.fetchone()
        if not row:
            raise db.AppError("That allocation no longer exists.")
        if row["status"] != "Active":
            raise db.AppError(f"This allocation is already {row['status'].lower()}.")
        cur.execute("UPDATE allocation SET status = 'Reclaimed' WHERE allocation_id = %s", (allocation_id,))


def list_allocations(status=None, department_id=None, text=None, license_id=None):
    sql = """SELECT a.allocation_id, u.name AS holder, hd.name AS home_department,
                    cd.name AS charged_department, p.name AS product, l.license_id, l.license_key,
                    dv.hostname AS device, a.allocated_date, a.expiry_date, a.status
               FROM allocation a
               JOIN app_user u ON u.user_id = a.user_id
               JOIN department hd ON hd.department_id = u.department_id
               JOIN department cd ON cd.department_id = a.department_id
               JOIN license l ON l.license_id = a.license_id
               JOIN purchase pu ON pu.purchase_id = l.purchase_id
               JOIN license_type lt ON lt.license_type_id = pu.license_type_id
               JOIN software_product p ON p.product_id = lt.product_id
               LEFT JOIN device dv ON dv.device_id = a.device_id
              WHERE 1 = 1"""
    params = []
    if status:
        sql += " AND a.status = %s"
        params.append(status)
    if department_id:
        sql += " AND a.department_id = %s"
        params.append(department_id)
    if license_id:
        sql += " AND a.license_id = %s"
        params.append(license_id)
    if text:
        like = f"%{text}%"
        sql += " AND (u.name LIKE %s OR p.name LIKE %s OR l.license_key LIKE %s)"
        params += [like] * 3
    return db.query(sql + " ORDER BY a.allocation_id DESC", params)


def expire_overdue():
    """Run the expiry sweep. Returns (licenses_expired, allocations_expired)."""
    out = db.call_procedure("sp_expire_overdue", [0, 0])
    return int(out[0]), int(out[1])
