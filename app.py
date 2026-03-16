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


def build_bar_chart(data, x_col, y_col, color_col=None, title=""):
    if data.empty:
        return None

    chart = alt.Chart(data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X(x_col, sort="-y", title=""),
        y=alt.Y(y_col, title="Attendance %"),
        tooltip=list(data.columns),
    )

    if color_col:
        chart = chart.encode(color=alt.Color(color_col, legend=None))

    chart = chart.properties(
        title=title,
        height=360
    )

    return chart


st.title("📊 BEST 2.0 Attendance Dashboard")
st.caption("Dashboard kehadiran ikut sekolah, subjek, dan tarikh")

df = load_data()

if df.empty:
    st.warning("Tiada cleaned data dijumpai. Semak CSV dan script cleaning.")
    st.stop()

st.sidebar.header("Filters")

available_dates = sorted([d for d in df["date"].dropna().unique().tolist()])
schools = sorted([s for s in df["school"].dropna().unique().tolist() if str(s).strip()])
subjects = sorted([s for s in df["subject"].dropna().unique().tolist() if str(s).strip()])
sessions = sorted([s for s in df["session"].dropna().unique().tolist() if str(s).strip()])

filter_mode = st.sidebar.radio(
    "Mode Tarikh",
    ["Semua Tarikh", "Pilih Satu Tarikh", "Julat Tarikh"],
    index=1
)

selected_single_date = None
selected_date_range = None

