# Khadia Seva

Production-ready MVP for a civic complaint management platform restricted to Khadia ward residents.

## Tech Stack
- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML + TailwindCSS + Vanilla JS
- **Auth:** Session + OTP simulation
- **Uploads:** Local `uploads/`

## Project Structure
```
Khadia-Seva/
├── app/
│   └── __init__.py
├── models/
│   ├── db.py
├── routes/
│   ├── auth.py
│   ├── user.py
│   └── admin.py
├── templates/
├── static/
│   └── js/
├── uploads/
├── requirements.txt
└── run.py
```

## Database Schema
Tables created automatically at app startup:
- `users` (citizens/admin)
- `complaints` (complaint records)
- `notifications` (in-app updates)
- `complaint_updates` (timeline/status history)

Admin account is auto-seeded:
- Mobile: `9999999999`
- Role: `admin`

## Setup
1. Create virtual env and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run server:
   ```bash
   python run.py
   ```

3. Open:
   - `http://127.0.0.1:5000`

## How OTP Login Works
- Enter mobile number
- OTP is simulated and shown in flash message
- Enter OTP + ward/pincode
- Ward restriction allows:
  - Ward = `Khadia`, OR
  - Pincode in allow-list (`380001`, `380002`, `380008`, `380016`)

## AI-Based Smart Features
1. **Auto Categorization:** Suggests complaint category based on keywords.
2. **Priority Detection:** Flags urgent words (danger, accident, leakage, etc.) as `High` priority.

## Core Flows
- **User:** login → submit complaint (title, desc, image, location) → track status/timeline
- **Admin:** login → filter/search complaints → assign team member → update status → user notification generated

