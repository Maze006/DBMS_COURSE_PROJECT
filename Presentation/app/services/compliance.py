import db

AUTO_TYPES = "('Over-allocation','Expired-in-use','Unused')"


def run_check():
    db.call_procedure("sp_run_compliance_check")
    return latest_summary()


def latest_summary():
    return db.query(f"""SELECT check_type, result, COUNT(*) AS licenses
                          FROM compliance_check
                         WHERE check_type IN {AUTO_TYPES}
                           AND check_date = (SELECT MAX(check_date) FROM compliance_check
                                              WHERE check_type IN {AUTO_TYPES})
                         GROUP BY check_type, result ORDER BY check_type, result""")


def current_gaps():
    return db.query("""SELECT license_id, license_key, vendor, product, gap_type, capacity,
                              active_allocated, detail, cost_at_risk
                         FROM vw_compliance_gaps ORDER BY gap_type, license_id""")


def history(result=None, check_type=None, license_id=None):
    sql = """SELECT c.check_id, c.check_date, c.license_id, l.license_key, c.check_type,
                    c.result, c.details
               FROM compliance_check c JOIN license l ON l.license_id = c.license_id WHERE 1 = 1"""
    params = []
    if result:
        sql += " AND c.result = %s"
        params.append(result)
    if check_type:
        sql += " AND c.check_type = %s"
        params.append(check_type)
    if license_id:
        sql += " AND c.license_id = %s"
        params.append(license_id)
    return db.query(sql + " ORDER BY c.check_date DESC, c.check_id DESC LIMIT 500", params)
