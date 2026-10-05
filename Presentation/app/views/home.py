import streamlit as st

from services import reports
from views import ui

_PAGES = {}

DESCRIPTIONS = {
    "dashboard": "Live numbers, expiring licenses, gaps and utilization at a glance.",
    "purchases": "Record what you bought and issue its license key in one step.",
    "licenses": "Search every license by key, product, vendor or status.",
    "allocate": "Assign seats to people and devices, never beyond what you bought.",
    "reclaim": "Take seats back from leavers and put them to work again.",
    "expiry": "See what lapses in the next 30, 60 and 90 days.",
    "renewals": "Extend a license and log the cost, atomically.",
    "compliance": "Catch over-allocated, expired and idle licenses.",
    "cost": "Spend by vendor and department, plus idle seat value.",
    "reports": "Six ready reports, one click to CSV.",
    "master": "Add, edit and remove vendors, products, users and devices.",
}

CSS = """
<style>
.sm-banner { background: #0B0B0B; border-radius: 6px; padding: 26px 30px; display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap;
             border-bottom: 6px solid #E63946; }
.sm-banner span { font-family: 'Archivo Black', Impact, sans-serif; font-size: clamp(44px, 7vw, 84px); line-height: .9; color: #F5ECD7; }
.sm-banner span.r { color: #E63946; }
.sm-banner small { margin-left: auto; font-size: 12px; letter-spacing: .3em; text-transform: uppercase; color: #F5ECD7; opacity: .7; }
.sm-sec { font-family: 'Archivo Black', Impact, sans-serif; font-size: 34px; letter-spacing: -.01em; margin: 34px 0 4px; color: #141414; }
.sm-sec em { color: #C8102E; font-style: normal; }
.sm-sub { color: #4a4235; margin: 0 0 20px; }
.sm-kpi { background: #0B0B0B; color: #F5ECD7; padding: 16px 18px; border-radius: 6px; border-left: 6px solid #E63946; }
.sm-kpi b { display: block; font-family: 'Archivo Black', Impact, sans-serif; font-size: 34px; line-height: 1.1; }
.sm-kpi span { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: #d9cfb8; }
.sm-kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }

.st-key-hcgrid { display: grid !important; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px !important; }
.st-key-hcgrid > div { width: 100% !important; min-width: 0; }
[class*="st-key-hc_"] { position: relative; background: #0B0B0B; border-radius: 6px; padding: 20px 20px 22px; overflow: hidden; gap: .35rem;
                        transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s; min-height: 190px; }
[class*="st-key-hc_"]::before { content: ''; position: absolute; left: 0; bottom: 0; height: 4px; width: 28%; background: #E63946; transition: width .4s; z-index: 1; }
[class*="st-key-hc_"]:hover { transform: translateY(-8px) rotate(-.6deg); box-shadow: 0 18px 30px -12px rgba(200,16,46,.55); }
[class*="st-key-hc_"]:hover::before { width: 100%; }
[class*="st-key-hc_"] .hc-n { font-family: 'Archivo Black', Impact, sans-serif; font-size: 38px; color: #E63946; line-height: 1; }
[class*="st-key-hc_"] .hc-t { margin-top: 8px; font-size: 20px; font-weight: 600; color: #F5ECD7; }
[class*="st-key-hc_"] .hc-d { margin-top: 4px; margin-bottom: 18px; font-size: 14px; line-height: 1.5; color: #d9cfb8; }
[class*="st-key-hc_"] .stElementContainer { position: static !important; }
[class*="st-key-hc_"] [data-testid="stPageLink"] a { padding: 0; background: transparent; min-height: 0; }
[class*="st-key-hc_"] [data-testid="stPageLink"] a:hover { background: transparent; }
[class*="st-key-hc_"] [data-testid="stPageLink"] a::after { content: ''; position: absolute; inset: 0; z-index: 2; }
[class*="st-key-hc_"] [data-testid="stPageLink"] p,
[class*="st-key-hc_"] [data-testid="stPageLink"] span { color: #E63946 !important; font-size: 12px; font-weight: 600; letter-spacing: .16em; text-transform: uppercase; }
</style>
"""


def set_pages(pages):
    """main.py hands over this user's st.Page objects (same ones used by the sidebar)."""
    _PAGES.clear()
    _PAGES.update(pages)


def render():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<div class='sm-banner'><span>SUB</span><span class='r'>MAG</span>"
                "<small>License &amp; subscription management</small></div>", unsafe_allow_html=True)

    user = ui.current_user()
    st.markdown(f"<div class='sm-sec'>Welcome back, <em>{user['name'].split()[0]}</em></div>"
                "<p class='sm-sub'>Here's where your licenses stand right now.</p>", unsafe_allow_html=True)
    ok, k = ui.attempt(reports.dashboard_kpis)
    if ok:
        st.markdown(
            "<div class='sm-kpis'>"
            f"<div class='sm-kpi'><b>{k['active_licenses']}</b><span>Active licenses</span></div>"
            f"<div class='sm-kpi'><b>{k['active_seats']}</b><span>Seats in use</span></div>"
            f"<div class='sm-kpi'><b>{k['expiring_30']}</b><span>Expiring in 30 days</span></div>"
            f"<div class='sm-kpi'><b>{k['gaps']}</b><span>Compliance gaps</span></div>"
            f"<div class='sm-kpi'><b>{k['total_spend']:,.0f}</b><span>Total spend</span></div>"
            "</div>", unsafe_allow_html=True)

    tools = [(key, page) for key, page in _PAGES.items() if key != "home"]
    if not tools:
        return
    st.markdown("<div class='sm-sec'>Your <em>toolkit</em></div>"
                f"<p class='sm-sub'>Everything your role ({user['role']}) can open. Tap a card to jump straight in.</p>",
                unsafe_allow_html=True)
    with st.container(key="hcgrid"):
        for i, (key, page) in enumerate(tools, 1):
            with st.container(key=f"hc_{key}"):
                st.markdown(f"<div class='hc-n'>{i:02d}</div><div class='hc-t'>{page.title}</div>"
                            f"<div class='hc-d'>{DESCRIPTIONS.get(key, '')}</div>", unsafe_allow_html=True)
                st.page_link(page, label="Open", icon=":material/arrow_forward:")
