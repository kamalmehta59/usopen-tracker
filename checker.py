"""
US Open Ticket Tracker
Checks the USTA/Ticketmaster US Open ticket page and emails you when
tickets become available. Runs on GitHub Actions every 15 minutes.
"""

import os
import json
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from playwright.sync_api import sync_playwright

# ── Config (loaded from GitHub Secrets) ──────────────────────────────────────
GMAIL_ADDRESS   = os.environ["GMAIL_ADDRESS"]    # your Gmail address
GMAIL_APP_PASS  = os.environ["GMAIL_APP_PASS"]   # Gmail app password (not your login password)
NOTIFY_EMAIL    = os.environ["NOTIFY_EMAIL"]     # where to send alerts (can be same as above)

# The US Open ticket page on Ticketmaster
TICKET_URL = "https://www.ticketmaster.com/us-open-tennis-tickets/artist/805173"

# File that stores the last known page state (so we only alert on changes)
STATE_FILE = "last_state.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_last_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def hash_content(text: str) -> str:
    """Return a short hash so we can detect page changes without storing full HTML."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def scrape_tickets(url: str) -> dict:
    """
    Opens the ticket page in a headless browser and pulls out any
    event listings it can find. Returns a dict of {event_label: status}.
    """
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page.goto(url, wait_until="networkidle", timeout=30_000)

        # Wait for event cards to load
        try:
            page.wait_for_selector("[class*='EventCard'], [data-testid*='event']", timeout=10_000)
        except Exception:
            pass  # page may have a different structure; we'll hash whatever loaded

        # Grab all event card text as a lightweight availability signal
        cards = page.query_selector_all("[class*='EventCard'], [data-testid*='event'], li[class*='event']")

        if cards:
            for card in cards:
                text = card.inner_text().strip()
                if text:
                    label = text[:120]  # trim to a readable length
                    results[label] = "available"
        else:
            # Fallback: hash the full page body so any change triggers an alert
            body = page.inner_text("body")
            results["__page_hash__"] = hash_content(body)

        browser.close()

    return results


def send_email(subject: str, body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = NOTIFY_EMAIL

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        server.sendmail(GMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())
    print("Alert email sent.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Checking: {TICKET_URL}")
    current = scrape_tickets(TICKET_URL)
    last    = load_last_state()

    new_listings = {k: v for k, v in current.items() if k not in last}
    changed      = current != last

    if new_listings:
        subject = "🎾 US Open tickets found!"
        lines   = [f"New ticket listings detected:\n"]
        for label in new_listings:
            lines.append(f"  • {label}")
        lines.append(f"\nBuy now: {TICKET_URL}")
        body = "\n".join(lines)
        send_email(subject, body)

    elif changed and "__page_hash__" in current:
        # Fallback: page changed but we couldn't parse specific cards
        subject = "🎾 US Open ticket page changed — check now!"
        body    = (
            "The US Open ticket page has changed since the last check.\n"
            "This may mean tickets have gone on sale.\n\n"
            f"Check here: {TICKET_URL}"
        )
        send_email(subject, body)

    else:
        print("No changes detected.")

    save_state(current)


if __name__ == "__main__":
    main()
