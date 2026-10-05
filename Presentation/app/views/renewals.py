from datetime import date, timedelta

import streamlit as st

from db import query_one
from services import lookups, renewals
from views import ui


def render():
    st.title("Renewals")
    ui.show_flash()
    tab_new, tab_hist = st.tabs(["Renew a license", "Renewal history"])

    with tab_new:
        if not ui.can_edit():
            ui.read_only_notice()
        else:
            renew_form()

    with tab_hist:
        lic = ui.pick("License", [(r["id"], r["label"]) for r in lookups.licenses()], key="rn_hist_lic",
                      none_label="All licenses")
        rows = renewals.list_renewals(lic)
        ui.table(rows, empty="No renewals recorded.", money=("renewal_cost",))
        ui.csv_button(rows, "renewals.csv", key="rn_csv")


def renew_form():
    lics = lookups.licenses(include_revoked=False)
    lid = ui.pick("License", [(r["id"], r["label"]) for r in lics], key="rn_lic")
    if lid is None:
        st.info("There are no licenses to renew.")
        return
    lic = next(r for r in lics if r["id"] == lid)
    sub = query_one("SELECT billing_cycle, cost_per_cycle FROM subscription WHERE license_id = %s", (lid,))

    c = st.columns(3)
    c[0].metric("Status", lic["status"])
    c[1].metric("Current end date", str(lic["end_date"]))
    c[2].metric("Billing", f"{sub['billing_cycle']} ({sub['cost_per_cycle']:,.2f})" if sub else "Not a subscription")

    base = max(lic["end_date"], date.today())
    with st.form(f"renew_form_{lid}"):
        a, b = st.columns(2)
        new_end = a.date_input("New end date", value=base + timedelta(days=365))
        cost = b.number_input("Renewal cost", min_value=0.0, value=float(sub["cost_per_cycle"]) if sub else 0.0,
                              step=10.0, format="%.2f")
        submitted = st.form_submit_button("Renew license", type="primary")
    if submitted:
        ok, _ = ui.attempt(lambda: renewals.renew_license(lid, new_end, float(cost), ui.current_user()["id"]))
        if ok:
            ui.flash(f"License #{lid} renewed until {new_end}.")
