from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task

class JobCategory(models.Model):
    TYPE_CHOICES = (
        ('white_collar', 'White Collar'),
        ('blue_collar', 'Blue Collar'),
        ('mixed', 'Mixed'),
    )
    name = models.CharField(max_length=100, unique=True)
    keywords = models.JSONField(default=list, blank=True)
    category_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='white_collar')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Job Categories"

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    
    primary_phone = models.CharField(max_length=20, blank=True, null=True)
    secondary_phone = models.CharField(max_length=20, blank=True, null=True)
    primary_email = models.EmailField(blank=True, null=True)
    secondary_email = models.EmailField(blank=True, null=True)
    
    founded_in = models.IntegerField(blank=True, null=True, help_text="Year the company was founded")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"

class JobListing(models.Model):
    LEVEL_CHOICES = (
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('College', 'College'),
        ('University', 'University'),
        ('None', 'None'),
    )
    TERM_CHOICES = (
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Contract', 'Contract'),
        ('Freelance', 'Freelance'),
        ('Internship', 'Internship'),
        ('Attachment', 'Attachment'),
        ('None', 'None'),
    )
    APPLICATION_METHOD_CHOICES = (
        ('email', 'Email Application'),
        ('website', 'External Website'),
        ('google_form', 'Google Form'),
        ('other', 'Other Method'),
    )
    
    terms = models.CharField(max_length=255, choices=TERM_CHOICES, default='Full Time')
    title = models.CharField(max_length=255)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='jobs')
    company = models.CharField(max_length=255) # Deprecated, keeping for migration
    company_profile = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    description = models.TextField()
    location = models.CharField(max_length=255)
    url = models.URLField()
    education_level_required = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='None')
    experience_required_years = models.IntegerField(blank=True, null=True)
    
    # Application method fields
    application_method = models.CharField(
        max_length=20, 
        choices=APPLICATION_METHOD_CHOICES, 
        default='website',
        help_text="How should users apply for this job?"
    )
    employer_email = models.EmailField(
        blank=True, 
        null=True, 
        help_text="Email address to send applications to (for email method)"
    )
    application_url = models.URLField(
        blank=True, 
        null=True, 
        help_text="External application URL (for website/Google Form methods)"
    )
    application_instructions = models.TextField(
        blank=True, 
        null=True,
        help_text="Special instructions for applying (optional)"
    )
    
    expiry_date = models.DateField(blank=True, null=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} at {self.company}"
    
    def get_application_method_display_text(self):
        """Returns user-friendly text for the application method"""
        method_texts = {
            'email': 'Apply via Email',
            'website': 'Apply on Website',
            'google_form': 'Apply via Google Form',
            'other': 'Apply Now',
        }
        return method_texts.get(self.application_method, 'Apply Now')


class Application(models.Model):
    STATUS_CHOICES = (
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Interviewing', 'Interviewing'),
        ('Rejected', 'Rejected'),
        ('Offer', 'Offer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Under Review')
    applied_at = models.DateTimeField(auto_now_add=True)
    cv_used = models.ForeignKey('users.UserDocument', on_delete=models.SET_NULL, null=True, blank=True)
    cover_letter = models.FileField(upload_to='cover_letters/', blank=True, null=True)
    cover_letter_text = models.TextField(blank=True, null=True)
    
    # New field to link to UserDocument with analysis
    cover_letter_document = models.ForeignKey(
        'users.UserDocument', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='application_cover_letters'
    )

    def __str__(self):
        return f"{self.user} - {self.job}"

class AutomationLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='automation_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    def __str__(self):
        return f"{self.action} for {self.user} at {self.timestamp}"

class JobRequirement(models.Model):
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='requirements')
    description = models.CharField(max_length=255)
    is_mandatory = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.description} ({'Mandatory' if self.is_mandatory else 'Optional'})"

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return f"{self.user.email} - {self.job.title}"

@receiver(post_save, sender=JobListing)
def trigger_job_notifications(sender, instance, created, **kwargs):
    if created:
        async_task('jobs.tasks.send_job_notification_task', instance.id)
