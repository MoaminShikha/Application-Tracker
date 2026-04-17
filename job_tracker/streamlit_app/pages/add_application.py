"""Add Application page — guided form with inline entity creation."""

from __future__ import annotations

from datetime import date

import streamlit as st

from job_tracker.models.position import VALID_LEVELS
from job_tracker.streamlit_app import cache
from job_tracker.streamlit_app.style import section_header


# ── inline creation forms ─────────────────────────────────────────────────────

def _add_company_form() -> None:
    with st.form("inline_co_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name     = c1.text_input("Name *",    max_chars=50)
        industry = c2.text_input("Industry",  max_chars=50)
        c3, _    = st.columns(2)
        location = c3.text_input("Location",  max_chars=50)
        ok       = st.form_submit_button("Add Company", type="primary")
    if ok:
        if not name.strip():
            st.error("Name is required.")
        else:
            try:
                co = cache.create_company(
                    name=name.strip(),
                    industry=industry.strip() or None,
                    location=location.strip() or None,
                    notes=None,
                )
                st.session_state["_presel_co"]  = co.name
                st.session_state["_show_add_co"] = False
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _add_position_form() -> None:
    with st.form("inline_pos_form", clear_on_submit=True):
        p1, p2 = st.columns(2)
        title = p1.text_input("Title *", max_chars=50)
        level = p2.selectbox("Level *", sorted(VALID_LEVELS))
        ok    = st.form_submit_button("Add Position", type="primary")
    if ok:
        if not title.strip():
            st.error("Title is required.")
        else:
            try:
                pos = cache.create_position(title=title.strip(), level=level)
                st.session_state["_presel_pos"]  = f"{pos.title} ({pos.level})"
                st.session_state["_show_add_pos"] = False
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _add_recruiter_form(companies) -> None:
    company_opts = {"— None —": None} | {c.name: c.id for c in companies}
    with st.form("inline_rec_form", clear_on_submit=True):
        r1, r2 = st.columns(2)
        r3, r4 = st.columns(2)
        name        = r1.text_input("Name *", max_chars=50)
        email       = r2.text_input("Email",  max_chars=50)
        phone       = r3.text_input("Phone",  max_chars=50)
        company_sel = r4.selectbox("Company", list(company_opts.keys()))
        ok          = st.form_submit_button("Add Recruiter", type="primary")
    if ok:
        if not name.strip():
            st.error("Name is required.")
        else:
            try:
                rec = cache.create_recruiter(
                    name=name.strip(),
                    email=email.strip() or None,
                    phone=phone.strip() or None,
                    company_id=company_opts[company_sel],
                )
                st.session_state["_presel_rec"]  = rec.name
                st.session_state["_show_add_rec"] = False
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


# ── selector row helper ───────────────────────────────────────────────────────

_LABEL_CSS = (
    "font-size:12px;font-weight:700;text-transform:uppercase;"
    "letter-spacing:0.5px;color:#6b7280;margin-bottom:4px;"
)

def _selector_row(label, options, presel_key, toggle_key, widget_key, add_btn_label="+ New"):
    """
    Render a labelled selectbox with a '+ New' button beside it.
    Returns the currently selected option string.
    """
    names   = list(options.keys()) if options else []
    presel  = st.session_state.pop(presel_key, None)
    idx     = names.index(presel) if presel and presel in names else 0

    st.markdown(f"<div style='{_LABEL_CSS}'>{label}</div>", unsafe_allow_html=True)
    sel_col, btn_col = st.columns([5, 1])
    selected = sel_col.selectbox(
        label, names or ["— none —"],
        index=idx,
        label_visibility="collapsed",
        key=widget_key,
        disabled=not names,
    )
    if btn_col.button(add_btn_label, key=f"btn_{toggle_key}", use_container_width=True):
        st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
        st.rerun()

    return selected


def _inline_card(content_fn, title: str) -> None:
    st.markdown(
        f"<div style='background:#f8faff;border:1px solid #dbeafe;border-radius:8px;"
        f"padding:14px 18px;margin:6px 0 10px;'>"
        f"<div style='font-size:13px;font-weight:600;color:#374151;margin-bottom:10px;'>{title}</div>",
        unsafe_allow_html=True,
    )
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)


# ── main render ───────────────────────────────────────────────────────────────

def render() -> None:
    companies  = cache.get_companies()
    positions  = cache.get_positions()
    recruiters = cache.get_recruiters()

    section_header("Add Application", "Log a new job application")

    st.markdown('<div class="st-card" style="max-width:740px;">', unsafe_allow_html=True)

    company_opts   = {c.name: c.id for c in companies}
    position_opts  = {f"{p.title} ({p.level})": p.id for p in positions}
    recruiter_opts = {"— No recruiter —": None} | {r.name: r.id for r in recruiters}

    # ── Company ───────────────────────────────────────────────────────────────
    company_sel = _selector_row(
        "Company *", company_opts,
        presel_key="_presel_co", toggle_key="_show_add_co",
        widget_key="app_co_sel",
    )
    if st.session_state.get("_show_add_co"):
        _inline_card(lambda: _add_company_form(), "New Company")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Position ──────────────────────────────────────────────────────────────
    position_sel = _selector_row(
        "Position *", position_opts,
        presel_key="_presel_pos", toggle_key="_show_add_pos",
        widget_key="app_pos_sel",
    )
    if st.session_state.get("_show_add_pos"):
        _inline_card(lambda: _add_position_form(), "New Position")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Recruiter ─────────────────────────────────────────────────────────────
    recruiter_sel = _selector_row(
        "Recruiter", recruiter_opts,
        presel_key="_presel_rec", toggle_key="_show_add_rec",
        widget_key="app_rec_sel",
        add_btn_label="+ New",
    )
    if st.session_state.get("_show_add_rec"):
        _inline_card(lambda: _add_recruiter_form(companies), "New Recruiter")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Applied date, Job ID, Notes + submit ──────────────────────────────────
    with st.form("add_application_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2)
        applied_date = fc1.date_input(
            "Applied Date *", value=date.today(), max_value=date.today()
        )
        job_id = fc2.text_input(
            "Job ID / URL",
            placeholder="e.g. REF-001 or https://linkedin.com/jobs/…",
            max_chars=2048,
        )
        notes = st.text_area(
            "Notes",
            placeholder="Referrals, role details, prep reminders…  (optional)",
            max_chars=255,
        )
        st.markdown(
            "<hr style='border:none;border-top:1px solid #e5e7eb;margin:14px 0 4px;'>",
            unsafe_allow_html=True,
        )
        submitted = st.form_submit_button(
            "Submit Application", type="primary", use_container_width=True
        )

    if submitted:
        if not company_opts:
            st.error("Add a company first (click **+ New** above).")
        elif not position_opts:
            st.error("Add a position first (click **+ New** above).")
        else:
            try:
                app = cache.create_application(
                    company_id=company_opts[company_sel],
                    position_id=position_opts[position_sel],
                    applied_date=applied_date,
                    recruiter_id=recruiter_opts[recruiter_sel],
                    job_id=job_id.strip() or None,
                    notes=notes.strip() or None,
                )
                st.success(
                    f"✅ Application **#{app.id}** added — **{company_sel}** · {position_sel}"
                )
            except Exception as exc:
                st.error(f"Failed to create application: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)
