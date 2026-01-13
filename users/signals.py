from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MyUser, PersonalProfile

@receiver(post_save, sender=MyUser)
def create_personal_profile(sender, instance, created, **kwargs):
    if created:
        PersonalProfile.objects.create(user=instance)

@receiver(post_save, sender=MyUser)
def save_personal_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
