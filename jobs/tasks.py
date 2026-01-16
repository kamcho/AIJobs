from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from users.models import MyUser, NotificationPreference, UserNotification
from .models import JobListing

def send_job_notification_task(job_id):
    try:
        job = JobListing.objects.get(id=job_id)
        category = job.category
        
        # Find users who:
        # 1. Have this category in their preferred_categories
        # 2. Have email_enabled = True in notification_preferences
        # 3. Are active
        users_to_notify = MyUser.objects.filter(
            profile__preferred_categories=category,
            notification_preferences__email_enabled=True,
            is_active=True
        ).distinct()
        
        domain = Site.objects.get_current().domain
        job_url = f"https://{domain}{reverse('job_detail', args=[job.id])}"
        preferences_url = f"https://{domain}{reverse('profile_detail')}" # Or specific preferences edit url
        
        for user in users_to_notify:
            user_name = getattr(user.profile, 'full_name', user.email)
            if not user_name:
                user_name = user.email.split('@')[0]
                
            context = {
                'user_name': user_name,
                'job': job,
                'category_name': category.name,
                'job_url': job_url,
                'preferences_url': preferences_url,
            }
            
            html_content = render_to_string('emails/job_notification.html', context)
            
            email = EmailMessage(
                subject=f"New Job Match: {job.title} at {job.company}",
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)

            # Record the notification in the database
            UserNotification.objects.create(
                user=user,
                job=job,
                message=f"New match for your profile: {job.title} at {job.company}."
            )
            
    except JobListing.DoesNotExist:
        print(f"Job with ID {job_id} not found for notification task.")
    except Exception as e:
        print(f"Error in send_job_notification_task: {str(e)}")
