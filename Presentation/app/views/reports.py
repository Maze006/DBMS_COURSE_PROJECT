import streamlit as st

from services import reports
from views import ui

MONEY = ("cost_at_risk", "total_renewal_cost", "avg_renewal_cost", "allocated_seat_cost",
         "purchase_spend", "renewal_spend", "total_spend")
PCT = ("utilization_pct", "cost_share_pct")


def render():
    st.title("Reports")
    name = st.selectbox("Report", list(reports.REPORTS), key="rp_name")
    ok, rows = ui.attempt(lambda: reports.run_report(name))
    if not ok:
        return
    st.caption(f"{len(rows)} row(s)")
    ui.table(rows, empty="This report has no rows.", money=MONEY, pct=PCT)
    ui.csv_button(rows, name.lower().replace(" ", "_") + ".csv", key="rp_csv")
