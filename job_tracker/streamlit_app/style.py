"""CSS injection, shared HTML helpers, status badges, and visual constants."""

import streamlit as st

# ── Status colour map ────────────────────────────────────────────────────────
STATUS_COLORS: dict[str, dict[str, str]] = {
    "Applied":             {"bg": "#dbeafe", "text": "#1E90FF", "dot": "#1E90FF"},
    "Interview Scheduled": {"bg": "#fef3c7", "text": "#b45309", "dot": "#f0a500"},
    "Interviewed":         {"bg": "#ffe5cc", "text": "#c05800", "dot": "#FF7F00"},
    "Offer":               {"bg": "#d1fae5", "text": "#065f46", "dot": "#28a745"},
    "Accepted":            {"bg": "#bbf7d0", "text": "#155724", "dot": "#155724"},
    "Rejected":            {"bg": "#fee2e2", "text": "#991b1b", "dot": "#dc3545"},
    "Withdrawn":           {"bg": "#f3f4f6", "text": "#4b5563", "dot": "#6c757d"},
}
_FALLBACK = {"bg": "#f3f4f6", "text": "#4b5563", "dot": "#9ca3af"}


# ── HTML component helpers ────────────────────────────────────────────────────

def status_badge(status: str) -> str:
    c = STATUS_COLORS.get(status, _FALLBACK)
    return (
        f'<span style="background:{c["bg"]};color:{c["text"]};'
        f'padding:3px 10px;border-radius:20px;font-size:11.5px;font-weight:600;white-space:nowrap;">'
        f'{status}</span>'
    )


def job_id_display(value: str | None) -> str:
    """
    Return an HTML snippet for a job_id / URL value.
    If the value starts with http(s), render it as a clickable link that opens
    in a new tab.  Otherwise return the plain text (or '—' if empty).
    """
    if not value:
        return "—"
    if value.startswith("http://") or value.startswith("https://"):
        short = value.split("//", 1)[-1][:60] + ("…" if len(value) > 67 else "")
        return (
            f'<a href="{value}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#ff4b4b;font-weight:500;text-decoration:none;">'
            f'{short} &#x2197;</a>'
        )
    return value


def status_dot(status: str) -> str:
    c = STATUS_COLORS.get(status, _FALLBACK)
    return (
        f'<span style="display:inline-block;width:9px;height:9px;border-radius:50%;'
        f'background:{c["dot"]};margin-right:6px;vertical-align:middle;"></span>'
    )


def kpi_card(
    label: str,
    value,
    color: str = "#1a1a2e",
    border_color: str | None = None,
    subtitle: str | None = None,
) -> str:
    """Return an HTML KPI card matching the mockup design."""
    border = f"border-left:4px solid {border_color};" if border_color else ""
    sub    = f'<div style="font-size:12px;color:#6b7280;margin-top:4px;">{subtitle}</div>' if subtitle else ""
    return (
        f'<div style="background:#fff;border-radius:12px;'
        f'box-shadow:0 1px 4px rgba(0,0,0,0.07),0 4px 16px rgba(0,0,0,0.04);'
        f'padding:20px 22px;{border}">'
        f'<div style="font-size:12px;font-weight:600;color:#9ca3af;'
        f'text-transform:uppercase;letter-spacing:0.6px;margin-bottom:6px;">{label}</div>'
        f'<div style="font-size:34px;font-weight:800;color:{color};line-height:1;">{value}</div>'
        f'{sub}</div>'
    )


def section_header(title: str, subtitle: str = "") -> None:
    """Render a section heading + optional subheading matching the mockup."""
    sub_html = (
        f'<div style="font-size:13px;color:#6b7280;margin-bottom:20px;margin-top:-10px;">'
        f'{subtitle}</div>'
    ) if subtitle else ""
    st.markdown(
        f'<div style="font-size:17px;font-weight:700;color:#1a1a2e;margin-bottom:16px;">{title}</div>'
        f'{sub_html}',
        unsafe_allow_html=True,
    )


