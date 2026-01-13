from django.contrib import admin
from .models import JobCategory, JobListing, Application, AutomationLog, JobRequirement

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

class JobRequirementInline(admin.TabularInline):
    model = JobRequirement
    extra = 1

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'category', 'location', 'posted_at')
    list_filter = ('category', 'location', 'posted_at')
    search_fields = ('title', 'company', 'description')
    inlines = [JobRequirementInline]

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__email', 'job__title', 'job__company')

@admin.register(AutomationLog)
class AutomationLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp')
    list_filter = ('timestamp', 'user')
    search_fields = ('action', 'details', 'user__email')

@admin.register(JobRequirement)
class JobRequirementAdmin(admin.ModelAdmin):
    list_display = ('description', 'job', 'is_mandatory')
    list_filter = ('is_mandatory',)
    search_fields = ('description', 'job__title')
