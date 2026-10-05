import streamlit as st

from services import compliance, lookups
from views import ui


def render():
    st.title("Compliance")
    ui.show_flash()

    if st.button("Run compliance check", type="primary"):
        ok, _ = ui.attempt(compliance.run_check)
        if ok:
            ui.flash("Compliance check complete. Results are stored in the history below.")

    st.subheader("Latest check")
    summary = compliance.latest_summary()
    ui.table(summary, empty="No check has been run yet.")

    st.subheader("Open gaps")
    gaps = compliance.current_gaps()
    ui.table(gaps, empty="No compliance gaps right now.", money=("cost_at_risk",))
    ui.csv_button(gaps, "compliance_gaps.csv", key="cp_csv")

    st.subheader("History")
    a, b, c = st.columns(3)
    result = a.selectbox("Result", ["All", "Fail", "Pass"], key="cp_result")
    ctype = b.selectbox("Check type", ["All", "Over-allocation", "Expired-in-use", "Unused", "Key-audit"], key="cp_type")
    with c:
        lic = ui.pick("License", [(r["id"], r["label"]) for r in lookups.licenses()], key="cp_lic",
                      none_label="All licenses")
    ui.table(compliance.history(None if result == "All" else result, None if ctype == "All" else ctype, lic),
             empty="No checks match.")
