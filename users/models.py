from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class MyUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Job Seeker', 'Job Seeker'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Job Seeker')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class PersonalProfile(models.Model):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    )

    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    phone_primary = models.CharField(max_length=15)
    phone_secondary = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    bio = models.TextField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    preferred_categories = models.ManyToManyField('jobs.JobCategory', blank=True, related_name='interested_users')

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"

class DocumentType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserDocument(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    file = models.FileField(upload_to='user_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_content = models.TextField(blank=True, null=True)
    ai_score = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.document_type.name} - {self.user.email}"

class CVAnalysis(models.Model):
    user_document = models.OneToOneField(UserDocument, on_delete=models.CASCADE, related_name='analysis')
    total_score = models.IntegerField()
    professionalism_score = models.IntegerField()
    relevance_score = models.IntegerField()
    experience_score = models.IntegerField()
    education_score = models.IntegerField()
    missing_sections = models.TextField(blank=True, null=True)
    improvement_suggestions = models.TextField(blank=True, null=True)
    raw_json_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.user_document.user.email}"

    @property
    def professionalism_pct(self):
        return (self.professionalism_score / 20) * 100

    @property
    def relevance_pct(self):
        return (self.relevance_score / 40) * 100

    @property
    def experience_pct(self):
        return (self.experience_score / 30) * 100

    @property
    def education_pct(self):
        return (self.education_score / 10) * 100

class MySkill(models.Model):
    PROFICIENCY_CHOICES = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Expert', 'Expert'),
    )

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

class WorkExperience(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='work_experiences')
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    referee_name = models.CharField(max_length=255, blank=True, null=True)
    referee_contact = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name} ({self.user.email})"

class Education(models.Model):
    LEVEL_CHOICES = (
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary'),
        ('College', 'College'),
        ('University', 'University'),
    )

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=255)
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    degree = models.CharField(max_length=255, blank=True, null=True)
    field_of_study = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    grade = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.level} at {self.institution} ({self.user.email})"
