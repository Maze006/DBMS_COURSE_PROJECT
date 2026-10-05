import pandas as pd
import streamlit as st

from services import compliance, reports
from views import ui


def render():
    st.title("Dashboard")
    ok, k = ui.attempt(reports.dashboard_kpis)
    if not ok:
        return

    c = st.columns(5)
    c[0].metric("Active licenses", k["active_licenses"])
    c[1].metric("Active seats", k["active_seats"])
    c[2].metric("Expiring in 30 days", k["expiring_30"])
    c[3].metric("Compliance gaps", k["gaps"])
    c[4].metric("Total spend", f"{k['total_spend']:,.0f}")

    left, right = st.columns(2)
    with left:
        st.subheader("Expiring soon")
        rows = reports.expiry_list()[:6]
        ui.table([{"Product": r["product"], "Ends": r["end_date"], "Days": r["days_remaining"],
                   "Seats in use": r["active_allocated"], "Bucket": r["expiry_bucket"]} for r in rows],
                 empty="No licenses expire in the next 90 days.")
    with right:
        st.subheader("Compliance gaps")
        gaps = compliance.current_gaps()
        ui.table([{"Product": g["product"], "Gap": g["gap_type"], "Detail": g["detail"]} for g in gaps],
                 empty="No compliance gaps. Nice.")

    left, right = st.columns(2)
    with left:
        st.subheader("Utilization by license")
        util = [r for r in reports.run_report("Utilization") if r["status"] == "Active"]
        if util:
            df = pd.DataFrame(util)
            df["license"] = "#" + df["license_id"].astype(str) + " " + df["product"]
            st.bar_chart(df.set_index("license")["utilization_pct"], horizontal=True)
    with right:
        st.subheader("Allocated cost by department")
        dept = reports.run_report("Department allocation")
        if dept:
            st.bar_chart(pd.DataFrame(dept).set_index("department")["allocated_seat_cost"])
