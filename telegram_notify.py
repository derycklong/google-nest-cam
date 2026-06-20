import os
import time
import datetime
import requests
from tools import logger

_last_sent_time = 0


def _get_config():
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    interval = int(os.environ.get("TELEGRAM_MESSAGE_INTERVAL", "60"))
    return token, chat_id, interval


def send_telegram_message(text):
    """Send a Telegram message. Rate-limited by TELEGRAM_MESSAGE_INTERVAL minutes."""
    token, chat_id, interval = _get_config()
    if not token or not chat_id:
        return False

    global _last_sent_time
    now = time.time()
    if now - _last_sent_time < interval * 60:
        logger.debug("Telegram message skipped due to message interval")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        resp.raise_for_status()
        _last_sent_time = now
        logger.info("Telegram notification sent")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def notify_auth_failure(reason):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram_message(
        f"<b>Nest Cam Alert</b>\n"
        f"Master token authentication failed.\n"
        f"<b>Reason:</b> {reason}\n"
        f"<b>Time:</b> {timestamp}"
    )
