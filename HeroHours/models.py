from django.db import models
from django.core.validators import MinValueValidator


# Create your models here.
class Users(models.Model):
    """
    Model representing a HERO member with check-in/check-out tracking.
    
    Tracks volunteer hours, check-in status, and activity for each member.
    """
    User_ID = models.IntegerField(primary_key=True)
    First_Name = models.CharField(max_length=50)
    Last_Name = models.CharField(max_length=50)
    Total_Hours = models.DurationField()
    Checked_In = models.BooleanField(default=False)
    Total_Seconds = models.FloatField(default=0, validators=[MinValueValidator(0)])
    Last_In = models.DateTimeField(null=True, blank=True)
    Last_Out = models.DateTimeField(null=True, blank=True)
    Is_Active = models.BooleanField(default=True)

    def get_total_hours(self):
        """
        Format total seconds as a human-readable hours/minutes/seconds string.
        
        Returns:
            str: Formatted string like "10h 30m 45s"
        """
        hours, remainder = divmod(int(self.Total_Seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    class Meta:
        # Specify the table name
        db_table = 'Users'
        verbose_name = "Members"
        verbose_name_plural = "Members"
        indexes = [
            models.Index(fields=['Last_Name', 'First_Name']),
            models.Index(fields=['Checked_In']),
            models.Index(fields=['Is_Active']),
        ]

    def __str__(self):
        return f"{self.First_Name} {self.Last_Name}: {self.User_ID} - {self.Total_Hours}"


class ActivityLog(models.Model):
    """
    Model representing activity log entries for check-in/check-out operations.
    
    Tracks all user interactions including check-ins, check-outs, and errors.
    """
    OPERATION_CHOICES = [
        ('Check In', 'Check In'),
        ('Check Out', 'Check Out'),
        ('None', "None"),
        ('Auto Check Out', 'Auto Check Out'),
        ('Reset', 'Reset'),
    ]

    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Error', 'Error'),
        ('User Not Found', 'User Not Found'),
        ('Inactive User', 'Inactive User'),
    ]

    user = models.ForeignKey(Users, models.CASCADE, blank=True, null=True, related_name='activity_logs')
    entered = models.TextField()
    operation = models.CharField(max_length=15, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(default='', blank=True)  # Optional message field
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp when creating

    def __str__(self):
        return f"{self.user_id} - {self.operation} - {self.status} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']  # Order by most recent logs first
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['operation', 'status']),
        ]