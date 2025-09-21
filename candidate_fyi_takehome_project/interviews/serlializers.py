from rest_framework import serializers
from datetime import datetime, timedelta, timezone

class InterviewAvailabilitySerializerIn(serializers.Serializer):
    search_start = serializers.DateTimeField(required=False)
    search_end = serializers.DateTimeField(required=False)
    valid_interval= serializers.IntegerField(required=False, default=30)
    
    def validate(self, data):
 
        if 'search_start' not in data:
            data['search_start'] = datetime.now(timezone.utc) + timedelta(hours=24, seconds=5)
        if 'search_end' not in data:
            data['search_end'] = datetime.now(timezone.utc) + timedelta(days=7)
        if 'valid_interval' not in data:
            data['valid_interval'] = 30
            
        errors = {}
        
        allowed_intervals = [60, 30, 15, 10, 5, 1]
        
        if data['search_start'] >= data['search_end']:
            errors['search_start'] = "Search start date must be earlier than search end date"
        
        if data['search_start'] < datetime.now(timezone.utc) + timedelta(hours=24):
            errors['search_start'] = f"Search start date must be at least 24 hours in the future"
        
        if data['valid_interval'] not in allowed_intervals:
            errors['valid_interval'] = f"Must be one of these values: {', '.join(map(str, allowed_intervals))}"
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
    
class InterviewerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

class AvailableSlotSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

class InterviewAvailabilitySerializerOut(serializers.Serializer):
    interviewId = serializers.IntegerField()
    name = serializers.CharField()
    duration = serializers.IntegerField()
    interviewers = InterviewerSerializer(many=True)
    availableSlots = AvailableSlotSerializer(many=True)
