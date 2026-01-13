from django.db import models
from django.conf import settings

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

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

    title = models.CharField(max_length=255)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE, related_name='jobs')
    company = models.CharField(max_length=255) # Deprecated, keeping for migration
    company_profile = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    description = models.TextField()
    location = models.CharField(max_length=255)
    url = models.URLField()
    education_level_required = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='None')
    experience_required_years = models.IntegerField(blank=True, null=True)
    employer_email = models.EmailField(blank=True, null=True, help_text="Email address to send applications to")
    expiry_date = models.DateField(blank=True, null=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class Application(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Applied', 'Applied'),
        ('Interviewing', 'Interviewing'),
        ('Rejected', 'Rejected'),
        ('Offer', 'Offer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    cv_used = models.ForeignKey('users.UserDocument', on_delete=models.SET_NULL, null=True, blank=True)
    cover_letter = models.FileField(upload_to='cover_letters/', blank=True, null=True)

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
