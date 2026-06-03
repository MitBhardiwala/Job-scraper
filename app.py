from flask import Flask, jsonify
from datetime import datetime
import traceback
import threading

from job_scraper import (
    load_seen_jobs,
    scrape_all_jobs,
    filter_new_jobs,
    build_email_html,
    send_email,
    save_seen_jobs,
)

app = Flask(__name__)

def scraper_task():
    """Runs in background thread — scrapes and sends email."""
    try:
        seen_jobs = load_seen_jobs()
        all_results = scrape_all_jobs()
        new_results, updated_seen = filter_new_jobs(all_results, seen_jobs)

        total_new = sum(len(v["jobs"]) for v in new_results.values())
        today_str = datetime.now().strftime("%d %b %Y")
        subject = f"Job Alert: {total_new} New Postings — {today_str}"
        html = build_email_html(new_results)
        send_email(subject, html)
        save_seen_jobs(updated_seen)
        print(f"✅ Scraper done. {total_new} new jobs found and emailed.")
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        traceback.print_exc()


@app.route("/run", methods=["GET"])
def run_scraper():
    thread = threading.Thread(target=scraper_task)
    thread.daemon = True
    thread.start()
    return jsonify({
        "status": "started",
        "message": "Scraper is running in background. Check your email in ~1-2 minutes.",
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Job Alert Bot is running",
        "endpoints": {
            "GET /run": "Trigger scraper and send email"
        }
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)