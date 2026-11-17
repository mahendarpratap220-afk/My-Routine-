"""
My Routine & Study Tracker — mobile-friendly Streamlit app

Run locally:
    pip install -r requirements.txt
    streamlit run routine_tracker.py

For phone-only access, upload these files to a GitHub repository from your
phone, then deploy the repository at https://share.streamlit.io/.
"""

import sqlite3
from datetime import date, datetime, time
from io import BytesIO
from pathlib import Path

import pandas as pd
import qrcode
import streamlit as st

DB_PATH = Path(__file__).with_name("routine_tracker.db")

DEFAULT_TASKS = [
    ("Morning CUET study", "05:00–07:00", "📚"),
    ("School", "08:00–14:30", "🏫"),
    ("Lunch and rest", "14:30–15:00", "🍽️"),
    ("CUET MCQ practice", "15:00–16:00", "✍️"),
    ("Teach tuition students", "16:00–17:00", "🧑‍🏫"),
    ("Evening walk", "17:00–17:45", "🚶"),
    ("Python practice", "17:45–18:45", "💻"),
    ("Dinner and break", "18:45–19:30", "🍲"),
    ("Trading education", "19:30–20:15", "📈"),
    ("Revision and plan tomorrow", "20:15–20:45", "📝"),
    ("Get ready for bed", "20:45–21:00", "🌙"),
]

DEFAULT_REMINDERS = [
    ("Morning CUET study", time(5, 0), True),
    ("CUET MCQ practice", time(15, 0), True),
    ("Evening walk", time(17, 0), True),
    ("Python practice", time(17, 45), True),
    ("Trading education", time(19, 30), True),
    ("Revision and plan tomorrow", time(20, 15), False),
]

