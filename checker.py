import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# --- CONFIG ---
TICKETMASTER_URL = "https://www.ticketmaster.com/us-open-tennis-tickets/artist/805173"
ALERT_CRITERIA = {
    "venue": "USTA Billie Jean King",
    "date_range": "Aug 25 – Sep 7",
    "max_price": 200,
}
SENDER_EMAIL = "nykamal@gmail.com"
RECIPIENT_EMAIL = "nykamal@gmail.com"
APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]  # never hardcode

def scrape_listings() -> list[dict]:
    """
    Replace this stub with your real scraping logic.
    Returns a list of dicts with keys: venue, date, section, row, seat, price, url
    """
    # Example — replace with actual parsed results:
    return [
        {"venue": "Arthur Ashe Stadium", "date": "Sep 2 (Day)", "section": "103", "row": "J", "seat": "14", "price": 148, "url": TICKETMASTER_URL},
        {"venue": "Louis Armstrong Stadium", "date": "Aug 28 (Evening)", "section": "201", "row": "C", "seat": "7", "price": 89, "url": TICKETMASTER_URL},
    ]

def build_listing_rows(listings: list[dict]) -> str:
    rows = ""
    for t in listings:
        rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 10px 8px;">
            <strong>{t['venue']}</strong><br>
            <span style="color: #666; font-size: 13px;">{t['date']} · Sec {t['section']}, Row {t['row']}, Seat {t['seat']}</span>
          </td>
          <td style="padding: 10px 8px; text-align: right; color: #1a7a4a; font-weight: bold;">${t['price']}</td>
          <td style="padding: 10px 8px; text-align: right;">
            <a href="{t['url']}" style="background:#1a5276; color:#fff; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 13px;">Buy now</a>
          </td>
        </tr>"""
    return rows

def build_html_email(listings: list[dict]) -> str:
    detected_at = datetime.now().strftime("%a %b %-d, %Y at %-I:%M %p")
    criteria = ALERT_CRITERIA
    rows = build_listing_rows(listings)
    count = len(listings)

    return f"""
    <html><body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
    <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; overflow: hidden;">

      <div style="background: #1a5276; padding: 20px; color: white;">
        <h2 style="margin: 0;">🎾 US Open ticket alert</h2>
        <p style="margin: 4px 0 0; font-size: 13px; opacity: 0.8;">
          Detected {detected_at} — act quickly, these sell fast
        </p>
      </div>

      <div style="padding: 16px 20px; background: #eaf2fb; border-bottom: 1px solid #d0e8f7;">
        <p style="margin: 0 0 8px; font-size: 12px; color: #555; text-transform: uppercase;">Your alert criteria</p>
        <span style="font-size: 13px; background: #d6eaf8; color: #1a5276; padding: 4px 10px; border-radius: 6px; margin-right: 6px;">📍 {criteria['venue']}</span>
        <span style="font-size: 13px; background: #d6eaf8; color: #1a5276; padding: 4px 10px; border-radius: 6px; margin-right: 6px;">📅 {criteria['date_range']}</span>
        <span style="font-size: 13px; background: #d6eaf8; color: #1a5276; padding: 4px 10px; border-radius: 6px;">💲 Max ${criteria['max_price']}</span>
      </div>

      <div style="padding: 20px;">
        <p style="margin: 0 0 12px; font-size: 12px; color: #888; text-transform: uppercase;">{count} new listing{'s' if count != 1 else ''} found</p>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
          {rows}
        </table>
      </div>

      <div style="padding: 14px 20px; border-top: 1px solid #eee; text-align: right;">
        <a href="{TICKETMASTER_URL}" style="background: #1a5276; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 13px;">
          View all listings →
        </a>
      </div>

      <div style="padding: 12px 20px; font-size: 11px; color: #aaa;">
        Sent by your US Open ticket watcher script.
      </div>
    </div>
    </body></html>"""

def send_alert(listings: list[dict]):
    if not listings:
        print("No listings found, skipping email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎾 US Open tickets found ({len(listings)} listing{'s' if len(listings) != 1 else ''})"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    html = build_html_email(listings)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print(f"Alert sent for {len(listings)} listing(s).")

if __name__ == "__main__":
    listings = scrape_listings()
    send_alert(listings)