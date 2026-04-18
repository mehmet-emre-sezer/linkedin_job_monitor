import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send_job_notification(job: dict, score: int | None, reason: str | None):
    score_line      = f"⭐ Puan: *{score}/100*\n"                    if score is not None      else ""
    reason_line     = f"🧠 {_escape(reason)}\n"                      if reason                 else ""
    location_line   = f"📍 {_escape(job.get('location', ''))}\n"     if job.get("location")    else ""
    posted_line     = f"🕐 {_escape(job.get('posted_at', ''))}\n"    if job.get("posted_at")   else ""
    applicants_line = f"👥 {_escape(job.get('applicants', ''))}\n"   if job.get("applicants")  else ""
    text = (
        f"🔥 *{_escape(job['title'])}*\n"
        f"🏢 {_escape(job['company'])}\n"
        f"{location_line}"
        f"{posted_line}"
        f"{applicants_line}"
        f"{score_line}"
        f"{reason_line}"
        f"🔗 [İlana Git]({job['link']})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"Notified: {job['title']} ({score})")
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")


def send_summary(total_scraped: int, total_scored: int, sent: int):
    text = (
        f"✅ *Tarama tamamlandı*\n"
        f"Taranan: {total_scraped} | Yeni: {total_scored} | Gönderilen: {sent}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        logger.error(f"Summary notification failed: {e}")


def _escape(text: str) -> str:
    for ch in ["_", "*", "[", "]", "`"]:
        text = text.replace(ch, f"\\{ch}")
    return text
