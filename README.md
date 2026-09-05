# 🇬🇧 Amazon UK Job Notifier (Coventry, Birmingham, Derby)

Automated monitoring system for [jobsatamazon.co.uk](https://www.jobsatamazon.co.uk/app#/jobSearch) that checks hourly for shift drops in **Coventry**, **Birmingham**, and **Derby** and dispatches instant push notifications directly to your **Telegram Mobile App**.

---

## 🚀 Quick Setup Guide

### Step 1: Create your Telegram Bot (Takes 60 Seconds)

1. Open **Telegram** on your phone or desktop and search for `@BotFather`.
2. Tap **Start** and send `/newbot`.
3. Follow the prompt to give your bot a name (e.g. `MyAmazonJobBot`) and a username ending in `bot` (e.g. `uk_job_notifier_bot`).
4. `@BotFather` will reply with your **HTTP API Token** (e.g., `7123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Copy this token!
5. Open your newly created bot in Telegram and tap **Start** (important!).
6. Next, search for `@userinfobot` in Telegram and send any message to get your numeric **Telegram Chat ID** (e.g., `123456789`).

---

### Step 2: Configure your Bot Credentials

Edit `config.json` in this folder:

```json
{
  "target_locations": [
    "Coventry",
    "Birmingham",
    "Derby"
  ],
  "check_interval_minutes": 60,
  "telegram": {
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID_HERE"
  },
  "url": "https://www.jobsatamazon.co.uk/app#/jobSearch"
}
```

---

### Step 3: Test your Telegram Connection

Run the test script from your terminal:

```bash
cd /Users/sumanmac/.gemini/antigravity/scratch/amazon_job_notifier
./venv/bin/python test_notifier.py
```

If configured correctly, you will receive a test message on your phone's Telegram app:
> 🎉 **Amazon UK Job Notifier is working!**

---

### Step 4: Run the Job Monitor

#### Option A: Run a single check now
```bash
./venv/bin/python monitor.py --single-run
```

#### Option B: Run continuously in background (Hourly Loop)
```bash
./venv/bin/python monitor.py
```

---

## 🛠️ Project Structure

| File | Purpose |
| :--- | :--- |
| [`monitor.py`](file:///Users/sumanmac/.gemini/antigravity/scratch/amazon_job_notifier/monitor.py) | Main Playwright scraper and filter loop |
| [`notifier.py`](file:///Users/sumanmac/.gemini/antigravity/scratch/amazon_job_notifier/notifier.py) | Telegram notification dispatch module |
| [`config.json`](file:///Users/sumanmac/.gemini/antigravity/scratch/amazon_job_notifier/config.json) | User preferences (locations, token, chat ID, interval) |
| [`seen_jobs.json`](file:///Users/sumanmac/.gemini/antigravity/scratch/amazon_job_notifier/seen_jobs.json) | Keeps track of notified jobs to prevent duplicates |
| [`test_notifier.py`](file:///Users/sumanmac/.gemini/antigravity/scratch/amazon_job_notifier/test_notifier.py) | Verifies Telegram bot credentials |

---

## 💡 Tips & Customizations
- **Change Check Frequency**: Edit `check_interval_minutes` in `config.json`.
- **Add Postcodes or Locations**: Add postcodes (e.g. `CV1`, `B1`, `DE1`) or nearby areas to `target_locations` in `config.json`.
