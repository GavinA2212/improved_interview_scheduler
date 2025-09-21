from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from services.mock_availability import get_free_busy_data
from candidate_fyi_takehome_project.interviews.serlializers import InterviewAvailabilitySerializerIn
from candidate_fyi_takehome_project.interviews.models import InterviewTemplate, Interviewer
from candidate_fyi_takehome_project.interviews.utils import compute_available_slots


class InterviewAvailabilityView(APIView):
    """
    -search_start (Optional) - datetime start of search window (default now + 24h)
    -search_end (Optional) - datetime end of search window (default now + 7d)
    -valid_interval_end (Optional) - integer (60, 30, 15, 10, 5, 1)
     determines what ending time interval the interview can be created (default 30)
        ex: 15 = xx:00, xx:15, xx:30, xx:45
    """
    def get(self, request, id):
        
        serializer = InterviewAvailabilitySerializerIn(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        search_start = validated_data.get("search_start")
        search_end = validated_data.get("search_end")
        valid_interval = validated_data.get("valid_interval")
        
        try:
            template = InterviewTemplate.objects.get(id=id)
        except InterviewTemplate.DoesNotExist:
            return Response({"error": "Interview Template not found"}, status.HTTP_404_NOT_FOUND)
        
        interviewers = template.interviewers.all()
        interviewer_ids = [p.id for p in interviewers]
        busy_data = get_free_busy_data(interviewer_ids)
        
        # Combine interviewer busy blocks into a single list
        all_busy_blocks = []
        for interviewer_data in busy_data:
            all_busy_blocks.extend(interviewer_data["busy"])

        available_interview_slots = compute_available_slots(search_start, search_end, valid_interval, all_busy_blocks, interviewers, template.duration)

        return Response(available_interview_slots)
