import base64
import json
import logging
from datetime import timedelta

import requests
import os

from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models import F, DurationField, ExpressionWrapper
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core import serializers
from dotenv import load_dotenv, find_dotenv

from . import models
from django.http import JsonResponse, HttpResponse
from django.forms.models import model_to_dict

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)


# Create your views here.
@permission_required("HeroHours.change_users")
def index(request):
    # Query all users from the database
    usersData = models.Users.objects.filter(Is_Active=True).order_by('Last_Name','First_Name')
    users_checked_in = models.Users.objects.filter(Checked_In=True).count()
    local_log_entries = models.ActivityLog.objects.all()[:9]

    # Pass the users data to the template
    return render(request, 'members.html',
                  {'usersData': usersData, "checked_in": users_checked_in, 'local_log_entries': local_log_entries})


@permission_required("HeroHours.change_users", raise_exception=True)
def handle_entry(request):
    user_input = request.POST.get('user_input')
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
        return JsonResponse({'status': "Error", 'newlog': {'userID': user_input, 'operation': "None", 'status': 'Error',
                                                           'message': str(e)}, 'state': None, 'count': count})

    # Perform Check-In or Check-Out operations
    operation_result = check_in_or_out(user, right_now, log, count)
    # Return JSON response with status and user info
    return JsonResponse(operation_result)


def handle_special_commands(user_id):
    if user_id == "Send":
        return redirect('send_data_to_google_sheet')

    if user_id in ['+00', '+01', '*']:
        return redirect('index')

    if user_id == "admin":
        return redirect('/admin/')

    return None


def handle_bulk_updates(user_id, at_time=None):
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

    models.Users.objects.bulk_update(updated_users, ["Checked_In", "Total_Hours", "Total_Seconds", "Last_Out"])
    models.ActivityLog.objects.bulk_create(updated_log)
    # Redirect to index after bulk updates
    return redirect('index')


def check_in_or_out(user, right_now, log, count):
    count2=count
    if user.Checked_In:
        count2 -= 1
        state = False
        log.operation = 'Check Out'
        if not user.Last_In:
            user.Last_In = right_now
        user.Total_Hours = ExpressionWrapper(F('Total_Hours') + (right_now - user.Last_In),
                                             output_field=DurationField())
        user.Total_Seconds = F('Total_Seconds') + round((right_now - user.Last_In).total_seconds())
        user.Last_Out = right_now
    else:
        count2 += 1
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
        count = count2
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
def send_data_to_google_sheet(request):
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
def sheet_pull(request):
    key = request.GET.get('key')
    if not key:
        raise BadRequest()

    username, password = base64.b64decode(key).decode('ascii').split(":")
    user = authenticate(request, username=username, password=password)
    if not user:
        raise PermissionDenied()
    members = models.Users.objects.all()
    response = 'User_ID,First_Name,Last_Name,Total_Hours,Total_Seconds,Last_In,Last_Out,Is_Active,\n'
    for member in members:
        response += f"{member.User_ID},{member.First_Name},{member.Last_Name},{member.get_total_hours()},{member.Total_Seconds},{member.Last_In},{member.Last_Out},{member.Is_Active}\n"
    return HttpResponse(response,content_type='text/csv')


def logout_view(request):
    logout(request)
    return redirect('login')


@permission_required("HeroHours.change_users")
def live_view(request):
    return render(request, 'live.html')