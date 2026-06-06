import json
import os
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry, Calendar
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "habits.json"
DATE_FMT = "%Y-%m-%d"


class HabitTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Habit Tracker")
        self.root.geometry("1100x700")
        self.root.minsize(1000, 650)

        self.habits = self.load_data()
        self.current_section = "overview"

        self.build_ui()
        self.show_overview()

    # ---------------------------
    # Data layer
    # ---------------------------
    def default_habits(self):
        """This method generates default habits"""
        today_obj = date.today()

        if today_obj.month == 12:
            last_day_of_month = date(today_obj.year, 12, 31)
        else:
            last_day_of_month = date(today_obj.year, today_obj.month + 1, 1) - timedelta(days=1)
        
        
        #Instead of giving a static days, I preferred to calculate remaining days in the month from the current date and generate daily or weekly default habits based on that. 
        # days_left_in_month is calculated by finding the difference in days between the last day of the month and today's date, and adding 1 to include today.

        days_left_in_month = (last_day_of_month - today_obj).days + 1

        daily_dates = [
            (today_obj + timedelta(days=i)).strftime(DATE_FMT)
            for i in range(days_left_in_month)
        ]

        weekly_dates = [
            d for d in daily_dates
            if datetime.strptime(d, DATE_FMT).date().weekday() == 0
        ] or [self.start_date_for_new_habit("weekly")]
   
        return [
            self.make_habit("Brush Teeth", "daily", daily_dates),
            self.make_habit("Wake Up Early", "daily", daily_dates),
            self.make_habit("After Work Sport", "daily", daily_dates),
            self.make_habit("Breakfast", "daily", daily_dates),
            self.make_habit("Go to Swimming Pool", "weekly", weekly_dates),
        ]

    def make_habit(self, name, periodicity, selected_dates):
        """This method creates a habit dictionary with the name, periodicity, and selected dates. 
        Also calculates the start and end dates based on the selected dates and initializes the records as an empty dictionary."""


        selected_dates = sorted(set(selected_dates))
        return {
            "name": name,
            "periodicity": periodicity,
            "selected_dates": selected_dates,
            "start_date": selected_dates[0] if selected_dates else "",
            "end_date": selected_dates[-1] if selected_dates else "",
            "target_periods": len(selected_dates),
            "records": {},
        }

    def load_data(self):
        """This method loads the habits data from the JSON file. If the file doesn't exist or is invalid, it creates default habits and saves them."""
        if not os.path.exists(DATA_FILE):
            habits = self.default_habits()
            self.save_data(habits)
            return habits

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Invalid JSON root")
            return data
        except Exception:
            messagebox.showwarning(
                "Warning",
                "Could not read habits.json. Default habits were loaded instead.",
            )
            habits = self.default_habits()
            self.save_data(habits)
            return habits

    def save_data(self, habits=None):
        """This method saves the habits data to the JSON file. If no specific habits list is provided, it saves the current state of self.habits."""
        if habits is None:
            habits = self.habits
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(habits, f, indent=4)

    # ---------------------------
    # Utility methods
    # ---------------------------
    def today_str(self):
        """This method returns today's date as a string formatted according to DATE_FMT."""
        return date.today().strftime(DATE_FMT)


    def current_period_key(self, habit):
        """This method calculates the current period's key (date string) for a given habit based on its periodicity and start date."""
        today = date.today()
        start = datetime.strptime(habit['start_date'], DATE_FMT).date()

        if habit["periodicity"] == "daily":
            return start.strftime(DATE_FMT) if today < start else today.strftime(DATE_FMT)

        if today < start:
            return start.strftime(DATE_FMT)

        monday = today - timedelta(days=today.weekday())
        return monday.strftime(DATE_FMT)
    def next_period_key(self, habit):
        """This method calculates the next period's key (date string) for a given habit based on its periodicity and selected dates."""
        today_str = self.today_str()
        selected_dates = sorted(set(habit.get("selected_dates", [])))
        for d in selected_dates:
            if d == today_str:
                return d 
            elif d > today_str:
                return d
            
    def period_label(self, habit):
        #This method defines what day or week is next task for habit and we put that into entry label.
        key = self.next_period_key(habit)
        if habit["periodicity"] == "daily":
            return f"Next days periods ({key})"
        return f"Next weeks periods  ({key})"

    def count_done(self, habit):
        """This method counts how many times a habit has been marked as done (True) in its records."""
        return sum(1 for v in habit["records"].values() if v is True)

    def count_missed(self, habit):
        """This method counts how many times a habit has been marked as missed (False) in its records."""
        return sum(1 for v in habit["records"].values() if v is False)
    

    
    def current_status(self, habit):
        """Return overall status based on all scheduled dates."""
        selected_dates = habit.get("selected_dates", [])
        records = habit.get("records", {})
         
        if not selected_dates:
            return "Pending"

        values = [records.get(d) for d in selected_dates]
        if len(records) < len(selected_dates):
          
            return "Pending"
        
        if all(value is True for value in values):
            return "Done"
        
        if all(value is False for value in values) or (any(value is False for value in values) or all(value is not True for value in values)):
            return "Missed"
     
 

    def sort_period_keys(self, keys):
        return sorted(keys, key=lambda x: datetime.strptime(x, DATE_FMT))

    def streak(self, habit):
        """Return True if all scheduled dates of the habit are marked as True."""
        total_dates = len(habit.get("selected_dates", []))
        true_count = sum(1 for value in habit.get("records", {}).values() if value is True)

        return total_dates > 0 and true_count == total_dates

    def streak_for_overall_longest(self, habit):
        """Return the streak value as days for overall longest streak calculation."""
        total_dates = len(habit.get("selected_dates", []))
        true_count = sum(1 for value in habit.get("records", {}).values() if value is True)
        if total_dates == true_count:
            return total_dates
        else:
            return 0
    def overall_longest_streak(self):
        """Return the longest streak value and all habits that share it."""
        if not self.habits:
            return 0, []

        best_habits = []
        best_streak = 0
        list_of_streaks = []
        for habit in self.habits:
            habit_streak = self.streak_for_overall_longest(habit)
            list_of_streaks.append(habit_streak)
        max_streak = max(list_of_streaks)
        for habit in self.habits:
            if self.streak_for_overall_longest(habit) == max_streak:
                best_habits.append(habit["name"])
        return best_streak, best_habits
 

    def get_habit_by_name(self, name):
        """This method searches for a habit by its name in the list of habits and returns the habit dictionary if found, or None if not found."""
        for habit in self.habits:
            if habit["name"] == name:
                return habit
        return None

    # ---------------------------
    # UI build
    # ---------------------------
    def build_ui(self):
        """This method sets up the main user interface of the application, including the top navigation bar with buttons for different sections 
        and the main content area where the details of each section will be displayed."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        topbar = tk.Frame(self.root, bg="#1f2937", height=60)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        for c in range(3):
            topbar.columnconfigure(c, weight=1)

        btn_style = {"font": ("Arial", 12, "bold"), "bd": 0, "fg": "white", "bg": "#1f2937", "activebackground": "#374151", "activeforeground": "white"}

        btn_overview = tk.Button(topbar, text="Overview to Habits", command=self.show_overview, **btn_style)
        btn_overview.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)
        btn_analytics  =tk.Button(topbar, text="Analytics", command=self.show_analytics, **btn_style)
        btn_analytics.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        btn_manage = tk.Button(topbar, text="Adding or Deleting Habits", command=self.show_manage, **btn_style)
        btn_manage.grid(row=0, column=2, sticky="nsew", padx=5, pady=10)

        self.content = tk.Frame(self.root, bg="#f3f4f6")
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self.add_hover_effect(btn_overview, normal_bg="#1f2937", hover_bg="#374151", normal_fg="white", hover_fg="white")
        self.add_hover_effect(btn_analytics, normal_bg="#1f2937", hover_bg="#374151", normal_fg="white", hover_fg="white")
        self.add_hover_effect(btn_manage, normal_bg="#1f2937", hover_bg="#374151", normal_fg="white", hover_fg="white")

    def clear_content(self):
        """This method clears all widgets from the main content area, 
        allowing for a fresh display when switching between different sections of the application."""
        for widget in self.content.winfo_children():
            widget.destroy()

    # ---------------------------
    # Overview section
    # ---------------------------
    def show_overview(self):
        """This method displays the overview section of the application, 
        which lists all habits with their details and allows users to mark them as done or missed for the current period."""
        self.current_section = "overview"
        self.clear_content()

        wrapper = tk.Frame(self.content, bg="#f3f4f6", padx=15, pady=15)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(2, weight=1)

        title = tk.Label(wrapper, text="Overview to Habits", font=("Arial", 20, "bold"), bg="#f3f4f6")
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        subtitle = tk.Label(
            wrapper,
            text="Mark habits as done or missed for the current daily/weekly period.",
            font=("Arial", 11),
            bg="#f3f4f6",
            fg="#374151",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(0, 15))

        # NEW: scrollable area
        canvas_frame = tk.Frame(wrapper, bg="#f3f4f6")
        canvas_frame.grid(row=2, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(canvas_frame, bg="#f3f4f6", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

        scrollable_frame = tk.Frame(canvas, bg="#f3f4f6")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def resize_scrollable_frame(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", resize_scrollable_frame)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        if not self.habits:
            tk.Label(scrollable_frame, text="No habits found.", font=("Arial", 12), bg="#f3f4f6").pack(anchor="w")
            return

        for habit in self.habits:
            card = tk.Frame(
                scrollable_frame,
                bg="white",
                highlightbackground="#d1d5db",
                highlightthickness=1,
                padx=12,
                pady=12
            )
            card.pack(fill="x", pady=8)

            header = tk.Frame(card, bg="white")
            header.pack(fill="x")
            header.columnconfigure(0, weight=1)

            tk.Label(header, text=habit["name"], font=("Arial", 16, "bold"), bg="white").grid(row=0, column=0, sticky="w")
            tk.Label(
                header,
                text=habit["periodicity"].capitalize(),
                font=("Arial", 11, "bold"),
                bg="white",
                fg="#2563eb"
            ).grid(row=0, column=1, sticky="e")

            info_text = (
                f"Start date: {habit['start_date']}    |    Target periods: {habit['target_periods']}    |    "
                f"Completed: {self.count_done(habit)}    |    Missed: {self.count_missed(habit)}    |    "
                f"Status: {self.current_status(habit)}"
            )
            tk.Label(card, text=info_text, font=("Arial", 10), bg="white", fg="#4b5563").pack(anchor="w", pady=(8, 5))
            tk.Label(card, text=self.period_label(habit), font=("Arial", 10, "italic"), bg="white", fg="#6b7280").pack(anchor="w", pady=(0, 10))

            actions = tk.Frame(card, bg="white")
            actions.pack(anchor="w")
            self.render_status_boxes(card, habit)
            btn_done = tk.Button(actions, text="Mark Done", width=14, command=lambda h=habit: self.mark_habit(h, True))
            btn_done.pack(side="left", padx=(0, 8))
            btn_miss = tk.Button(actions, text="Mark Missed", width=14, command=lambda h=habit: self.mark_habit(h, False))
            btn_miss.pack(side="left")
            self.add_hover_effect(btn_done, hover_bg="#dcfce7")
            self.add_hover_effect(btn_miss, hover_bg="#fee2e2")
    def move_box_tooltip(self, event):
        """Move the tooltip together with the cursor."""
        if hasattr(self, "box_tooltip") and self.box_tooltip:
            self.box_tooltip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 12}")


    def hide_box_tooltip(self, event=None):
        """Hide the tooltip if it exists."""
        if hasattr(self, "box_tooltip") and self.box_tooltip:
            self.box_tooltip.destroy()
            self.box_tooltip = None
    def show_box_tooltip(self, event, date_str):
        """Show a small tooltip near the cursor with the date."""
        self.hide_box_tooltip()

        self.box_tooltip = tk.Toplevel(self.root)
        self.box_tooltip.wm_overrideredirect(True)
        self.box_tooltip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 12}")

        label = tk.Label(
            self.box_tooltip,
            text=date_str,
            bg="#fff7cc",
            fg="black",
            relief="solid",
            bd=1,
            font=("Arial", 9)
        )
        label.pack()
    def render_status_boxes(self, parent, habit):
        """This method renders a series of boxes representing the progress of a habit over its selected dates."""
        boxes_frame = tk.Frame(parent, bg="white")
        boxes_frame.pack(anchor="w", pady=(6, 10), fill="x")

        tk.Label(
            boxes_frame,
            text="Progress:",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#374151"
        ).pack(anchor="w", pady=(0, 6))

        icons_wrap = tk.Frame(boxes_frame, bg="white")
        icons_wrap.pack(anchor="w", fill="x")

        selected_dates = habit.get("selected_dates", [])
        today_str = date.today().strftime(DATE_FMT)

        max_columns = 12

        for idx, date_str in enumerate(selected_dates):
            row = idx // max_columns
            col = idx % max_columns

            record_value = habit["records"].get(date_str)

            if record_value is None:
                if date_str < today_str:
                    symbol, color = "✗", "#dc2626"  # failed task
                    habit["records"][date_str] = False
                    self.save_data()
                             
                else:
                    symbol, color = "–", "#9ca3af"   # indefinite / pending
            else:
                symbol, color = self.get_box_symbol_and_color(record_value)

            box = tk.Label(
                icons_wrap,
                text=symbol,
                width=3,
                height=1,
                font=("Arial", 11, "bold"),
                bg="white",
                fg=color,
                relief="solid",
                bd=1
            )
            box.grid(row=row, column=col, padx=3, pady=3)

            box.bind(
                "<Enter>",
                lambda e, d=date_str: (
                    e.widget.config(bg="#e5e7eb", cursor="hand2"),
                    self.show_box_tooltip(e, d)
                )
            )
            box.bind("<Motion>", self.move_box_tooltip)
            box.bind(
                "<Leave>",
                lambda e: (
                    e.widget.config(bg="white", cursor=""),
                    self.hide_box_tooltip(e)
                )
            )
    def get_box_symbol_and_color(self, value):
        """This method returns the appropriate symbol and color for a status box based on whether the habit was done, missed, or is pending."""
        if value is True:
            return "✓", "#16a34a"   
        if value is False:
            return "✗", "#dc2626"   
        return "–", "#9ca3af"  
    
    
    # Analytics section ---->>>>>>>
    def mark_habit(self, habit, value):
        """This method marks a habit as done or not done for today only if the habit is intersected with today's date."""
        today_str = date.today().strftime(DATE_FMT)

        selected_dates = habit.get("selected_dates", [])

        if today_str not in selected_dates:
            messagebox.showinfo(
                "Not Scheduled Today",
                f"This habit is not scheduled for today ({today_str})."
            )
            return

        habit["records"][today_str] = value
        self.save_data()
        self.show_overview()
    def show_analytics(self):
        #Analytics section with two main parts: top cards with overall stats and a detailed area with lists and streaks.
        self.current_section = "analytics"
        self.clear_content()

        wrapper = tk.Frame(self.content, bg="#f3f4f6", padx=15, pady=15)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)

        tk.Label(wrapper, text="Analytics", font=("Arial", 20, "bold"), bg="#f3f4f6").grid(row=0, column=0, sticky="w", pady=(0, 12))

        top_cards = tk.Frame(wrapper, bg="#f3f4f6")
        top_cards.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        for i in range(4):
            top_cards.columnconfigure(i, weight=1)

        total = len(self.habits)
        daily_count = sum(1 for h in self.habits if h["periodicity"] == "daily")
        weekly_count = sum(1 for h in self.habits if h["periodicity"] == "weekly")

        #List of tuples with the label and value for each card in the analytics section.         
        stats = [
            ("Current Habits", str(total)),
            ("Daily Habits", str(daily_count)),
            ("Weekly Habits", str(weekly_count)),
             
        ] 

        for i, (label, value) in enumerate(stats):

            #This is a helper function to create the top cards in the analytics section. 
            #It creates a frame for each card, sets the label and value, and styles it with padding and borders.
            
            box = tk.Frame(top_cards, bg="white", padx=10, pady=10, highlightbackground="#d1d5db", highlightthickness=1)
            box.grid(row=0, column=i, sticky="nsew", padx=5)
            tk.Label(box, text=label, font=("Arial", 11), bg="white", fg="#6b7280").pack(anchor="w")
            tk.Label(box, text=value, font=("Arial", 18, "bold"), bg="white").pack(anchor="w", pady=(4, 0))

        area = tk.Frame(wrapper, bg="#f3f4f6")
        area.grid(row=2, column=0, sticky="nsew")
        area.columnconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)

        # Left: all habits / same periodicity
        left = tk.Frame(area, bg="white", padx=12, pady=12, highlightbackground="#d1d5db", highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(left, text="Habit Lists", font=("Arial", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 8))

        btns = tk.Frame(left, bg="white")
        btns.pack(anchor="w", pady=(0, 10))
        show_current_habits = tk.Button(btns, text="Show All Current Habits", command=self.analytics_show_all)
        show_current_habits.pack(side="left", padx=(0, 8))
        self.add_hover_effect(show_current_habits, hover_bg="#dbeafe")
        show_daily_only= tk.Button(btns, text="Show Daily Only", command=lambda: self.analytics_show_by_periodicity("daily"))
        show_daily_only.pack(side="left", padx=(0, 8))
        self.add_hover_effect(show_daily_only, hover_bg="#dbeafe")
        show_weekly_only = tk.Button(btns, text="Show Weekly Only", command=lambda: self.analytics_show_by_periodicity("weekly"))
        show_weekly_only.pack(side="left")
        self.add_hover_effect(show_weekly_only, hover_bg="#dbeafe")
        self.analytics_text = tk.Text(left, height=18, wrap="word", font=("Consolas", 10))
        self.analytics_text.pack(fill="both", expand=True)

        # Right: streaks
        right = tk.Frame(area, bg="white", padx=12, pady=12, highlightbackground="#d1d5db", highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(right, text="Streak Analytics", font=("Arial", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 8))

        top_line = tk.Frame(right, bg="white")
        top_line.pack(fill="x", pady=(0, 8))
        show_longest_streak = tk.Button(top_line, text="Show Longest Streak of All Habits", command=self.analytics_show_longest_all)
        show_longest_streak.pack(side="left")
        self.add_hover_effect(show_longest_streak, hover_bg="#dbeafe")

        choose_line = tk.Frame(right, bg="white")
        choose_line.pack(fill="x", pady=(0, 8))

        self.selected_habit_var = tk.StringVar()
        names = [h["name"] for h in self.habits]
        combo = ttk.Combobox(choose_line, textvariable=self.selected_habit_var, values=names, state="readonly", width=30)
        combo.pack(side="left", padx=(0, 8))
        if names:
            combo.current(0)
        btn_show_habit_streak = tk.Button(choose_line, text="Show Chosen Habit Streak", command=self.analytics_show_habit_streak)
        btn_show_habit_streak.pack(side="left")
        self.add_hover_effect(btn_show_habit_streak, hover_bg="#dbeafe")

        self.streak_text = tk.Text(right, height=18, wrap="word", font=("Consolas", 10))
        self.streak_text.pack(fill="both", expand=True)

        self.analytics_show_all()
       
    def analytics_show_all(self):
        """This method displays all current habits in the analytics text box."""
        self.analytics_text.config(state="normal")
        self.analytics_text.delete("1.0", tk.END)
        if not self.habits:
            self.analytics_text.insert(tk.END, "No habits found.\n")
            return
        self.analytics_text.insert(tk.END, "All current habits:\n\n")
        for habit in self.habits:
            self.analytics_text.insert(
                tk.END,
                f"- {habit['name']} | {habit['periodicity']} | Completed: {self.count_done(habit)} | Missed: {self.count_missed(habit)}\n",
            )
        self.analytics_text.config(state="disabled")
    def analytics_show_by_periodicity(self, periodicity):
        """This method displays habits filtered by their periodicity in the analytics text box."""
        self.analytics_text.config(state="normal")
        self.analytics_text.delete("1.0", tk.END)
        filtered = [h for h in self.habits if h["periodicity"] == periodicity]
        self.analytics_text.insert(tk.END, f"Habits with periodicity = {periodicity}:\n\n")
        if not filtered:
            self.analytics_text.insert(tk.END, "No matching habits found.\n")
            return
        for habit in filtered:
            self.analytics_text.insert(
                tk.END,
                f"- {habit['name']} | Completed: {self.count_done(habit)} | Missed: {self.count_missed(habit)} | Streak: {self.streak(habit)}\n",
            )
        self.analytics_text.config(state="disabled")
    def analytics_show_longest_all(self):
        """This method displays the longest streak of all habits in the streak text box."""

        self.streak_text.config(state="normal")
        self.streak_text.delete("1.0", tk.END)
        streak, habit_name = self.overall_longest_streak()
        if habit_name is None:
            self.streak_text.insert(tk.END, "No habits found.\n")
            return
        self.streak_text.insert(
            tk.END,
            f"Longest streak of all habits:Habit: {habit_name}\n",
        )
        self.streak_text.config(state="disabled")


    def analytics_show_habit_streak(self):
        """This method displays the longest streak for the selected habit in the streak text box."""
        self.streak_text.config(state="normal")
        self.streak_text.delete("1.0", tk.END)
        name = self.selected_habit_var.get().strip()
        habit = self.get_habit_by_name(name)
        if not habit:
            self.streak_text.insert(tk.END, "Please choose a habit.\n")
            return
        streak = self.streak(habit)
        self.streak_text.insert(
            tk.END,
            f"Longest streak for chosen habit:\n\nHabit: {habit['name']}\nPeriodicity: {habit['periodicity']}\nStreak: {streak}\n",
        )
        self.streak_text.config(state="disabled")


  
    # Manage section---->>>>>>>
    
 

        self.refresh_selected_dates_listbox()




    def validate_integer(self, value_if_allowed):
        """This method checks and validates if the input is an integer or not to avoid invalid entries."""
        if value_if_allowed == "":
            return True
        if value_if_allowed.isdigit():
            return True

        messagebox.showwarning("Invalid Input", "Target periods must be an integer.")
        return False   
    def show_manage(self):
        """This method displays the manage section of the application, which allows users to add new habits with specific details and delete existing habits from the list."""
        self.current_section = "manage"
        self.clear_content()

        wrapper = tk.Frame(self.content, bg="#f3f4f6", padx=15, pady=15)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.columnconfigure(0, weight=1)
        wrapper.columnconfigure(1, weight=1)

        tk.Label(wrapper, text="Adding or Deleting Habits", font=("Arial", 20, "bold"), bg="#f3f4f6").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

 
        # Add panel --------------------------------------- 
        
        add_panel = tk.Frame(wrapper, bg="white", padx=15, pady=15, highlightbackground="#d1d5db", highlightthickness=1)
        add_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        add_panel.columnconfigure(1, weight=1)

        tk.Label(add_panel, text="Add New Habit", font=("Arial", 14, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(add_panel, text="Habit name:", bg="white", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=6)
        self.new_name_var = tk.StringVar()
        tk.Entry(add_panel, textvariable=self.new_name_var, width=32).grid(row=1, column=1, sticky="ew", pady=6)

        tk.Label(add_panel, text="Periodicity:", bg="white", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=6)
        self.new_period_var = tk.StringVar(value="daily")
        ttk.Combobox(
            add_panel,
            textvariable=self.new_period_var,
            values=["daily", "weekly"],
            state="readonly",
            width=29
        ).grid(row=2, column=1, sticky="ew", pady=6)

        tk.Label(add_panel, text="Choose dates:", bg="white", font=("Arial", 11)).grid(row=3, column=0, sticky="nw", pady=6)

        calendar_area = tk.Frame(add_panel, bg="white")
        calendar_area.grid(row=3, column=1, sticky="ew", pady=6)

        self.calendar_widget = Calendar(
            calendar_area,
            selectmode="day",
            date_pattern="yyyy-mm-dd"
        )
        self.calendar_widget.pack(anchor="w", pady=(0, 8))

        buttons_line = tk.Frame(calendar_area, bg="white")
        buttons_line.pack(anchor="w", pady=(0, 8))

        btn_add_date = tk.Button(buttons_line, text="Add Selected Date", command=self.add_selected_date)
        btn_add_date.pack(side="left", padx=(0, 8))
        btn_remove = tk.Button(buttons_line, text="Remove Selected Date", command=self.remove_selected_date)
        btn_remove.pack(side="left", padx=(0, 8))
        btn_clear = tk.Button(buttons_line, text="Clear Dates", command=self.clear_selected_dates)
        btn_clear.pack(side="left")
        self.add_hover_effect(btn_add_date, hover_bg="#dbeafe")
        self.add_hover_effect(btn_remove, hover_bg="#fee2e2")
        self.add_hover_effect(btn_clear, hover_bg="#f3f4f6")
        tk.Label(calendar_area, text="Selected dates:", bg="white", font=("Arial", 11)).pack(anchor="w", pady=(6, 4))

        self.selected_dates_listbox = tk.Listbox(calendar_area, height=8)
        self.selected_dates_listbox.pack(fill="x", expand=True)

        self.selected_dates_buffer = []

        tk.Label(add_panel, text="Target periods:", bg="white", font=("Arial", 11)).grid(row=4, column=0, sticky="w", pady=6)
        self.new_target_var = tk.StringVar(value="0")
        vcmd = (self.root.register(self.validate_integer), "%P")

        self.target_entry = tk.Entry(add_panel, textvariable=self.new_target_var,validate="key",validatecommand=vcmd, width=32)    
     
        self.target_entry.grid(row=4, column=1, sticky="ew", pady=6)

        btn_add_habit = tk.Button(add_panel, text="Add Habit", command=self.add_habit, width=16)
        btn_add_habit.grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.add_hover_effect(btn_add_habit, hover_bg="#dbeafe")

        # Delete panel ---------------------------------------
        delete_panel = tk.Frame(wrapper, bg="white", padx=15, pady=15, highlightbackground="#d1d5db", highlightthickness=1)
        delete_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(delete_panel, text="Delete Habit", font=("Arial", 14, "bold"), bg="white").pack(anchor="w", pady=(0, 10))

        self.delete_listbox = tk.Listbox(delete_panel, height=15)
        self.delete_listbox.pack(fill="both", expand=True, pady=(0, 10))
        self.refresh_delete_list()

        btn_delete_habit = tk.Button(delete_panel, text="Delete Selected Habit", command=self.delete_selected_habit, width=22)
        btn_delete_habit.pack(anchor="w")
        self.add_hover_effect(btn_delete_habit, hover_bg="#fee2e2")

    def add_habit(self):
        """This method handles the logic for adding a new habit based on user input from the manage section."""
        name = self.new_name_var.get().strip()
        periodicity = self.new_period_var.get().strip().lower()

        if not name:
            messagebox.showerror("Error", "Habit name cannot be empty.")
            return

        if periodicity not in ("daily", "weekly"):
            messagebox.showerror("Error", "Periodicity must be daily or weekly.")
            return

        if any(h["name"].lower() == name.lower() for h in self.habits):
            messagebox.showerror("Error", "A habit with this name already exists.")
            return

        if not self.selected_dates_buffer and self.new_target_var.get().strip() == "0":
            messagebox.showerror("Error", "Please choose at least one date.")
            return

        selected_dates = sorted(set(self.selected_dates_buffer))
        if selected_dates == [] and periodicity == "daily" and self.new_target_var.get().strip() != "0":
            start_date = self.start_date_for_new_habit(periodicity)
            target_days = int(self.new_target_var.get().strip())

            start_obj = datetime.strptime(start_date, DATE_FMT).date()

            selected_dates = [
                (start_obj + timedelta(days=i)).strftime(DATE_FMT)
                for i in range(target_days)
            ]

        #If user didn't used calendar but just defined Target Period, then take the current day and calculate the next weeks.

        if selected_dates == [] and periodicity == "weekly" and self.new_target_var.get().strip() != "0":
            start_date = self.start_date_for_new_habit2()
            target_days = int(self.new_target_var.get().strip())

            start_obj = datetime.strptime(start_date, DATE_FMT).date()

            selected_dates = [
                (start_obj + timedelta(days=i*7)).strftime(DATE_FMT)
                for i in range(target_days)
            ]

        self.habits.append(self.make_habit(name, periodicity, selected_dates))
        self.save_data()

        self.new_name_var.set("")
        self.new_period_var.set("daily")
        self.selected_dates_buffer = []
        self.refresh_selected_dates_listbox()
        self.refresh_delete_list()
        self.show_overview()

        messagebox.showinfo(
            "Success",
            f"Habit '{name}' added successfully.\nTarget periods: {len(selected_dates)}"
        )

    def refresh_delete_list(self):
        """This method refreshes the list of habits in the delete section to reflect any changes after adding or deleting habits."""
        if not hasattr(self, "delete_listbox"):
            return
        self.delete_listbox.delete(0, tk.END)
        for habit in self.habits:
            self.delete_listbox.insert(tk.END, f"{habit['name']} ({habit['periodicity']})")

    def start_date_for_new_habit(self, periodicity):
        today = date.today()
        if periodicity == "daily":
            return today.strftime(DATE_FMT)

        # weekly habit: if today is Monday, start today; otherwise start next Monday
        if today.weekday() == 0:
            return today.strftime(DATE_FMT)
        next_monday = today + timedelta(days=(7 - today.weekday()))
        
        return next_monday.strftime(DATE_FMT)
    

    def start_date_for_new_habit2(self):
        """This method calculates the start date for a new habit based on the current date and the periodicity of the habit, but only for weekly choices."""
        today = date.today()
        
        today.strftime(DATE_FMT)


        return today.strftime(DATE_FMT)
    

    def delete_selected_habit(self):
        """This method handles the deleting task of a selected habit from the list in the manage section."""
        selection = self.delete_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a habit to delete.")
            return

        index = selection[0]
        habit_name = self.habits[index]["name"]
        confirm = messagebox.askyesno("Confirm Delete", f"Delete habit '{habit_name}'?")
        if not confirm:
            return

        del self.habits[index]
        self.save_data()
        self.refresh_delete_list()
        messagebox.showinfo("Deleted", f"Habit '{habit_name}' deleted.")

    def refresh_selected_dates_listbox(self):
        
        self.selected_dates_buffer = sorted(set(self.selected_dates_buffer))
        self.selected_dates_listbox.delete(0, tk.END)

        for d in self.selected_dates_buffer:
            self.selected_dates_listbox.insert(tk.END, d)

        self.new_target_var.set(str(len(self.selected_dates_buffer)))


    def add_selected_date(self):
        """This method adds the date selected in the calendar widget to the list of selected dates."""
        selected_date = self.calendar_widget.get_date()

        if selected_date not in self.selected_dates_buffer:
            self.selected_dates_buffer.append(selected_date)

        self.refresh_selected_dates_listbox()
        self.target_entry.config(state="disabled")

    def remove_selected_date(self):
        """This method removes the date selected in the listbox from the list of selected dates."""
        selection = self.selected_dates_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a date to remove.")
            return

        index = selection[0]
        del self.selected_dates_buffer[index]
        self.refresh_selected_dates_listbox()


    def clear_selected_dates(self):
        """This method clears all the selected dates from the list."""
        self.selected_dates_buffer = []
        self.refresh_selected_dates_listbox()



    def add_hover_effect(self, widget, normal_bg=None, hover_bg=None, normal_fg=None, hover_fg=None, cursor="hand2"):

        #Visual effect for elements, when user hovers over them, it changes the background and foreground colors and cursor style to indicate interactivity.

        if normal_bg is None:
            normal_bg = widget.cget("bg")
        if normal_fg is None:
            normal_fg = widget.cget("fg")

        def on_enter(event):
            event.widget.config(cursor=cursor)
            if hover_bg is not None:
                event.widget.config(bg=hover_bg)
            if hover_fg is not None:
                event.widget.config(fg=hover_fg)

        def on_leave(event):
            event.widget.config(cursor="")
            if normal_bg is not None:
                event.widget.config(bg=normal_bg)
            if normal_fg is not None:
                event.widget.config(fg=normal_fg)

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

if __name__ == "__main__":
    root = tk.Tk()
    app = HabitTrackerApp(root)
    root.mainloop()
