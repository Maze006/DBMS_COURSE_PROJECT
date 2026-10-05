
import streamlit as st

from services import master
from views import ui


def render():
    st.title("Master data")
    ui.show_flash()
    entity = st.selectbox("Table", list(master.MASTER), key="md_entity")
    spec = master.MASTER[entity]

    tab_list, tab_add, tab_edit, tab_del = st.tabs(["Browse", "Add", "Edit", "Delete"])

    with tab_list:
        text = st.text_input("Search", key=f"md_search_{entity}")
        ok, rows = ui.attempt(lambda: master.list_rows(entity, text or None))
        if ok:
            ui.table(rows, empty="No records found.")
            ui.csv_button(rows, entity.lower().replace(" ", "_") + ".csv", key=f"md_csv_{entity}")

    with tab_add:
        with st.form(f"md_add_{entity}", clear_on_submit=True):
            values = field_inputs(spec["fields"], {}, f"add_{entity}")
            if st.form_submit_button("Add", type="primary"):
                ok, new_id = ui.attempt(lambda: master.insert_row(entity, values))
                if ok:
                    ui.flash(f"{entity[:-1] if entity.endswith('s') else entity} added (id {new_id}).")

    rows = master.list_rows(entity)
    ids = [(r[spec["pk"]], " - ".join(str(v) for k, v in r.items() if k != spec["pk"])[:90]) for r in rows]

    with tab_edit:
        rid = ui.pick("Record", ids, key=f"md_edit_pick_{entity}")
        if rid is not None:
            current = master.get_row(entity, rid) or {}
            with st.form(f"md_edit_{entity}_{rid}"):
                values = field_inputs(spec["fields"], current, f"edit_{entity}_{rid}")
                if st.form_submit_button("Save changes", type="primary"):
                    ok, _ = ui.attempt(lambda: master.update_row(entity, rid, values))
                    if ok:
                        ui.flash("Changes saved.")

    with tab_del:
        rid = ui.pick("Record", ids, key=f"md_del_pick_{entity}")
        sure = st.checkbox("I understand this can't be undone", key=f"md_del_ok_{entity}_{rid}")
        if st.button("Delete record", key=f"md_del_btn_{entity}"):
            if not sure:
                st.error("Tick the box to confirm the deletion.")
            elif rid is not None:
                ok, _ = ui.attempt(lambda: master.delete_row(entity, rid))
                if ok:
                    ui.flash("Record deleted.")


def field_inputs(fields, current, prefix):
    values = {}
    for f in fields:
        label = f["label"] + ("" if f["required"] else " (optional)")
        key = f"{prefix}_{f['name']}"
        cur = current.get(f["name"])
        kind = f["kind"]
        if kind == "select":
            pairs = f["options"]()
            idx = next((i for i, p in enumerate(pairs) if p[0] == cur), 0)
            values[f["name"]] = ui.pick(label, pairs, key=key, index=idx)
        elif kind == "choice":
            opts = f["options"]()
            values[f["name"]] = st.selectbox(label, opts, index=opts.index(cur) if cur in opts else 0, key=key)
        elif kind == "int":
            values[f["name"]] = int(st.number_input(label, min_value=1, value=int(cur or 1), step=1, key=key))
        else:
            values[f["name"]] = st.text_input(label, value=cur or "", max_chars=f["max"], key=key)
    return values
