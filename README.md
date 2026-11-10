# NoizVpn Subscription Service

سرویس جمع‌آوری و انتشار کانفیگ‌های V2Ray (VLESS, VMess, Trojan, Shadowsocks, Reality, Hysteria2, TUIC)
به صورت یک لینک ساب که کلاینت‌هایی مثل **NPV Tunnel**، **v2box**، **v2rayNG**، **v2rayN**،
**Hiddify** و **NekoBox** می‌توانند از آن استفاده کنند.

## لینک های اشتراک

| فرمت | لینک |
|---|---|
| Base64 (استاندارد) | `https://raw.githubusercontent.com/<owner>/<repo>/main/output/base64.txt` |
| متن ساده | `https://raw.githubusercontent.com/<owner>/<repo>/main/output/plain.txt` |

## نحوه استفاده

1. یکی از لینک‌های بالا را کپی کنید.
2. در کلاینت (مثلا NPV Tunnel یا v2box) به بخش **Subscription** بروید.
3. **Add Subscription** را بزنید، لینک را پیست کنید و ذخیره کنید.
4. **Update / Refresh** را بزنید تا کانفیگ‌های جدید بیاید.

## ویژگی ها

- جمع‌آوری خودکار از **کانال‌های عمومی تلگرام** و **لینک‌های ساب خارجی**.
- تغییر نام و ایموجی همه کانفیگ‌ها به فرمت:
  `[Random Emoji]==>@NoizVpn جوین شو تلگرام`
- یک کانفیگ امضا در ابتدای لیست:
  `[👾]==>@NoizVpn برای دریافت کانفیگ های پرسرعت`
- حذف کانفیگ‌های تکراری.
- حداکثر **۲۰۰۰** کانفیگ در هر لیست (برای جلوگیری از هنگ کردن کلاینت).
- به‌روزرسانی خودکار هر **۱۲ ساعت** با GitHub Actions.

## افزودن منبع جدید

فایل `sources.json` را ویرایش کنید:

```json
{
  "telegram_channels": [
    "channel_username"
  ],
  "subscription_links": [
    "https://example.com/subscription.txt"
  ]
}
```

- `telegram_channels`: نام کاربری کانال عمومی تلگرام (بدون `@` هم مشکلی نیست).
- `subscription_links`: لینک‌های ساب خارجی که می‌خواهید کانفیگ‌های داخلشان هم به لیست ما بیاید.

بعد از تغییر، کامیت و پوش کنید؛ اولین اجرای بعدی منابع جدید را می‌خواند.

## ساختار پروژه

```
noizvpn-sub/
├── config.py                  # تنظیمات (حد اکثر، الگوی نام، ایموجی‌ها، امضا)
├── parser.py                  # استخراج و تغییر نام کانفیگ‌ها
├── collector.py               # جمع‌آوری، دیdup، خروجی
├── sources.json               # لیست منابع
├── requirements.txt
├── output/
│   ├── plain.txt              # خروجی متن ساده
│   └── base64.txt             # خروجی base64 (فرمت استاندارد کلاینت‌ها)
├── last_update.txt            # زمان آخرین به‌روزرسانی
└── .github/workflows/update.yml
```

## اجرای محلی

```bash
pip install -r requirements.txt
python collector.py
```

برای تست بدون نوشتن فایل:

```bash
python collector.py --dry-run
```

## نکات فنی

- فرمت خروجی، base64 از لیست خطوط (هر خط یک کانفیگ) است؛ کلاینت یک بار decode می‌کند و خطوط را پارس می‌کند.
- تغییر نام فقط روی `remark` اعمال می‌شود؛ پارامترهای `security`, `type`, `flow`, `sni`, `path`, `host` و غیره دست‌نخورده باقی می‌مانند.
- اگر هیچ منبعی در دسترس نباشد، خروجی قبلی حفظ می‌شود (ساب خالی نمی‌شود تا لیست کلاینت پاک نشود).
- اگر خروجی قبلی وجود نداشته باشد و منابع هم نباشند، فقط کانفیگ امضا نوشته می‌شود.

## مجوز

MIT
