# Test Data Setup Guide

This document explains how to use the `setup_test_data` management command to quickly set up the HeroHours application with test users and data for development and testing.

## Quick Start

```bash
# Set up the application with default test data
python manage.py setup_test_data --confirm

# Access the application:
# - Admin: http://127.0.0.1:5892/admin/ (admin/admin123)
# - Main app: http://127.0.0.1:5892/HeroHours/ (staff1 or staff2/staff123)
```

## Safety Features

This command includes **multiple layers of protection** to prevent accidental execution:

### 1. Required --confirm Flag
The command will not run without the `--confirm` flag:
```bash
# ❌ This will fail:
python manage.py setup_test_data

# ✅ This is required:
python manage.py setup_test_data --confirm
```

### 2. DEBUG Mode Check
The command refuses to run if `DEBUG=False` (production mode):
```bash
# If DEBUG=False, you'll see:
🚫 SAFETY BLOCK: This command will NOT run in production mode!
   DEBUG is False, which indicates a production environment.
   This command is designed for development/testing only.
```

### 3. Preview + Interactive Confirmation
Before making any changes, the command shows:
- What will be created
- Current environment (DEBUG mode, database)
- Requires you to type "yes" to proceed

### 4. Override (Emergency Use Only)
If you really need to run in production (not recommended):
```bash
python manage.py setup_test_data --confirm --i-am-sure
```

## Usage Examples

### Basic Usage
Create 5 test members (default):
```bash
python manage.py setup_test_data --confirm
```

### Create More Members
Create 10 test members:
```bash
python manage.py setup_test_data --confirm --members 10
```

### Clear and Recreate
Clear existing test data and create fresh data:
```bash
python manage.py setup_test_data --confirm --clear
```

### Skip Certain Data
Skip creating staff users:
```bash
python manage.py setup_test_data --confirm --no-staff
```

Skip creating superuser:
```bash
python manage.py setup_test_data --confirm --no-superuser
```

### Combine Options
Create 15 members without staff users:
```bash
python manage.py setup_test_data --confirm --members 15 --no-staff
```

## What Gets Created

### 1. Superuser
- **Username:** admin
- **Password:** admin123
- **Email:** admin@herohours.test
- Full admin access to Django admin interface

### 2. Staff Users
Two staff users with permissions to manage members:
- **Username:** staff1, **Password:** staff123
- **Username:** staff2, **Password:** staff123

### 3. Test Members
Members with varying data for realistic testing:

| ID   | Name             | Hours  | Status      | Description |
|------|------------------|--------|-------------|-------------|
| 1001 | Alice Anderson   | 0h     | Not checked in | New member |
| 1002 | Bob Builder      | 0h     | Not checked in | New member |
| 1003 | Carol Cooper     | 1h     | Not checked in | Some hours |
| 1004 | David Davis      | 5.5h   | Not checked in | Moderate hours |
| 1005 | Emma Evans       | 2h     | **Checked in** | Currently working |
| 1006 | Frank Foster     | 10h    | Not checked in | Significant hours |
| 1007 | Grace Garcia     | 25h    | Not checked in | High hours |
| 1008 | Henry Harris     | 1.5h   | **Inactive** | Inactive member |
| 1009 | Iris Irving      | 4h     | Not checked in | Medium hours |
| 1010 | Jack Johnson     | 8h     | **Checked in** | Currently working |

### 4. Activity Logs
Sample activity log entries showing check-ins and check-outs for testing the history features.

## Command Output

When you run the command, you'll see colorful output showing progress:

