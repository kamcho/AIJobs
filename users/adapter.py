from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import PersonalProfile

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of signup, the
        unsaved user instance is passed and should be saved by this
        method.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Get extra data from sociallogin
        data = sociallogin.account.extra_data
        print(f"DEBUG: save_user extra_data: {data}")
        
        # In Google, 'name' is usually the full name
        full_name = data.get('name') or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()
        print(f"DEBUG: save_user extracted full_name: '{full_name}'")
        
        if full_name:
            try:
                profile, created = PersonalProfile.objects.get_or_create(user=user)
                print(f"DEBUG: save_user profile found/created: {profile}, created: {created}")
                profile.full_name = full_name
                profile.save()
                # Update the cached profile on the user instance
                user.profile = profile
                print(f"DEBUG: save_user profile updated successfully with name: '{full_name}'")
            except Exception as e:
                print(f"DEBUG ERROR: save_user failed to update profile: {str(e)}")
            
        return user

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).
        """
        print(f"DEBUG: pre_social_login called. Existing: {sociallogin.is_existing}")
        
        # If the user already exists, we might want to update their profile name
        if sociallogin.is_existing:
            data = sociallogin.account.extra_data
            print(f"DEBUG: pre_social_login extra_data: {data}")
            full_name = data.get('name') or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()
            print(f"DEBUG: pre_social_login extracted full_name: '{full_name}'")
            
            if full_name:
                try:
                    user = sociallogin.user
                    profile, created = PersonalProfile.objects.get_or_create(user=user)
                    print(f"DEBUG: pre_social_login profile found/created: {profile}, created: {created}")
                    
                    # Only update if current full_name is empty or we want to overwrite it
                    if not profile.full_name or profile.full_name.strip() == "":
                        profile.full_name = full_name
                        profile.save()
                        # Update the cached profile on the user instance
                        user.profile = profile
                        print(f"DEBUG: pre_social_login profile updated successfully with name: '{full_name}'")
                    else:
                        print(f"DEBUG: pre_social_login profile already has name: '{profile.full_name}', skipping update.")
                except Exception as e:
                    print(f"DEBUG ERROR: pre_social_login failed to update profile: {str(e)}")

    def populate_user(self, request, sociallogin, data):
        """
        Populates the user instance with data from the sociallogin.
        """
        user = super().populate_user(request, sociallogin, data)
        # We don't need to do much here since MyUser uses email as username
        # and allauth handles that via ACCOUNT_USER_MODEL_USERNAME_FIELD = None
        return user
