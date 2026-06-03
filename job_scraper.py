"""
Job Alert Mailer - Prototype
Scrapes job postings from major IT companies and sends a daily digest email.
"""

import smtplib
import json
import os
import hashlib
import time
import random
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote_plus
from urllib.error import URLError
import xml.etree.ElementTree as ET

# ── Config ──────────────────────────────────────────────────────────────────

EMAIL_SENDER   = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SEEN_JOBS_FILE = "seen_jobs.json"

# ── Companies & their Google Jobs search queries ─────────────────────────────
COMPANIES = [
    {
        "name": "TCS",
        "query": "TCS Tata Consultancy Services software engineer jobs India 2025",
        "logo": "🔵",
        "color": "#003087"
    },
    {
        "name": "Infosys",
        "query": "Infosys software engineer fresher jobs India 2025",
        "logo": "🟤",
        "color": "#007CC3"
    },
    {
        "name": "Accenture",
        "query": "Accenture software engineer associate jobs India 2025",
        "logo": "🟣",
        "color": "#A100FF"
    },
    {
        "name": "Deloitte",
        "query": "Deloitte software engineer analyst jobs India 2025",
        "logo": "🟢",
        "color": "#86BC25"
    },
    {
        "name": "Mindtree",
        "query": "Mindtree LTIMindtree software engineer jobs India 2025",
        "logo": "🔵",
        "color": "#00A0E3"
    },
    {
        "name": "Wipro",
        "query": "Wipro software engineer WILP freshers jobs India 2025",
        "logo": "🟠",
        "color": "#341C5A"
    },
]

# Walk-in search queries (India-specific)
WALKIN_QUERIES = [
    "TCS walk-in interview software engineer 2025",
    "Infosys walk-in drive software engineer 2025",
    "Wipro walk-in interview freshers 2025",
    "Accenture walk-in software engineer India 2025",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def job_id(title, link):
    return hashlib.md5(f"{title}{link}".encode()).hexdigest()

def fetch_google_rss(query):
    """Fetch jobs via Google News RSS (searches recent news about job postings)."""
    jobs = []
    try:
        encoded = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0)"})
        with urlopen(req, timeout=10) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        if channel is None:
            return jobs
        for item in channel.findall("item")[:5]:  # top 5 results per query
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            desc_el = item.find("description")
            title = title_el.text if title_el is not None else "No Title"
            link = link_el.text if link_el is not None else "#"
            pub = pub_el.text if pub_el is not None else ""
            desc = desc_el.text if desc_el is not None else ""
            # Filter: only include if it looks like a job/hiring post
            keywords = ["hire", "hiring", "job", "career", "recruit", "opening",
                        "walk-in", "walkin", "fresher", "engineer", "vacancy", "drive"]
            combined = (title + desc).lower()
            if any(k in combined for k in keywords):
                jobs.append({
                    "title": title,
                    "link": link,
                    "date": pub[:16] if pub else "Recent",
                    "source": "Google News"
                })
        time.sleep(random.uniform(1.0, 2.0))  # polite delay
    except (URLError, ET.ParseError) as e:
        print(f"  ⚠ RSS fetch error for '{query}': {e}")
    return jobs


def scrape_all_jobs():
    """Scrape jobs for all companies and walk-ins."""
    all_results = {}

    print("🔍 Scraping company job feeds...")
    for company in COMPANIES:
        print(f"  → {company['name']}...")
        jobs = fetch_google_rss(company["query"])
        print(jobs)
        all_results[company["name"]] = {
            "meta": company,
            "jobs": jobs
        }

    print("🚶 Scraping walk-in drives...")
    walkin_jobs = []
    for q in WALKIN_QUERIES:
        print(f"  → {q[:50]}...")
        walkin_jobs.extend(fetch_google_rss(q))
    all_results["Walk-in Drives"] = {
        "meta": {"name": "Walk-in Drives", "logo": "🚶", "color": "#E67E22"},
        "jobs": walkin_jobs
    }

    return all_results


def filter_new_jobs(all_results, seen_jobs):
    """Remove jobs already seen in previous runs."""
    new_results = {}
    new_seen = set(seen_jobs)

    for company_name, data in all_results.items():
        new_jobs = []
        for job in data["jobs"]:
            jid = job_id(job["title"], job["link"])
            if jid not in seen_jobs:
                new_jobs.append(job)
                new_seen.add(jid)
        if new_jobs:
            new_results[company_name] = {
                "meta": data["meta"],
                "jobs": new_jobs
            }

    return new_results, new_seen


