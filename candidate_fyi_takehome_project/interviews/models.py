from django.db import models

# Create your models here.
class Interviewer(models.Model):
    workday_start_hour = models.IntegerField(default = 9)
    workday_end_hour = models.IntegerField(default = 17)
    timezone = models.CharField( default = "UTC")
    
    def __str__(self):
        return f"Interviewer {self.id}"
    
class InterviewTemplate(models.Model):
    name = models.CharField(max_length=255)
    duration = models.IntegerField() # Duration in minutes
    interviewers = models.ManyToManyField(Interviewer, related_name="interview_template")
    
    