```
======================================================================
⚠️  TEST DATA SETUP PREVIEW
======================================================================

📋 What will be created:
  👤 Superuser: admin (password: admin123)
  👥 Staff users: staff1, staff2 (password: staff123)
  🎭 Test members: 10 members
  📝 Activity logs: Sample log entries

🌍 Environment:
  DEBUG mode: True
  Database: /path/to/db.sqlite3

⚠️  Are you sure you want to proceed? This will modify the database.
Type "yes" to continue: yes

👤 Creating superuser...
  ✅ Created superuser: admin (password: admin123)

👥 Creating staff users...
  ✅ Created Staff group with permissions
  ✅ Created staff user: staff1 (password: staff123)
  ✅ Created staff user: staff2 (password: staff123)

🎭 Creating 10 test members...
  ⚪ Created: Alice Anderson (ID: 1001, Hours: 0h 0m 0s)
  ⚪ Created: Bob Builder (ID: 1002, Hours: 0h 0m 0s)
  ⚪ Created: Carol Cooper (ID: 1003, Hours: 1h 0m 0s)
  ⚪ Created: David Davis (ID: 1004, Hours: 5h 30m 0s)
  🟢 Created: Emma Evans (ID: 1005, Hours: 2h 0m 0s)
  ⚪ Created: Frank Foster (ID: 1006, Hours: 10h 0m 0s)
  ⚪ Created: Grace Garcia (ID: 1007, Hours: 25h 0m 0s)
  ⚪ Created: Henry Harris (ID: 1008, Hours: 1h 30m 0s)
  ⚪ Created: Iris Irving (ID: 1009, Hours: 4h 0m 0s)
  🟢 Created: Jack Johnson (ID: 1010, Hours: 8h 0m 0s)
  ✅ Created 10 test members

📝 Creating sample activity logs...
  ✅ Created 9 activity log entries

✅ Test data setup complete!

📊 Summary:
  👤 Superusers: 1
  👥 Staff users: 2
  🎭 Total members: 10
  ✅ Active members: 9
  🟢 Checked in: 2
  📝 Activity logs: 9

🎉 You can now access the application:
  🌐 Admin: http://127.0.0.1:5892/admin/
     Username: admin, Password: admin123
  🌐 Main app: http://127.0.0.1:5892/HeroHours/
     Use admin or staff1/staff2 (password: staff123)
```

## Idempotent Behavior

The command can be run multiple times safely:
- Existing users are detected and skipped
- Only missing data is created
- No duplicates are created

Example:
```bash
# First run - creates 5 members
python manage.py setup_test_data --confirm --members 5

# Second run - creates 5 MORE members (total 10)
python manage.py setup_test_data --confirm --members 10
```

## Clearing Test Data

To start fresh, use the `--clear` flag:
```bash
python manage.py setup_test_data --confirm --clear
```

This removes:
- Test members (IDs 1000-9999)
- Test auth users (admin, staff1, staff2)
- Associated activity logs

## Testing Workflow

### Typical Development Setup

1. **Initial Setup:**
   ```bash
   python manage.py migrate
   python manage.py setup_test_data --confirm --members 10
   python manage.py runserver
   ```

2. **Access the Application:**
   - Open http://127.0.0.1:5892/admin/
   - Login with admin/admin123
   - View the test members

3. **Reset When Needed:**
   ```bash
   python manage.py setup_test_data --confirm --clear --members 5
   ```

### CI/CD Integration

For automated testing, the command detects non-interactive mode:
```bash
# In CI/CD pipeline (no interactive prompt)
python manage.py setup_test_data --confirm --members 5
```

## Auto Sign-Out Hour Docking

The application includes an auto sign-out feature that "docks" an hour when users are checked in too long:

- **Threshold:** 1 hour (3600 seconds) by default
- **Behavior:** If checked in > threshold, subtracts 1 hour from credited time
- **Example:** Checked in for 3 hours → Credits only 2 hours
- **Configuration:** Set `AUTO_LOGOUT_THRESHOLD_SECONDS` environment variable

This feature has been tested and verified to work correctly with the test data setup.

## Troubleshooting

### Command Won't Run
**Error:** `the following arguments are required: --confirm`
**Solution:** Add the `--confirm` flag

### Production Block
**Error:** `SAFETY BLOCK: This command will NOT run in production mode!`
**Solution:** This is intentional. Set `DEBUG=True` in development or use `--i-am-sure` (not recommended)

### Permission Errors
**Error:** Database permission errors
**Solution:** Ensure you have write access to the database file

### Import Errors
**Error:** `ModuleNotFoundError: No module named 'django'`
**Solution:** Install dependencies with `pip install -r requirements.txt`

## Advanced Usage

### Custom Environment Variables

```bash
# Use custom threshold for auto sign-out testing
export AUTO_LOGOUT_THRESHOLD_SECONDS=7200  # 2 hours
python manage.py setup_test_data --confirm
```

### Database Configuration

The command respects your Django database settings:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'herohours_dev',
        # ...
    }
}
```

## Help

View all available options:
```bash
python manage.py setup_test_data --help
```

For more information, see the main project documentation.
