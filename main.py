import os
import sys
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from twilio.rest import Client
from utils import log_and_print
from utils import safe_print  # make sure this is in utils.py

# === Load environment variables ===
load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
LOGIN_URL = os.getenv("LOGIN_URL", "https://n.tmura.co.il/amuta/?source=amuta")
KEYWORD = "קיץ"

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# === Setup logging ===
log_file_path = os.path.join(os.path.dirname(__file__), "check_log.txt")

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)

def send_sms_alert(message):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        sms = client.messages.create(
            body=message,
            from_=TWILIO_FROM,
            to=TWILIO_TO
        )
        logging.info(f"📩 SMS alert sent. SID: {sms.sid}")
        log_and_print(f"📩 SMS alert sent. SID: {sms.sid}")
    except Exception as e:
        logging.error(f"❌ Failed to send SMS: {e}")
        log_and_print(f"❌ Failed to send SMS: {e}")

def check_vacation_proposals():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            log_and_print("🔐 Navigating to login page...")
            page.goto(LOGIN_URL, timeout=60000)
            if not USERNAME or not PASSWORD:
                log_and_print("❌ Missing USERNAME or PASSWORD in .env file")
                sys.exit(1)

            page.fill("#userName", USERNAME)
            page.fill("#password", PASSWORD)
            page.click("button.btn-loginPass")
            page.wait_for_timeout(5000)

            proposal_divs = page.query_selector_all('div[data-font-size="20"]')
            log_and_print(f"🔍 Found {len(proposal_divs)} proposals to scan.",is_hebrew=True)
            logging.info(f"🔍 Found {len(proposal_divs)} proposals to scan.")

            found = False
            for div in proposal_divs:
                try:
                    text = div.inner_text().strip()
                    logging.info(f"📝 Scanning: {text}")
                    log_and_print(f"📝 Scanning: {text}")
                    if KEYWORD in text:
                        logging.info(f"✅ Proposal matched: {text}")
                        log_and_print("🎉 Proposal found! Sending SMS...")
                        send_sms_alert(f"🏖️🏖️🏖️🏖️ יש מידע לגבי חופשות {KEYWORD}! ✈️\n{text}")
                        found = True
                except Exception as scan_err:
                    logging.warning(f"⚠️ Could not read proposal text: {scan_err}")


            if not found:
                logging.info(f"❌ No proposals containing '{KEYWORD}' found.")
                log_and_print(f"❌ No proposals containing '{KEYWORD}' found.",is_hebrew=True)
                send_sms_alert(f"\n אין מידע לגבי חופשות {KEYWORD} ✈️")


            browser.close()

    except Exception as e:
        logging.error(f"❗ Script failed: {e}")
        log_and_print(f"❗ Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_vacation_proposals()
