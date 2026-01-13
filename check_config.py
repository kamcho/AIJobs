import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIJobs.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken

def check():
    print("--- SITE CONFIG ---")
    current_site = Site.objects.get_current()
    print(f"Current Site: {current_site.name} (ID: {current_site.id})")
    
    print("\n--- SOCIAL APP CONFIG ---")
    apps = SocialApp.objects.filter(provider='google')
    if not apps.exists():
        print("No Google SocialApp found!")
        return
        
    for app in apps:
        print(f"App: {app.name} (Provider: {app.provider})")
        app_sites = list(app.sites.all())
        print(f"  Linked Sites: {[f'{s.name} (ID: {s.id})' for s in app_sites]}")
        if current_site not in app_sites:
            print(f"  WARNING: App is NOT linked to current site!")
            
    print("\n--- DATA CHECK ---")
    print(f"SocialAccounts: {SocialAccount.objects.count()}")
    print(f"SocialTokens: {SocialToken.objects.count()}")
    
    for sa in SocialAccount.objects.all():
        print(f"  Account for {sa.user.email} (Provider: {sa.provider})")
        token = SocialToken.objects.filter(account=sa).first()
        print(f"    Token exists: {token is not None}")
        if token:
            print(f"    Token (first 10): {token.token[:10]}...")

if __name__ == "__main__":
    check()