if filter_mode == "Pilih Satu Tarikh":
    selected_single_date = st.sidebar.selectbox(
        "Pilih Tarikh",
        options=available_dates,
        index=len(available_dates) - 1 if available_dates else 0
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

selected_schools = st.sidebar.multiselect("Sekolah", schools, default=schools)
selected_subjects = st.sidebar.multiselect("Subjek", subjects, default=subjects)
selected_sessions = st.sidebar.multiselect("Sesi", sessions, default=sessions)

filtered_df = df.copy()

if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
    filtered_df = filtered_df[filtered_df["date"] == selected_single_date]

elif filter_mode == "Julat Tarikh" and selected_date_range:
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
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

if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
    st.info(f"Paparan semasa untuk tarikh: **{selected_single_date}**")
elif filter_mode == "Julat Tarikh" and selected_date_range:
    st.info(f"Paparan semasa untuk julat tarikh: **{start_date} hingga {end_date}**")
else:
    st.info("Paparan semasa untuk: **semua tarikh**")

st.divider()

summary_df = make_school_subject_summary(filtered_df)
daily_summary_df = make_daily_school_subject_summary(filtered_df)

tab1, tab2, tab3 = st.tabs(["Sekolah", "Subjek", "Tarikh"])

with tab1:
    st.subheader("Sekolah Overview")

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

    st.markdown("### Bar Chart: Overall Attendance by School")

    school_chart_df = (
        filtered_df.groupby("school", dropna=False)
        .agg(total_present=("present", "sum"), total_students=("total", "sum"))
        .reset_index()
    )
    school_chart_df["attendance_pct"] = (
        school_chart_df["total_present"] / school_chart_df["total_students"] * 100
    ).round(2)

    school_chart = build_bar_chart(
        school_chart_df,
        x_col="school:N",
        y_col="attendance_pct:Q",
        title="Attendance by School"
    )
    if school_chart is not None:
        st.altair_chart(school_chart, use_container_width=True)

    st.markdown("### School Breakdown")

    school_list = sorted(summary_df["school"].dropna().unique().tolist())

    for school in school_list:
        school_df = summary_df[summary_df["school"] == school].copy()
        st.markdown(f"#### {school}")

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

with tab2:
    st.subheader("Subjek Overview")

    subject_summary = (
        filtered_df.groupby("subject", dropna=False)
        .agg(total_present=("present", "sum"), total_students=("total", "sum"))
        .reset_index()
    )
    subject_summary["attendance_pct"] = (
        subject_summary["total_present"] / subject_summary["total_students"] * 100
    ).round(2)

    st.dataframe(subject_summary, use_container_width=True)

    st.markdown("### Bar Chart: Attendance by Subject")
    subject_chart = build_bar_chart(
        subject_summary,
        x_col="subject:N",
        y_col="attendance_pct:Q",
        title="Attendance by Subject"
    )
    if subject_chart is not None:
        st.altair_chart(subject_chart, use_container_width=True)

    st.markdown("### Subjek pada hari / filter semasa")

    for subject in ["BM", "BI", "MATH", "SEJ"]:
        sub_df = filtered_df[filtered_df["subject"] == subject].copy()

        if sub_df.empty:
            continue

        total_present = sub_df["present"].sum()
        total_students = sub_df["total"].sum()
        pct = (total_present / total_students * 100) if total_students else None

        st.markdown(f"#### {subject}")
        render_subject_card(
            subject,
            pct,
            f"{int(total_present)}/{int(total_students)} hadir"
        )

        by_school = (
            sub_df.groupby("school", dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        by_school["attendance_pct"] = (
            by_school["total_present"] / by_school["total_students"] * 100
        ).round(2)

        chart = build_bar_chart(
            by_school,
            x_col="school:N",
            y_col="attendance_pct:Q",
            title=f"{subject} Attendance by School"
        )
        if chart is not None:
            st.altair_chart(chart, use_container_width=True)

        st.dataframe(by_school, use_container_width=True)
        st.divider()

with tab3:
    st.subheader("Tarikh Overview")

    by_date = (
        df.groupby("date", dropna=False)
        .agg(total_present=("present", "sum"), total_students=("total", "sum"))
        .reset_index()
    )
    by_date["attendance_pct"] = (
        by_date["total_present"] / by_date["total_students"] * 100
    ).round(2)

    date_chart = build_bar_chart(
        by_date,
        x_col="date:T",
        y_col="attendance_pct:Q",
        title="Attendance by Date"
    )
    if date_chart is not None:
        st.altair_chart(date_chart, use_container_width=True)

    st.markdown("### Breakdown ikut tarikh yang dipilih / semasa")

    if filter_mode == "Pilih Satu Tarikh" and selected_single_date is not None:
        selected_day_df = filtered_df.copy()

        st.markdown(f"#### Kehadiran pada {selected_single_date}")

        day_summary = (
            selected_day_df.groupby(["school", "subject"], dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        day_summary["attendance_pct"] = (
            day_summary["total_present"] / day_summary["total_students"] * 100
        ).round(2)

        st.dataframe(day_summary, use_container_width=True)

        st.markdown("### Bar Chart: Subject Attendance for Selected Date")
        day_subject = (
            selected_day_df.groupby("subject", dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        day_subject["attendance_pct"] = (
            day_subject["total_present"] / day_subject["total_students"] * 100
        ).round(2)

        day_subject_chart = build_bar_chart(
            day_subject,
            x_col="subject:N",
            y_col="attendance_pct:Q",
            title=f"Attendance by Subject on {selected_single_date}"
        )
        if day_subject_chart is not None:
            st.altair_chart(day_subject_chart, use_container_width=True)

        st.markdown("### Bar Chart: School Attendance for Selected Date")
        day_school = (
            selected_day_df.groupby("school", dropna=False)
            .agg(total_present=("present", "sum"), total_students=("total", "sum"))
            .reset_index()
        )
        day_school["attendance_pct"] = (
            day_school["total_present"] / day_school["total_students"] * 100
        ).round(2)

        day_school_chart = build_bar_chart(
            day_school,
            x_col="school:N",
            y_col="attendance_pct:Q",
            title=f"Attendance by School on {selected_single_date}"
        )
        if day_school_chart is not None:
            st.altair_chart(day_school_chart, use_container_width=True)

    else:
        st.info("Pilih mode **Pilih Satu Tarikh** untuk tengok attendance pada hari itu sahaja.")

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