st.set_page_config(
    page_title="My Routine Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
:root { --ink:#172033; --muted:#64748b; --line:#e7ebf2; }
.block-container {max-width: 1050px; padding-top: 1.1rem; padding-bottom: 3rem;}
header[data-testid="stHeader"] {background: transparent;}
.hero {
  padding: 1.35rem 1.4rem; border-radius: 22px;
  background: linear-gradient(125deg,#172554 0%,#334b91 58%,#6476c8 100%);
  color: white; margin-bottom: 1rem;
}
.hero h1 {font-size: clamp(1.65rem,5vw,2.45rem); margin:0; color:white;}
.hero p {color:#e0e7ff; margin:.35rem 0 0 0; font-size:.96rem;}
div[data-testid="stMetric"] {
  background:#f7f8fc; border:1px solid #e9edf5;
  padding: .8rem; border-radius:16px;
}
div[data-testid="stMetricLabel"] {font-size:.82rem;}
div[data-testid="stTabs"] button {font-weight:600;}
div.stButton > button, div.stDownloadButton > button {
  border-radius:12px; min-height:2.8rem; font-weight:600;
}
div[data-testid="stCheckbox"] {padding:.22rem 0;}
.card {
  border:1px solid #e8ecf3; border-radius:16px;
  padding:1rem; background:white; margin-bottom:.6rem;
}
.small-muted {color:#64748b; font-size:.86rem;}
@media(max-width:640px) {
 .block-container {padding-left: .85rem; padding-right: .85rem;}
 .hero {padding:1.1rem; border-radius:17px;}
 div[data-testid="stMetric"] {padding:.65rem;}
}
</style>
""", unsafe_allow_html=True)


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily (
            day TEXT PRIMARY KEY,
            completed TEXT NOT NULL DEFAULT '',
            steps INTEGER NOT NULL DEFAULT 0,
            walk_minutes INTEGER NOT NULL DEFAULT 0,
            cuet_minutes INTEGER NOT NULL DEFAULT 0,
            mcq_count INTEGER NOT NULL DEFAULT 0,
            python_minutes INTEGER NOT NULL DEFAULT 0,
            trading_minutes INTEGER NOT NULL DEFAULT 0,
            tuition_minutes INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT ''
        )
    """)
    conn.commit()
    return conn


def load_day(day_value):
    with connect() as conn:
        row = conn.execute("SELECT * FROM daily WHERE day=?", (day_value.isoformat(),)).fetchone()
    if not row:
        return {
            "completed": [], "steps": 0, "walk_minutes": 0, "cuet_minutes": 0,
            "mcq_count": 0, "python_minutes": 0, "trading_minutes": 0,
            "tuition_minutes": 0, "notes": ""
        }
    return {
        "completed": [x for x in row[1].split("|") if x],
        "steps": row[2], "walk_minutes": row[3], "cuet_minutes": row[4],
        "mcq_count": row[5], "python_minutes": row[6],
        "trading_minutes": row[7], "tuition_minutes": row[8], "notes": row[9]
    }


def save_day(day_value, data):
    values = (
        day_value.isoformat(), "|".join(data["completed"]), data["steps"],
        data["walk_minutes"], data["cuet_minutes"], data["mcq_count"],
        data["python_minutes"], data["trading_minutes"], data["tuition_minutes"],
        data["notes"]
    )
    with connect() as conn:
        conn.execute("""
            INSERT INTO daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(day) DO UPDATE SET
              completed=excluded.completed, steps=excluded.steps,
              walk_minutes=excluded.walk_minutes, cuet_minutes=excluded.cuet_minutes,
              mcq_count=excluded.mcq_count, python_minutes=excluded.python_minutes,
              trading_minutes=excluded.trading_minutes,
              tuition_minutes=excluded.tuition_minutes, notes=excluded.notes
        """, values)
        conn.commit()


def all_records():
    with connect() as conn:
        return pd.read_sql_query("SELECT * FROM daily ORDER BY day", conn)


def qr_png(url):
    qr = qrcode.QRCode(box_size=8, border=3)
    qr.add_data(url.strip())
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def init_reminders():
    if "reminders" not in st.session_state:
        st.session_state.reminders = [
            {"name": n, "at": t, "enabled": e} for n, t, e in DEFAULT_REMINDERS
        ]
    if "last_reminder_key" not in st.session_state:
        st.session_state.last_reminder_key = ""


def reminder_checker():
    """Checks reminders while this app page is open and periodically reruns."""
    now = datetime.now()
    current_minute = now.strftime("%Y-%m-%d %H:%M")
    for item in st.session_state.reminders:
        if item["enabled"] and now.strftime("%H:%M") == item["at"].strftime("%H:%M"):
            key = f'{current_minute}|{item["name"]}'
            if st.session_state.last_reminder_key != key:
                st.session_state.last_reminder_key = key
                st.toast(f'⏰ Time for {item["name"]}!', icon="🔔")


init_reminders()

st.markdown("""
<div class="hero">
  <h1>📚 My Routine & Study Tracker</h1>
  <p>Your daily dashboard for CUET, teaching, Python, learning and walking.</p>
</div>
""", unsafe_allow_html=True)

today = date.today()
if "selected_day" not in st.session_state:
    st.session_state.selected_day = today

with st.container():
    top1, top2 = st.columns([1.2, 2.2])
    with top1:
        selected_date = st.date_input("📅 Choose tracking date", value=st.session_state.selected_day)
        st.session_state.selected_day = selected_date
    with top2:
        st.markdown(
            f"### {selected_date.strftime('%A, %d %B %Y')}\n"
            "<span class='small-muted'>Select any date to review or update its record.</span>",
            unsafe_allow_html=True,
        )

data = load_day(selected_date)
records = all_records()
done_default = set(data["completed"])

# Main navigation: selectbox is easier to use on narrow phone screens than tabs.
page = st.radio(
    "Navigate",
    ["Today", "Activity log", "Monthly progress", "Reminders", "Backup & QR"],
    horizontal=True,
    label_visibility="collapsed",
)

if page == "Today":
    st.subheader("Today's overview")
    completed_count = len(done_default.intersection({x[0] for x in DEFAULT_TASKS}))
    percent = round(completed_count / len(DEFAULT_TASKS) * 100)
    m1, m2, m3 = st.columns(3)
    m1.metric("Routine completed", f"{percent}%")
    m2.metric("Steps recorded", f"{data['steps']:,}")
    m3.metric("Walk time", f"{data['walk_minutes']} min")
    st.progress(percent / 100)

    st.subheader("Daily checklist")
    st.caption("Tick an activity when you finish it. Your selections are saved when you tap Save today's progress.")
    completed = []
    for idx, (task, timing, emoji) in enumerate(DEFAULT_TASKS):
        is_done = st.checkbox(
            f"{emoji}  {task}  ·  {timing}",
            value=task in done_default,
            key=f"check_{selected_date.isoformat()}_{idx}",
        )
        if is_done:
            completed.append(task)

    st.divider()
    st.subheader("Quick reflection")
    notes = st.text_area(
        "What went well today? What will you improve tomorrow?",
        value=data["notes"],
        height=95,
        placeholder="Write a short note...",
    )
    if st.button("💾 Save today's progress", type="primary", use_container_width=True):
        save_day(selected_date, {**data, "completed": completed, "notes": notes})
        st.success("Your checklist and notes have been saved.")
        st.rerun()

elif page == "Activity log":
    st.subheader("Study & activity log")
    st.caption("Enter what you actually completed. You can edit past dates too.")
    with st.form("activity_form"):
        a, b = st.columns(2)
        with a:
            steps = st.number_input("👟 Total steps", 0, 100000, int(data["steps"]), 500)
            walk = st.number_input("🚶 Walking (minutes)", 0, 600, int(data["walk_minutes"]), 5)
            cuet = st.number_input("📚 CUET study (minutes)", 0, 1000, int(data["cuet_minutes"]), 15)
            mcqs = st.number_input("✍️ MCQs attempted", 0, 10000, int(data["mcq_count"]), 5)
        with b:
            python_m = st.number_input("💻 Python practice (minutes)", 0, 1000, int(data["python_minutes"]), 15)
            trading = st.number_input("📈 Trading education (minutes)", 0, 1000, int(data["trading_minutes"]), 15)
            tuition = st.number_input("🧑‍🏫 Tuition teaching (minutes)", 0, 1000, int(data["tuition_minutes"]), 15)
            notes = st.text_area("Notes / what I learned", value=data["notes"], height=100)
        save_activity = st.form_submit_button("Save activity log", type="primary", use_container_width=True)
    if save_activity:
        save_day(selected_date, {
            **data, "steps": int(steps), "walk_minutes": int(walk),
            "cuet_minutes": int(cuet), "mcq_count": int(mcqs),
            "python_minutes": int(python_m), "trading_minutes": int(trading),
            "tuition_minutes": int(tuition), "notes": notes
        })
        st.success("Activity log saved.")
        st.rerun()
    st.info("A 30–45 minute evening walk is a useful starting target. Build activity gradually; total daily steps can vary.")

elif page == "Monthly progress":
    st.subheader("Monthly progress")
    month = st.date_input("Choose a month", value=selected_date, key="month_select")
    if records.empty:
        st.info("No records yet. Save your first day to start your monthly report.")
    else:
        records["day"] = pd.to_datetime(records["day"])
        subset = records[
            (records["day"].dt.year == month.year) &
            (records["day"].dt.month == month.month)
        ].copy()
        if subset.empty:
            st.info("No saved records for this month yet.")
        else:
            subset["completed_count"] = subset["completed"].apply(
                lambda s: len([x for x in str(s).split("|") if x])
            )
            x1, x2, x3 = st.columns(3)
            x1.metric("Days tracked", len(subset))
            x2.metric("CUET study", f"{subset['cuet_minutes'].sum()/60:.1f} hr")
            x3.metric("Python practice", f"{subset['python_minutes'].sum()/60:.1f} hr")
            st.markdown("**Study time by day (minutes)**")
            st.line_chart(subset.set_index("day")[["cuet_minutes", "python_minutes", "trading_minutes"]])
            st.markdown("**Daily records**")
            st.dataframe(
                subset[["day", "completed_count", "steps", "walk_minutes", "cuet_minutes",
                        "mcq_count", "python_minutes", "trading_minutes", "tuition_minutes"]],
                use_container_width=True, hide_index=True
            )

elif page == "Reminders":
    st.subheader("🔔 Daily reminders")
    st.write("Set the times that suit you. Reminders appear inside the app while it is open.")
    st.warning(
        "Important: this version checks reminders while the tracker is open. "
        "It cannot send reliable notifications when the app/browser is closed or the phone is asleep."
    )
    for i, item in enumerate(st.session_state.reminders):
        with st.container(border=True):
            left, middle, right = st.columns([2.2, 1.2, 1])
            with left:
                st.session_state.reminders[i]["enabled"] = st.checkbox(
                    item["name"], value=item["enabled"], key=f"rem_enabled_{i}"
                )
            with middle:
                st.session_state.reminders[i]["at"] = st.time_input(
                    "Time", value=item["at"], key=f"rem_time_{i}", label_visibility="collapsed"
                )
            with right:
                st.caption("ON" if st.session_state.reminders[i]["enabled"] else "OFF")
    if st.button("🔔 Test reminder", use_container_width=True):
        st.toast("This is a test reminder. Your tracker is working!", icon="🔔")
        st.success("Test reminder displayed.")
    st.caption("Keep this page open for the reminder checker to run. Streamlit may pause updates when the browser is in the background.")

elif page == "Backup & QR":
    st.subheader("Backup your records")
    records = all_records()
    if not records.empty:
        st.download_button(
            "⬇️ Download CSV backup",
            data=records.to_csv(index=False).encode("utf-8"),
            file_name="routine_tracker_backup.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Your backup will be available after you save some daily records.")

    st.divider()
    st.subheader("Create a QR code")
    app_url = st.text_input("Your published app URL", placeholder="https://your-app.streamlit.app")
    if st.button("Generate QR code", use_container_width=True):
        if app_url.startswith(("https://", "http://")):
            png = qr_png(app_url)
            st.image(png, caption="Scan to open your tracker")
            st.download_button("Download QR code", png, "routine_tracker_qr.png", "image/png")
        else:
            st.error("Enter a valid web address beginning with https:// or http://.")

    st.divider()
    st.subheader("About your data")
    st.caption(
        "This starter app uses SQLite. On a hosted free service, local files may be reset "
        "when the app restarts or redeploys. Download CSV backups regularly. For dependable "
        "long-term cloud sync, connect a hosted database such as Supabase."
    )

# Periodic in-app reminder checks. These are not operating-system push notifications.
@st.fragment(run_every="30s")
def reminder_loop():
    reminder_checker()

reminder_loop()

st.markdown(
    "<p class='small-muted' style='text-align:center;margin-top:2rem'>"
    "Made for steady progress • Your routine can be adjusted as your needs change</p>",
    unsafe_allow_html=True,
)
