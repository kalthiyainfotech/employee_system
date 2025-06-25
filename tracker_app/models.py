from django.db import models
from django.utils import timezone

# Create your models here.
class Employee(models.Model):
    name = models.CharField(max_length=20)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=128) 
    

class TimeLog(models.Model):
    emp = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate) 
    start_tracker = models.DateTimeField(null=True, blank=True)
    end_tracker = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(null=True, blank=True)
    pause_time = models.DurationField(null=True, blank=True)
    work_time = models.DurationField(null=True, blank=True)

    class Meta:
        unique_together = ('emp', 'date')
