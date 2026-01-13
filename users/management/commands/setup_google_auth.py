from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Create a placeholder Google SocialApp'

    def handle(self, *args, **options):
        # Ensure Site exists
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={'domain': '127.0.0.1:8000', 'name': '127.0.0.1:8000'}
        )
        
        # Create SocialApp
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            name='Google Login',
            defaults={
                'client_id': 'PLACEHOLDER_CLIENT_ID',
                'secret': 'PLACEHOLDER_SECRET',
            }
        )
        app.sites.add(site)
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created placeholder Google SocialApp'))
        else:
            self.stdout.write(self.style.WARNING('Google SocialApp already exists'))
