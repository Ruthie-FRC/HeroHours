# Standard library imports
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

# Third-party imports
import requests
from django.contrib.auth import logout
from django.contrib.auth.decorators import permission_required
from django.core import serializers
from django.db.models import DurationField, ExpressionWrapper, F
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from dotenv import find_dotenv, load_dotenv

# Local imports
from . import models

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)


# Create your views here.
@permission_required("HeroHours.change_users")
def index(request: HttpRequest) -> HttpResponse:
    """
    Main dashboard view displaying active members and check-in status.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered members.html template with user data
    """
    # Query all users from the database
    users_data = models.Users.objects.filter(Is_Active=True).order_by('Last_Name', 'First_Name')
    users_checked_in = models.Users.objects.filter(Checked_In=True).count()
    local_log_entries = models.ActivityLog.objects.all()[:9]

    # Pass the users data to the template
    return render(request, 'members.html',
                  {'usersData': users_data, "checked_in": users_checked_in, 'local_log_entries': local_log_entries})


@permission_required("HeroHours.change_users", raise_exception=True)
@ratelimit(key='user', rate='60/m', method='POST')
def handle_entry(request: HttpRequest) -> JsonResponse:
    user_input = request.POST.get('user_input', '').strip()
    
    # Input validation: limit length and sanitize
    if not user_input:
        return JsonResponse({'status': 'Error', 'message': 'No input provided'})
    
    if len(user_input) > 100:
        return JsonResponse({'status': 'Error', 'message': 'Input too long'})
    
    right_now = timezone.now()

    # Handle special commands first
    special_result = handle_special_commands(user_input)
    if special_result:
        return special_result

    if user_input in ['-404', '+404']:
        return handle_bulk_updates(user_input)
    if user_input == "---":
        logout(request)
        return redirect('login')

    log = models.ActivityLog(
        entered=user_input,
        operation='None',
        status='Error',  # Initial status
    )
    count = models.Users.objects.only("Checked_In").filter(Checked_In=True).count()
    try:
        user = models.Users.objects.filter(User_ID=user_input).first()
        log.user = user
        if not user:
            log.status = "User Not Found"
            log.save()
            return JsonResponse(
                {'status': 'User Not Found', 'user_id': None, 'operation': None, 'newlog': model_to_dict(log),
                 'count': count})
    except Exception as e:
        logger.error(f"Error in handle_entry: {str(e)}")
        return JsonResponse({'status': "Error", 'newlog': {'userID': user_input, 'operation': "None", 'status': 'Error',
                                                           'message': 'An error occurred'}, 'state': None, 'count': count})

    # Perform Check-In or Check-Out operations
    operation_result = check_in_or_out(user, right_now, log, count)
    # Return JSON response with status and user info
    return JsonResponse(operation_result)


def handle_special_commands(user_id: str) -> Optional[HttpResponse]:
    """
    Process special command inputs like 'Send', 'admin', etc.
    
    Args:
        user_id: Input string from user
        
    Returns:
        HttpResponse or None: Redirect response if special command, None otherwise
    """
    if user_id == "Send":
        return redirect('send_data_to_google_sheet')

    if user_id in ['+00', '+01', '*']:
        return redirect('index')

    if user_id == "admin":
        return redirect('/admin/')

    return None


def handle_bulk_updates(user_id: str, at_time: Optional[datetime] = None) -> HttpResponse:
    """
    Bulk check-in or check-out all users (DEBUG mode only for check-in).
    
    Args:
        user_id: '-404' for bulk check-in, '+404' for auto check-out
        at_time: Optional datetime for the operation, defaults to now
        
    Returns:
        HttpResponse: Redirect to index page
    """
    if at_time is None:
        at_time = timezone.now()
    updated_users = []
    updated_log = []

    if user_id == '-404':
        if not os.environ.get('DEBUG', 'False') == 'True':
            return redirect('index')
        getall = models.Users.objects.filter(Checked_In=False)
    else:
        getall = models.Users.objects.filter(Checked_In=True)

    for user in getall:
        log = models.ActivityLog(user_id=user.User_ID,entered=user.User_ID, operation='Check In' if user_id == '-404' else 'Auto Check Out',
                                 status='Success')

        if user_id == '-404':
            user.Checked_In = True
            user.Last_In = at_time
        else:
            if not user.Last_In:
                user.Last_In = at_time
            user.Checked_In = False
            threshold = int(os.environ.get('AUTO_LOGOUT_THRESHOLD_SECONDS',3600))
            if (at_time - user.Last_In) > timedelta(seconds=threshold):
                user.Total_Hours = ExpressionWrapper(F('Total_Hours') + ((at_time-timedelta(seconds=threshold)) - user.Last_In),
                                                      output_field=DurationField())
                user.Total_Seconds = F('Total_Seconds') + round(((at_time-timedelta(seconds=threshold)) - user.Last_In).total_seconds())
            else:
                user.Total_Hours = ExpressionWrapper(F('Total_Hours') + (at_time - user.Last_In),
                                                  output_field=DurationField())
                user.Total_Seconds = F('Total_Seconds') + round((at_time - user.Last_In).total_seconds())
            user.Last_Out = at_time

        updated_log.append(log)
        updated_users.append(user)

    models.Users.objects.bulk_update(updated_users, ["Checked_In", "Total_Hours", "Total_Seconds", "Last_In", "Last_Out"])
    models.ActivityLog.objects.bulk_create(updated_log)
    # Redirect to index after bulk updates
    return redirect('index')


