import os
import sys
import json
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from twilio.rest import Client
from utils import log_and_print
from utils import safe_print  # make sure this is in utils.py

# === Load environment variables ===
load_dotenv(override=True)

LOGIN_URL = os.getenv("LOGIN_URL", "https://n.tmura.co.il/amuta/Category")

# Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM = os.getenv("TWILIO_FROM", "").strip()
TWILIO_TO = os.getenv("TWILIO_TO", "").strip()
USERNAME = os.getenv("USERNAME", "").strip()
PASSWORD = os.getenv("PASSWORD", "").strip()

# === Setup logging ===
log_file_path = os.path.join(os.path.dirname(__file__), "check_log.txt")
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    encoding="utf-8"
)

PROPOSALS_FILE = "proposals.json"

def load_previous_proposals():
    if os.path.exists(PROPOSALS_FILE):
        with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_proposals_to_file(proposals):
    with open(PROPOSALS_FILE, "w", encoding="utf-8") as f:
        json.dump(proposals, f, ensure_ascii=False, indent=2)

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
            try:
                page.goto(LOGIN_URL, timeout=120000)
            except Exception as e:
                log_and_print(f"❌ Page navigation failed: {e}")
                browser.close()
                return

            if not USERNAME or not PASSWORD:
                log_and_print("❌ Missing USERNAME or PASSWORD in .env file")
                sys.exit(1)
          
            page.fill("#userName", USERNAME)
            page.fill("#password", PASSWORD)
            page.click("button.btn-loginPass")
            page.wait_for_timeout(5000)
            page.screenshot(path="after_login.png", full_page=True)

            proposal_divs = page.query_selector_all('div[data-font-size="20"]')
            log_and_print(f"🔍 Found {len(proposal_divs)} proposals to scan.", is_hebrew=True)
            logging.info(f"🔍 Found {len(proposal_divs)} proposals to scan.")

            current_proposals = []
            for div in proposal_divs:
                try:
                    text = div.inner_text().strip()
                    current_proposals.append(text)
                    log_and_print(f"📝 הצעה נמצאה: {text}", is_hebrew=True)
                except Exception as scan_err:
                    logging.warning(f"⚠️ Could not read proposal text: {scan_err}")

            previous_proposals = load_previous_proposals()
            new_proposals = [p for p in current_proposals if p not in previous_proposals]

            if new_proposals:
                log_and_print(f"{len(new_proposals)} נמצאו הצעות חדשות!", is_hebrew=True)
                for proposal in new_proposals:
                    log_and_print(f"✨ חדשה: {proposal}", is_hebrew=True)
                send_sms_alert(f"📣 הצעות חדשות להצגה באתר {len(new_proposals)} ")
                save_proposals_to_file(current_proposals)
            else:
                log_and_print("❌ אין הצעות חדשות מהפעם הקודמת.", is_hebrew=True)

            browser.close()

    except Exception as e:
        logging.error(f"❗ Script failed: {e}")
        log_and_print(f"❗ Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_vacation_proposals()
