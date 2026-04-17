"""Applications tab — filterable table, inline row expansion, status update, delete."""

from __future__ import annotations

from datetime import date

import streamlit as st

from job_tracker.services.status_service import ALLOWED_TRANSITIONS
from job_tracker.streamlit_app import cache
from job_tracker.streamlit_app.style import html_table, job_id_display, section_header, status_badge


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_lookup(items, key="id"):
    return {getattr(i, key): i for i in items}


# ── filter bar ────────────────────────────────────────────────────────────────

def _filters(companies, statuses):
    c1, c2, c3, c4 = st.columns([2.5, 2.5, 2, 2])

    company_opts = {"All Companies": None} | {c.name: c.id for c in companies}
    status_opts  = {"All Statuses": None}  | {s.status_name: s.id for s in statuses}
    sort_opts    = {
        "Created at":   "created_at",
        "Applied Date": "applied_date",
        "Status":       "current_status",
        "ID":           "id",
    }

    co_key  = c1.selectbox("Company",  list(company_opts.keys()), key="apps_co")
    st_key  = c2.selectbox("Status",   list(status_opts.keys()),  key="apps_st")
    so_key  = c3.selectbox("Sort By",  list(sort_opts.keys()),    key="apps_sort")
    dir_key = c4.selectbox("Order",    ["Newest first", "Oldest first"], key="apps_dir")

    return (
        company_opts[co_key],
        status_opts[st_key],
        sort_opts[so_key],
        "desc" if dir_key == "Newest first" else "asc",
    )


# ── table header (rendered once) ─────────────────────────────────────────────

_HDR_STYLE = (
    "font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;"
    "color:#9ca3af;padding:6px 4px;"
)

def _table_header():
    h1, h2, h3, h4, h5, h6 = st.columns([0.5, 2.2, 2.8, 1.3, 1.8, 0.5])
    h1.markdown(f"<div style='{_HDR_STYLE}'>ID</div>",          unsafe_allow_html=True)
    h2.markdown(f"<div style='{_HDR_STYLE}'>Company</div>",     unsafe_allow_html=True)
    h3.markdown(f"<div style='{_HDR_STYLE}'>Position</div>",    unsafe_allow_html=True)
    h4.markdown(f"<div style='{_HDR_STYLE}'>Applied</div>",     unsafe_allow_html=True)
    h5.markdown(f"<div style='{_HDR_STYLE}'>Status</div>",      unsafe_allow_html=True)
    h6.markdown(f"<div style='{_HDR_STYLE}'></div>",            unsafe_allow_html=True)
    st.markdown(
        "<hr style='margin:0;border:none;border-top:1px solid #e5e7eb;'>",
        unsafe_allow_html=True,
    )


# ── detail panel ─────────────────────────────────────────────────────────────

