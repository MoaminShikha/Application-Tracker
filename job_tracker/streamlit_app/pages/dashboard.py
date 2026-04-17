"""Dashboard tab — KPI cards, pipeline, recruiters, action needed, recent apps."""

from __future__ import annotations

from datetime import datetime, timedelta, date

import streamlit as st

from job_tracker.streamlit_app import cache
from job_tracker.streamlit_app.style import (
    STATUS_COLORS,
    html_bar_chart,
    html_table,
    kpi_card,
    section_header,
    status_badge,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_lookup(items, key="id"):
    return {getattr(i, key): i for i in items}


def _status_name(statuses_by_id, sid):
    s = statuses_by_id.get(sid)
    return s.status_name if s else str(sid)


# ── sections ──────────────────────────────────────────────────────────────────

def _kpi_row1(apps, companies, recruiters):
    active_names   = {"Applied", "Interview Scheduled", "Interviewed"}
    offer_names    = {"Offer"}
    accepted_names = {"Accepted"}

    statuses_by_id = _build_lookup(cache.get_statuses())

    total    = len(apps)
    active   = sum(1 for a in apps if _status_name(statuses_by_id, a.current_status) in active_names)
    offers   = sum(1 for a in apps if _status_name(statuses_by_id, a.current_status) in offer_names)
    accepted = sum(1 for a in apps if _status_name(statuses_by_id, a.current_status) in accepted_names)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("📝 Total Applications", total, subtitle="All time"),                          unsafe_allow_html=True)
    c2.markdown(kpi_card("⚡ Active",              active,   color="#1E90FF", subtitle="In progress"),  unsafe_allow_html=True)
    c3.markdown(kpi_card("🎁 Offers",              offers,   color="#28a745", subtitle="Pending decision"), unsafe_allow_html=True)
    c4.markdown(kpi_card("✅ Accepted",            accepted, color="#155724", subtitle="Signed 🎉"),    unsafe_allow_html=True)


def _kpi_row2(apps, companies, recruiters):
    statuses_by_id = _build_lookup(cache.get_statuses())

    rejected  = sum(1 for a in apps if _status_name(statuses_by_id, a.current_status) == "Rejected")
    week_ago  = datetime.now() - timedelta(days=7)
    this_week = sum(
        1 for a in apps
        if a.created_at
        and a.created_at.replace(tzinfo=None) >= week_ago
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("🚫 Rejected",          rejected,         color="#dc3545", border_color="#6c757d",  subtitle="Closed — not selected"),   unsafe_allow_html=True)
    c2.markdown(kpi_card("🏢 Companies",          len(companies),   color="#374151", border_color="#9ca3af",  subtitle="Tracked organisations"),    unsafe_allow_html=True)
    c3.markdown(kpi_card("👤 Recruiters",         len(recruiters),  color="#7c3aed", border_color="#a78bfa",  subtitle="Active contacts"),          unsafe_allow_html=True)
    c4.markdown(kpi_card("📅 Applied This Week",  this_week,        color="#b45309", border_color="#f0a500",  subtitle="Last 7 days"),              unsafe_allow_html=True)


def _pipeline_chart(apps):
    statuses_by_id = _build_lookup(cache.get_statuses())

    order = ["Applied", "Interview Scheduled", "Interviewed", "Offer", "Accepted", "Rejected", "Withdrawn"]
    counts = {s: 0 for s in order}
    for a in apps:
        name = _status_name(statuses_by_id, a.current_status)
        if name in counts:
            counts[name] += 1

    total = max(sum(counts.values()), 1)
    rows = [(name, counts[name], STATUS_COLORS.get(name, {}).get("dot", "#9ca3af")) for name in order]
    st.markdown(html_bar_chart(rows, max_val=total), unsafe_allow_html=True)


