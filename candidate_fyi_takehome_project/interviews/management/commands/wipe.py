from django.core.management.base import BaseCommand
from candidate_fyi_takehome_project.interviews.models import Interviewer, InterviewTemplate


class Command(BaseCommand):
    help = "Delete all Interviewers and InterviewTemplates from the database"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )
    
    def handle(self, *args, **options):
        if not options['force']:
            confirm = input("This will delete ALL interviewers and interview templates. Are you sure? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING("Operation cancelled."))
                return
        
        # Count existing records
        interviewer_count = Interviewer.objects.count()
        template_count = InterviewTemplate.objects.count()
        
        if interviewer_count == 0 and template_count == 0:
            self.stdout.write(self.style.WARNING("No data to delete."))
            return
        
        # Delete all records
        InterviewTemplate.objects.all().delete()
        Interviewer.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {template_count} interview templates and {interviewer_count} interviewers."
            )
        )