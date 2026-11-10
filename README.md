# IT Travel — туристтик сайт (Django)

Ош шаарындагы туристтик агенттиктин чыныгы иштеген сайты: тур каталогу, онлайн брондоо,
катталуу жана жеке кабинет, пикирлер, издөө/чыпка, админ-панель. Интерфейс **кыргызча жана орусча**.

> Эски статикалык версия (HTML/CSS) `legacy/` папкасында сакталды.

## Мүмкүнчүлүктөр

| Бөлүм | Эмне кылат |
|---|---|
| Башкы бет | Издөө формасы, өлкөлөр, ысык турлар, акыркы пикирлер |
| Турлар `/tours/` | Издөө (кырг./орус.), өлкө, тур түрү, баа боюнча чыпка, иреттөө, барактоо |
| Өлкө барагы | Сүрөттөмө, Google карта (API ачкычсыз), фотогалерея, мейманканалар, турлар |
| Тур барагы | Программа, баага эмне кирет, мейманкана тандоо, **брондоо формасы бааны дароо эсептейт**, пикирлер (1–5 жылдыз) |
| Брондоо | Текшерүү (күн, телефон, киши саны), менеджерге email, статус: Жаңы → Ырасталды → Төлөндү |
| Кабинет `/accounts/cabinet/` | Менин брондоолорум, жокко чыгаруу, пикирлерим, профиль, сырсөз алмаштыруу |
| Байланыш | Форма — билдирүүлөр админкага сакталат, WhatsApp шилтемеси |
| Админка `/admin/` | Өлкө/тур/мейманкана/сүрөт кошуу, бааларды тизмеден эле өзгөртүү, брондоолордун статусу, пикирлерди модерациялоо |
| Сакталган турлар ♥ | Жаккан турду бир басуу менен сактоо (бет жаңырбайт), кабинетте тизмеси |
| Промокоддор | Админкада түзүлөт (%, мөөнөт, лимит); брондоодо арзандатуу дароо көрүнөт. Демо: `WELCOME10` |
| Блог `/blog/` | Макалалар (виза, кеңештер), өлкөгө байланыштуу турлар, бөлүшүү баскычтары |
| FAQ `/faq/` | Суроо-жооптор админкадан башкарылат, башкы бетте да көрүнөт |
| Өлкө маалыматы | Виза, валюта, учуу убактысы, мыкты мезгил |
| Билдирүүлөр | Жаңы брондоо жана байланыш билдирүүсү Telegram'га жана email'ге келет |
| Жазылуу | Футерде акцияларга email менен жазылуу (админкада тизме) |
| Дизайн | Адаптивдүү (телефон/планшет), караңгы тема, KY/RU которгуч; сүрөт жүктөлбөсө кооз SVG заглушка чыгат |

## Технологиялар

Python 3.10+ · Django 5 · SQLite (же PostgreSQL) · HTML/CSS/JS (китепканасыз) · WhiteNoise · Gunicorn

## Компьютерде иштетүү (Windows)

```bash
git clone https://github.com/batyrov-beka/tur-sait.git
cd tur-sait
python -m venv venv
venv\Scripts\activate            # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

python manage.py makemigrations tours bookings
python manage.py migrate
python manage.py seed_demo        # 6 өлкө, турлар, мейманканалар, сүрөттөр
python manage.py createsuperuser  # админ үчүн логин/сырсөз
python manage.py runserver
```

Ачыңыз: http://127.0.0.1:8000 — сайт, http://127.0.0.1:8000/admin — админка.

Иштеп чыгууда брондоо каттары **терминалга** чыгат (почта жөндөлбөсө).

## Жаңыртуу (мурунку версия орнотулган болсо)

```bash
python manage.py makemigrations tours bookings
python manage.py migrate
python manage.py seed_demo      # 12 өлкө, 18 тур, макалалар, FAQ, промокод
```

## Telegram билдирүүлөрү

1. Telegram'да @BotFather → `/newbot` → токенди алыңыз.
2. Ботуңузга каалаган билдирүү жазыңыз, андан кийин @userinfobot аркылуу өзүңүздүн chat id'ңизди билиңиз.
3. Чөйрө өзгөрмөлөрүн коюңуз (Windows PowerShell, серверди иштетүүдөн мурун):

```powershell
$env:TELEGRAM_BOT_TOKEN="123456:ABC..."
$env:TELEGRAM_CHAT_ID="123456789"
python manage.py runserver
```

## Котормолор

Шаблондордогу тексттер кыргызча жазылган, орусчасы — `locale/ru/LC_MESSAGES/django.po`.
Жаңы текст кошкондо же котормону өзгөрткөндө:

```bash
python scripts/compile_po.py      # gettext орнотуунун кереги жок
```

Тур, өлкө жана мейманкананын тексттери админкада эки тилде (`... (кырг.)` / `... (орус.)`) толтурулат.

## Серверге чыгаруу (production)

Чөйрө өзгөрмөлөрүн коюңуз (`.env.example` караңыз):

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<узун кокус сап>
DJANGO_ALLOWED_HOSTS=ittravel.kg,www.ittravel.kg
DJANGO_CSRF_TRUSTED_ORIGINS=https://ittravel.kg
```

Андан кийин:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Ылайыктуу хостингдер: **PythonAnywhere** (бекер план бар, Django үчүн эң жөнөкөй), Render, Railway, же
өзүңүздүн VPS (Nginx + Gunicorn). Жүктөлгөн сүрөттөр `media/` папкасында сакталат — VPS'те Nginx аркылуу бериңиз.

Чыныгы email үчүн (мисалы Gmail "App password"):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=<app password>
BOOKING_NOTIFY_EMAIL=you@gmail.com
```

## Долбоордун түзүлүшү

```
config/        — жөндөөлөр, негизги URL'дар
tours/         — Өлкө, Тур, Мейманкана, Сүрөт, Пикир, Байланыш билдирүүсү; seed_demo командасы
bookings/      — Брондоо модели, форма, бааны эсептөө, админ аракеттери
accounts/      — катталуу, кабинет, профиль
templates/     — HTML шаблондор
static/        — css/style.css, js/main.js
locale/ru/     — орусча котормо
scripts/       — compile_po.py
legacy/        — эски статикалык сайт
```

## Баа кантип эсептелет

`чоңдор × тур баасы + балдар × тур баасы × 50% + мейманкана (бир түн) × тур күндөрү`
— `bookings/models.py` ичиндеги `Booking.calculate_price`. Демо баалар мисал үчүн гана, админкадан өзгөртүңүз.
