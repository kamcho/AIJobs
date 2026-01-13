import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIJobs.settings')
django.setup()

from users.models import MyUser, PersonalProfile

def test():
    email = 'test_sync_script@example.com'
    # Delete if exists
    MyUser.objects.filter(email=email).delete()
    
    print(f"Creating user with email: {email}")
    try:
        user = MyUser.objects.create(email=email)
        print(f"User created successfully: {user}")
    except Exception as e:
        print(f"Error creating user: {e}")
        return

    # Check if profile was created by signal
    try:
        profile = PersonalProfile.objects.get(user=user)
        print(f"Profile found for user. full_name is: '{profile.full_name}'")
    except PersonalProfile.DoesNotExist:
        print("Profile NOT found for user. Signal might not be working.")
    except Exception as e:
        print(f"Error getting profile: {e}")

    # Test the sync logic from the adapter
    print("Simulating adapter sync logic...")
    fake_full_name = "Google User Name"
    if fake_full_name:
        profile, created = PersonalProfile.objects.get_or_create(user=user)
        print(f"get_or_create profile: created={created}, current full_name='{profile.full_name}'")
        profile.full_name = fake_full_name
        profile.save()
        print(f"Updated full_name to: '{profile.full_name}'")

    # Final check
    profile.refresh_from_db()
    print(f"Final full_name in DB: '{profile.full_name}'")

if __name__ == "__main__":
    test()
