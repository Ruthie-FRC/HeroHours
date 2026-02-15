# Third-party imports
from django.db.models import Subquery
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_csv import renderers as csv_renderers

# Local imports
from HeroHours.models import ActivityLog, Users
from HeroHours_api.authentication import URLTokenAuthentication


# Create your views here.
class SheetPullThrottle(UserRateThrottle):
    rate = '30/hour'

class SheetPullRenderer(csv_renderers.CSVRenderer):
    header = ['Id','Last Name','First Name','Is Active','Hours','Checked In','Last In','Last Out']

class SheetPullAPI(APIView):
    renderer_classes = [SheetPullRenderer]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [SheetPullThrottle]

    def get(self, request, *args, **kwargs):
        members = Users.objects.all().order_by('Last_Name','First_Name')
        content = [{
                    'Id': member.User_ID,
                    'Last Name': member.Last_Name,
                    'First Name': member.First_Name,
                    'Is Active': member.Is_Active,
                    'Hours': member.get_total_hours(),
                    'Checked In': member.Checked_In,
                    'Last In': member.Last_In,
                    'Last Out': member.Last_Out,
                    } for member in members]
        return Response(content, status=status.HTTP_200_OK)

class MeetingListThrottle(UserRateThrottle):
    rate = '30/hour'

class MeetingListRender(csv_renderers.CSVRenderer):
    header = ['user_id','user__Last_Name','user__First_Name']
    labels = {
        'user_id': 'Id',
        'user__Last_Name': 'Last Name',
        'user__First_Name': 'First Name',
    }

class MeetingPullAPI(APIView):
    renderer_classes = [MeetingListRender]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [MeetingListThrottle]

    def get(self, request, day, month, year, *args, **kwargs):
        # Validate input parameters
        try:
            day = int(day)
            month = int(month)
            year = int(year)
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                return Response({'error': 'Invalid date parameters'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid date parameters'}, status=status.HTTP_400_BAD_REQUEST)
            
        query = ActivityLog.objects.filter(id__in=Subquery(
            ActivityLog.objects.all()
            .filter(timestamp__day=day, timestamp__month=month, timestamp__year=year, operation='Check In')
            .order_by('user_id').distinct('user_id').values('id')
        )).order_by('user__Last_Name', 'user__First_Name').values('user_id', 'user__First_Name', 'user__Last_Name')
        members = list(query)

        return Response(members, status=status.HTTP_200_OK)
