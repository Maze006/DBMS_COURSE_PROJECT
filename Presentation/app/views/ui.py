import pandas as pd
import streamlit as st

from db import AppError, ValidationError

EDIT_ROLES = {"Admin", "LicenseManager"}


def current_user():
    return st.session_state["user"]


def can_edit():
    return current_user()["role"] in EDIT_ROLES


def table(rows, empty="Nothing to show.", money=(), pct=()):
    if not rows:
        st.info(empty)
        return
    df = pd.DataFrame(rows)
    cfg = {c: st.column_config.NumberColumn(format="%.2f") for c in money if c in df}
    cfg.update({c: st.column_config.NumberColumn(format="%.1f%%") for c in pct if c in df})
    st.dataframe(df, width="stretch", hide_index=True, column_config=cfg)


def csv_button(rows, filename, label="Download CSV", key=None):
    if rows:
        st.download_button(label, pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
                           file_name=filename, mime="text/csv", key=key)


def attempt(fn):
    """Run fn(); show a friendly error and return (False, None) on failure."""
    try:
        return True, fn()
    except ValidationError as e:
        for msg in e.errors:
            st.error(msg)
    except AppError as e:
        st.error(str(e))
    return False, None


def pick(label, pairs, key=None, none_label=None, index=0, help=None):
    """Selectbox over (id, label) pairs; returns the chosen id (or None)."""
    ids = [p[0] for p in pairs]
    names = {p[0]: p[1] for p in pairs}
    if none_label is not None:
        ids = [None] + ids
        names[None] = none_label
    if not ids:
        st.selectbox(label, ["(none available)"], key=key, disabled=True)
        return None
    return st.selectbox(label, ids, format_func=lambda i: names[i], key=key,
                        index=min(index, len(ids) - 1), help=help)


def flash(message):
    """Show a success message after the page refreshes with the new data."""
    st.session_state["_flash"] = message
    st.rerun()


def show_flash():
    msg = st.session_state.pop("_flash", None)
    if msg:
        st.success(msg)


def read_only_notice():
    st.info(f"Your role ({current_user()['role']}) has read-only access to this page.")
