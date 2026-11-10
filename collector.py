"""
NoizVpn Subscription Service - main collector
جمع‌آوری کانفیگ از کانال‌های تلگرام و لینک‌های ساب خارجی،
تغییر نام و ایموجی، حذف تکراری، محدود کردن به ۲۰۰۰،
و انتشار به صورت لینک ساب (plain + base64).
"""

import base64
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

import config
import parser

USER_AGENT = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

STATS = {"telegram": 0, "subscriptions": 0, "total": 0, "unique": 0, "failed": []}


def log(msg):
    print(f"[noizvpn] {msg}", flush=True)


def fetch(url, timeout=30):
    resp = requests.get(url, timeout=timeout, headers=USER_AGENT)
    resp.raise_for_status()
    return resp.text


def fetch_telegram_channel(channel):
    """پیام‌های یک کانال عمومی تلگرام را از ویجت وب می‌خواند."""
    name = channel.strip().lstrip("@")
    url = f"https://t.me/s/{name}"
    html = fetch(url)
    soup = BeautifulSoup(html, "html.parser")
    texts = []
    for div in soup.find_all("div", class_="tgme_widget_message_text"):
        texts.append(div.get_text("\n"))
    for tag in soup.find_all(["code", "pre"]):
        texts.append(tag.get_text())
    if not texts:
        raise RuntimeError(f"no messages parsed from {channel}")
    return "\n".join(texts)


def fetch_subscription(url):
    """لینک ساب خارجی را می‌خواند؛ اگر base64 باشد decode می‌کند."""
    body = fetch(url).strip()
    compact = "".join(body.split())
    if compact:
        try:
            decoded = base64.b64decode(compact, validate=True).decode("utf-8")
            if re.search(r"(vless|vmess|trojan|ss|hysteria2|tuic|juicity|ssr)://", decoded):
                return decoded
        except Exception:
            pass
    return body


def fetch_telegram_via_telethon(channels):
    """fallback: اگر TELEGRAM_API_ID/TELEGRAM_API_HASH تنظیم شده باشد."""
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        return None
    try:
        from telethon import TelegramClient
    except ImportError:
        log("telethon is not installed; skipping fallback")
        return None

    texts = []
    with TelegramClient("noizvpn_session", int(api_id), api_hash) as client:
        for channel in channels:
            try:
                for message in client.iter_messages(channel.strip().lstrip("@"), limit=50):
                    if message.text:
                        texts.append(message.text)
            except Exception as exc:
                log(f"telethon failed for {channel}: {exc}")
    return "\n".join(texts) if texts else None


def collect_sources(sources):
    """همه منابع را می‌خواند و متن خام برمی‌گاند."""
    raw_texts = []

    channels = sources.get("telegram_channels", [])
    if channels:
        telethon_text = fetch_telegram_via_telethon(channels)
        if telethon_text:
            raw_texts.append(telethon_text)
            log(f"telethon: got text from {len(channels)} channel(s)")
        else:
            for channel in channels:
                try:
                    text = fetch_telegram_channel(channel)
                    raw_texts.append(text)
                    STATS["telegram"] += 1
                    log(f"telegram {channel}: ok")
                except Exception as exc:
                    STATS["failed"].append(f"telegram:{channel}")
                    log(f"telegram {channel}: FAILED ({exc})")

    for url in sources.get("subscription_links", []):
        try:
            body = fetch_subscription(url)
            raw_texts.append(body)
            STATS["subscriptions"] += 1
            log(f"sub {url}: ok")
        except Exception as exc:
            STATS["failed"].append(f"sub:{url}")
            log(f"sub {url}: FAILED ({exc})")

    return "\n".join(raw_texts)


def build_configs(raw_text):
    """استخراج، دیdup و تغییر نام کانفیگ‌ها."""
    uris = parser.extract_uris(raw_text)
    STATS["total"] = len(uris)

    seen = set()
    configs = []
    for uri in uris:
        base = parser.strip_remark(uri)
        if base in seen:
            continue
        seen.add(base)
        emoji = random.choice(config.EMOJI_POOL)
        remark = config.REMARK_TEMPLATE.format(emoji=emoji)
        renamed = parser.set_remark(uri, remark)
        if renamed:
            configs.append(renamed)

    STATS["unique"] = len(configs)
    return configs


def write_output(configs):
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    plain = "\n".join(configs) + "\n"
    encoded = base64.b64encode(plain.encode("utf-8")).decode("utf-8")

    with open(os.path.join(config.OUTPUT_DIR, "plain.txt"), "w", encoding="utf-8") as f:
        f.write(plain)
    with open(os.path.join(config.OUTPUT_DIR, "base64.txt"), "w", encoding="utf-8") as f:
        f.write(encoded)
    return plain, encoded


def load_previous():
    path = os.path.join(config.OUTPUT_DIR, "plain.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def main():
    dry_run = "--dry-run" in sys.argv

    with open(config.SOURCES_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    log(f"sources: {len(sources.get('telegram_channels', []))} telegram, "
        f"{len(sources.get('subscription_links', []))} subscription links")

    raw_text = collect_sources(sources)
    log(f"raw text length: {len(raw_text)} chars")

    configs = build_configs(raw_text)
    log(f"extracted={STATS['total']} unique={STATS['unique']}")

    # کانفیگ امضا اول می‌رود
    final = [config.SIGNATURE_URI]
    final += configs[: max(0, config.MAX_CONFIGS - 1)]

    if not configs:
        previous = load_previous()
        if previous:
            log("WARNING: no new configs; keeping previous output")
            final = previous.splitlines()
        else:
            log("WARNING: no new configs and no previous output; writing signature only")

    now = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    stamp = now.strftime("%Y-%m-%d %H:%M %Z")
    # خروجی فقط شامل کانفیگ‌ها باشد (هیچ خط توضیحی که کلاینت را گیر بیندازد)
    final_with_footer = final

    if dry_run:
        log("DRY RUN: not writing files")
        for c in final_with_footer[:5]:
            print("  " + c)
        print(f"  ... total {len(final_with_footer)} lines")
        return

    plain, encoded = write_output(final_with_footer)

    with open(config.LAST_UPDATE_FILE, "w", encoding="utf-8") as f:
        f.write(stamp + "\n")

    log(f"wrote {len(final)} configs ({len(plain)} bytes plain, {len(encoded)} bytes base64)")
    log(f"sub link: https://raw.githubusercontent.com/<owner>/<repo>/main/output/base64.txt")
    if STATS["failed"]:
        log(f"failed sources: {', '.join(STATS['failed'])}")


if __name__ == "__main__":
    main()
