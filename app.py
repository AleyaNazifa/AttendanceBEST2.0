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

    # Colour ramp based on value
    base = alt.Chart(data).mark_bar(
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
    ).encode(
        x=alt.X(x_col, sort="-y", title="",
                axis=alt.Axis(labelColor="#64748b", tickColor="#1e2535", domainColor="#1e2535",
                              labelFont="Plus Jakarta Sans", labelFontSize=12)),
        y=alt.Y(y_col, title="Attendance %", scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelColor="#64748b", tickColor="#1e2535", domainColor="#1e2535",
                              gridColor="#1e2535", labelFont="Plus Jakarta Sans")),
        color=alt.condition(
            alt.datum.attendance_pct >= 90,
            alt.value("#22c55e"),
            alt.condition(
                alt.datum.attendance_pct >= 80,
                alt.value("#f59e0b"),
                alt.value("#ef4444"),
            ),
        ),
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
    <div style="margin-bottom: 8px;">
        <div style="font-size: 11px; font-weight: 700; letter-spacing: 2px;
                    color: #1d4ed8; text-transform: uppercase; margin-bottom: 6px;">
            PROGRAMME DASHBOARD
        </div>
        <h1 style="font-size: 2rem; margin: 0; padding: 0;">
            📊 BEST 2.0 Attendance Dashboard
        </h1>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Dashboard kehadiran ikut sekolah, subjek, dan tarikh")

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

# ── KPI metrics ───────────────────────────────────────────────────────────────
overall_present = filtered_df["present"].sum()
overall_total = filtered_df["total"].sum()
overall_pct = (overall_present / overall_total * 100) if overall_total else 0

pct_color = kpi_color(overall_pct)

col1, col2, col3 = st.columns(3)
col1.metric("👥 Jumlah Hadir", f"{int(overall_present):,}")
col2.metric("📋 Jumlah Direkod", f"{int(overall_total):,}")
col3.metric("📈 Overall Attendance", f"{overall_pct:.1f}%")

# Date context banner
if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
    label = f"📅 Paparan untuk tarikh: **{selected_single_date}**"
elif filter_mode == "Julat Tarikh" and selected_date_range:
    label = f"📅 Paparan untuk julat: **{start_date} hingga {end_date}**"
else:
    label = "📅 Paparan untuk: **semua tarikh**"

st.info(label)
st.divider()

# ── Summaries ─────────────────────────────────────────────────────────────────
summary_df = make_school_subject_summary(filtered_df)
daily_summary_df = make_daily_school_subject_summary(filtered_df)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏫  Sekolah", "📚  Subjek", "📅  Tarikh"])

# ─────────────── TAB 1: SEKOLAH ──────────────────────────────────────────────
with tab1:
    st.markdown("### 🏫 Sekolah Overview")

    pivot = summary_df.pivot(index="school", columns="subject", values="attendance_pct")
    for subject in ["BM", "BI", "MATH", "SEJ"]:
        if subject not in pivot.columns:
            pivot[subject] = pd.NA
    pivot = pivot[["BM", "BI", "MATH", "SEJ"]]
    pivot_display = pivot.copy()
    for col in pivot_display.columns:
        pivot_display[col] = pivot_display[col].map(
            lambda x: "—" if pd.isna(x) else f"{x:.1f}%"
        )
    st.dataframe(pivot_display, use_container_width=True)

    st.markdown("#### 📊 Overall Attendance by School")
    school_chart_df = (
        filtered_df.groupby("school", dropna=False)
        .agg(total_present=("present", "sum"), total_students=("total", "sum"))
        .reset_index()
    )
    school_chart_df["attendance_pct"] = (
        school_chart_df["total_present"] / school_chart_df["total_students"] * 100
    ).round(2)
    school_chart = build_bar_chart(
        school_chart_df, x_col="school:N", y_col="attendance_pct:Q", title="Attendance by School"
    )
    if school_chart is not None:
        st.altair_chart(school_chart, use_container_width=True)

    st.markdown("#### 🏫 School Breakdown")
    school_list = sorted(summary_df["school"].dropna().unique().tolist())

    for school in school_list:
        school_df = summary_df[summary_df["school"] == school].copy()

        # School header pill
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