def html_bar_chart(
    rows: list[tuple[str, int, str]],
    max_val: int | None = None,
) -> str:
    """
    Return an HTML horizontal bar-chart string.

    rows: list of (label, count, hex_color)
    max_val: denominator for percentage (defaults to max count in rows)
    """
    top = max_val or max((r[1] for r in rows), default=1) or 1
    html = ""
    for label, count, color in rows:
        pct = min((count / top) * 100, 100)
        min_w = "4px" if count > 0 else "0"
        html += (
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
            f'<span style="font-size:12.5px;color:#374151;min-width:130px;font-weight:500;">{label}</span>'
            f'<div style="flex:1;background:#f3f4f6;border-radius:4px;height:18px;overflow:hidden;">'
            f'<div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:4px;'
            f'min-width:{min_w};"></div></div>'
            f'<span style="font-size:12px;color:#6b7280;min-width:20px;font-weight:600;'
            f'text-align:right;">{count}</span>'
            f'</div>'
        )
    return html


def html_funnel_chart(stages: list[tuple[str, float]]) -> str:
    """
    Return an HTML horizontal funnel chart string.

    stages: list of (label, percentage_0_to_100)
    """
    html = ""
    for label, pct in stages:
        min_w = "4px" if pct > 0 else "0"
        html += (
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
            f'<span style="font-size:12.5px;color:#374151;min-width:90px;font-weight:500;">{label}</span>'
            f'<div style="flex:1;background:#f3f4f6;border-radius:4px;height:18px;overflow:hidden;">'
            f'<div style="width:{pct:.1f}%;height:100%;border-radius:4px;min-width:{min_w};'
            f'background:linear-gradient(90deg,#1a1a2e,#ff4b4b);"></div></div>'
            f'<span style="font-size:12px;color:#6b7280;min-width:36px;font-weight:600;'
            f'text-align:right;">{pct:.0f}%</span>'
            f'</div>'
        )
    return html


def html_table(
    headers: list[str],
    rows_html: str,
    col_styles: list[str] | None = None,
) -> str:
    """Return a styled HTML table."""
    th_base = (
        "text-align:left;padding:10px 14px;font-size:11px;font-weight:700;"
        "text-transform:uppercase;letter-spacing:0.5px;color:#9ca3af;"
        "background:#f9fafb;border-bottom:1px solid #e5e7eb;"
    )
    ths = "".join(
        f'<th style="{th_base}{(col_styles[i] if col_styles and i < len(col_styles) else "")}">'
        f'{h}</th>'
        for i, h in enumerate(headers)
    )
    return (
        f'<table style="width:100%;border-collapse:collapse;font-size:13.5px;">'
        f'<thead><tr>{ths}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table>'
    )


# ── CSS injection ─────────────────────────────────────────────────────────────

