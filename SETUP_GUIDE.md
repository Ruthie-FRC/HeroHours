# HeroHours Setup Guide

This guide explains the **two distinct ways** to run the HeroHours application:

1. 🛠️ **Development/Testing Mode** - With test data
2. 🚀 **Production Mode** - With real user data

---

## Quick Reference

| Aspect | Development/Testing | Production |
|--------|---------------------|------------|
| **Purpose** | Development, testing, demos | Live operational use |
| **Data** | Test users (IDs 1000-9999) | Real users |
| **Credentials** | Known test credentials | Real user credentials |
| **DEBUG Mode** | `DEBUG=True` (required) | `DEBUG=False` (required) |
| **Database** | SQLite (local) or test DB | PostgreSQL (recommended) |
| **Data Setup** | `setup_test_data` command | Manual user creation/import |
| **Reset Data** | ✅ Safe to clear & recreate | ❌ Never clear production data |
| **WebSockets** | InMemoryChannelLayer | Redis (required) |

---

## 🛠️ Development/Testing Setup (With Test Data)

### Purpose
Use this mode for:
- Local development
- Testing new features
- Debugging issues
- Demos and training
- CI/CD automated tests

### Quick Start

```bash
# 1. Set up environment
export SECRET_KEY='your-dev-secret-key'
export DEBUG='True'
export DJANGO_DATABASE='local'

# 2. Initialize database
python manage.py migrate

# 3. Create test data (REQUIRES --confirm flag)
python manage.py setup_test_data --confirm

# 4. Start development server
python manage.py runserver

# 5. Access the application
# Admin: http://127.0.0.1:8000/admin/
# Username: admin
# Password: admin123
```

### Test Data Created

The `setup_test_data` command creates:

**Superuser:**
- Username: `admin`
- Password: `admin123`
- Full admin access

**Staff Users:**
- Username: `staff1`, Password: `staff123`
- Username: `staff2`, Password: `staff123`

**Test Members (IDs 1000-1010):**
```
ID 1001: Alice Anderson    (0 hours, not checked in)
ID 1002: Bob Builder       (0 hours, not checked in)
ID 1003: Carol Cooper      (1 hour, not checked in)
ID 1004: David Davis       (5.5 hours, not checked in)
ID 1005: Emma Evans        (2 hours, CHECKED IN)
ID 1006: Frank Foster      (10 hours, not checked in)
ID 1007: Grace Garcia      (25 hours, not checked in)
ID 1008: Henry Harris      (1.5 hours, INACTIVE)
ID 1009: Iris Irving       (4 hours, not checked in)
ID 1010: Jack Johnson      (8 hours, CHECKED IN)
```

### Safety Features

The test data command **cannot run accidentally**:

1. ✅ **Requires `--confirm` flag** - Command fails without it
2. ✅ **Requires DEBUG=True** - Blocks in production mode
3. ✅ **Shows preview** - Displays what will be created
4. ✅ **Requires confirmation** - Must type "yes" to proceed

```bash
# This WILL NOT work (missing --confirm):
python manage.py setup_test_data

# This IS REQUIRED:
python manage.py setup_test_data --confirm
```

### Resetting Development Data

```bash
# Clear and recreate test data
python manage.py setup_test_data --confirm --clear

# Create more test members
python manage.py setup_test_data --confirm --members 10
```

### Development Environment Variables

```bash
# .env file for development
SECRET_KEY='django-insecure-dev-key-do-not-use-in-production'
DEBUG='True'
DJANGO_DATABASE='local'
DATABASE_URL=''
AUTO_LOGOUT_THRESHOLD_SECONDS='3600'
```

---

## 🚀 Production Setup (With Real Data)

### Purpose
Use this mode for:
- Live operational deployment
- Real user tracking
- Actual hour logging
- Production workloads

### Prerequisites

1. **PostgreSQL Database**
   ```bash
   # Install PostgreSQL
   sudo apt-get install postgresql postgresql-contrib
   
   # Create database
   sudo -u postgres createdb herohours_prod
   sudo -u postgres createuser herohours_user -P
   ```

2. **Redis Server**
   ```bash
   # Required for WebSocket support
   sudo apt-get install redis-server
   sudo systemctl enable redis-server
   sudo systemctl start redis-server
   ```

3. **Strong Secret Key**
   ```bash
   # Generate a secure secret key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

### Production Setup Steps

#### 1. Environment Configuration

Create `.env` file with production settings:
```bash
# NEVER commit this file to version control!
SECRET_KEY='<your-strong-50+-character-secret-key>'
DEBUG='False'
DJANGO_DATABASE='postgresql'
DATABASE_URL='postgresql://herohours_user:password@localhost/herohours_prod'
REDIS_URL='redis://localhost:6379/0'
ALLOWED_HOSTS='your-domain.com,www.your-domain.com'
CSRF_TRUSTED_ORIGINS='https://your-domain.com,https://www.your-domain.com'
AUTO_LOGOUT_THRESHOLD_SECONDS='3600'
```

#### 2. Database Initialization

```bash
# Apply migrations
python manage.py migrate

# Create superuser (for admin access)
python manage.py createsuperuser
# Follow prompts to set username/email/password
```

#### 3. Static Files

```bash
# Collect static files for serving
python manage.py collectstatic --noinput
```

#### 4. Start Production Server

```bash
# Option 1: Using Gunicorn + Daphne
gunicorn HeroHoursRemake.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Option 2: Using systemd service (recommended)
sudo systemctl enable herohours
sudo systemctl start herohours
```

### Adding Real Users in Production

**Option 1: Admin Interface**
1. Log in to `/admin/`
2. Go to "Users" section
3. Click "Add User"
4. Enter user details and save

**Option 2: Import from CSV**
```bash
python manage.py import_users users.csv
```

CSV format:
```csv
User_ID,First_Name,Last_Name,Total_Hours,Checked_In,Total_Seconds
2001,John,Smith,0:00:00,FALSE,0
2002,Jane,Doe,0:00:00,FALSE,0
```

**Option 3: Bulk Creation Script**
```python
# create_users.py
from HeroHours.models import Users
from datetime import timedelta

