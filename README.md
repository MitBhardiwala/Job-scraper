# 💼 Daily Job Alert Bot — Prototype

Sends a daily 7 AM email digest of new software engineer job postings from:
**TCS · Infosys · Accenture · Deloitte · Mindtree · Wipro** + Walk-in Drives

---

## 📁 Project Structure

```
job-mailer/
├── job_scraper.py          # Main script: scrapes + sends email
├── config.py               # Your credentials (DO NOT commit this!)
├── requirements.txt        # Dependencies (all built-in for prototype)
├── seen_jobs.json          # Auto-created: tracks sent jobs (no duplicates)
└── .github/
    └── workflows/
        └── daily_job_alert.yml   # GitHub Actions cron (free cloud scheduler)
```

---

## ⚙️ Setup Guide

### Step 1 — Clone / Download
```bash
git clone <your-repo-url>
cd job-mailer
```

### Step 2 — Get Gmail App Password
1. Go to [myaccount.google.com](https://myaccount.google.com) → **Security**
2. Enable **2-Step Verification** (required)
3. Search for **"App Passwords"** → Select app: Mail → Generate
4. Copy the 16-character password shown

### Step 3 — Edit config.py
```python
EMAIL_SENDER   = "you@gmail.com"
EMAIL_PASSWORD = "abcd efgh ijkl mnop"  # your App Password
EMAIL_RECEIVER = "you@gmail.com"        # where to receive alerts
```

### Step 4 — Test locally
```bash
python job_scraper.py
```
Check your inbox. You should receive a formatted job digest email!

---

## ⏰ Scheduling Options

### Option A — GitHub Actions (Recommended, Free, No server needed)

1. Push your code to a **private** GitHub repo
2. Go to repo → **Settings → Secrets and variables → Actions**
3. Add these 3 secrets:
   - `EMAIL_SENDER`
   - `EMAIL_PASSWORD`
   - `EMAIL_RECEIVER`
4. The `.github/workflows/daily_job_alert.yml` runs automatically at **7 AM IST** every day

> ✅ Free, reliable, no server required, works 24/7

---

### Option B — Cron Job (Linux / Mac / WSL)

```bash
# Open crontab editor
crontab -e

# Add this line (runs at 7:00 AM IST = 1:30 AM UTC)
30 1 * * * cd /path/to/job-mailer && python3 job_scraper.py >> logs/cron.log 2>&1
```

---

### Option C — Windows Task Scheduler

1. Open **Task Scheduler** → Create Basic Task
2. Trigger: **Daily at 7:00 AM**
3. Action: **Start a program**
   - Program: `python`
   - Arguments: `C:\path\to\job-mailer\job_scraper.py`
   - Start in: `C:\path\to\job-mailer\`

---

## 🔮 Roadmap (Future Additions)

| Feature | How to add |
|---|---|
| Naukri.com jobs | Scrape their RSS or use Selenium |
| LinkedIn jobs | LinkedIn Jobs RSS: `linkedin.com/jobs/search/?keywords=...&format=rss` |
| Indeed jobs | Indeed RSS: `indeed.com/rss?q=software+engineer&l=India` |
| Superset | Direct API/scrape of superset.ai |
| Telegram alert | Add `python-telegram-bot` alongside email |
| Filter by city | Add city filter to queries (e.g., "Bangalore", "Pune") |
| Experience level | Add "fresher" / "0-2 years" filter |
| Unsubscribe link | Add a simple Flask endpoint |

---

## ⚠️ Important Notes

- `config.py` is in `.gitignore` — never push your credentials
- `seen_jobs.json` grows over time — safe to delete to "reset" and resend all
- Google News RSS may occasionally miss postings; direct Naukri/LinkedIn scraping (future) will be more reliable
- For production use, consider storing credentials in environment variables or a `.env` file

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `SMTPAuthenticationError` | Use App Password, not your Gmail password |
| No jobs found | Google News RSS may be rate-limiting; try again in 30 min |
| Email goes to spam | Add your sender to contacts; use a proper email subject |
| `ModuleNotFoundError` | All modules are built-in; check Python version ≥ 3.7 |
