from datetime import date, timedelta

import streamlit as st

from services import lookups, purchases
from validators import BILLING_CYCLES
from views import ui


def render():
    st.title("Purchases")
    tab_new, tab_hist = st.tabs(["Record purchase", "Purchase history"])

    with tab_new:
        if not ui.can_edit():
            ui.read_only_notice()
        else:
            record_form()

    with tab_hist:
        c1, c2 = st.columns([2, 1])
        text = c1.text_input("Search", placeholder="Product, vendor, order reference or license key", key="ph_text")
        vendor = ui.pick("Vendor", lookups.vendors(), key="ph_vendor", none_label="All vendors")
        ok, rows = ui.attempt(lambda: purchases.list_purchases(text or None, vendor))
        if ok:
            ui.table(rows, empty="No purchases match.", money=("unit_cost", "total_cost"))
            ui.csv_button(rows, "purchases.csv", key="ph_csv")


def record_form():
    types = lookups.license_types()
    by_id = {t["id"]: t for t in types}
    type_id = ui.pick("License type", [(t["id"], t["label"]) for t in types], key="pu_type")
    if type_id is None:
        return
    lt = by_id[type_id]
    is_sub = lt["pricing_model"] == "Subscription"

    with st.form(f"purchase_form_{type_id}"):
        c1, c2, c3 = st.columns(3)
        qty = c1.number_input("Quantity (units)", min_value=1, value=1, step=1)
        cost = c2.number_input("Unit cost", min_value=0.0, value=0.0, step=10.0, format="%.2f")
        pdate = c3.date_input("Purchase date", value=date.today())
        c4, c5 = st.columns(2)
        sdate = c4.date_input("License start", value=date.today())
        edate = c5.date_input("License end", value=date.today() + timedelta(days=365))
        c6, c7 = st.columns(2)
        order = c6.text_input("Order reference", placeholder="PO-2026-020", max_chars=50)
        key = c7.text_input("License key", placeholder="Leave blank to generate one", max_chars=100)

        cycle = auto = cpc = None
        if is_sub:
            st.caption("Subscription billing")
            d1, d2, d3 = st.columns(3)
            cycle = d1.selectbox("Billing cycle", BILLING_CYCLES, index=2)
            cpc = d2.number_input("Cost per cycle", min_value=0.0, value=0.0, step=10.0, format="%.2f",
                                  help="Leave at 0 to use the total purchase cost.")
            auto = d3.checkbox("Auto-renew", value=False)

        seats = int(qty) * lt["seats_per_license"]
        st.caption(f"This creates a license with {seats} seat(s). Total cost: {qty * cost:,.2f}")
        submitted = st.form_submit_button("Record purchase", type="primary")

    if submitted:
        if is_sub and not cpc:
            cpc = float(qty) * float(cost)
        ok, res = ui.attempt(lambda: purchases.record_purchase(
            type_id, int(qty), float(cost), pdate, order, key, sdate, edate, cycle, auto, cpc))
        if ok:
            st.success(f"Purchase recorded. License #{res['license_id']} created with key {res['license_key']} "
                       f"({res['seats']} seats).")