# ─────────────── TAB 2: SUBJEK ───────────────────────────────────────────────
with tab2:
    st.markdown("### 📚 Subjek Overview")

    subject_summary = (
        filtered_df.groupby("subject", dropna=False)
        .agg(total_present=("present", "sum"), total_students=("total", "sum"))
        .reset_index()
    )
    subject_summary["attendance_pct"] = (
        subject_summary["total_present"] / subject_summary["total_students"] * 100
    ).round(2)
    st.dataframe(subject_summary, use_container_width=True)

    st.markdown("#### 📊 Attendance by Subject")
    subject_chart = build_bar_chart(
        subject_summary, x_col="subject:N", y_col="attendance_pct:Q", title="Attendance by Subject"
    )
    if subject_chart is not None:
        st.altair_chart(subject_chart, use_container_width=True)

    st.markdown("#### 📖 Subjek Breakdown")
    for subject in ["BM", "BI", "MATH", "SEJ"]:
        sub_df = filtered_df[filtered_df["subject"] == subject].copy()
        if sub_df.empty:
            continue

        total_present = sub_df["present"].sum()
        total_students = sub_df["total"].sum()
        pct = (total_present / total_students * 100) if total_students else None

        st.markdown(
            f"""
            <div style="
                display: inline-flex; align-items: center; gap: 10px;
                background: #1a2035; border: 1px solid #1e2d4a;
                border-radius: 12px; padding: 10px 18px; margin: 16px 0 8px;
            ">
                <span style="font-size: 18px;">📖</span>
                <span style="font-size: 15px; font-weight: 700; color: #e2e8f0;">{subject}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_subject_card(subject, pct, f"{int(total_present)}/{int(total_students)} hadir")

        by_school = (
            sub_df.groupby("school", dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        by_school["attendance_pct"] = (
            by_school["total_present"] / by_school["total_students"] * 100
        ).round(2)

        chart = build_bar_chart(
            by_school, x_col="school:N", y_col="attendance_pct:Q",
            title=f"{subject} Attendance by School"
        )
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)

        st.dataframe(by_school, use_container_width=True)
        st.divider()

# ─────────────── TAB 3: TARIKH ───────────────────────────────────────────────
with tab3:
    st.markdown("### 📅 Tarikh Overview")

    by_date = (
        df.groupby("date", dropna=False)
        .agg(total_present=("present", "sum"), total_students=("total", "sum"))
        .reset_index()
    )
    by_date["attendance_pct"] = (
        by_date["total_present"] / by_date["total_students"] * 100
    ).round(2)

    date_chart = build_bar_chart(
        by_date, x_col="date:T", y_col="attendance_pct:Q", title="Attendance by Date"
    )
    if date_chart is not None:
        st.altair_chart(date_chart, use_container_width=True)

    st.markdown("#### Breakdown Tarikh Semasa")

    if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
        selected_day_df = filtered_df.copy()
        st.markdown(f"##### Kehadiran pada {selected_single_date}")

        day_summary = (
            selected_day_df.groupby(["school", "subject"], dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        day_summary["attendance_pct"] = (
            day_summary["total_present"] / day_summary["total_students"] * 100
        ).round(2)
        st.dataframe(day_summary, use_container_width=True)

        st.markdown("##### 📊 Subject Attendance — Tarikh Dipilih")
        day_subject = (
            selected_day_df.groupby("subject", dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        day_subject["attendance_pct"] = (
            day_subject["total_present"] / day_subject["total_students"] * 100
        ).round(2)
        day_subject_chart = build_bar_chart(
            day_subject, x_col="subject:N", y_col="attendance_pct:Q",
            title=f"Attendance by Subject on {selected_single_date}"
        )
        if day_subject_chart is not None:
            st.altair_chart(day_subject_chart, use_container_width=True)

        st.markdown("##### 🏫 School Attendance — Tarikh Dipilih")
        day_school = (
            selected_day_df.groupby("school", dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        day_school["attendance_pct"] = (
            day_school["total_present"] / day_school["total_students"] * 100
        ).round(2)
        day_school_chart = build_bar_chart(
            day_school, x_col="school:N", y_col="attendance_pct:Q",
            title=f"Attendance by School on {selected_single_date}"
        )
        if day_school_chart is not None:
            st.altair_chart(day_school_chart, use_container_width=True)
    else:
        st.info("Pilih mode **Pilih Satu Tarikh** untuk tengok attendance pada hari itu sahaja.")

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
