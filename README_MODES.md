# HeroHours - Two Ways to Run

> **Yes, there are TWO very separate ways to run HeroHours!**

---

## 🛠️ Development Mode

**For:** Testing, development, learning

```bash
python manage.py setup_test_data --confirm
```

- ✅ Creates test users automatically
- ✅ Test credentials: `admin/admin123`
- ✅ Safe to reset anytime
- ✅ No Redis needed
- ⚙️ Requires: `DEBUG=True`

---

## 🚀 Production Mode  

**For:** Live operations with real users

```bash
python manage.py createsuperuser
python manage.py import_users users.csv
```

- ✅ Real user data
- ✅ Secure credentials
- ✅ Data persistence critical
- ✅ Redis required
- ⚙️ Requires: `DEBUG=False`

---

## 🚨 They Cannot Be Mixed!

The `setup_test_data` command:
- ✅ Works in development (`DEBUG=True`)
- ❌ **BLOCKED** in production (`DEBUG=False`)

This ensures test data **never** ends up in production!

---

## 📚 Full Documentation

- **Quick Start:** `QUICK_START.md`
- **Complete Guide:** `SETUP_GUIDE.md`
- **Visual Comparison:** `MODES_COMPARISON.txt`

**TL;DR:** Development and Production are completely separate with multiple safety mechanisms!
