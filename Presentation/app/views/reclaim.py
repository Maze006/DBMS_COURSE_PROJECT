import streamlit as st

from services import allocations, lookups
from views import ui


def render():
    st.title("Reclaim license")
    ui.show_flash()
    if not ui.can_edit():
        ui.read_only_notice()
        return

    c1, c2 = st.columns([2, 1])
    text = c1.text_input("Search", placeholder="User, product or license key", key="rc_text")
    with c2:
        dept = ui.pick("Charged department", lookups.departments(), key="rc_dept", none_label="All departments")

    ok, rows = ui.attempt(lambda: allocations.list_allocations("Active", dept, text or None))
    if not ok:
        return
    st.caption(f"{len(rows)} active allocation(s)")
    ui.table(rows, empty="No active allocations match.")
    if not rows:
        return

    st.divider()
    aid = ui.pick("Allocation to reclaim",
                  [(r["allocation_id"], f"#{r['allocation_id']} {r['holder']} - {r['product']}"
                                        f"{' on ' + r['device'] if r['device'] else ''}") for r in rows],
                  key="rc_pick")
    sure = st.checkbox("Reclaim this seat and make it available again", key=f"rc_ok_{aid}")
    if st.button("Reclaim", type="primary"):
        if not sure:
            st.error("Tick the box to confirm.")
        else:
            ok, _ = ui.attempt(lambda: allocations.reclaim(aid))
            if ok:
                ui.flash("Seat reclaimed and available again.")
