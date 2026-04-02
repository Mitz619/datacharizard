"""
utils/email_sender.py  —  send HTML emails via Gmail (app password method)

Setup (one time):
  1. Go to myaccount.google.com → Security → App passwords
  2. Create one called "DataCharizard"
  3. Add GMAIL_APP_PASSWORD=xxxx to your .env
"""
import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import GMAIL_SENDER, GMAIL_RECIPIENT


def send_email(subject: str, html_body: str, recipient: str = None):
    """Send an HTML email through Gmail SMTP."""
    password = os.getenv("GMAIL_APP_PASSWORD", "")
    to = recipient or GMAIL_RECIPIENT

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, password)
            server.sendmail(GMAIL_SENDER, to, msg.as_string())
        print(f"  ✉️  Email sent → {to}: {subject}")
    except Exception as e:
        print(f"  ❌  Email failed: {e}")


def build_news_email(news_items: list, jobs: list = None) -> str:
    """Build a nice HTML digest."""
    rows = ""
    for item in news_items:
        rows += f"""
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid #eee">
            <a href="{item['url']}" style="font-weight:600;color:#e25822;
               text-decoration:none">{item['title']}</a>
            <br><span style="color:#888;font-size:13px">{item['source']}</span>
            <p style="margin:8px 0 0;color:#444;font-size:14px">{item['summary']}</p>
          </td>
        </tr>"""

    job_section = ""
    if jobs:
        jrows = "".join(f"""
        <tr>
          <td style="padding:8px 0;border-bottom:1px solid #f5f5f5">
            <a href="{j['url']}" style="font-weight:600;color:#333;text-decoration:none">
              {j['title']}</a> — <span style="color:#888">{j['company']}, {j['location']}</span>
          </td>
        </tr>""" for j in jobs)
        job_section = f"""
        <h2 style="color:#e25822;margin-top:32px">🧑‍💻 New jobs in Australia</h2>
        <table style="width:100%">{jrows}</table>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:640px;
                       margin:auto;padding:24px;color:#222">
      <h1 style="color:#e25822">🔥 DataCharizard Daily Digest</h1>
      <h2 style="color:#e25822">📰 Data Engineering News</h2>
      <table style="width:100%">{rows}</table>
      {job_section}
      <p style="margin-top:40px;color:#aaa;font-size:12px">
        Powered by DataCharizard · your personal data career agent
      </p>
    </body></html>"""
