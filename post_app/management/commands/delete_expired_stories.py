from django.core.management.base import BaseCommand
from django.utils import timezone
from post_app.models import Story

class Command(BaseCommand):
    help = 'Delete expired stories'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        expired = Story.objects.filter(expires_at__lt=now)
        count = expired.count()
        expired.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired stories."))