# ── Email Builder ─────────────────────────────────────────────────────────────

def build_email_html(results):
    today = datetime.now().strftime("%A, %d %B %Y")
    total = sum(len(v["jobs"]) for v in results.values())

    sections = ""
    for company_name, data in results.items():
        meta = data["meta"]
        jobs = data["jobs"]
        if not jobs:
            continue

        job_rows = ""
        for j in jobs:
            title = j['title'].replace('<', '&lt;').replace('>', '&gt;')
            job_rows += f"""
            <tr>
              <td style="padding:12px 16px; border-bottom:1px solid #f0f0f0;">
                <a href="{j['link']}" style="color:#1a1a2e; font-weight:600;
                   text-decoration:none; font-size:14px; line-height:1.4;">{title}</a>
                <div style="color:#888; font-size:12px; margin-top:4px;">
                  📅 {j['date']} &nbsp;·&nbsp; 🔗 {j['source']}
                </div>
              </td>
            </tr>"""

        sections += f"""
        <div style="margin-bottom:28px; border-radius:12px; overflow:hidden;
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <div style="background:{meta['color']}; padding:14px 20px;
                      display:flex; align-items:center;">
            <span style="font-size:22px; margin-right:10px;">{meta['logo']}</span>
            <span style="color:#fff; font-weight:700; font-size:18px;
                         letter-spacing:0.5px;">{meta['name']}</span>
            <span style="margin-left:auto; background:rgba(255,255,255,0.25);
                         color:#fff; font-size:12px; padding:3px 10px;
                         border-radius:20px;">{len(jobs)} new</span>
          </div>
          <table style="width:100%; border-collapse:collapse; background:#fff;">
            {job_rows}
          </table>
        </div>"""

    if not sections:
        sections = """
        <div style="text-align:center; padding:40px; color:#888;">
          <div style="font-size:48px;">😴</div>
          <p style="font-size:16px;">No new job postings found today. Check back tomorrow!</p>
        </div>"""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0; padding:0; background:#f5f5f5; font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:640px; margin:0 auto; padding:20px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
                border-radius:16px; padding:30px; margin-bottom:24px; text-align:center;">
      <div style="font-size:36px; margin-bottom:8px;">💼</div>
      <h1 style="color:#fff; margin:0; font-size:24px; font-weight:700;">
        Daily Job Alert
      </h1>
      <p style="color:#a0b4cc; margin:8px 0 0; font-size:14px;">{today}</p>
      <div style="margin-top:16px; background:rgba(255,255,255,0.1);
                  border-radius:8px; padding:10px; display:inline-block;">
        <span style="color:#4fc3f7; font-size:28px; font-weight:700;">{total}</span>
        <span style="color:#a0b4cc; font-size:14px; margin-left:6px;">new postings found</span>
      </div>
    </div>

    <!-- Companies -->
    {sections}

    <!-- Footer -->
    <div style="text-align:center; color:#bbb; font-size:12px; padding:20px 0 10px;">
      <p>🤖 Auto-generated by your Job Alert Bot · Sources: Google News</p>
      <p style="margin-top:4px;">Coming soon: Naukri · LinkedIn · Indeed · Superset</p>
    </div>
  </div>
</body>
</html>"""


def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html_body, "html"))

    print(f"📧 Sending email to {EMAIL_RECEIVER}...")
    # Port 465 with SSL — works on Render
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_PASSWORD, msg.as_string())
    print("✅ Email sent!")    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.attach(MIMEText(html_body, "html"))

    print(f"📧 Sending email to {EMAIL_RECEIVER}...")
    # FIXED - port 587, TLS (works on Render and most cloud hosts)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
    print("✅ Email sent!")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*50}")
    print(f"  Job Alert Bot - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    seen_jobs = load_seen_jobs()
    all_results = scrape_all_jobs()
    new_results, updated_seen = filter_new_jobs(all_results, seen_jobs)

    total_new = sum(len(v["jobs"]) for v in new_results.values())
    print(f"\n📊 Found {total_new} new job postings\n")

    today_str = datetime.now().strftime("%d %b %Y")
    subject = f"💼 Job Alert: {total_new} New Postings — {today_str}"

    # Build and send email (even if 0 new jobs, sends a "nothing new" email)
    html = build_email_html(new_results)
    send_email(subject, html)

    save_seen_jobs(updated_seen)
    print("\n✅ Done! seen_jobs.json updated.\n")


if __name__ == "__main__":
    main()
