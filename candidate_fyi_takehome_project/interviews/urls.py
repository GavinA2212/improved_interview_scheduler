from django.urls import path
from .views import InterviewAvailabilityView

app_name = "interviews"

urlpatterns = [
    path("<int:id>/availability/", InterviewAvailabilityView.as_view(), name="interview_availabilty"),
]