import pandas as pd
import streamlit as st

from services import reports
from views import ui


def render():
    st.title("Cost analysis")
    k = reports.dashboard_kpis()
    idle = reports.idle_spend()
    c = st.columns(3)
    c[0].metric("Total spend (purchases + renewals)", f"{k['total_spend']:,.2f}")
    c[1].metric("Idle seat value", f"{sum(r['idle_cost'] for r in idle):,.2f}")
    c[2].metric("Idle seats", sum(r["seats_available"] for r in idle))

    t1, t2, t3, t4 = st.tabs(["By vendor", "By department", "Idle spend", "Renewal forecast"])

    with t1:
        rows = reports.run_report("Vendor portfolio")
        if rows:
            st.bar_chart(pd.DataFrame(rows).set_index("vendor")[["purchase_spend", "renewal_spend"]])
        ui.table(rows, money=("purchase_spend", "renewal_spend", "total_spend"))
        st.caption("By product")
        ui.table(reports.spend_by_product(), money=("purchase_spend",))

    with t2:
        rows = reports.run_report("Department allocation")
        if rows:
            st.bar_chart(pd.DataFrame(rows).set_index("department")["allocated_seat_cost"])
        ui.table(rows, money=("allocated_seat_cost",), pct=("cost_share_pct",))

    with t3:
        st.write("Seats paid for but not allocated, on licenses that are still valid.")
        ui.table(idle, empty="No idle seats.", money=("cost_per_seat", "idle_cost"))
        ui.csv_button(idle, "idle_spend.csv", key="co_idle_csv")

    with t4:
        days = st.select_slider("Window (days)", [30, 60, 90, 180], value=90, key="co_days")
        rows = reports.renewal_forecast(days)
        if rows:
            st.metric("Renewal commitments in window", f"{sum(r['cost_per_cycle'] for r in rows):,.2f}")
        ui.table(rows, empty="No subscription renewals fall in this window.", money=("cost_per_cycle",))