users = [
    {'User_ID': 2001, 'First_Name': 'John', 'Last_Name': 'Smith'},
    {'User_ID': 2002, 'First_Name': 'Jane', 'Last_Name': 'Doe'},
    # ... more users
]

for user_data in users:
    Users.objects.create(
        User_ID=user_data['User_ID'],
        First_Name=user_data['First_Name'],
        Last_Name=user_data['Last_Name'],
        Total_Hours=timedelta(0),
        Total_Seconds=0,
        Checked_In=False,
        Is_Active=True
    )
```

Run with: `python manage.py shell < create_users.py`

### Production Security Checklist

- [ ] `DEBUG=False` is set
- [ ] Strong `SECRET_KEY` (50+ characters, random)
- [ ] PostgreSQL database configured
- [ ] Redis configured for WebSockets
- [ ] `ALLOWED_HOSTS` set correctly
- [ ] `CSRF_TRUSTED_ORIGINS` set correctly
- [ ] SSL/HTTPS enabled
- [ ] Regular database backups scheduled
- [ ] Firewall configured
- [ ] Security headers enabled (already in code)
- [ ] Rate limiting configured (already in code)

---

## 🔄 Switching Between Modes

### From Development to Production

1. **Change Environment Variables:**
   ```bash
   DEBUG='False'  # Was 'True'
   DJANGO_DATABASE='postgresql'  # Was 'local'
   # Add production DATABASE_URL, REDIS_URL, etc.
   ```

2. **Use Production Database:**
   - Switch from SQLite to PostgreSQL
   - Run migrations on production database

3. **Remove Test Data:**
   - Test data setup command will be blocked (DEBUG=False)
   - Production starts with empty database
   - Add real users using production methods

### From Production to Development

1. **Change Environment Variables:**
   ```bash
   DEBUG='True'  # Was 'False'
   DJANGO_DATABASE='local'  # Was 'postgresql'
   ```

2. **Use Development Database:**
   - Switch to local SQLite database
   - Run migrations if needed

3. **Add Test Data:**
   ```bash
   python manage.py setup_test_data --confirm
   ```

---

## 🚨 Important Distinctions

### Test Data vs Real Data

| Feature | Test Data | Real Data |
|---------|-----------|-----------|
| **User IDs** | 1000-9999 | Any (typically 2000+) |
| **Creation Method** | `setup_test_data` command | Manual/CSV import |
| **Credentials** | Public test credentials | Private real credentials |
| **Can Be Deleted** | ✅ Yes, safe to clear | ❌ NO! Critical data |
| **DEBUG Required** | ✅ Yes (DEBUG=True) | ❌ No (DEBUG=False) |

### Key Safety Mechanisms

1. **Test Data Command Protection:**
   - Won't run without `--confirm` flag
   - Won't run in production (DEBUG=False)
   - Shows preview before execution
   - Requires interactive confirmation

2. **Production Protection:**
   - Test data command is blocked
   - Must use explicit user creation methods
   - Database changes require migrations
   - Activity logs track all operations

---

## 📝 Common Workflows

### Development Workflow

```bash
# 1. Start fresh
rm db.sqlite3
python manage.py migrate

# 2. Create test data
python manage.py setup_test_data --confirm

# 3. Develop and test
python manage.py runserver

# 4. Reset when needed
python manage.py setup_test_data --confirm --clear
```

### Production Workflow

```bash
# 1. Initial setup (once)
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic

# 2. Import real users
python manage.py import_users real_users.csv

# 3. Start production server
sudo systemctl start herohours

# 4. Monitor and maintain
# - Regular backups
# - Monitor logs
# - Update dependencies
# - Never use setup_test_data command!
```

---

## 🆘 Troubleshooting

### "Command requires --confirm flag"
**Issue:** Forgot to add `--confirm` flag  
**Solution:** Add `--confirm` to the command
```bash
python manage.py setup_test_data --confirm
```

### "Command will NOT run in production mode"
**Issue:** DEBUG=False (production mode)  
**Solution:** This is intentional! Don't use test data in production. Use real user creation methods instead.

### "Setup test data vs real users?"
**Question:** When should I use which?
- Use `setup_test_data` ONLY for development/testing
- Use manual creation/CSV import for production
- Never mix test data with real data

### "How do I know which mode I'm in?"
**Check DEBUG setting:**
```bash
python manage.py shell
>>> from django.conf import settings
>>> print(f"DEBUG: {settings.DEBUG}")
>>> print(f"Database: {settings.DATABASES['default']['ENGINE']}")
```

- `DEBUG=True` + SQLite = Development mode
- `DEBUG=False` + PostgreSQL = Production mode

---

## 📚 Additional Documentation

- **Test Data Details:** See `TEST_DATA_SETUP.md`
- **Security Audit:** See `FULL_SYSTEM_AUDIT_REPORT.md`
- **Code Modernization:** See `CODE_MODERNIZATION_SUMMARY.md`
- **Security Details:** See `SECURITY_AUDIT_SUMMARY.md`

---

## Summary

✅ **Development/Testing:** Use `setup_test_data` command with DEBUG=True  
✅ **Production:** Use real user creation methods with DEBUG=False  
✅ **Clear Separation:** Multiple safety mechanisms prevent mixing  
✅ **Well Documented:** Comprehensive guides for each mode  

**Remember:** Test data is for development only. Production uses real data with proper security and backup procedures.
