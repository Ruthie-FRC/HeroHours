# Quick Start Guide

Choose your setup mode:

---

## 🛠️ Development Mode (With Test Data)

**Use when:** Developing, testing, debugging, or learning

### Setup in 3 Commands

```bash
# 1. Migrate database
python manage.py migrate

# 2. Create test users (requires --confirm)
python manage.py setup_test_data --confirm

# 3. Start server
python manage.py runserver
```

### Login Credentials

```
Admin:   admin / admin123
Staff:   staff1 / staff123
         staff2 / staff123
```

### Access

- Admin: http://127.0.0.1:8000/admin/
- App: http://127.0.0.1:8000/HeroHours/

### Environment

```bash
DEBUG='True'
DJANGO_DATABASE='local'
```

### Features

- ✅ Test users with known credentials
- ✅ Sample data already loaded
- ✅ Safe to reset anytime
- ✅ No Redis required
- ✅ SQLite database (simple)

---

## 🚀 Production Mode (With Real Data)

**Use when:** Running live system with real users

### Setup Steps

```bash
# 1. Set production environment
export DEBUG='False'
export DATABASE_URL='postgresql://...'
export REDIS_URL='redis://...'

# 2. Migrate database
python manage.py migrate

# 3. Create admin user
python manage.py createsuperuser

# 4. Import real users
python manage.py import_users users.csv

# 5. Collect static files
python manage.py collectstatic

# 6. Start production server
gunicorn HeroHoursRemake.asgi:application -k uvicorn.workers.UvicornWorker
```

### Security Requirements

```
✅ DEBUG=False
✅ Strong SECRET_KEY (50+ chars)
✅ PostgreSQL database
✅ Redis for WebSockets
✅ SSL/HTTPS enabled
✅ ALLOWED_HOSTS configured
```

### Features

- ✅ Real user data
- ✅ Secure credentials
- ✅ Production-grade database
- ✅ WebSocket support (Redis)
- ✅ Data persistence critical

---

## 🚨 Key Differences

| What | Development | Production |
|------|-------------|------------|
| **Command** | `setup_test_data --confirm` | Manual user creation |
| **DEBUG** | ✅ True | ❌ False |
| **Database** | SQLite | PostgreSQL |
| **Users** | Test (IDs 1000-9999) | Real (any ID) |
| **Credentials** | Public test creds | Private real creds |
| **Reset Data** | ✅ Safe | ❌ NEVER |
| **WebSockets** | InMemory | Redis |

---

## ⚠️ Safety Notes

### Development

```bash
# ✅ This is SAFE in development:
python manage.py setup_test_data --confirm --clear

# Creates fresh test data anytime
```

### Production

```bash
# ❌ This is BLOCKED in production:
python manage.py setup_test_data --confirm
# Returns error: "Command will NOT run in production mode!"

# ✅ This is correct for production:
# - Create users via admin interface
# - Import users from CSV
# - Never use test data command
```

---

## 🔍 How to Tell Which Mode You're In

```bash
python manage.py shell -c "from django.conf import settings; print(f'DEBUG: {settings.DEBUG}')"
```

- `DEBUG: True` = Development mode (can use test data)
- `DEBUG: False` = Production mode (test data blocked)

---

## 📚 Full Documentation

- **Setup Guide:** `SETUP_GUIDE.md` (complete workflows)
- **Test Data:** `TEST_DATA_SETUP.md` (test data details)
- **Security:** `SECURITY_AUDIT_SUMMARY.md` (security info)

---

## Quick Decision Tree

```
Are you developing/testing?
├─ YES → Use Development Mode
│        • Set DEBUG=True
│        • Run: setup_test_data --confirm
│        • Use test credentials
│
└─ NO → Use Production Mode
         • Set DEBUG=False
         • Import real users
         • Use secure credentials
```
