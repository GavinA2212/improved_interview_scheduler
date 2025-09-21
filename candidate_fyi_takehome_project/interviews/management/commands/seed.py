from django.core.management.base import BaseCommand
from candidate_fyi_takehome_project.interviews.models import Interviewer, InterviewTemplate


class Command(BaseCommand):
    help = "Seed the database with Interviewers and an InterviewTemplate"
    
    def handle(self, *args, **options):
        # Create Interviewers with different timezones
        seed_interviewers = [
            {"timezone": "America/Chicago", "workday_start_hour": 9, "workday_end_hour": 17},
            {"timezone": "America/New_York", "workday_start_hour": 8, "workday_end_hour": 16},
            {"timezone": "America/Los_Angeles", "workday_start_hour": 10, "workday_end_hour": 18},
        ]

        interviewer_objs = []
        for interviewer_data in seed_interviewers:
            obj, created = Interviewer.objects.get_or_create(**interviewer_data)
            interviewer_objs.append(obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Interviewer: {obj.id} ({obj.timezone})"))
            else:
                self.stdout.write(self.style.WARNING(f"Interviewer already exists: {obj.id} ({obj.timezone})"))

        # Create InterviewTemplate
        template, created = InterviewTemplate.objects.get_or_create(
            name="Test Interview",
            defaults={"duration": 60}
        )
        
        # Add all interviewers to the template
        template.interviewers.set(interviewer_objs)
        template.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created InterviewTemplate: {template.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"InterviewTemplate already exists: {template.name}"))
            
        self.stdout.write(self.style.SUCCESS(f"Template has {template.interviewers.count()} interviewers assigned"))