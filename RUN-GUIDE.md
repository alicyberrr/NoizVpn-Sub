# آموزش اجرای NoizVpn Subscription Service

این پروژه کانفیگ‌های V2Ray را از کانال‌های تلگرام و لینک‌های ساب خارجی جمع می‌کند،
نام و ایموجی‌شان را یکدست می‌کند، تکراری‌ها را حذف می‌کند، به ۲۰۰۰ کانفیگ محدود می‌کند
و به صورت یک لینک ساب منتشر می‌کند که کلاینت‌هایی مثل NPV Tunnel و v2box می‌توانند از آن استفاده کنند.

---

## ۱. پیش‌نیازها

- **Python 3.9 یا بالاتر**
- **pip** (همراه پایتون)
- اتصال به اینترنت

در اوبونتو/دبیان:
```bash
sudo apt update
sudo apt install -y python3 python3-pip git
```

در آرچ:
```bash
sudo pacman -S python python-pip git
```

---

## ۲. نصب و اجرای محلی

```bash
# ۱. پروژه را باز کنید
cd noizvpn-sub

# ۲. پیش‌نیازها را نصب کنید
pip install -r requirements.txt

# ۳. اجرای پروژه
python3 collector.py
```

بعد از اجرا، فایل‌های خروجی ساخته می‌شوند:
```
output/plain.txt     ← همه کانفیگ‌ها، یکی در هر خط
output/base64.txt    ← همان لیست به فرمت base64 (همین را به کلاینت می‌دهیم)
last_update.txt      ← زمان آخرین به‌روزرسانی
```

**برای تست بدون نوشتن فایل:**
```bash
python3 collector.py --dry-run
```

**برای اجرای تست‌ها:**
```bash
python3 -m unittest discover -s tests -v
```

---

## ۳. افزودن منبع جدید

فایل `sources.json` را باز کنید و منابع خود را اضافه کنید:

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

- **telegram_channels**: نام کاربری کانال عمومی تلگرام (با یا بدون `@`).
- **subscription_links**: لینک‌های ساب خارجی که می‌خواهید کانفیگ‌های داخلشان هم وارد لیست شود.

بعد از تغییر، دوباره اجرا کنید:
```bash
python3 collector.py
```

---

## ۴. ساختار فایل‌ها

```
noizvpn-sub/
├── config.py                  ← تنظیمات اصلی (حد اکثر، الگوی نام، ایموجی‌ها، امضا)
├── parser.py                  ← استخراج کانفیگ از متن و تغییر نام (remark)
├── collector.py               ← جمع‌آوری، حذف تکراری، محدودسازی، خروجی
├── sources.json               ← لیست منابع (کانال تلگرام + لینک ساب خارجی)
├── requirements.txt           ← کتابخانه‌های مورد نیاز
├── tests/
│   └── test_collector.py      ← تست‌های واحد
├── output/
│   ├── plain.txt              ← خروجی متن ساده
│   └── base64.txt             ← خروجی base64 (فرمت استاندارد کلاینت‌ها)
├── last_update.txt            ← زمان آخرین به‌روزرسانی
└── .github/workflows/
    └── update.yml             ← اکشن گیت‌هاب (اجرای خودکار هر ۱۲ ساعت)
```

---

## ۵. تنظیمات (config.py)

| متغیر | توضیح | پیش‌فرض |
|---|---|---|
| `MAX_CONFIGS` | حداکثر تعداد کانفیگ در خروجی | `2000` |
| `REMARK_TEMPLATE` | الگوی نام کانفیگ‌ها | `[{emoji}]==>@NoizVpn جوین شو تلگرام` |
| `SIGNATURE_REMARK` | نام کانفیگ امضا | `[👾]==>@NoizVpn برای دریافت کانفیگ های پرسرعت` |
| `EMOJI_POOL` | استخر ایموجی‌های تصادفی | لیست حدود ۱۰۰ ایموجی |

برای تغییر الگوی نام، `REMARK_TEMPLATE` را ویرایش کنید. `{emoji}` به ایموجی تصادفی تبدیل می‌شود.

---

## ۶. استقرار روی گیت‌هاب (اجرای خودکار هر ۱۲ ساعت)

این پروژه برای اجرای خودکار با **GitHub Actions** طراحی شده است.

### ۱. ریپو را بسازید
یک ریپوی جدید در گیت‌هاب بسازید و این پروژه را پوش کنید:

```bash
git init
git add -A
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

### ۲. دسترسی اکشن را روی "Read and write" بگذارید
در ریپو: **Settings → Actions → General → Workflow permissions**
گزینهٔ **Read and write permissions** را انتخاب و Save کنید.

### ۳. لینک ساب
بعد از اولین اجرا، لینک ساب آماده است:

```
https://raw.githubusercontent.com/<username>/<repo>/main/output/base64.txt
```

### ۴. اجرای دستی (اختیاری)
اگر می‌خواهید فوراً اجرا شود، در ریپو بروید به **Actions → Update NoizVpn Subscription → Run workflow**.

---

## ۷. استفاده در کلاینت

### NPV Tunnel (اندروید / iOS)
1. لینک base64 را کپی کنید.
2. در NPV به **Subscriptions** بروید.
3. **+** را بزنید و لینک را پیست کنید.
4. **Update** را بزنید.

### v2box (اندروید / iOS)
1. لینک base64 را کپی کنید.
2. در v2box به **Subscription** بروید.
3. **Add Subscription** و لینک را پیست کنید.
4. **Update** را بزنید.

### v2rayNG / v2rayN / Hiddify / NekoBox
همه از لینک base64 پشتیبانی می‌کنند. کافی است لینک را در بخش Subscription اضافه کنید.

---

## ۸. عیب‌یابی

| مشکل | راه‌حل |
|---|---|
| `ModuleNotFoundError: requests` | `pip install -r requirements.txt` را اجرا کنید |
| خروجی خالی است | اتصال اینترنت را چک کنید؛ منابع ممکن است در دسترس نباشند |
| کانال تلگرام خوانده نمی‌شود | نام کاربری کانال را چک کنید؛ کانال باید **عمومی** باشد |
| لینک ساب بارگذاری نمی‌شود | اگر `raw.githubusercontent.com` مسدود است، لینک را از طریق یک پروکسی یا Mirror دیگر باز کنید |
| تعداد کانفیگ‌ها کم است | منابع بیشتری اضافه کنید؛ کانفیگ‌های رایگان سریع منقضی می‌شوند |

---

## ۹. نکات فنی

- فرمت خروجی، **base64 از لیست خطوط** است (هر خط یک کانفیگ). کلاینت یک بار decode می‌کند و خطوط را پارس می‌کند.
- تغییر نام فقط روی `remark` اعمال می‌شود؛ پارامترهای `security`, `type`, `flow`, `sni`, `path`, `host` و غیره دست‌نخورده باقی می‌مانند.
- اگر هیچ منبعی در دسترس نباشد، خروجی قبلی حفظ می‌شود (ساب خالی نمی‌شود تا لیست کلاینت پاک نشود).
- کانفیگ امضا در ابتدای لیست قرار دارد و آدرس آن `127.0.0.1` است؛ فقط برای شناسایی ساب است و اتصال نمی‌شود.

---

## ۱۰. پشتیبانی

- کانال تلگرام: @NoizVpn
- ریپوی گیت‌هاب: https://github.com/alicyberrr/NoizVpn-Sub
