from pathlib import Path
import pandas as pd
import numpy as np
import re


# =========================
# CONFIG
# =========================
INPUT_FILE = Path("Kelas Tambahan BEST 2.0 (Refleksi Guru Kelas Tambahan) (Responses) - Form Responses 1.csv")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_SESSIONS_FILE = OUTPUT_DIR / "cleaned_sessions.csv"
SUMMARY_FILE = OUTPUT_DIR / "summary_by_school_subject.csv"
UNRESOLVED_FILE = OUTPUT_DIR / "unresolved_rows.csv"

# Optional:
# Kalau ada row yang tak tulis 23/25, tapi ada list pelajar tak hadir,
# kau boleh isi jumlah pelajar sebenar dekat sini untuk bantu kiraan.
CLASS_SIZE_MAP = {
    # ("SMK Bandar Chiku", "BM"): 25,
    # ("SMK Bandar Chiku", "BI"): 25,
    # ("SMK Bandar Chiku", "MATH"): 25,
    # ("SMK Bandar Chiku", "SEJ"): 25,
}


# =========================
# HELPERS
# =========================
def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def standardize_subject(raw_subject):
    s = normalize_text(raw_subject).lower()

    if "bahasa melayu" in s or s == "bm":
        return "BM"
    if "bahasa inggeris" in s or "english" in s or s == "bi":
        return "BI"
    if "matematik" in s or "math" in s or s == "maths":
        return "MATH"
    if "sejarah" in s or s == "sej":
        return "SEJ"

    return normalize_text(raw_subject).upper()


