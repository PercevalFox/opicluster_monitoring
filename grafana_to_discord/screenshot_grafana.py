import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

current_time = datetime.now().strftime("%H:%M")

# Load env vars from .env file
load_dotenv()
GRAFANA_URL = os.getenv("GRAFANA_DASHBOARD_URL")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
SCREENSHOT_PATH = "/tmp/grafana.png"
LAST_MESSAGE_ID_FILE = "/tmp/last_discord_message_id.txt"

# Safety check
if not GRAFANA_URL or not WEBHOOK_URL:
    print("❌ Missing required env vars. Please set GRAFANA_DASHBOARD_URL and DISCORD_WEBHOOK.")
    exit(1)

# Setup headless Chrome
options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    print(f"[INFO] Accessing Grafana dashboard at {GRAFANA_URL}")
    driver.get(GRAFANA_URL)

    # Wait for canvas or SVG elements (rendered graphs)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "canvas, svg.panel-render"))
        )

        # Trigger rendering of lazy panels
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

        print("[INFO] Dashboard fully rendered.")

    except Exception as e:
        print("[ERROR] Timeout while waiting for dashboard rendering.")
        driver.save_screenshot("/tmp/grafana_error.png")
        raise e

    driver.save_screenshot(SCREENSHOT_PATH)
    print(f"[INFO] Screenshot saved to {SCREENSHOT_PATH}")

finally:
    driver.quit()

# Delete previous message
def delete_last_message():
    if os.path.exists(LAST_MESSAGE_ID_FILE):
        with open(LAST_MESSAGE_ID_FILE, "r") as f:
            last_id = f.read().strip()
        if last_id:
            print(f"[INFO] Deleting previous Discord message ID {last_id}")
            delete_url = f"{WEBHOOK_URL}/messages/{last_id}"
            response = requests.delete(delete_url)
            if response.status_code == 204:
                print("[✅] Previous message successfully deleted.")
            else:
                print(f"[⚠️] Failed to delete message {last_id}")
                print(f"[DEBUG] Status code: {response.status_code}")
                print(f"[DEBUG] Response: {response.text}")

# Post new message
def post_new_message():
    with open(SCREENSHOT_PATH, "rb") as img:
        response = requests.post(
            WEBHOOK_URL,
            files={"file": ("grafana.png", img, "image/png")},
            data = {"content": f"📊 Opicluster status update ({current_time})"},
        )
        if response.status_code == 200:
            msg_id = response.json()["id"]
            with open(LAST_MESSAGE_ID_FILE, "w") as f:
                f.write(msg_id)
            print(f"[INFO] New message sent (ID: {msg_id})")
        else:
            print(f"[ERROR] Failed to send message: {response.status_code} - {response.text}")

# Execute logic
delete_last_message()
post_new_message()
