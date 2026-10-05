from datetime import date

import streamlit as st

from services import allocations, lookups
from views import ui


def render():
    st.title("Allocate license")
    ui.show_flash()
    if not ui.can_edit():
        ui.read_only_notice()
        return

    lics = lookups.licenses(only_valid=True)
    lid = ui.pick("License", [(r["id"], r["label"]) for r in lics], key="al_lic",
                  help="Only active, unexpired licenses are listed.")
    if lid is None:
        st.info("There are no active licenses to allocate.")
        return
    lic = next(r for r in lics if r["id"] == lid)

    c = st.columns(3)
    c[0].metric("Capacity", lic["capacity"])
    c[1].metric("Free seats", lic["seats_available"])
    c[2].metric("Valid until", str(lic["end_date"]))

    users = lookups.users()
    uid = ui.pick("User", [(u["id"], u["label"]) for u in users], key=f"al_user_{lid}")
    home = next((u["department_id"] for u in users if u["id"] == uid), None)
    depts = lookups.departments()
    dept_idx = next((i for i, d in enumerate(depts) if d[0] == home), 0)

    a, b = st.columns(2)
    with a:
        dept = ui.pick("Charge to department", depts, key=f"al_dept_{lid}_{uid}", index=dept_idx,
                       help="Defaults to the user's home department. Change it to cross-charge.")
    with b:
        dev = ui.pick("Device (optional)", lookups.devices(), key=f"al_dev_{lid}", none_label="No device")
    d1, d2 = st.columns(2)
    start = max(date.today(), lic["start_date"])
    adate = d1.date_input("Allocated on", value=start, key=f"al_from_{lid}")
    edate = d2.date_input("Expires on", value=lic["end_date"], key=f"al_to_{lid}")

    if st.button("Allocate", type="primary"):
        ok, _ = ui.attempt(lambda: allocations.allocate(lid, uid, dev, dept, adate, edate))
        if ok:
            ui.flash("License allocated.")

    st.subheader("Current allocations on this license")
    ui.table(allocations.list_allocations(status="Active", license_id=lid),
             empty="No active allocations on this license yet.")