def extract_school_from_terminal(raw_terminal):
    """
    Ambil nama sekolah daripada column Terminal.
    Contoh:
    - Terminal 1 (SMK Bandar Chiku) (DGM)
    - Terminal 2 : SMK Tengku Indera Petra 1 (DKK)
    """
    s = normalize_text(raw_terminal)
    if not s:
        return ""

    groups = re.findall(r"\(([^()]*)\)", s)
    for g in groups:
        if "smk" in g.lower():
            return g.strip()

    match = re.search(r"(SMK[^(\n\r]*)", s, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return s


def collect_absent_columns(df):
    return [c for c in df.columns if str(c).startswith("Sila tick nama pelajar yang TIDAK hadir")]


def combine_absent_values(row, absent_cols):
    values = []
    for col in absent_cols:
        val = normalize_text(row.get(col, ""))
        if val:
            values.append(val)
    return " | ".join(values)


def count_absent_students(absent_text):
    txt = normalize_text(absent_text)
    if not txt:
        return 0

    txt_lower = txt.lower().strip()
    if txt_lower in {"tiada", "none", "-", "_", "nan"}:
        return 0

    tmp = txt.replace("\n", "|").replace(",", "|").replace(";", "|")
    parts = [p.strip() for p in tmp.split("|") if p.strip()]
    cleaned = [p for p in parts if p.lower() not in {"tiada", "none", "-", "_", "nan"}]
    return len(cleaned)


def parse_date(row):
    candidates = [
        row.get("Tarikh Sesi"),
        row.get("Tarikh Sesi.1"),
        row.get("Timestamp"),
    ]

    for item in candidates:
        if pd.notna(item):
            dt = pd.to_datetime(item, errors="coerce")
            if pd.notna(dt):
                return dt.date()

    return pd.NaT


def extract_fraction_pairs(text):
    txt = normalize_text(text)
    if not txt:
        return []
    pairs = re.findall(r"(\d+)\s*/\s*(\d+)", txt)
    return [(int(a), int(b)) for a, b in pairs]


def split_multischool_attendance(text):
    """
    Contoh:
    SMK SYP1: 9/13
    SMK BANDAR: 0/12
    """
    txt = normalize_text(text)
    if not txt:
        return []

    lines = [line.strip() for line in txt.splitlines() if line.strip()]
    items = []

    for line in lines:
        m = re.search(r"(.+?)\s*:\s*(\d+)\s*/\s*(\d+)", line, flags=re.IGNORECASE)
        if m:
            items.append(
                {
                    "school_hint": m.group(1).strip(),
                    "present": int(m.group(2)),
                    "total": int(m.group(3)),
                }
            )

    return items


def map_school_hint_to_real_school(hint, default_school):
    h = normalize_text(hint).lower()
    d = normalize_text(default_school)

    if not h:
        return d

    if "bandar" in h:
        return "SMK Bandar Chiku"
    if "syp" in h or "yahya" in h:
        return "SMK Sultan Yahya Petra 1"
    if "tip" in h or "tengku" in h or "indera petra" in h:
        return "SMK Tengku Indera Petra 1"
    if "keroh" in h:
        return "SMK Keroh"
    if "jeli" in h:
        return "SMK Jeli"
    if "kandis" in h:
        return "SMK Kandis"
    if "kuala balah" in h:
        return "SMK Kuala Balah"
    if "sri gunung" in h:
        return "SMK Sri Gunung"
    if "tanah merah" in h:
        return "SMK Tanah Merah 1"

    return d


def infer_attendance_from_absent(absent_text, school, subject):
    key = (school, subject)
    class_size = CLASS_SIZE_MAP.get(key)

    if not class_size:
        return None, None, "NO_CLASS_SIZE"

    absent_count = count_absent_students(absent_text)
    present = max(class_size - absent_count, 0)
    total = class_size
    return present, total, "INFERRED_FROM_ABSENT_LIST"


def build_clean_rows(df):
    attendance_col = 'Jumlah Kehadiran Pelajar (cnth: 23/25)\n(Jika pelajar tidak hadir: nyatakan nama dan sebab)'
    absent_cols = collect_absent_columns(df)

    clean_rows = []
    unresolved_rows = []

    for _, row in df.iterrows():
        date_value = parse_date(row)
        teacher_name = normalize_text(row.get("Nama Penuh (Huruf Besar)", ""))
        subject = standardize_subject(row.get("Guru mata pelajaran", ""))
        session = normalize_text(row.get("Column 5", ""))
        terminal_raw = normalize_text(row.get("Terminal ", ""))
        default_school = extract_school_from_terminal(terminal_raw)

        attendance_text = normalize_text(row.get(attendance_col, ""))
        absent_text = combine_absent_values(row, absent_cols)
        challenge = normalize_text(row.get("Cabaran utama semasa kelas dijalankan", ""))
        objective = normalize_text(row.get("Adakah objektif pembelajaran hari ini tercapai? ", ""))
        engagement = normalize_text(row.get("Tahap penglibatan pelajar dalam kelas hari ini ", ""))
        mastery = normalize_text(row.get("Tahap penguasaan pelajar terhadap topik hari ini ", ""))

        # Case 1: lebih 1 sekolah dalam satu cell
        multi_items = split_multischool_attendance(attendance_text)
        if multi_items:
            for item in multi_items:
                school = map_school_hint_to_real_school(item["school_hint"], default_school)
                present = item["present"]
                total = item["total"]
                pct = round((present / total) * 100, 2) if total else np.nan

                clean_rows.append(
                    {
                        "date": date_value,
                        "teacher_name": teacher_name,
                        "subject": subject,
                        "session": session,
                        "school": school,
                        "terminal_raw": terminal_raw,
                        "present": present,
                        "total": total,
                        "attendance_pct": pct,
                        "attendance_source": "DIRECT_MULTI_SCHOOL_FRACTION",
                        "attendance_text_raw": attendance_text,
                        "absent_text_raw": absent_text,
                        "mastery_level": mastery,
                        "engagement_level": engagement,
                        "objective_achieved": objective,
                        "challenge": challenge,
                    }
                )
            continue

        # Case 2: fraction biasa 23/25
        pairs = extract_fraction_pairs(attendance_text)
        if pairs:
            present, total = pairs[0]
            pct = round((present / total) * 100, 2) if total else np.nan

            clean_rows.append(
                {
                    "date": date_value,
                    "teacher_name": teacher_name,
                    "subject": subject,
                    "session": session,
                    "school": default_school,
                    "terminal_raw": terminal_raw,
                    "present": present,
                    "total": total,
                    "attendance_pct": pct,
                    "attendance_source": "DIRECT_FRACTION",
                    "attendance_text_raw": attendance_text,
                    "absent_text_raw": absent_text,
                    "mastery_level": mastery,
                    "engagement_level": engagement,
                    "objective_achieved": objective,
                    "challenge": challenge,
                }
            )
            continue

        # Case 3: infer dari absent list
        inferred_present, inferred_total, source = infer_attendance_from_absent(
            absent_text=absent_text,
            school=default_school,
            subject=subject,
        )

        if inferred_present is not None and inferred_total is not None:
            pct = round((inferred_present / inferred_total) * 100, 2) if inferred_total else np.nan

            clean_rows.append(
                {
                    "date": date_value,
                    "teacher_name": teacher_name,
                    "subject": subject,
                    "session": session,
                    "school": default_school,
                    "terminal_raw": terminal_raw,
                    "present": inferred_present,
                    "total": inferred_total,
                    "attendance_pct": pct,
                    "attendance_source": source,
                    "attendance_text_raw": attendance_text,
                    "absent_text_raw": absent_text,
                    "mastery_level": mastery,
                    "engagement_level": engagement,
                    "objective_achieved": objective,
                    "challenge": challenge,
                }
            )
        else:
            unresolved_rows.append(
                {
                    "date": date_value,
                    "teacher_name": teacher_name,
                    "subject": subject,
                    "session": session,
                    "school": default_school,
                    "terminal_raw": terminal_raw,
                    "attendance_text_raw": attendance_text,
                    "absent_text_raw": absent_text,
                    "reason": "Could not parse attendance fraction and no class size mapping available.",
                }
            )

    clean_df = pd.DataFrame(clean_rows)
    unresolved_df = pd.DataFrame(unresolved_rows)
    return clean_df, unresolved_df


def make_summary(clean_df):
    if clean_df.empty:
        return pd.DataFrame()

    summary = (
        clean_df.groupby(["school", "subject"], dropna=False)
        .agg(
            total_present=("present", "sum"),
            total_students=("total", "sum"),
            sessions=("date", "count"),
        )
        .reset_index()
    )

    summary["attendance_pct"] = np.where(
        summary["total_students"] > 0,
        (summary["total_present"] / summary["total_students"] * 100).round(2),
        np.nan,
    )

    return summary.sort_values(["school", "subject"]).reset_index(drop=True)


def run_cleaning():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    clean_df, unresolved_df = build_clean_rows(df)
    summary_df = make_summary(clean_df)

    clean_df.to_csv(CLEANED_SESSIONS_FILE, index=False)
    summary_df.to_csv(SUMMARY_FILE, index=False)
    unresolved_df.to_csv(UNRESOLVED_FILE, index=False)

    return clean_df, summary_df, unresolved_df


def main():
    clean_df, summary_df, unresolved_df = run_cleaning()

    print("Done cleaning.")
    print(f"Cleaned sessions saved to: {CLEANED_SESSIONS_FILE}")
    print(f"Summary saved to: {SUMMARY_FILE}")
    print(f"Unresolved rows saved to: {UNRESOLVED_FILE}")
    print()
    print(f"Parsed rows: {len(clean_df)}")
    print(f"Unresolved rows: {len(unresolved_df)}")

    if not clean_df.empty:
        print("\nSample cleaned rows:")
        print(clean_df.head(10).to_string(index=False))

    if not summary_df.empty:
        print("\nSummary preview:")
        print(summary_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