def check_in_or_out(user: models.Users, right_now: datetime, log: models.ActivityLog, count: int) -> dict:
    """
    Toggle user check-in status and update hours.
    
    Args:
        user: Users model instance
        right_now: Current datetime
        log: ActivityLog instance to save
        count: Current count of checked-in users
        
    Returns:
        dict: Status information including operation, state, log, and count
    """
    new_count = count
    if user.Checked_In:
        new_count -= 1
        state = False
        log.operation = 'Check Out'
        if not user.Last_In:
            user.Last_In = right_now
        user.Total_Hours = ExpressionWrapper(F('Total_Hours') + (right_now - user.Last_In),
                                             output_field=DurationField())
        user.Total_Seconds = F('Total_Seconds') + round((right_now - user.Last_In).total_seconds())
        user.Last_Out = right_now
    else:
        new_count += 1
        state = True
        log.operation = 'Check In'
        user.Last_In = right_now

    user.Checked_In = not user.Checked_In
    log.status = 'Success'
    operation = "Check Out" if not state else "Check In"
    if not user.Is_Active:
        log.operation = "None"
        state = None
        log.status = "Inactive User"
    else:
        count = new_count
        user.save()

    # Save log and user updates
    log.save()
    return {
        'status': operation,
        'state': state,
        'newlog': model_to_dict(log),
        'count': count,
    }


APP_SCRIPT_URL = os.environ.get('APP_SCRIPT_URL', '')


@permission_required("HeroHours.change_users", raise_exception=True)
@ratelimit(key='user', rate='10/m', method='POST')
def send_data_to_google_sheet(request: HttpRequest) -> JsonResponse:
    """
    Export all users and activity logs to Google Sheets via Apps Script.
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse: Status of the export operation
    """
    users = models.Users.objects.all()
    serialized_data = serializers.serialize('json', users, use_natural_foreign_keys=True)
    serialized_data2 = serializers.serialize('json', models.ActivityLog.objects.all(), use_natural_foreign_keys=True)
    together = [serialized_data, serialized_data2]
    all_data = json.dumps(obj=together)
    count = users.filter(Checked_In=True).count()

    # Send POST request to the Apps Script API
    try:
        response = requests.post(APP_SCRIPT_URL, json=json.loads(all_data))
        # Handle the response (for example, check if it was successful)
        if response.status_code == 200:
            result = response.json()
            return JsonResponse({'status': 'Sent', 'result': result, 'count': count})
        else:
            return JsonResponse({'status': 'Sent', 'message': 'Failed to send data', 'count': count})
    except Exception as e:
        logger.error("Failed to send data to Google Sheet: %s", e)
        return JsonResponse({'status': 'error', 'message': str(e), 'count': count})


@permission_required("HeroHours.view_users", raise_exception=True)
@ratelimit(key='user', rate='30/m', method='GET')
def sheet_pull(request: HttpRequest) -> HttpResponse:
    """
    Export users data to CSV format.
    This view is deprecated. Use the API endpoint /api/sheet-pull/ with token authentication instead.
    """
    members = models.Users.objects.all()
    response = 'User_ID,First_Name,Last_Name,Total_Hours,Total_Seconds,Last_In,Last_Out,Is_Active,\n'
    for member in members:
        response += f"{member.User_ID},{member.First_Name},{member.Last_Name},{member.get_total_hours()},{member.Total_Seconds},{member.Last_In},{member.Last_Out},{member.Is_Active}\n"
    return HttpResponse(response, content_type='text/csv')


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('login')


@permission_required("HeroHours.change_users")
def live_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'live.html')
