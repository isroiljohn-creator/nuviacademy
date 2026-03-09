# Fitness AI Telegram Bot 🤖

Professional Telegram Bot for fitness tracking, AI workout/meal plans, and gamification.

## 🚀 Features

- **Smart Onboarding**: Button-based registration (Name, Age, Gender, Height, Weight, Goal, Allergy).
- **AI Integration**: Google Gemini 2.5 Flash for personalized plans and Q&A.
- **Database**: SQLite (via SQLAlchemy) for user data and tracking.
- **Admin Panel**: Broadcast messages, view statistics.
- **Gamification**: Points system, challenges, leaderboard.
- **Premium**: Subscription model for advanced AI features.

## 📂 Project Structure

```
fitness_bot/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── .env.example         # Environment variables
├── core/
│   ├── db.py            # SQLite Database Manager
│   ├── ai.py            # AI Service + Fallback
│   └── utils.py         # Utilities
└── bot/
    ├── handlers.py      # Handler Aggregator
    ├── keyboards.py     # Inline & Reply Keyboards
    ├── onboarding.py    # Registration Flow
    ├── menu.py          # Main Menu Logic
    ├── workout.py       # AI Plan Generation
    ├── referral.py      # Referral System
    ├── gamification.py  # Daily Tasks
    ├── admin.py         # Admin Panel
    └── reminders.py     # Background Thread
```

## 🛠 Installation & Run

### 1. Clone & Setup
```bash
# Create project directory
mkdir fitness_bot
cd fitness_bot

# Copy files (if not already done)
# ...
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Rename `.env.example` to `.env` and fill in your details:
```ini
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ADMIN_ID=your_telegram_id
```

### 4. Run the Bot
```bash
python main.py
```

## ☁️ Deployment Guide

### PythonAnywhere
1. Upload files to PythonAnywhere.
2. Open a Bash console.
3. Run `pip install -r requirements.txt --user`.
4. Go to **Web** tab (if using webhook) or just run `python main.py` in a **Always-on task** (recommended for polling).

### Render / Railway
1. Create a new service connected to your repo.
2. Set Build Command: `pip install -r requirements.txt`
3. Set Start Command: `python main.py`
4. Add Environment Variables in the dashboard.

### VPS (Systemd Service)
Create a service file `/etc/systemd/system/fitness_bot.service`:
```ini
[Unit]
Description=Fitness AI Bot
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/fitness_bot
ExecStart=/usr/bin/python3 /path/to/fitness_bot/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable and start:
```bash
sudo systemctl enable fitness_bot
sudo systemctl start fitness_bot
```

## 🛡 Debugging
- If AI fails, the bot automatically switches to **Offline Fallback**.
- Check `fitness_bot.db` for user data.
- Logs are printed to the console.
