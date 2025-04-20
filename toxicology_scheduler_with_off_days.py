
from datetime import datetime, timedelta
import calendar
import pandas as pd
import streamlit as st
import random

st.set_page_config(page_title="Toxicology On-Call Scheduler", layout="centered")
st.title("📅 Toxicology Fellow On-Call Scheduler")

# === INPUT SECTIONS ===

# 1. Input first-year and second-year fellows
first_year_fellows = st.text_input("Enter First-Year Fellows (comma-separated)", "Shin, Mahony")
second_year_fellows = st.text_input("Enter Second-Year Fellows (comma-separated)", "Burke, Johnson")
first_year_fellows = [f.strip() for f in first_year_fellows.split(",") if f.strip()]
second_year_fellows = [f.strip() for f in second_year_fellows.split(",") if f.strip()]
all_fellows = first_year_fellows + second_year_fellows

# 2. Select month and year
col1, col2 = st.columns(2)
with col1:
    selected_month = st.selectbox("Select Month", list(calendar.month_name)[1:], index=datetime.today().month - 1)
with col2:
    selected_year = st.number_input("Select Year", min_value=2000, max_value=2100, value=datetime.today().year)

# Calculate first and last day of the month
month_number = list(calendar.month_name).index(selected_month)
start_date = datetime(selected_year, month_number, 1).date()
_, last_day = calendar.monthrange(selected_year, month_number)
end_date = datetime(selected_year, month_number, last_day).date()

# 3. Clinic day input
clinic_date = st.date_input("Toxicology Clinic Date (usually Thursday)", datetime.today())

# 4. Upload EM shift schedule
em_schedule_file = st.file_uploader("Upload EM Shift Schedule (CSV or Excel)", type=["csv", "xlsx"])
if em_schedule_file:
    if em_schedule_file.name.endswith(".csv"):
        em_df = pd.read_csv(em_schedule_file)
    else:
        em_df = pd.read_excel(em_schedule_file)
    em_df["Date"] = pd.to_datetime(em_df["Date"]).dt.date
    em_df["Start_Time"] = pd.to_datetime(em_df["Start_Time"], format="%H:%M").dt.time
    em_blocked = em_df[em_df["Start_Time"] < datetime.strptime("23:00", "%H:%M").time()]
    em_blocked_dict = em_blocked.groupby("Fellow")["Date"].apply(set).to_dict()
else:
    em_blocked_dict = {}

# 5. Upload off-day request file
off_day_file = st.file_uploader("Upload Off-Day Requests (CSV or Excel)", type=["csv", "xlsx"])
if off_day_file:
    if off_day_file.name.endswith(".csv"):
        off_df = pd.read_csv(off_day_file)
    else:
        off_df = pd.read_excel(off_day_file)
    off_df["Off_Date"] = pd.to_datetime(off_df["Off_Date"]).dt.date
    off_day_dict = off_df.groupby("Fellow")["Off_Date"].apply(set).to_dict()
else:
    off_day_dict = {}

# === SCHEDULING ===

if st.button("Generate Schedule"):
    if not first_year_fellows or not second_year_fellows:
        st.error("Please enter both first-year and second-year fellows.")
    elif start_date >= end_date:
        st.error("End date must be after start date.")
    else:
        date_range = pd.date_range(start=start_date, end=end_date)
        days = date_range.date.tolist()
        weekend_days = [d for d in days if d.weekday() >= 5]
        weekday_days = [d for d in days if d.weekday() < 5]

        # WEEKEND SCHEDULING
        weekend_schedule = []
        shuffled_fellows = all_fellows.copy()
        random.shuffle(shuffled_fellows)
        base_weekend = len(weekend_days) // len(all_fellows)
        extra = len(weekend_days) % len(all_fellows)
        weekend_counts = {f: base_weekend for f in all_fellows}
        for i in range(extra):
            weekend_counts[shuffled_fellows[i]] += 1
        weekend_assignments = []
        for f, c in weekend_counts.items():
            weekend_assignments += [f] * c
        random.shuffle(weekend_assignments)

        assigned_days = set()
        i = 0
        for date in weekend_days:
            while i < len(weekend_assignments):
                fellow = weekend_assignments[i]
                if date not in em_blocked_dict.get(fellow, set()) and date not in off_day_dict.get(fellow, set()):
                    weekend_schedule.append({"Date": date, "Fellow": fellow})
                    assigned_days.add(date)
                    i += 1
                    break
                i += 1

        # WEEKDAY SCHEDULING
        weekday_schedule = []
        available_weekdays = [d for d in weekday_days if d not in assigned_days]
        base_shifts = len(available_weekdays) // len(all_fellows)
        weekday_plan = []
        for f in first_year_fellows:
            weekday_plan += [f] * (base_shifts + 1)
        for f in second_year_fellows:
            weekday_plan += [f] * base_shifts
        while len(weekday_plan) > len(available_weekdays):
            weekday_plan.pop()
        while len(weekday_plan) < len(available_weekdays):
            weekday_plan.append(random.choice(first_year_fellows))
        random.shuffle(weekday_plan)

        i = 0
        for date in available_weekdays:
            while i < len(weekday_plan):
                fellow = weekday_plan[i]
                if date not in em_blocked_dict.get(fellow, set()) and date not in off_day_dict.get(fellow, set()):
                    weekday_schedule.append({"Date": date, "Fellow": fellow})
                    assigned_days.add(date)
                    i += 1
                    break
                i += 1

        # FINALIZE SCHEDULE
        full_schedule = weekend_schedule + weekday_schedule
        df_schedule = pd.DataFrame(full_schedule).sort_values(by="Date")
        df_schedule["Day"] = pd.to_datetime(df_schedule["Date"]).dt.strftime('%A')
        df_schedule = df_schedule[["Date", "Day", "Fellow"]]

        st.success("Schedule generated successfully!")
        st.dataframe(df_schedule, use_container_width=True)

        clinic_fellow = df_schedule[df_schedule["Date"] == clinic_date]["Fellow"]
        if not clinic_fellow.empty:
            st.markdown("### 🧑‍⚕️ Clinic Day Coverage")
            st.success(f"{clinic_fellow.values[0]} is on call for the clinic day: {clinic_date.strftime('%A, %B %d, %Y')}")
        else:
            st.warning("No fellow is assigned for the clinic day you selected.")

        df_schedule["Weekend"] = pd.to_datetime(df_schedule["Date"]).dt.weekday >= 5
        summary = df_schedule.groupby("Fellow").agg(
            Total_Shifts=("Date", "count"),
            Weekend_Shifts=("Weekend", "sum")
        ).reset_index()
        st.markdown("### 📊 Shift Summary per Fellow")
        st.dataframe(summary)

        csv = df_schedule.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Schedule as CSV",
            data=csv,
            file_name="toxicology_schedule.csv",
            mime="text/csv",
        )
