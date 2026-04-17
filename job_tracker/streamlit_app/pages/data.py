"""Data tab — manage Companies, Positions, and Recruiters."""

from __future__ import annotations

import streamlit as st

from job_tracker.models.position import VALID_LEVELS
from job_tracker.streamlit_app import cache
from job_tracker.streamlit_app.style import html_table, section_header


# ── shared helpers ────────────────────────────────────────────────────────────

_TD = "padding:10px 14px;color:#374151;border-bottom:1px solid #f3f4f6;"
_TD_MUTED = _TD + "color:#6b7280;font-size:13px;"
_TD_SM    = _TD + "color:#9ca3af;font-size:12px;"


def _sub_header(label: str, count: int, add_key: str) -> None:
    """Render the 'N items  [+ Add ...]' sub-header row."""
    hc1, hc2 = st.columns([5, 1])
    hc1.markdown(
        f"<span style='font-size:13px;color:#9ca3af;'>{count} {label}</span>",
        unsafe_allow_html=True,
    )
    if hc2.button(f"+ Add {label.rstrip('s')}", key=f"toggle_{add_key}", type="primary"):
        st.session_state[add_key] = not st.session_state.get(add_key, False)
        st.rerun()


# ── Companies ─────────────────────────────────────────────────────────────────

def _companies_tab() -> None:
    companies = cache.get_companies()
    form_key  = "show_add_company"

    _sub_header("companies", len(companies), form_key)

    if st.session_state.get(form_key, False):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        with st.form("add_company_form", clear_on_submit=True):
            r1c1, r1c2 = st.columns(2)
            r2c1, r2c2 = st.columns(2)
            name     = r1c1.text_input("Name *",   max_chars=50)
            industry = r1c2.text_input("Industry", max_chars=50)
            location = r2c1.text_input("Location", max_chars=50)
            notes    = r2c2.text_input("Notes",    max_chars=255)
            submitted = st.form_submit_button("Add Company", type="primary")

        if submitted:
            if not name.strip():
                st.error("Company name is required.")
            else:
                try:
                    cache.create_company(
                        name=name.strip(),
                        industry=industry.strip() or None,
                        location=location.strip() or None,
                        notes=notes.strip() or None,
                    )
                    st.success(f"Company **{name.strip()}** added.")
                    st.session_state[form_key] = False
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not companies:
        st.caption("No companies yet.")
        return

    confirm_key = "del_company"
    rows_html = ""
    for c in companies:
        rows_html += (
            f"<tr>"
            f"<td style='{_TD_SM}'>{c.id}</td>"
            f"<td style='{_TD}'><strong>{c.name}</strong></td>"
            f"<td style='{_TD_MUTED}'>{c.industry or '—'}</td>"
            f"<td style='{_TD_MUTED}'>{c.location or '—'}</td>"
            f"<td style='{_TD}'></td>"
            f"</tr>"
        )

    st.markdown(
        html_table(["ID", "Name", "Industry", "Location", "Actions"], rows_html),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Delete controls below the table
    del_opts = {f"#{c.id} — {c.name}": c.id for c in companies}
    dc1, dc2 = st.columns([3, 1])
    sel = dc1.selectbox("Select company to delete", ["— select —"] + list(del_opts.keys()), key="co_del_sel", label_visibility="collapsed")
    if dc2.button("🗑️ Delete", key="co_del_btn"):
        if sel != "— select —":
            st.session_state[confirm_key] = del_opts[sel]
            st.rerun()

    if confirm_key in st.session_state:
        cid   = st.session_state[confirm_key]
        cname = next((c.name for c in companies if c.id == cid), str(cid))
        st.warning(f"Delete **{cname}**? Remove any linked applications and recruiters first.")
        ok1, ok2 = st.columns(2)
        if ok1.button("Confirm", key="co_del_confirm", type="primary"):
            try:
                cache.delete_company(cid)
                st.session_state.pop(confirm_key, None)
                st.success(f"{cname} deleted.")
                st.rerun()
            except Exception as exc:
                st.error(f"Cannot delete: {exc}")
        if ok2.button("Cancel", key="co_del_cancel"):
            st.session_state.pop(confirm_key, None)
            st.rerun()


# ── Positions ─────────────────────────────────────────────────────────────────

def _positions_tab() -> None:
    positions = cache.get_positions()
    levels    = sorted(VALID_LEVELS)
    form_key  = "show_add_position"

    _sub_header("positions", len(positions), form_key)

    if st.session_state.get(form_key, False):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        with st.form("add_position_form", clear_on_submit=True):
            p1, p2 = st.columns(2)
            title     = p1.text_input("Title *", max_chars=50)
            level     = p2.selectbox("Level *", levels)
            submitted = st.form_submit_button("Add Position", type="primary")

        if submitted:
            if not title.strip():
                st.error("Position title is required.")
            else:
                try:
                    cache.create_position(title=title.strip(), level=level)
                    st.success(f"Position **{title.strip()} ({level})** added.")
                    st.session_state[form_key] = False
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not positions:
        st.caption("No positions yet.")
        return

    confirm_key = "del_position"
    rows_html = ""
    for p in positions:
        rows_html += (
            f"<tr>"
            f"<td style='{_TD_SM}'>{p.id}</td>"
            f"<td style='{_TD}'>{p.title}</td>"
            f"<td style='{_TD_MUTED}'>{p.level}</td>"
            f"<td style='{_TD}'></td>"
            f"</tr>"
        )

    st.markdown(
        html_table(["ID", "Title", "Level", "Actions"], rows_html),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    del_opts = {f"#{p.id} — {p.title} ({p.level})": p.id for p in positions}
    dc1, dc2 = st.columns([3, 1])
    sel = dc1.selectbox("Select position to delete", ["— select —"] + list(del_opts.keys()), key="pos_del_sel", label_visibility="collapsed")
    if dc2.button("🗑️ Delete", key="pos_del_btn"):
        if sel != "— select —":
            st.session_state[confirm_key] = del_opts[sel]
            st.rerun()

    if confirm_key in st.session_state:
        pid   = st.session_state[confirm_key]
        pname = next((f"{p.title} ({p.level})" for p in positions if p.id == pid), str(pid))
        st.warning(f"Delete **{pname}**? Remove any linked applications first.")
        ok1, ok2 = st.columns(2)
        if ok1.button("Confirm", key="pos_del_confirm", type="primary"):
            try:
                cache.delete_position(pid)
                st.session_state.pop(confirm_key, None)
                st.success("Position deleted.")
                st.rerun()
            except Exception as exc:
                st.error(f"Cannot delete: {exc}")
        if ok2.button("Cancel", key="pos_del_cancel"):
            st.session_state.pop(confirm_key, None)
            st.rerun()


# ── Recruiters ────────────────────────────────────────────────────────────────

def _recruiters_tab() -> None:
    recruiters      = cache.get_recruiters()
    companies       = cache.get_companies()
    companies_by_id = {c.id: c for c in companies}
    form_key        = "show_add_recruiter"

    _sub_header("recruiters", len(recruiters), form_key)

    if st.session_state.get(form_key, False):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        company_opts = {"— None —": None} | {c.name: c.id for c in companies}
        with st.form("add_recruiter_form", clear_on_submit=True):
            r1c1, r1c2 = st.columns(2)
            r2c1, r2c2 = st.columns(2)
            name        = r1c1.text_input("Name *", max_chars=50)
            email       = r1c2.text_input("Email",  max_chars=50)
            phone       = r2c1.text_input("Phone",  max_chars=50)
            company_sel = r2c2.selectbox("Company", list(company_opts.keys()))
            submitted   = st.form_submit_button("Add Recruiter", type="primary")

        if submitted:
            if not name.strip():
                st.error("Recruiter name is required.")
            else:
                try:
                    cache.create_recruiter(
                        name=name.strip(),
                        email=email.strip() or None,
                        phone=phone.strip() or None,
                        company_id=company_opts[company_sel],
                    )
                    st.success(f"Recruiter **{name.strip()}** added.")
                    st.session_state[form_key] = False
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if not recruiters:
        st.caption("No recruiters yet.")
        return

    confirm_key = "del_recruiter"
    rows_html = ""
    for r in recruiters:
        comp      = companies_by_id.get(r.company_id)
        comp_name = comp.name if comp else "—"
        rows_html += (
            f"<tr>"
            f"<td style='{_TD_SM}'>{r.id}</td>"
            f"<td style='{_TD}'>{r.name}</td>"
            f"<td style='{_TD_MUTED}'>{r.email or '—'}</td>"
            f"<td style='{_TD_MUTED}'>{comp_name}</td>"
            f"<td style='{_TD}'></td>"
            f"</tr>"
        )

    st.markdown(
        html_table(["ID", "Name", "Email", "Company", "Actions"], rows_html),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    del_opts = {f"#{r.id} — {r.name}": r.id for r in recruiters}
    dc1, dc2 = st.columns([3, 1])
    sel = dc1.selectbox("Select recruiter to delete", ["— select —"] + list(del_opts.keys()), key="rec_del_sel", label_visibility="collapsed")
    if dc2.button("🗑️ Delete", key="rec_del_btn"):
        if sel != "— select —":
            st.session_state[confirm_key] = del_opts[sel]
            st.rerun()

    if confirm_key in st.session_state:
        rid   = st.session_state[confirm_key]
        rname = next((r.name for r in recruiters if r.id == rid), str(rid))
        st.warning(f"Delete recruiter **{rname}**?")
        ok1, ok2 = st.columns(2)
        if ok1.button("Confirm", key="rec_del_confirm", type="primary"):
            try:
                cache.delete_recruiter(rid)
                st.session_state.pop(confirm_key, None)
                st.success("Recruiter deleted.")
                st.rerun()
            except Exception as exc:
                st.error(f"Cannot delete: {exc}")
        if ok2.button("Cancel", key="rec_del_cancel"):
            st.session_state.pop(confirm_key, None)
            st.rerun()


# ── entry point ───────────────────────────────────────────────────────────────

def render() -> None:
    section_header("Data", "Manage companies, positions, and recruiters")

    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    tab_co, tab_pos, tab_rec = st.tabs(["Companies", "Positions", "Recruiters"])
    with tab_co:  _companies_tab()
    with tab_pos: _positions_tab()
    with tab_rec: _recruiters_tab()
    st.markdown("</div>", unsafe_allow_html=True)
