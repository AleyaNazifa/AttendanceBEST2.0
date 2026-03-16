from pathlib import Path
import subprocess
import sys
import pandas as pd
import streamlit as st
import altair as alt


st.set_page_config(
    page_title="BEST 2.0 Attendance Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* ── Page background ── */
    .stApp {
        background: #0f1117;
        color: #e2e8f0;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #161b27 !important;
        border-right: 1px solid #1e2535;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] p {
        color: #94a3b8 !important;
        font-size: 13px;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #e2e8f0 !important;
    }

    /* ── Headings ── */
    h1 { color: #f1f5f9 !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    h2, h3, h4 { color: #e2e8f0 !important; font-weight: 700 !important; }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: #1a2035;
        border: 1px solid #1e2d4a;
        border-radius: 16px;
        padding: 20px 24px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #161b27;
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #1e2535;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 9px;
        color: #64748b !important;
        font-weight: 600;
        font-size: 13px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #1d4ed8 !important;
        color: #fff !important;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #1e2535 !important;
    }

    /* ── Info / warning banners ── */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        font-size: 13px;
    }

    /* ── Divider ── */
    hr { border-color: #1e2535 !important; margin: 24px 0 !important; }

    /* ── Expander ── */
    [data-testid="stExpander"] {
        background: #161b27;
        border: 1px solid #1e2535 !important;
        border-radius: 12px !important;
    }

    /* ── Caption ── */
    .stCaption { color: #475569 !important; font-size: 12px; }

    /* ── Multiselect tags — kill the red, go subtle blue-grey ── */
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: #1e2d4a !important;
        border: 1px solid #2d4a7a !important;
        border-radius: 6px !important;
        color: #93c5fd !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 2px 8px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tag"] span {
        color: #93c5fd !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tag"] [role="presentation"] svg {
        fill: #60a5fa !important;
    }

    /* ── Multiselect container box ── */
    [data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
        background: #0f1520 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div:first-child:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
    }

    /* ── Selectbox (Pilih Tarikh) ── */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
        background: #0f1520 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-size: 13px !important;
    }

    /* ── Section labels in sidebar ── */
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio > label {
        color: #64748b !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }

    /* ── Date input ── */
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
        background: #0f1520 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
        font-size: 13px !important;
    }

    /* ── Dropdown popup ── */
    [data-baseweb="popover"] [data-baseweb="menu"] {
        background: #161b27 !important;
        border: 1px solid #1e2d4a !important;
        border-radius: 10px !important;
    }
    [data-baseweb="popover"] [role="option"] {
        color: #cbd5e1 !important;
        font-size: 13px !important;
    }
    [data-baseweb="popover"] [role="option"]:hover,
    [data-baseweb="popover"] [aria-selected="true"] {
        background: #1e2d4a !important;
        color: #93c5fd !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

CLEANED_FILE = Path("output/cleaned_sessions.csv")


def ensure_cleaned_data():
    if not CLEANED_FILE.exists():
        subprocess.run([sys.executable, "clean_attendance.py"], check=True)


@st.cache_data
def load_data():
    ensure_cleaned_data()
    if not CLEANED_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(CLEANED_FILE)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    for col in ["present", "total", "attendance_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def kpi_color(value):
    if pd.isna(value):
        return "#475569"
    if value >= 90:
        return "#22c55e"
    if value >= 80:
        return "#f59e0b"
    return "#ef4444"


def kpi_bg(value):
    if pd.isna(value):
        return "#1a2035"
    if value >= 90:
        return "#052e16"
    if value >= 80:
        return "#1c1204"
    return "#1f0707"


def kpi_border(value):
    if pd.isna(value):
        return "#1e2535"
    if value >= 90:
        return "#166534"
    if value >= 80:
        return "#92400e"
    return "#991b1b"


def kpi_badge(value):
    if pd.isna(value):
        return "NO DATA", "#1e2535", "#475569"
    if value >= 90:
        return "✓ KPI MET", "#052e16", "#22c55e"
    if value >= 80:
        return "~ MODERATE", "#1c1204", "#f59e0b"
    return "✗ BELOW KPI", "#1f0707", "#ef4444"


def render_subject_card(subject, pct, present_total_text):
    color = kpi_color(pct)
    bg = kpi_bg(pct)
    border = kpi_border(pct)
    badge_text, badge_bg, badge_color = kpi_badge(pct)
    pct_display = "—" if pd.isna(pct) else f"{pct:.1f}%"

    st.markdown(
        f"""
        <div style="
            border: 1px solid {border};
            border-radius: 16px;
            padding: 18px 20px;
            background: {bg};
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            margin-bottom: 12px;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute; top: 0; right: 0;
                width: 80px; height: 80px;
                background: {color}08;
                border-radius: 0 16px 0 80px;
            "></div>
            <div style="
                font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
                color: {badge_color}; background: {badge_bg};
                border: 1px solid {border};
                display: inline-block; padding: 2px 8px; border-radius: 20px;
                margin-bottom: 10px;
            ">{badge_text}</div>
            <div style="font-size: 12px; color: #64748b; font-weight: 600;
                        text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">
                {subject}
            </div>
            <div style="font-size: 32px; font-weight: 800; color: {color};
                        font-family: 'JetBrains Mono', monospace; line-height: 1.1;">
                {pct_display}
            </div>
            <div style="font-size: 12px; color: #475569; margin-top: 8px; font-weight: 500;">
                {present_total_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def make_school_subject_summary(df):
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby(["school", "subject"], dropna=False)
        .agg(
            total_present=("present", "sum"),
            total_students=("total", "sum"),
            sessions=("date", "count"),
        )
        .reset_index()
    )
    summary["attendance_pct"] = (
        summary["total_present"] / summary["total_students"] * 100
    ).round(2)
    return summary.sort_values(["school", "subject"]).reset_index(drop=True)


def make_daily_school_subject_summary(df):
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby(["date", "school", "subject"], dropna=False)
        .agg(
            total_present=("present", "sum"),
            total_students=("total", "sum"),
            sessions=("date", "count"),
        )
        .reset_index()
    )
    summary["attendance_pct"] = (
        summary["total_present"] / summary["total_students"] * 100
    ).round(2)
    return summary.sort_values(["date", "school", "subject"]).reset_index(drop=True)


# ── Altair dark theme chart builder ─────────────────────────────────────────
def build_bar_chart(data, x_col, y_col, color_col=None, title=""):
    if data.empty:
        return None

    # Add a colour category column so we avoid nested alt.condition (unsupported)
    chart_data = data.copy()
    chart_data["_color"] = chart_data["attendance_pct"].apply(
        lambda v: "≥90%" if v >= 90 else ("80–89%" if v >= 80 else "<80%")
    )

    color_scale = alt.Scale(
        domain=["≥90%", "80–89%", "<80%"],
        range=["#22c55e", "#f59e0b", "#ef4444"],
    )

    base = alt.Chart(chart_data).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
    ).encode(
        x=alt.X(x_col, sort="-y", title="",
                axis=alt.Axis(labelColor="#64748b", tickColor="#1e2535", domainColor="#1e2535",
                              labelFont="Plus Jakarta Sans", labelFontSize=12)),
        y=alt.Y(y_col, title="Attendance %", scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelColor="#64748b", tickColor="#1e2535", domainColor="#1e2535",
                              gridColor="#1e2535", labelFont="Plus Jakarta Sans")),
        color=alt.Color("_color:N", scale=color_scale, legend=None),
        tooltip=list(data.columns),
    ).properties(
        title=alt.TitleParams(
            title,
            color="#94a3b8",
            font="Plus Jakarta Sans",
            fontSize=14,
            fontWeight=600,
        ),
        height=320,
        background="#161b27",
        padding={"left": 16, "right": 16, "top": 16, "bottom": 8},
    ).configure_view(
        strokeWidth=0,
    )

    return base


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="margin-bottom: 24px;">
        <div style="font-size: 11px; font-weight: 700; letter-spacing: 2px;
                    color: #1d4ed8; text-transform: uppercase; margin-bottom: 6px;">
            PROGRAMME DASHBOARD
        </div>
        <h1 style="font-size: 2rem; margin: 0; padding: 0;">
            🏫 BEST 2.0 — School Breakdown
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

df = load_data()

if df.empty:
    st.warning("Tiada cleaned data dijumpai. Semak CSV dan script cleaning.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    "<div style='font-size:11px;letter-spacing:2px;font-weight:700;"
    "color:#1d4ed8;text-transform:uppercase;margin-bottom:16px;'>FILTERS</div>",
    unsafe_allow_html=True,
)

available_dates = sorted([d for d in df["date"].dropna().unique().tolist()])
schools = sorted([s for s in df["school"].dropna().unique().tolist() if str(s).strip()])
subjects = sorted([s for s in df["subject"].dropna().unique().tolist() if str(s).strip()])
sessions = sorted([s for s in df["session"].dropna().unique().tolist() if str(s).strip()])

filter_mode = st.sidebar.radio(
    "Mode Tarikh",
    ["Semua Tarikh", "Pilih Satu Tarikh", "Julat Tarikh"],
    index=1,
)

selected_single_date = None
selected_date_range = None

if filter_mode == "Pilih Satu Tarikh":
    selected_single_date = st.sidebar.selectbox(
        "Pilih Tarikh",
        options=available_dates,
        index=len(available_dates) - 1 if available_dates else 0,
    )
elif filter_mode == "Julat Tarikh":
    min_date = min(available_dates)
    max_date = max(available_dates)
    selected_date_range = st.sidebar.date_input(
        "Julat Tarikh",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

st.sidebar.markdown("<hr style='border-color:#1e2535;margin:12px 0;'>", unsafe_allow_html=True)
selected_schools = st.sidebar.multiselect("Sekolah", schools, default=schools)
selected_subjects = st.sidebar.multiselect("Subjek", subjects, default=subjects)
selected_sessions = st.sidebar.multiselect("Sesi", sessions, default=sessions)

# ── Filter logic ─────────────────────────────────────────────────────────────
filtered_df = df.copy()

if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
    filtered_df = filtered_df[filtered_df["date"] == selected_single_date]
elif filter_mode == "Julat Tarikh" and selected_date_range:
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        filtered_df = filtered_df[
            (filtered_df["date"] >= start_date) & (filtered_df["date"] <= end_date)
        ]

if selected_schools:
    filtered_df = filtered_df[filtered_df["school"].isin(selected_schools)]
if selected_subjects:
    filtered_df = filtered_df[filtered_df["subject"].isin(selected_subjects)]
if selected_sessions:
    filtered_df = filtered_df[filtered_df["session"].isin(selected_sessions)]

if filtered_df.empty:
    st.info("Tiada data untuk filter yang dipilih.")
    st.stop()

# ── Summaries ─────────────────────────────────────────────────────────────────
summary_df = make_school_subject_summary(filtered_df)

# Date context pill
if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
    date_label = f"📅 {selected_single_date}"
elif filter_mode == "Julat Tarikh" and selected_date_range:
    date_label = f"📅 {start_date} — {end_date}"
else:
    date_label = "📅 Semua Tarikh"

st.markdown(
    f"""
    <div style="display:inline-block; background:#1e2d4a; border:1px solid #2d4a7a;
                border-radius:20px; padding:5px 14px; font-size:12px; font-weight:600;
                color:#93c5fd; margin-bottom:24px;">
        {date_label}
    </div>
    """,
    unsafe_allow_html=True,
)

# ── School Breakdown ──────────────────────────────────────────────────────────
school_list = sorted(summary_df["school"].dropna().unique().tolist())

for school in school_list:
    school_df = summary_df[summary_df["school"] == school].copy()

    st.markdown(
        f"""
        <div style="
            display: inline-flex; align-items: center; gap: 10px;
            background: #1a2035; border: 1px solid #1e2d4a;
            border-radius: 12px; padding: 10px 18px; margin: 16px 0 12px;
        ">
            <span style="font-size: 18px;">🏫</span>
            <span style="font-size: 15px; font-weight: 700; color: #e2e8f0;">{school}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    wanted_subjects = ["BM", "BI", "MATH", "SEJ"]
    subject_map = {row["subject"]: row for _, row in school_df.iterrows()}
    cols = st.columns(4)

    for i, subject in enumerate(wanted_subjects):
        row = subject_map.get(subject)
        if row is not None:
            pct = row["attendance_pct"]
            pt_text = f'{int(row["total_present"])}/{int(row["total_students"])} hadir'
        else:
            pct = None
            pt_text = "Tiada data"
        with cols[i]:
            render_subject_card(subject, pct, pt_text)

    with st.expander(f"📋 Lihat rekod sesi untuk {school}"):
        school_sessions = filtered_df[filtered_df["school"] == school].copy()
        display_cols = [
            "date", "subject", "session", "teacher_name",
            "present", "total", "attendance_pct", "attendance_source",
            "attendance_text_raw", "absent_text_raw", "mastery_level",
            "engagement_level", "objective_achieved", "challenge",
        ]
        existing_cols = [c for c in display_cols if c in school_sessions.columns]
        school_sessions = school_sessions[existing_cols].sort_values(
            ["date", "subject", "session"], ascending=[False, True, True]
        )
        st.dataframe(school_sessions, use_container_width=True)

    st.divider()

# ── Below KPI section ─────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="font-size:22px;">⚠️</span>
        <span style="font-size:18px;font-weight:700;color:#f87171;">
            Subject Below KPI 90%
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

low_kpi = summary_df[summary_df["attendance_pct"] < 90].copy()
low_kpi = low_kpi.sort_values(["attendance_pct", "school", "subject"])

if low_kpi.empty:
    st.success("✅ Semua subject yang ada data capai KPI 90% ke atas.")
else:
    st.dataframe(
        low_kpi[["school", "subject", "attendance_pct", "total_present", "total_students", "sessions"]],
        use_container_width=True,
    )

with st.expander("🔍 Show cleaned raw data"):
    st.dataframe(filtered_df, use_container_width=True)
