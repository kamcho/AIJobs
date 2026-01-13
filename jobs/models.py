from django.db import models
from django.conf import settings

class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Job Categories"

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
    company = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    url = models.URLField()
    education_level_required = models.CharField(max_length=50, choices=LEVEL_CHOICES, default='None')
    experience_required_years = models.IntegerField(blank=True, null=True)
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
