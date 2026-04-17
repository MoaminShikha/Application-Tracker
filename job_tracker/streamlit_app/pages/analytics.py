"""Analytics tab — status distribution, conversion funnel, timeline, stats."""

from __future__ import annotations

from collections import Counter
from datetime import timedelta

import plotly.graph_objects as go
import streamlit as st

from job_tracker.streamlit_app import cache
from job_tracker.streamlit_app.style import (
    STATUS_COLORS,
    html_bar_chart,
    html_funnel_chart,
    kpi_card,
    section_header,
)


# ── chart helpers ─────────────────────────────────────────────────────────────

def _status_bar_chart(distribution: list) -> None:
    if not distribution:
        st.caption("No status data yet.")
        return
    max_count = max((r["count"] for r in distribution), default=1) or 1
    rows = [
        (r["status_name"], r["count"], STATUS_COLORS.get(r["status_name"], {}).get("dot", "#9ca3af"))
        for r in distribution
    ]
    st.markdown(html_bar_chart(rows, max_val=max_count), unsafe_allow_html=True)


def _conversion_funnel(conversion: dict) -> None:
    stages = [
        ("Applied",    100.0),
        ("Interviewed", conversion.get("application_to_interview_pct", 0.0)),
        ("Offered",     conversion.get("application_to_offer_pct",     0.0)),
        ("Accepted",    conversion.get("application_to_accept_pct",    0.0)),
    ]
    st.markdown(html_funnel_chart(stages), unsafe_allow_html=True)


def _conversion_stats(overview: dict, conversion: dict) -> None:
    total       = overview.get("total_applications", 0) or 1
    reached_int = round(total * conversion.get("application_to_interview_pct", 0) / 100)
    reached_off = round(total * conversion.get("application_to_offer_pct",     0) / 100)
    accepted    = overview.get("accepted", 0)
    offers      = overview.get("offers",   0)

    interview_pct = conversion.get("application_to_interview_pct", 0.0)
    offer_pct     = conversion.get("application_to_offer_pct",     0.0)
    accept_pct    = conversion.get("application_to_accept_pct",    0.0)
    offer_to_acc  = round((accepted / offers * 100), 1) if offers else 0.0

    stats = [
        ("Applied → Interview",  f"{interview_pct:.0f}%", f"{reached_int} of {total} advanced"),
        ("Interview → Offer",    f"{offer_pct:.0f}%",     f"{reached_off} of {reached_int} converted"),
        ("Offer → Accepted",     f"{offer_to_acc:.0f}%",  f"{accepted} of {offers} accepted so far"),
        ("Overall Success",      f"{accept_pct:.0f}%",    f"{accepted} accepted of {total} total"),
    ]

    cols = st.columns(4)
    for col, (label, value, desc) in zip(cols, stats):
        col.markdown(
            f'<div class="conv-stat">'
            f'<div class="conv-stat-label">{label}</div>'
            f'<div class="conv-stat-value">{value}</div>'
            f'<div class="conv-stat-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _timeline_chart(apps: list) -> None:
    """Vertical bar chart of applications per week using Plotly."""
    if not apps:
        st.caption("No application data yet.")
        return

    counts: Counter = Counter()
    for a in apps:
        if a.applied_date:
            week_start = a.applied_date - timedelta(days=a.applied_date.weekday())
            counts[week_start] += 1

    if not counts:
        st.caption("No applied dates recorded.")
        return

    all_weeks = sorted(counts.keys())
    if len(all_weeks) > 1:
        wk = all_weeks[0]
        while wk <= all_weeks[-1]:
            counts.setdefault(wk, 0)
            wk += timedelta(weeks=1)
        all_weeks = sorted(counts.keys())

    labels = [w.strftime("%b %d") for w in all_weeks]
    values = [counts[w] for w in all_weeks]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color="#ff4b4b",
        marker_opacity=0.82,
        hovertemplate="Week of %{x}: %{y} apps<extra></extra>",
        text=values,
        textposition="outside",
        textfont=dict(size=11, color="#374151"),
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=180,
        xaxis=dict(showgrid=False, tickfont=dict(size=10), tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", dtick=1, rangemode="tozero",
                   showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.35,
    )

    peak = max(values, default=0)
    peak_label = labels[values.index(peak)] if values else "—"

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;padding-top:8px;"
        f"border-top:1px solid #f3f4f6;font-size:12px;color:#9ca3af;'>"
        f"<span>{all_weeks[0].strftime('%b %Y') if all_weeks else '—'} – "
        f"{all_weeks[-1].strftime('%b %Y') if all_weeks else '—'}</span>"
        f"<span>Peak: {peak} apps/week ({peak_label})</span></div>",
        unsafe_allow_html=True,
    )


# ── main render ───────────────────────────────────────────────────────────────

def render() -> None:
    overview      = cache.get_analytics_overview()
    distribution  = cache.get_status_distribution()
    conversion    = cache.get_conversion_rates()
    apps          = cache.get_applications()

    section_header("Analytics", "Visualize your job search performance")

    # ── KPI row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(kpi_card("📝 Total",    overview.get("total_applications", 0)), unsafe_allow_html=True)
    c2.markdown(kpi_card("⚡ Active",   overview.get("active_applications", 0), color="#1E90FF"), unsafe_allow_html=True)
    c3.markdown(kpi_card("🎁 Offers",   overview.get("offers",   0), color="#28a745"), unsafe_allow_html=True)
    c4.markdown(kpi_card("✅ Accepted", overview.get("accepted", 0), color="#155724"), unsafe_allow_html=True)
    c5.markdown(kpi_card("🚫 Rejected", overview.get("rejected", 0), color="#dc3545"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Row 1: distribution + funnel ──────────────────────────────────────────
    col_l, col_r = st.columns([1, 1], gap="medium")

    with col_l:
        st.markdown('<div class="st-card"><div class="card-title">Status Distribution</div>', unsafe_allow_html=True)
        _status_bar_chart(distribution)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="st-card"><div class="card-title">Conversion Funnel</div>', unsafe_allow_html=True)
        _conversion_funnel(conversion)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Conversion stat cards ─────────────────────────────────────────────────
    _conversion_stats(overview, conversion)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Timeline ─────────────────────────────────────────────────────────────
    st.markdown('<div class="st-card"><div class="card-title">Applications Over Time</div>', unsafe_allow_html=True)
    _timeline_chart(apps)
    st.markdown("</div>", unsafe_allow_html=True)
