import db

REPORTS = {
    "License expiry": """SELECT license_id, license_key, vendor, product, end_date, days_remaining,
                                expiry_bucket, active_allocated, auto_renew
                           FROM vw_license_expiry ORDER BY days_remaining""",
    "Utilization": """SELECT license_id, vendor, product, license_type, status, capacity,
                             active_allocated, seats_available, utilization_pct, end_date
                        FROM vw_license_utilization ORDER BY utilization_pct DESC""",
    "Compliance gaps": """SELECT license_id, license_key, vendor, product, gap_type, capacity,
                                 active_allocated, detail, cost_at_risk
                            FROM vw_compliance_gaps ORDER BY gap_type, license_id""",
    "Renewal cost": """SELECT renewal_year, vendor, product, renewals, total_renewal_cost, avg_renewal_cost
                         FROM vw_renewal_cost_summary ORDER BY renewal_year DESC, total_renewal_cost DESC""",
    "Department allocation": """SELECT department, cost_center_code, active_seats, licenses_in_use,
                                       allocated_seat_cost, cost_share_pct
                                  FROM vw_department_allocation ORDER BY allocated_seat_cost DESC""",
    "Vendor portfolio": """SELECT vendor, products, licenses, total_seats, seats_allocated,
                                  purchase_spend, renewal_spend, total_spend
                             FROM vw_vendor_portfolio ORDER BY total_spend DESC""",
}


def run_report(name):
    return db.query(REPORTS[name])


def dashboard_kpis():
    return db.query_one("""
        SELECT (SELECT COUNT(*) FROM license WHERE status = 'Active' AND end_date >= CURDATE()) AS active_licenses,
               (SELECT COUNT(*) FROM allocation WHERE status = 'Active') AS active_seats,
               (SELECT COUNT(*) FROM vw_license_expiry WHERE days_remaining BETWEEN 0 AND 30) AS expiring_30,
               (SELECT COUNT(*) FROM vw_compliance_gaps) AS gaps,
               (SELECT COALESCE(SUM(total_spend), 0) FROM vw_vendor_portfolio) AS total_spend""")


def expiry_list(bucket=None):
    sql = """SELECT license_id, license_key, vendor, product, end_date, days_remaining,
                    expiry_bucket, active_allocated, auto_renew FROM vw_license_expiry"""
    params = []
    if bucket:
        sql += " WHERE expiry_bucket = %s"
        params.append(bucket)
    return db.query(sql + " ORDER BY days_remaining", params)


def spend_by_product():
    return db.query("""SELECT vendor, product, SUM(purchase_cost) AS purchase_spend,
                              SUM(capacity) AS seats, SUM(active_allocated) AS seats_used
                         FROM vw_license_utilization
                        GROUP BY vendor_id, vendor, product_id, product
                        ORDER BY purchase_spend DESC""")


def idle_spend():
    return db.query("""SELECT license_id, vendor, product, capacity, active_allocated, seats_available,
                              cost_per_seat, ROUND(seats_available * cost_per_seat, 2) AS idle_cost
                         FROM vw_license_utilization
                        WHERE status = 'Active' AND end_date >= CURDATE() AND seats_available > 0
                        ORDER BY idle_cost DESC""")


def renewal_forecast(days=90):
    return db.query("""SELECT e.license_id, e.vendor, e.product, e.end_date, e.days_remaining, e.auto_renew,
                              s.billing_cycle, s.cost_per_cycle
                         FROM vw_license_expiry e JOIN subscription s ON s.license_id = e.license_id
                        WHERE e.days_remaining BETWEEN 0 AND %s ORDER BY e.end_date""", (days,))
