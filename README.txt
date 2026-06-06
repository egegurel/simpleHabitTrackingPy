# Habit Tracker

## Project Description
Habit Tracker is a Python desktop application developed with Tkinter in easy to understand GUI.  
The program allows users to easily create, manage, and track habits with daily or weekly periodicity as well as with streaks for each habit.  
The application stores habit data in a JSON file.

## Features
- Predefined habits available at beginning.
- Add new habits with custom selected dates, names and periodicity. 
- Deleting the habits
- Mark habits as done or missed
- Show progress with status boxes
- Save and load data using JSON
- Analytics section for:
  - all current habits.
  - habits by periodicity.
  - longest streak of all habits.
  - streak data of a selected habit if there is a streak.

## Technologies Used
- Python
- Tkinter
- JSON
- unittest
- tkcalendar

## Data Storage
Habit data is stored in a file called `habits.json`.

Each habit includes:
- name
- periodicity
- selected dates
- start date
- end date
- target periods
- records of done/missed dates

Example JSON structure:

```json
{
    "name": "Brush Teeth",
    "periodicity": "daily",
    "selected_dates": [
        "2026-04-07",
        "2026-04-08",
        "2026-04-09"
    ],
    "start_date": "2026-04-07",
    "end_date": "2026-04-09",
    "target_periods": 3,
    "records": {
        "2026-04-07": true
    }
}


## Installation

Before running the program, make sure Python is installed on your computer and PATH given to Python program.

1) Clone or download the project
Download the project folder to your computer.

2) Open Command Prompt in the project folder
Example:

```bash
cd "C:\Users\YourName\Desktop\HabitTracking" 

pip install -r requirements.txt

if it doesn't works, then try this:

python -m pip install -r requirements.txt

## Run the program

'python HabitPy.py' or 'py HabitPy.py' 

or you can use a code editor such as VS2019, VS2022 or any other code editor and open file and run the HabitPy.py 

##Run the test

python -m unittest UnitTestPy -v

