# Toxicology On-Call Scheduler

A Streamlit-based application to help schedule toxicology fellows for on-call shifts.

## Features

- Input first-year and second-year fellow names
- Select a specific month and year to auto-generate daily dates
- Assigns one fellow per day for 24-hour call shifts (no duplicates)
- Ensures first-year fellows receive one more shift per month than second-years
- Distributes weekend shifts evenly across all fellows
- Upload Emergency Medicine shift schedules:
  - Automatically blocks fellows from tox call if they have an EM shift starting before 11 PM
- Upload off-day requests:
  - Blocks fellows from tox call on their requested dates (supports multi-day and non-consecutive days)
- Input a specific toxicology clinic day and view who is on call that day
- Automatically generates the day of the week for each schedule date
- Summary table of total and weekend shifts per fellow
- Downloadable CSV of final schedule

## How to Deploy on Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in with GitHub.
3. Click “New app”, choose this repository, and point to `toxicology_scheduler_with_off_days.py`.
4. Click “Deploy”.

## Sample Input Files

- `sample_em_shift_schedule_multi.csv`: Sample Emergency Medicine shift input
- `sample_off_day_requests.csv`: Sample off-day request input

