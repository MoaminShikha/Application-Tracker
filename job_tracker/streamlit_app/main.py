"""Application Tracker — Streamlit entry point.

Run with:
    streamlit run job_tracker/streamlit_app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# When launched via `streamlit run`, only the script's own directory is added to
# sys.path.  Insert the project root so that `import job_tracker` always resolves,
# regardless of whether the package was installed with `pip install -e .`.
_project_root = str(Path(__file__).parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

from job_tracker.streamlit_app.pages import (
    add_application,
    analytics,
    applications,
    dashboard,
    data,
)
from job_tracker.streamlit_app.style import inject_css, page_header

st.set_page_config(
    page_title="Application Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
page_header()

tab_dash, tab_apps, tab_add, tab_data, tab_analytics = st.tabs([
    "📊 Dashboard",
    "📋 Applications",
    "➕ Add Application",
    "🗄️ Data",
    "📈 Analytics",
])

with tab_dash:
    dashboard.render()

with tab_apps:
    applications.render()

with tab_add:
    add_application.render()

with tab_data:
    data.render()

with tab_analytics:
    analytics.render()
