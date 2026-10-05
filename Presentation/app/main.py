import streamlit as st

from db import AppError
from services import lookups
from views import (allocate, compliance, cost, dashboard, expiry, home, licenses, master_data,
                   purchases, reclaim, renewals, reports, splash)

st.set_page_config(page_title="SUB MAG", page_icon=":material/key:", layout="wide")

PAGES = {
    "home": (home.render, "Home", ":material/home:"),
    "dashboard": (dashboard.render, "Dashboard", ":material/dashboard:"),
    "purchases": (purchases.render, "Purchases", ":material/shopping_cart:"),
    "licenses": (licenses.render, "Licenses", ":material/badge:"),
    "allocate": (allocate.render, "Allocate", ":material/person_add:"),
    "reclaim": (reclaim.render, "Reclaim", ":material/person_remove:"),
    "expiry": (expiry.render, "Expiry monitor", ":material/event_upcoming:"),
    "renewals": (renewals.render, "Renewals", ":material/autorenew:"),
    "compliance": (compliance.render, "Compliance", ":material/verified_user:"),
    "cost": (cost.render, "Cost analysis", ":material/payments:"),
    "reports": (reports.render, "Reports", ":material/assessment:"),
    "master": (master_data.render, "Master data", ":material/database:"),
}

ROLE_PAGES = {
    "Admin": list(PAGES),
    "LicenseManager": ["home", "dashboard", "purchases", "licenses", "allocate", "reclaim", "expiry",
                       "renewals", "cost", "reports"],
    "Compliance": ["home", "dashboard", "licenses", "expiry", "compliance", "cost", "reports"],
    "Manager": ["home", "dashboard", "cost", "reports"],
    "Employee": ["home", "dashboard"],
}


def sign_in():
    try:
        users = lookups.users()
    except AppError as e:
        st.error(str(e))
        st.stop()
    if not users:
        st.error("No users found. Load sql/03_seed_data.sql first.")
        st.stop()

    default = next((i for i, u in enumerate(users) if u["role"] == "LicenseManager"), 0)
    with st.sidebar:
        st.markdown("### SUB MAG")
        choice = st.selectbox("Signed in as", users, index=default, format_func=lambda u: f"{u['name']} ({u['role']})")
    st.session_state["user"] = choice


splash.inject()
sign_in()
user = st.session_state["user"]
allowed = ROLE_PAGES.get(user["role"], ["home", "dashboard"])
page_objs = {k: st.Page(PAGES[k][0], title=PAGES[k][1], icon=PAGES[k][2], url_path=k)
             for k in allowed}
home.set_pages(page_objs)
nav = st.navigation(list(page_objs.values()))
nav.run()
