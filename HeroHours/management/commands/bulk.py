import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from HeroHours.models import Users
from HeroHours.views import handle_bulk_updates

class Command(BaseCommand):
    help = 'Run a command at a specific time'

    def add_arguments(self, parser):
       parser.add_argument('userID', type=str, help='The userID/Command to run')
       parser.add_argument('time', type=str, help='The time to use (format: YYYY MM DD HH MM)')

    def handle(self, *args, **options):
        userID = options["userID"]
        time_string = options["time"].split()
        year = int(time_string[0])
        month = int(time_string[1])
        day = int(time_string[2])
        hour = int(time_string[3])
        minute = int(time_string[4])
        handle_bulk_updates(user_id=userID, at_time=datetime(year, month, day, hour, minute))
    