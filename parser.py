"""
NoizVpn Subscription Service - URI parser / renamer
استخراج کانفیگ از متن و تغییر نام (remark) بدون دست زدن به پارامترهای پروتکل.
"""

import base64
import json
import re

# پروتکل‌هایی که پشتیبانی می‌شوند
SCHEME_RE = re.compile(
    r"(?<![\w-])(vless|vmess|trojan|ss|ssr|hysteria2|hy2|tuic|juicity|wireguard|wg|socks5|socks)://[^\s<>\"'`]+",
    re.IGNORECASE,
)

# کاراکترهای مزخرف که نباید انتهای کانفیگ باشند
TRAILING_JUNK = ".,;:)]}>\"'`"

# حذف کاما از ته کانفیگ (بعضی کانال‌ها با کاما جدا می‌کنند)
TRAILING_COMMA = ","


def extract_uris(text):
    """همه URI های کانفیگ را از یک متن استخراج می‌کند."""
    found = []
    for match in SCHEME_RE.finditer(text):
        uri = match.group(0).rstrip(TRAILING_JUNK)
        uri = uri.rstrip(TRAILING_COMMA)
        if uri and len(uri) > 8:
            found.append(uri)
    return found


def _split_vmess(uri):
    """vmess را به بدنه و شرح قدیمی تقسیم می‌کند."""
    payload = uri[len("vmess://"):]
    if "#" in payload:
        payload = payload.split("#", 1)[0]
    return payload


def strip_remark(uri):
    """کانفیگ را بدون شرح (remark) برمی‌گاند تا برای دیdup استفاده شود."""
    if uri.lower().startswith("vmess://"):
        return "vmess://" + _split_vmess(uri)
    return uri.split("#", 1)[0]


def set_remark(uri, remark):
    """
    شرح جدید را روی کانفیگ می‌گذارد و همه پارامترهای حمل‌ونقل را دست‌نخورده نگه می‌دارد.
    اگر کانفیگ خراب باشد None برمی‌گاند.
    """
    if uri.lower().startswith("vmess://"):
        payload = _split_vmess(uri)
        try:
            padded = payload + "=" * (-len(payload) % 4)
            data = json.loads(base64.b64decode(padded).decode("utf-8"))
            data["ps"] = remark
            new_payload = base64.b64encode(
                json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).decode("utf-8")
            return "vmess://" + new_payload
        except Exception:
            return None

    base = uri.split("#", 1)[0]
    return base + "#" + remark


def protocol_of(uri):
    return uri.split("://", 1)[0].lower()


def host_port_of(uri):
    """هاست و پورت را برای جلوه خروجی استخراج می‌کند (اگر ممکن باشد)."""
    try:
        body = uri.split("://", 1)[1]
        body = body.split("#", 1)[0]
        body = body.split("?", 1)[0]
        if uri.lower().startswith("vmess://"):
            padded = body + "=" * (-len(body) % 4)
            data = json.loads(base64.b64decode(padded).decode("utf-8"))
            return str(data.get("add", "")), str(data.get("port", ""))
        # userinfo@host:port
        if "@" in body:
            hostpart = body.rsplit("@", 1)[1]
        else:
            hostpart = body
        hostpart = hostpart.strip("[]")
        if hostpart.startswith("["):
            host, _, rest = hostpart.partition("]")
            port = rest.lstrip(":").split("/")[0]
            return host, port
        if ":" in hostpart:
            host, port = hostpart.rsplit(":", 1)
            return host, port.split("/")[0]
        return hostpart, ""
    except Exception:
        return "", ""