def _detail_panel(app, statuses, statuses_by_id, companies_by_id, positions_by_id, recruiters_by_id):
    current_status = statuses_by_id.get(app.current_status)
    current_name   = current_status.status_name if current_status else "Unknown"
    comp_name      = getattr(companies_by_id.get(app.company_id), "name", f"#{app.company_id}")
    pos            = positions_by_id.get(app.position_id)
    pos_label      = f"{pos.title} ({pos.level})" if pos else f"#{app.position_id}"
    recruiter      = recruiters_by_id.get(app.recruiter_id) if app.recruiter_id else None
    rec_label      = recruiter.name if recruiter else "—"
    applied_str    = app.applied_date.strftime("%b %d, %Y") if app.applied_date else "—"

    st.markdown(
        f'<div style="background:#f8faff;border:1px solid #dbeafe;border-radius:10px;'
        f'padding:18px 22px;margin:4px 0 12px 0;">',
        unsafe_allow_html=True,
    )

    col_meta, col_right = st.columns([1, 1], gap="medium")

    with col_meta:
        # 2-column field grid
        st.markdown(
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">'
            f'<div><div style="font-size:11px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.5px;color:#9ca3af;margin-bottom:3px;">Applied Date</div>'
            f'<div style="font-size:13.5px;color:#1a1a2e;font-weight:500;">{applied_str}</div></div>'
            f'<div><div style="font-size:11px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.5px;color:#9ca3af;margin-bottom:3px;">Recruiter</div>'
            f'<div style="font-size:13.5px;color:#1a1a2e;font-weight:500;">{rec_label}</div></div>'
            f'<div><div style="font-size:11px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.5px;color:#9ca3af;margin-bottom:3px;">Job ID / URL</div>'
            f'<div style="font-size:13.5px;color:#1a1a2e;font-weight:500;">{job_id_display(app.job_id)}</div></div>'
            f'<div><div style="font-size:11px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.5px;color:#9ca3af;margin-bottom:3px;">Position</div>'
            f'<div style="font-size:13.5px;color:#1a1a2e;font-weight:500;">{pos_label}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if app.notes:
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.5px;color:#9ca3af;margin-bottom:6px;">Notes</div>'
                f'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:7px;'
                f'padding:10px 14px;font-size:13px;color:#374151;line-height:1.5;">'
                f'{app.notes}</div>',
                unsafe_allow_html=True,
            )

    with col_right:
        # Status update
        allowed_next = sorted(ALLOWED_TRANSITIONS.get(current_name, set()))
        if allowed_next:
            st.markdown(
                '<div style="font-size:12px;font-weight:600;color:#6b7280;margin-bottom:6px;">'
                'Update Status:</div>',
                unsafe_allow_html=True,
            )
            status_name_to_id = {s.status_name: s.id for s in statuses}
            with st.form(f"status_form_{app.id}", clear_on_submit=True):
                uc1, uc2 = st.columns([2, 1])
                new_name = uc1.selectbox(
                    "New status", allowed_next,
                    label_visibility="collapsed",
                    key=f"status_sel_{app.id}",
                )
                if uc2.form_submit_button("Update", type="primary", use_container_width=True):
                    new_id = status_name_to_id.get(new_name)
                    if new_id:
                        try:
                            cache.update_application_status(app.id, new_id)
                            st.success(f"→ {new_name}")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
        else:
            st.info(f"**{current_name}** is a terminal state.")

        # Timeline
        st.markdown(
            '<div style="font-size:12px;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.5px;color:#9ca3af;margin:14px 0 10px;">Timeline</div>',
            unsafe_allow_html=True,
        )
        events = cache.get_events(app.id)
        if events:
            items_html = ""
            for ev in reversed(events):
                d    = ev.event_date.strftime("%b %d, %Y  %H:%M") if ev.event_date else "—"
                note = f'<div class="tl-note">{ev.notes}</div>' if ev.notes else ""
                items_html += (
                    f"<li><div class='tl-date'>{d}</div>"
                    f"<div class='tl-event'>{ev.event_type}</div>{note}</li>"
                )
            st.markdown(f'<ul class="timeline">{items_html}</ul>', unsafe_allow_html=True)
        else:
            st.caption("No events yet.")

        # Delete
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        confirm_key = "apps_confirm_delete"
        if st.session_state.get(confirm_key) == app.id:
            st.warning(f"Delete application #{app.id}? **Cannot be undone.**")
            dc1, dc2 = st.columns(2)
            if dc1.button("Confirm Delete", type="primary", key=f"del_confirm_{app.id}"):
                try:
                    cache.delete_application(app.id)
                    st.session_state.pop(confirm_key, None)
                    st.session_state.pop("view_app", None)
                    st.success("Deleted.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if dc2.button("Cancel", key=f"del_cancel_{app.id}"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
        else:
            if st.button("🗑️ Delete", key=f"del_btn_{app.id}"):
                st.session_state[confirm_key] = app.id
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ── main render ───────────────────────────────────────────────────────────────

def render() -> None:
    companies  = cache.get_companies()
    statuses   = cache.get_statuses()
    positions  = cache.get_positions()
    recruiters = cache.get_recruiters()

    statuses_by_id   = _build_lookup(statuses)
    companies_by_id  = _build_lookup(companies)
    positions_by_id  = _build_lookup(positions)
    recruiters_by_id = _build_lookup(recruiters)

    section_header("Applications", "Browse, filter, and manage all your applications")

    company_id, status_id, sort_by, sort_dir = _filters(companies, statuses)

    apps = cache.get_applications(
        company_id=company_id,
        status_id=status_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if not apps:
        st.info("No applications match the current filters.")
        return

    st.markdown(
        f'<span style="font-size:13px;color:#9ca3af;">'
        f'{len(apps)} application{"s" if len(apps) != 1 else ""}</span>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Card wrapper + table header
    st.markdown('<div class="st-card" style="padding:0;overflow:hidden;">', unsafe_allow_html=True)

    # Column headers
    st.markdown("<div style='padding:0 18px;'>", unsafe_allow_html=True)
    _table_header()
    st.markdown("</div>", unsafe_allow_html=True)

    # Rows
    today = date.today()
    view_key = "view_app"
    for a in apps:
        status_obj   = statuses_by_id.get(a.current_status)
        status_name  = status_obj.status_name if status_obj else "—"
        comp_name    = getattr(companies_by_id.get(a.company_id), "name", f"#{a.company_id}")
        pos          = positions_by_id.get(a.position_id)
        pos_label    = f"{pos.title} ({pos.level})" if pos else f"#{a.position_id}"
        applied_str  = a.applied_date.strftime("%b %d, %Y") if a.applied_date else "—"
        is_open      = st.session_state.get(view_key) == a.id

        row_bg = "background:#eef2ff;border-left:3px solid #6366f1;" if is_open else "border-left:3px solid transparent;"
        st.markdown(
            f"<div style='padding:0 18px 0 15px;border-bottom:1px solid #f3f4f6;{row_bg}'>",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2.2, 2.8, 1.3, 1.8, 0.5])
        c1.markdown(
            f"<div style='color:#9ca3af;font-size:12px;padding:8px 0;'>#{a.id}</div>",
            unsafe_allow_html=True,
        )
        c2.markdown(
            f"<div style='font-weight:600;color:#111827;padding:8px 0;'>{comp_name}</div>",
            unsafe_allow_html=True,
        )
        c3.markdown(
            f"<div style='color:#374151;padding:8px 0;font-size:13px;'>{pos_label}</div>",
            unsafe_allow_html=True,
        )
        c4.markdown(
            f"<div style='color:#6b7280;padding:8px 0;font-size:13px;'>{applied_str}</div>",
            unsafe_allow_html=True,
        )
        c5.markdown(
            f"<div style='padding:6px 0;'>{status_badge(status_name)}</div>",
            unsafe_allow_html=True,
        )

        arrow = "↓" if is_open else "→"
        btn_style = "color:#ff4b4b;" if is_open else ""
        # Use a tiny styled button
        if c6.button(arrow, key=f"view_btn_{a.id}", help="View / hide details"):
            st.session_state[view_key] = None if is_open else a.id
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        if is_open:
            st.markdown("<div style='padding:0 18px;'>", unsafe_allow_html=True)
            _detail_panel(
                a, statuses, statuses_by_id,
                companies_by_id, positions_by_id, recruiters_by_id,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # /st-card
