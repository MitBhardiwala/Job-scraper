from flask import Flask, jsonify
from datetime import datetime
import traceback

from job_scraper import (
    load_seen_jobs,
    scrape_all_jobs,
    filter_new_jobs,
    build_email_html,
    send_email,
    save_seen_jobs,
)

app = Flask(__name__)


@app.route("/run", methods=["GET"])
def run_scraper():
    try:
        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        seen_jobs = load_seen_jobs()
        all_results = scrape_all_jobs()
        new_results, updated_seen = filter_new_jobs(all_results, seen_jobs)

        total_new = sum(len(v["jobs"]) for v in new_results.values())

        today_str = datetime.now().strftime("%d %b %Y")
        subject = f"Job Alert: {total_new} New Postings — {today_str}"
        html = build_email_html(new_results)
        send_email(subject, html)

        save_seen_jobs(updated_seen)

        # Build a simple summary to show in browser
        summary = {}
        for company, data in new_results.items():
            summary[company] = [
                {"title": j["title"], "link": j["link"], "date": j["date"]}
                for j in data["jobs"]
            ]

        return jsonify({
            "status": "success",
            "started_at": started_at,
            "total_new_jobs": total_new,
            "email_sent_to": "configured receiver",
            "jobs": summary,
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc(),
        }), 500


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Job Alert Bot is running",
        "endpoints": {
            "GET /run": "Trigger scraper, send email, return found jobs as JSON"
        }
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
