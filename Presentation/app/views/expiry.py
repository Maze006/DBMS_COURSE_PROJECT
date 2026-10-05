import streamlit as st

from db import query_one
from services import allocations, reports
from views import ui

BUCKETS = ["All", "Expired", "0-30 days", "31-60 days", "61-90 days"]


def render():
    st.title("Expiry monitor")
    ui.show_flash()
    bucket = st.segmented_control("Show", BUCKETS, default="All", key="ex_bucket") or "All"
    ok, rows = ui.attempt(lambda: reports.expiry_list(None if bucket == "All" else bucket))
    if not ok:
        return

    c = st.columns(4)
    for col, b in zip(c, BUCKETS[1:]):
        col.metric(b, sum(1 for r in reports.expiry_list() if r["expiry_bucket"] == b))

    ui.table(rows, empty="No licenses in this window.")
    ui.csv_button(rows, "expiry.csv", key="ex_csv")
    st.caption("Renew a license from the Renewals page.")

    if not ui.can_edit():
        return
    st.divider()
    st.subheader("Expiry sweep")
    pending = query_one("""SELECT (SELECT COUNT(*) FROM license WHERE status = 'Active' AND end_date < CURDATE()) AS lic,
                                  (SELECT COUNT(*) FROM allocation a JOIN license l ON l.license_id = a.license_id
                                    WHERE a.status = 'Active' AND (a.expiry_date < CURDATE() OR l.status = 'Expired'
                                          OR l.end_date < CURDATE())) AS alloc""")
    st.write(f"{pending['lic']} license(s) and {pending['alloc']} allocation(s) are past their end date "
             "but still marked Active.")
    sure = st.checkbox("Mark them as Expired", key="ex_sweep_ok")
    if st.button("Run expiry sweep"):
        if not sure:
            st.error("Tick the box to confirm.")
        else:
            ok, res = ui.attempt(allocations.expire_overdue)
            if ok:
                ui.flash(f"Expired {res[0]} license(s) and {res[1]} allocation(s).")
