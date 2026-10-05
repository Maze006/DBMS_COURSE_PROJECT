import streamlit as st

from services import licenses, lookups
from validators import LICENSE_STATUSES
from views import ui

WINDOWS = {"Any time": None, "Expired or within 30 days": 30, "Within 60 days": 60, "Within 90 days": 90}


def render():
    st.title("Licenses")
    ui.show_flash()
    c1, c2, c3, c4 = st.columns([2, 1.2, 1, 1.4])
    text = c1.text_input("Search", placeholder="License key, product or vendor", key="lic_text")
    with c2:
        vendor = ui.pick("Vendor", lookups.vendors(), key="lic_vendor", none_label="All vendors")
    status = c3.selectbox("Status", ["All", *LICENSE_STATUSES], key="lic_status")
    window = c4.selectbox("Ends", list(WINDOWS), key="lic_window")

    ok, rows = ui.attempt(lambda: licenses.search_licenses(
        text or None, vendor, None if status == "All" else status, WINDOWS[window]))
    if not ok:
        return
    st.caption(f"{len(rows)} license(s)")
    ui.table(rows, empty="No licenses match these filters.", pct=("utilization_pct",))
    ui.csv_button(rows, "licenses.csv", key="lic_csv")

    if not rows:
        return
    st.divider()
    st.subheader("Edit or delete a license")
    if not ui.can_edit():
        ui.read_only_notice()
        return

    lid = ui.pick("License", [(r["license_id"], f"#{r['license_id']} {r['product']} - {r['license_key']}") for r in rows],
                  key="lic_pick")
    lic = licenses.get_license(lid)
    if not lic:
        st.warning("That license no longer exists.")
        return

    with st.form(f"lic_edit_{lid}"):
        a, b = st.columns(2)
        key = a.text_input("License key", value=lic["license_key"], max_chars=100)
        qty = b.number_input("Seat capacity", min_value=1, value=int(lic["quantity"]), step=1)
        c, d, e = st.columns(3)
        sd = c.date_input("Start date", value=lic["start_date"])
        ed = d.date_input("End date", value=lic["end_date"])
        stt = e.selectbox("Status", LICENSE_STATUSES, index=LICENSE_STATUSES.index(lic["status"]))
        saved = st.form_submit_button("Save changes", type="primary")
    if saved:
        ok, _ = ui.attempt(lambda: licenses.update_license(lid, key, int(qty), sd, ed, stt))
        if ok:
            ui.flash("License updated.")

    with st.expander("Delete this license"):
        st.caption("Only licenses with no allocations, renewals or compliance history can be deleted. "
                   "Otherwise set the status to Revoked.")
        sure = st.checkbox("I understand this can't be undone", key=f"lic_del_ok_{lid}")
        if st.button("Delete license", key=f"lic_del_{lid}"):
            if not sure:
                st.error("Tick the box to confirm the deletion.")
            else:
                ok, _ = ui.attempt(lambda: licenses.delete_license(lid))
                if ok:
                    ui.flash("License deleted.")
