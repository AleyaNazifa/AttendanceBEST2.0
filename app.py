from pathlib import Path
import subprocess
import sys
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="BEST 2.0 Attendance Dashboard",
    page_icon="📊",
    layout="wide",
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
        return "#9CA3AF"
    if value >= 90:
        return "#16A34A"
    if value >= 80:
        return "#F59E0B"
    return "#DC2626"


def render_subject_card(subject, pct, present_total_text):
    color = kpi_color(pct)
    pct_display = "-" if pd.isna(pct) else f"{pct:.1f}%"

    st.markdown(
        f"""
        <div style="
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 16px;
            background: white;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
            margin-bottom: 12px;
        ">
            <div style="font-size: 14px; color: #6b7280; margin-bottom: 8px;">
                {subject}
            </div>
            <div style="font-size: 30px; font-weight: 700; color: {color};">
                {pct_display}
            </div>
            <div style="font-size: 13px; color: #6b7280; margin-top: 6px;">
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


st.title("📊 BEST 2.0 Attendance Dashboard")
st.caption("Dashboard kehadiran ikut sekolah dan subjek")

df = load_data()

if df.empty:
    st.warning("Tiada cleaned data dijumpai. Semak CSV dan script cleaning.")
    st.stop()

st.sidebar.header("Filters")

min_date = df["date"].min()
max_date = df["date"].max()

selected_date_range = st.sidebar.date_input(
    "Tarikh",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
else:
    start_date = min_date
    end_date = max_date

schools = sorted([s for s in df["school"].dropna().unique().tolist() if str(s).strip()])
subjects = sorted([s for s in df["subject"].dropna().unique().tolist() if str(s).strip()])
sessions = sorted([s for s in df["session"].dropna().unique().tolist() if str(s).strip()])

selected_schools = st.sidebar.multiselect("Sekolah", schools, default=schools)
selected_subjects = st.sidebar.multiselect("Subjek", subjects, default=subjects)
selected_sessions = st.sidebar.multiselect("Sesi", sessions, default=sessions)

filtered_df = df.copy()
filtered_df = filtered_df[
    (filtered_df["date"] >= start_date) &
    (filtered_df["date"] <= end_date)
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

overall_present = filtered_df["present"].sum()
overall_total = filtered_df["total"].sum()
overall_pct = (overall_present / overall_total * 100) if overall_total else 0

col1, col2, col3 = st.columns(3)
col1.metric("Jumlah Hadir", f"{int(overall_present)}")
col2.metric("Jumlah Direkod", f"{int(overall_total)}")
col3.metric("Overall Attendance", f"{overall_pct:.1f}%")

st.divider()

st.subheader("Summary Table by School and Subject")

summary_df = make_school_subject_summary(filtered_df)

pivot = summary_df.pivot(index="school", columns="subject", values="attendance_pct")
for subject in ["BM", "BI", "MATH", "SEJ"]:
    if subject not in pivot.columns:
        pivot[subject] = pd.NA

pivot = pivot[["BM", "BI", "MATH", "SEJ"]]
pivot_display = pivot.copy()

for col in pivot_display.columns:
    pivot_display[col] = pivot_display[col].map(
        lambda x: "-" if pd.isna(x) else f"{x:.1f}%"
    )

st.dataframe(pivot_display, use_container_width=True)

st.divider()

st.subheader("School Breakdown")

school_list = sorted(summary_df["school"].dropna().unique().tolist())

for school in school_list:
    school_df = summary_df[summary_df["school"] == school].copy()
    st.markdown(f"### {school}")

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
            pt_text = "No data"

        with cols[i]:
            render_subject_card(subject, pct, pt_text)

    with st.expander(f"Lihat rekod sesi untuk {school}"):
        school_sessions = filtered_df[filtered_df["school"] == school].copy()

        display_cols = [
            "date",
            "subject",
            "session",
            "teacher_name",
            "present",
            "total",
            "attendance_pct",
            "attendance_source",
            "attendance_text_raw",
            "absent_text_raw",
            "mastery_level",
            "engagement_level",
            "objective_achieved",
            "challenge",
        ]

        existing_cols = [c for c in display_cols if c in school_sessions.columns]
        school_sessions = school_sessions[existing_cols].sort_values(
            ["date", "subject", "session"],
            ascending=[False, True, True]
        )

        st.dataframe(school_sessions, use_container_width=True)

    st.divider()

st.subheader("⚠️ Subject Below KPI 90%")

low_kpi = summary_df[summary_df["attendance_pct"] < 90].copy()
low_kpi = low_kpi.sort_values(["attendance_pct", "school", "subject"])

if low_kpi.empty:
    st.success("Semua subject yang ada data capai KPI 90% ke atas.")
else:
    st.dataframe(
        low_kpi[["school", "subject", "attendance_pct", "total_present", "total_students", "sessions"]],
        use_container_width=True,
    )

with st.expander("Show cleaned raw data"):
    st.dataframe(filtered_df, use_container_width=True)
