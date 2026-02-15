#!/bin/bash

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "                    FULL SYSTEM TEST & SECURITY AUDIT"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Setup environment
export SECRET_KEY='django-insecure-test-key-for-full-audit-12345'
export APP_SCRIPT_URL='https://script.google.com/macros/s/test/exec'
export DATABASE_URL=''
export DJANGO_DATABASE='local'
export DEBUG='True'

mkdir -p logs

echo "PHASE 1: SYSTEM SETUP & VALIDATION"
echo "───────────────────────────────────────────────────────────────────────────────"

# Clean start
rm -f db.sqlite3

# Check Django
echo "✓ Checking Django installation..."
python -c "import django; print(f'  Django version: {django.get_version()}')" || exit 1

# System checks
echo "✓ Running Django system checks..."
python manage.py check --deploy 2>&1 | grep -E "(System check|issue|Error)" | head -5

# Migrate
echo "✓ Applying migrations..."
python manage.py migrate --run-syncdb 2>&1 | tail -3

echo ""
echo "PHASE 2: FUNCTIONAL TESTING"
echo "───────────────────────────────────────────────────────────────────────────────"

# Setup test data
echo "✓ Setting up test data..."
echo "yes" | python manage.py setup_test_data --confirm 2>&1 | grep -E "(Creating|Created|Summary)" | head -15

echo ""
echo "PHASE 3: AUTO SIGN-OUT BEHAVIOR TEST"
echo "───────────────────────────────────────────────────────────────────────────────"

python manage.py shell << 'PYEOF'
from datetime import timedelta
from django.utils import timezone
from HeroHours.models import Users, ActivityLog
from HeroHours.views import handle_bulk_updates, check_in_or_out

print("\n✓ Testing Mass Sign-Out (with hour docking)...")
user1 = Users.objects.create(
    User_ID=9991,
    First_Name='Test', Last_Name='MassSignOut',
    Total_Hours=timedelta(0), Total_Seconds=0,
    Checked_In=True, Is_Active=True,
    Last_In=timezone.now() - timedelta(hours=3)
)
handle_bulk_updates('+404', timezone.now())
user1.refresh_from_db()
expected = 7200  # 3h - 1h = 2h
status = "✅ PASS" if abs(user1.Total_Seconds - expected) < 10 else "❌ FAIL"
print(f"  Result: {user1.Total_Seconds/3600:.2f}h credited (expected 2h) - {status}")

print("\n✓ Testing Individual Check-Out (no docking)...")
user2 = Users.objects.create(
    User_ID=9992,
    First_Name='Test', Last_Name='IndividualOut',
    Total_Hours=timedelta(0), Total_Seconds=0,
    Checked_In=True, Is_Active=True,
    Last_In=timezone.now() - timedelta(hours=3)
)
log = ActivityLog(user=user2, entered='9992', operation='', status='')
check_in_or_out(user2, timezone.now(), log, 1)
user2.refresh_from_db()
expected = 10800  # Full 3h
status = "✅ PASS" if abs(user2.Total_Seconds - expected) < 10 else "❌ FAIL"
print(f"  Result: {user2.Total_Seconds/3600:.2f}h credited (expected 3h) - {status}")

Users.objects.filter(User_ID__in=[9991, 9992]).delete()
PYEOF

echo ""
echo "PHASE 4: SECURITY AUDIT"
echo "───────────────────────────────────────────────────────────────────────────────"

echo "✓ Checking for vulnerable dependencies..."
pip list 2>&1 | grep -E "(Django|cryptography|urllib3)" | head -5

echo ""
echo "✓ Verifying security settings..."
python manage.py shell << 'PYEOF'
from django.conf import settings
import os

checks = {
    "DEBUG mode": os.environ.get('DEBUG', 'False'),
    "SECRET_KEY set": "Yes" if settings.SECRET_KEY else "No",
    "SECURE_BROWSER_XSS_FILTER": getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False),
    "X_FRAME_OPTIONS": getattr(settings, 'X_FRAME_OPTIONS', 'Not set'),
    "SECURE_CONTENT_TYPE_NOSNIFF": getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False),
}

for check, value in checks.items():
    print(f"  {check}: {value}")
PYEOF

echo ""
echo "PHASE 5: DATABASE & QUERIES"
echo "───────────────────────────────────────────────────────────────────────────────"

python manage.py shell << 'PYEOF'
from HeroHours.models import Users, ActivityLog

users = Users.objects.count()
active = Users.objects.filter(Is_Active=True).count()
checked_in = Users.objects.filter(Checked_In=True).count()
logs = ActivityLog.objects.count()

print(f"✓ Database operational:")
print(f"  Total users: {users}")
print(f"  Active users: {active}")
print(f"  Checked in: {checked_in}")
print(f"  Activity logs: {logs}")
PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "                         AUDIT COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"

