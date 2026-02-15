"""
Management command to set up test data for HeroHours application.

⚠️  SAFETY: This command includes multiple safeguards to prevent accidental execution:
    - Only runs in DEBUG mode (development)
    - Requires --confirm flag to execute
    - Shows preview of what will be created before execution
    - Will not run in production environments

This command creates:
- Test superuser(s) for admin access
- Test staff users with appropriate permissions
- Test members with varying hours and check-in states
- Sample activity log entries

Usage:
    python manage.py setup_test_data --confirm              # Create test data
    python manage.py setup_test_data --confirm --clear      # Clear and recreate
    python manage.py setup_test_data --confirm --members 10 # Create 10 members
"""

import sys
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from HeroHours.models import ActivityLog, Users


class Command(BaseCommand):
    help = '⚠️  Set up TEST DATA - requires --confirm flag and DEBUG mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            required=True,
            help='REQUIRED: Confirm you want to create test data (safety measure)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new data',
        )
        parser.add_argument(
            '--members',
            type=int,
            default=5,
            help='Number of test members to create (default: 5)',
        )
        parser.add_argument(
            '--no-superuser',
            action='store_true',
            help='Skip creating superuser',
        )
        parser.add_argument(
            '--no-staff',
            action='store_true',
            help='Skip creating staff users',
        )
        parser.add_argument(
            '--i-am-sure',
            action='store_true',
            help='Override DEBUG mode check (USE WITH EXTREME CAUTION)',
        )

    def handle(self, *args, **options):
        # Safety check 1: Confirm flag is required
        if not options['confirm']:
            raise CommandError(
                '⚠️  ERROR: The --confirm flag is required to run this command.\n'
                'This is a safety measure to prevent accidental execution.\n'
                'Usage: python manage.py setup_test_data --confirm'
            )

        # Safety check 2: Only run in DEBUG mode (unless overridden)
        if not settings.DEBUG and not options['i_am_sure']:
            raise CommandError(
                '🚫 SAFETY BLOCK: This command will NOT run in production mode!\n'
                '   DEBUG is False, which indicates a production environment.\n'
                '   This command is designed for development/testing only.\n\n'
                '   If you REALLY need to run this (not recommended), use:\n'
                '   python manage.py setup_test_data --confirm --i-am-sure\n'
            )

        clear_data = options['clear']
        num_members = options['members']
        create_superuser = not options['no_superuser']
        create_staff = not options['no_staff']

        # Safety check 3: Show what will happen and require confirmation
        self._show_preview(clear_data, num_members, create_superuser, create_staff)
        
        if not self._confirm_execution():
            self.stdout.write(self.style.WARNING('\n❌ Cancelled by user'))
            return

        try:
            with transaction.atomic():
                if clear_data:
                    self._clear_test_data()

                if create_superuser:
                    self._create_superuser()

                if create_staff:
                    self._create_staff_users()

                self._create_test_members(num_members)
                self._create_sample_logs()

                self.stdout.write(self.style.SUCCESS('\n✅ Test data setup complete!'))
                self._print_summary()

        except Exception as e:
            raise CommandError(f'Error setting up test data: {str(e)}')

    def _show_preview(self, clear_data: bool, num_members: int, 
                     create_superuser: bool, create_staff: bool):
        """Show preview of what will be created."""
        self.stdout.write(self.style.WARNING('\n' + '=' * 70))
        self.stdout.write(self.style.WARNING('⚠️  TEST DATA SETUP PREVIEW'))
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(f'\n📋 What will be created:')
        
        if clear_data:
            self.stdout.write(self.style.ERROR(
                '  🗑️  CLEAR: All test data will be DELETED first!'
            ))
        
        if create_superuser:
            self.stdout.write('  👤 Superuser: admin (password: admin123)')
        
        if create_staff:
            self.stdout.write('  👥 Staff users: staff1, staff2 (password: staff123)')
        
        self.stdout.write(f'  🎭 Test members: {num_members} members')
        self.stdout.write('  📝 Activity logs: Sample log entries')
        
        self.stdout.write(f'\n🌍 Environment:')
        self.stdout.write(f'  DEBUG mode: {settings.DEBUG}')
        self.stdout.write(f'  Database: {settings.DATABASES["default"]["NAME"]}')

    def _confirm_execution(self) -> bool:
        """Ask user to confirm execution."""
        self.stdout.write(self.style.WARNING(
            '\n⚠️  Are you sure you want to proceed? This will modify the database.'
        ))
        
        # In non-interactive mode (automated scripts), don't ask for confirmation
        if not sys.stdin.isatty():
            self.stdout.write('  Non-interactive mode detected - proceeding automatically')
            return True
        
        response = input('Type "yes" to continue: ').strip().lower()
        return response == 'yes'

    def _clear_test_data(self):
        """Clear existing test data."""
        self.stdout.write(self.style.WARNING('\n🗑️  Clearing existing test data...'))
        
        # Delete test users (ID range 1000-9999 for test members)
        deleted_members = Users.objects.filter(User_ID__range=(1000, 9999)).delete()
        self.stdout.write(f'  - Deleted {deleted_members[0]} test members')
        
        # Delete test staff/admin users (but keep real ones)
        test_usernames = ['admin', 'staff1', 'staff2', 'teststaff']
        deleted_users = User.objects.filter(username__in=test_usernames).delete()
        self.stdout.write(f'  - Deleted {deleted_users[0]} test auth users')

    def _create_superuser(self):
        """Create test superuser."""
        self.stdout.write(self.style.HTTP_INFO('\n👤 Creating superuser...'))
        
        username = 'admin'
        email = 'admin@herohours.test'
        password = 'admin123'
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'  ℹ️  Superuser "{username}" already exists')
        else:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ Created superuser: {username} (password: {password})'
            ))

    def _create_staff_users(self):
        """Create test staff users with appropriate permissions."""
        self.stdout.write(self.style.HTTP_INFO('\n👥 Creating staff users...'))
        
        # Get or create Staff group
        staff_group, created = Group.objects.get_or_create(name='Staff')
        if created:
            content_type = ContentType.objects.get_for_model(Users)
            permissions = Permission.objects.filter(content_type=content_type)
            staff_group.permissions.set(permissions)
            self.stdout.write('  ✅ Created Staff group with permissions')
        
        # Create staff users
        staff_users = [
            {'username': 'staff1', 'first_name': 'Staff', 'last_name': 'Member1', 'email': 'staff1@test.com'},
            {'username': 'staff2', 'first_name': 'Staff', 'last_name': 'Member2', 'email': 'staff2@test.com'},
        ]
        
        for user_data in staff_users:
            username = user_data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  ℹ️  Staff user "{username}" already exists')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=user_data['email'],
                    password='staff123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                )
                user.is_staff = True
                user.save()
                user.groups.add(staff_group)
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ Created staff user: {username} (password: staff123)'
                ))

    def _create_test_members(self, count: int):
        """Create test members with varying data."""
        self.stdout.write(self.style.HTTP_INFO(f'\n🎭 Creating {count} test members...'))
        
        test_members = [
            # Members with no hours
            {'id': 1001, 'first': 'Alice', 'last': 'Anderson', 'hours': 0, 'checked_in': False},
            {'id': 1002, 'first': 'Bob', 'last': 'Builder', 'hours': 0, 'checked_in': False},
            
            # Members with some hours, not checked in
            {'id': 1003, 'first': 'Carol', 'last': 'Cooper', 'hours': 3600, 'checked_in': False},  # 1 hour
            {'id': 1004, 'first': 'David', 'last': 'Davis', 'hours': 19800, 'checked_in': False},  # 5.5 hours
            
            # Members currently checked in
            {'id': 1005, 'first': 'Emma', 'last': 'Evans', 'hours': 7200, 'checked_in': True},  # 2 hours
            
            # Members with significant hours
            {'id': 1006, 'first': 'Frank', 'last': 'Foster', 'hours': 36000, 'checked_in': False},  # 10 hours
            {'id': 1007, 'first': 'Grace', 'last': 'Garcia', 'hours': 90000, 'checked_in': False},  # 25 hours
            
            # Inactive member
            {'id': 1008, 'first': 'Henry', 'last': 'Harris', 'hours': 5400, 'checked_in': False, 'active': False},
            
            # More members for testing
            {'id': 1009, 'first': 'Iris', 'last': 'Irving', 'hours': 14400, 'checked_in': False},  # 4 hours
            {'id': 1010, 'first': 'Jack', 'last': 'Johnson', 'hours': 28800, 'checked_in': True},  # 8 hours
        ]
        
        created_count = 0
        for member_data in test_members[:count]:
            user_id = member_data['id']
            
            # Check if member already exists
            if Users.objects.filter(User_ID=user_id).exists():
                self.stdout.write(f'  ℹ️  Member {user_id} already exists, skipping')
                continue
            
            # Create member
            total_seconds = member_data['hours']
            member = Users.objects.create(
                User_ID=user_id,
                First_Name=member_data['first'],
                Last_Name=member_data['last'],
                Total_Hours=timedelta(seconds=total_seconds),
                Total_Seconds=total_seconds,
                Checked_In=member_data['checked_in'],
                Is_Active=member_data.get('active', True),
                Last_In=timezone.now() if member_data['checked_in'] else None,
            )
            
            created_count += 1
            status = '🟢' if member.Checked_In else '⚪'
            self.stdout.write(
                f'  {status} Created: {member.First_Name} {member.Last_Name} '
                f'(ID: {member.User_ID}, Hours: {member.get_total_hours()})'
            )
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_count} test members'))

    def _create_sample_logs(self):
        """Create sample activity log entries."""
        self.stdout.write(self.style.HTTP_INFO('\n📝 Creating sample activity logs...'))
        
        # Get some members to create logs for
        members = list(Users.objects.filter(User_ID__range=(1001, 1010)).order_by('User_ID'))
        
        if not members:
            self.stdout.write('  ⚠️  No members found to create logs for')
            return
        
        # Create logs based on available members
        log_entries = []
        if len(members) >= 1:
            log_entries.append({'user': members[0], 'operation': 'Check In', 'status': 'Success'})
            log_entries.append({'user': members[0], 'operation': 'Check Out', 'status': 'Success'})
        if len(members) >= 2:
            log_entries.append({'user': members[1], 'operation': 'Check In', 'status': 'Success'})
        if len(members) >= 3:
            log_entries.append({'user': members[2], 'operation': 'Check Out', 'status': 'Success'})
        if len(members) >= 4:
            log_entries.append({'user': members[3], 'operation': 'Check In', 'status': 'Success'})
        
        created_count = 0
        for log_data in log_entries:
            ActivityLog.objects.create(
                user=log_data['user'],
                entered=str(log_data['user'].User_ID),
                operation=log_data['operation'],
                status=log_data['status'],
            )
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {created_count} activity log entries'))

    def _print_summary(self):
        """Print summary of created data."""
        self.stdout.write(self.style.HTTP_INFO('\n📊 Summary:'))
        
        # Count users
        superusers = User.objects.filter(is_superuser=True).count()
        staff_users = User.objects.filter(is_staff=True, is_superuser=False).count()
        
        # Count members
        total_members = Users.objects.count()
        active_members = Users.objects.filter(Is_Active=True).count()
        checked_in = Users.objects.filter(Checked_In=True).count()
        
        # Count logs
        total_logs = ActivityLog.objects.count()
        
        self.stdout.write(f'  👤 Superusers: {superusers}')
        self.stdout.write(f'  👥 Staff users: {staff_users}')
        self.stdout.write(f'  🎭 Total members: {total_members}')
        self.stdout.write(f'  ✅ Active members: {active_members}')
        self.stdout.write(f'  🟢 Checked in: {checked_in}')
        self.stdout.write(f'  📝 Activity logs: {total_logs}')
        
        self.stdout.write(self.style.SUCCESS('\n🎉 You can now access the application:'))
        self.stdout.write('  🌐 Admin: http://127.0.0.1:5892/admin/')
        self.stdout.write('     Username: admin, Password: admin123')
        self.stdout.write('  🌐 Main app: http://127.0.0.1:5892/HeroHours/')
        self.stdout.write('     Use admin or staff1/staff2 (password: staff123)')
