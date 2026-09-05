import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = (bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
        self.chat_id = (chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, text: str) -> bool:
        if not self.bot_token or self.bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
            logging.warning("Telegram Bot Token is not configured. Message logged to console instead:\n" + text)
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            data = response.json()
            if data.get("ok"):
                logging.info(f"Telegram notification sent successfully to chat {self.chat_id}.")
                return True
            else:
                logging.error(f"Failed to send Telegram message: {data.get('description')}")
                return False
        except Exception as e:
            logging.error(f"Error sending Telegram notification: {e}")
            return False

    def send_job_alert(self, job: dict, search_url: str) -> bool:
        title = job.get("title", "Amazon Warehouse Position")
        location = job.get("location", "Unknown Location")
        pay_rate = job.get("pay_rate", "See Website")
        job_type = job.get("job_type", "Standard Shift")
        duration = job.get("duration", "Fixed-term / Permanent")

        message = (
            f"⚡ *NEW AMAZON UK JOB DETECTED!*\n\n"
            f"📋 *Role:* {title}\n"
            f"📍 *Location:* {location}\n"
            f"💰 *Pay Rate:* {pay_rate}\n"
            f"⏳ *Type:* {job_type} ({duration})\n\n"
            f"🔗 [Click Here to Claim Shift on JobsAtAmazon]({search_url})\n\n"
            f"⏰ _Detected at {job.get('detected_at', 'Now')}_"
        )
        return self.send_message(message)
