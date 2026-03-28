# 📚 Study Buddy Tracker

A simple, intuitive study tracking app inspired by platforms like LeetCode and GitHub. Track your daily study habits, build streaks, and visualize your consistency over time.

---

## 🚀 Overview

Study Buddy Tracker helps users stay consistent with their learning by:

- Logging daily study sessions  
- Tracking total study time  
- Maintaining streaks  
- Visualizing activity through a heatmap (green boxes)  
- Identifying subjects that may need extra attention  

---

## 🎯 Features

### ✅ Core Features
- Add study sessions with:
  - Subject
  - Source (class, bootcamp, YouTube, textbook, etc.)
  - Notes (summary of what was learned)
  - Time spent studying

- Daily tracking:
  - Total hours studied per day
  - Number of sessions per day

- Streak system:
  - Current streak
  - Maximum streak

- Activity heatmap:
  - Visual representation of study consistency
  - Color intensity based on study time

- Stats dashboard:
  - Total hours studied
  - Days active
  - Max hours in a day
  - Current streak
  - Max streak

---

### 💡 Bonus Feature (In Progress)
- Tutoring recommendations:
  - Suggest subjects where users may need help
  - Based on:
    - Low study time (neglected subjects)
    - High repetition (potential difficulty)

---

## 🧱 Tech Stack

### Backend
- Python
- Flask

### Frontend
- React

### Database
- SQLite

---

## 🗄️ Database Schema

### `study_sessions`

| Column    | Type    | Description                          |
|----------|--------|--------------------------------------|
| id       | INTEGER | Primary Key                         |
| date     | TEXT    | Study date (YYYY-MM-DD)             |
| subject  | TEXT    | Subject studied                     |
| source   | TEXT    | Source of learning                  |
| notes    | TEXT    | Summary of session                  |
| duration | INTEGER | Time spent (in minutes or hours)    |

---

## ⚙️ How It Works

1. User logs a study session  
2. Data is stored in SQLite  
3. Backend aggregates data by date and subject  
4. Frontend displays:
   - Heatmap
   - Stats
   - Streaks  

---

## 🧠 Struggle Detection Logic

Subjects may be flagged for tutoring if:

- They have **low total study time** (neglected)  
- OR  
- They have **high total time + high frequency** (potential difficulty)  

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/study-buddy-tracker.git
cd study-buddy-tracker