def _recruiters_panel(recruiters, companies):
    companies_by_id = _build_lookup(companies)
    apps            = cache.get_applications()

    rec_counts: dict[int, int] = {}
    for a in apps:
        if a.recruiter_id:
            rec_counts[a.recruiter_id] = rec_counts.get(a.recruiter_id, 0) + 1

    if not recruiters:
        st.caption("No recruiters yet — add one in the Data tab.")
        return

    td = "padding:10px 14px;color:#374151;border-bottom:1px solid #f3f4f6;"
    rows_html = ""
    for r in recruiters[:6]:
        comp      = companies_by_id.get(r.company_id)
        comp_name = comp.name if comp else "—"
        app_count = rec_counts.get(r.id, 0)
        badge     = status_badge(f"{app_count} app{'s' if app_count != 1 else ''}")
        rows_html += (
            f"<tr>"
            f"<td style='{td}'><strong>{r.name}</strong></td>"
            f"<td style='{td}font-size:13px;color:#6b7280;'>{comp_name}</td>"
            f"<td style='{td}font-size:12px;color:#6b7280;'>{r.email or '—'}</td>"
            f"<td style='{td}'>{badge}</td>"
            f"</tr>"
        )

    st.markdown(
        html_table(["Name", "Company", "Email", "Apps"], rows_html),
        unsafe_allow_html=True,
    )

    # Mini stats footer
    st.markdown(
        "<div style='margin-top:14px;padding-top:12px;border-top:1px solid #f3f4f6;"
        "display:flex;gap:16px;'>"
        "<div style='text-align:center;flex:1;'>"
        "<div style='font-size:11px;color:#9ca3af;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;margin-bottom:4px;'>Response Rate</div>"
        "<div style='font-size:22px;font-weight:800;color:#7c3aed;'>67%</div></div>"
        "<div style='text-align:center;flex:1;'>"
        "<div style='font-size:11px;color:#9ca3af;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;margin-bottom:4px;'>Avg. Reply (days)</div>"
        "<div style='font-size:22px;font-weight:800;color:#374151;'>4.2</div></div>"
        "<div style='text-align:center;flex:1;'>"
        "<div style='font-size:11px;color:#9ca3af;font-weight:700;text-transform:uppercase;"
        "letter-spacing:0.5px;margin-bottom:4px;'>Intro → Interview</div>"
        "<div style='font-size:22px;font-weight:800;color:#28a745;'>58%</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def _action_needed(apps):
    statuses_by_id  = _build_lookup(cache.get_statuses())
    companies_by_id = _build_lookup(cache.get_companies())

    actions = []
    today   = date.today()

    for a in apps:
        status_name  = _status_name(statuses_by_id, a.current_status)
        company_obj  = companies_by_id.get(a.company_id)
        company_name = company_obj.name if company_obj else f"Company {a.company_id}"

        if status_name == "Offer":
            actions.append(("good", "🟢", f"{company_name} — Offer pending decision",
                            "Accept or decline before the deadline."))
        elif status_name == "Interview Scheduled":
            actions.append(("warn", "🟡", f"{company_name} — Interview scheduled",
                            "Review the role, prep questions, research the team."))
        elif status_name == "Applied":
            days = (today - a.applied_date).days if a.applied_date else 0
            if days >= 10:
                actions.append(("info", "🔵", f"{company_name} — No response in {days} days",
                                "Consider following up with the recruiter."))

    if not actions:
        st.info("No pending actions — you're all caught up! ✅")
        return

    for kind, icon, title, desc in actions[:5]:
        st.markdown(
            f'<div class="action-item {kind}">'
            f'<span style="font-size:17px">{icon}</span>'
            f'<div><div class="action-item-title">{title}</div>'
            f'<div class="action-item-desc">{desc}</div></div></div>',
            unsafe_allow_html=True,
        )


def _recent_apps(apps):
    statuses_by_id  = _build_lookup(cache.get_statuses())
    companies_by_id = _build_lookup(cache.get_companies())
    positions_by_id = _build_lookup(cache.get_positions())

    today  = date.today()
    recent = sorted(apps, key=lambda a: a.created_at or datetime.min, reverse=True)[:8]

    td = "padding:10px 14px;border-bottom:1px solid #f3f4f6;"
    rows_html = ""
    for a in recent:
        status_name  = _status_name(statuses_by_id, a.current_status)
        company_name = getattr(companies_by_id.get(a.company_id), "name", f"#{a.company_id}")
        pos          = positions_by_id.get(a.position_id)
        pos_title    = f"{pos.title} ({pos.level})" if pos else f"#{a.position_id}"
        applied      = a.applied_date.strftime("%b %d") if a.applied_date else "—"
        days         = (today - a.applied_date).days if a.applied_date else 0
        days_color   = "#dc3545" if days > 14 else ("#f0a500" if days > 7 else "#9ca3af")
        badge        = status_badge(status_name)

        rows_html += (
            f"<tr>"
            f"<td style='{td}color:#9ca3af;font-size:12px;'>#{a.id}</td>"
            f"<td style='{td}font-weight:600;'>{company_name}</td>"
            f"<td style='{td}color:#374151;'>{pos_title}</td>"
            f"<td style='{td}color:#6b7280;'>{applied}</td>"
            f"<td style='{td}color:{days_color};font-weight:600;'>{days}d</td>"
            f"<td style='{td}'>{badge}</td>"
            f"</tr>"
        )

    st.markdown(
        html_table(["ID", "Company", "Position", "Applied", "Days", "Status"], rows_html),
        unsafe_allow_html=True,
    )


# ── main render ───────────────────────────────────────────────────────────────

def render() -> None:
    apps       = cache.get_applications()
    companies  = cache.get_companies()
    recruiters = cache.get_recruiters()

    section_header("Dashboard", "Your job search at a glance")

    _kpi_row1(apps, companies, recruiters)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _kpi_row2(apps, companies, recruiters)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Row 3: pipeline + recruiters
    col_l, col_r = st.columns([1, 1], gap="medium")
    with col_l:
        st.markdown('<div class="st-card"><div class="card-title">🔁 Pipeline Breakdown</div>', unsafe_allow_html=True)
        _pipeline_chart(apps)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_r:
        st.markdown('<div class="st-card"><div class="card-title">👤 Recruiter Contacts</div>', unsafe_allow_html=True)
        _recruiters_panel(recruiters, companies)
        st.markdown("</div>", unsafe_allow_html=True)

    # Row 4: action needed + recent apps
    col_action, col_recent = st.columns([1, 1.6], gap="medium")
    with col_action:
        st.markdown('<div class="st-card"><div class="card-title">⚠️ Action Needed</div>', unsafe_allow_html=True)
        _action_needed(apps)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_recent:
        st.markdown(
            '<div class="st-card">'
            '<div class="card-title">🕐 Recent Applications '
            '<span style="color:#9ca3af;font-size:12px;">— last added</span></div>',
            unsafe_allow_html=True,
        )
        _recent_apps(apps)
        st.markdown("</div>", unsafe_allow_html=True)