def inject_css() -> None:
    st.markdown(
        """
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #f0f2f6; }
[data-testid="stHeader"]           { display: none; }
footer                              { display: none; }

/* ── Dark header bar ── */
.app-header {
    background: #1a1a2e;
    color: #fff;
    padding: 14px 28px 0;
    margin: -1rem -1rem 0 -1rem;
}
.app-header h1 {
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 12px;
    letter-spacing: 0.3px;
}

/* ── Tabs — light bar ── */
[data-testid="stTabs"] [role="tablist"] {
    background: #ffffff;
    margin: 0 -1rem;
    padding: 0 28px;
    gap: 0;
    border-bottom: 2px solid #e5e7eb;
}
[data-testid="stTabs"] button[role="tab"] {
    color: #6b7280 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    border-radius: 0 !important;
    border-bottom: 3px solid transparent !important;
    background: none !important;
    letter-spacing: 0.2px;
    white-space: nowrap;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: #1a1a2e !important;
    background: none !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #ff4b4b !important;
    border-bottom: 3px solid #ff4b4b !important;
    font-weight: 600 !important;
    background: none !important;
}
/* Remove the default Streamlit tab underline */
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-border"]    { display: none !important; }

/* ── Card wrapper ── */
.st-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.04);
    margin-bottom: 16px;
}
.card-title {
    font-size: 14px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f3f4f6;
}

/* ── Action items (dashboard) ── */
.action-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 8px;
}
.action-item.warn { background: #fff8e1; border-left: 3px solid #f0a500; }
.action-item.good { background: #f0fff4; border-left: 3px solid #28a745; }
.action-item.info { background: #fafafa; border-left: 3px solid #e5e7eb; }
.action-item-title { font-size: 13px; font-weight: 600; color: #374151; }
.action-item-desc  { font-size: 12px; color: #6b7280; margin-top: 2px; }

/* ── Timeline ── */
.timeline { list-style: none; padding-left: 16px; border-left: 2px solid #e5e7eb; margin: 0; }
.timeline li { position: relative; padding: 0 0 16px 18px; font-size: 13px; color: #374151; }
.timeline li:last-child { padding-bottom: 0; }
.timeline li::before {
    content: '';
    position: absolute;
    left: -7px; top: 5px;
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #ff4b4b;
    border: 2px solid #fff;
    box-shadow: 0 0 0 2px #ff4b4b;
}
.tl-date  { font-size: 11px; color: #9ca3af; font-weight: 600; margin-bottom: 2px; }
.tl-event { font-weight: 600; color: #1a1a2e; }
.tl-note  { color: #6b7280; font-size: 12.5px; margin-top: 2px; }

/* ── Detail panel ── */
.detail-panel {
    background: #f8faff;
    border: 1px solid #dbeafe;
    border-radius: 10px;
    padding: 18px 22px;
}
.detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-bottom: 14px;
}
.detail-field label {
    display: block;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #9ca3af;
    margin-bottom: 3px;
}
.detail-field span { font-size: 13.5px; color: #1a1a2e; font-weight: 500; }
.detail-notes {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 7px;
    padding: 10px 14px;
    font-size: 13px;
    color: #374151;
    margin-bottom: 14px;
    line-height: 1.5;
}
.detail-section-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #9ca3af;
    margin-bottom: 10px;
    margin-top: 14px;
}

/* ── Conversion stat cards (analytics) ── */
.conv-stat {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    padding: 14px 20px;
    flex: 1;
    min-width: 140px;
}
.conv-stat-label { font-size: 11.5px; color: #9ca3af; font-weight: 600; margin-bottom: 4px; }
.conv-stat-value { font-size: 26px; font-weight: 800; color: #ff4b4b; }
.conv-stat-desc  { font-size: 11px; color: #6b7280; margin-top: 2px; }

/* ── Form inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input {
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    font-size: 13.5px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stSelectbox"] > div > div:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #ff4b4b !important;
    box-shadow: 0 0 0 3px rgba(255,75,75,0.12) !important;
}

/* ── Buttons ── */
[data-testid="stFormSubmitButton"] button,
button[kind="primary"] {
    background: #ff4b4b !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* ── Section label (small uppercase) ── */
.section-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9ca3af;
    margin: 14px 0 8px;
}

/* ── App table rows ── */
.app-table-row {
    border-bottom: 1px solid #f3f4f6;
    padding: 2px 0;
}
.app-table-row:hover { background: #f0f4ff; border-radius: 6px; }
</style>
        """,
        unsafe_allow_html=True,
    )


def page_header() -> None:
    st.markdown(
        '<div class="app-header"><h1>📋 Application Tracker</h1></div>',
        unsafe_allow_html=True,
    )


def card(content_fn, title: str = "") -> None:
    title_html = f'<div class="card-title">{title}</div>' if title else ""
    st.markdown(f'<div class="st-card">{title_html}', unsafe_allow_html=True)
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)
