from django.contrib import admin
from .models import MyUser, PersonalProfile, DocumentType, UserDocument, MySkill, WorkExperience, Education

@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'is_staff', 'is_active')
    search_fields = ('email',)
    list_filter = ('role', 'is_staff', 'is_active')

@admin.register(PersonalProfile)
class PersonalProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'country', 'gender')
    search_fields = ('full_name', 'user__email', 'city')
    list_filter = ('gender', 'country')

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'user', 'uploaded_at', 'extracted_content')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('user__email', 'extracted_content')

@admin.register(MySkill)
class MySkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'proficiency')
    list_filter = ('proficiency',)
    search_fields = ('name', 'user__email')

@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'user', 'start_date', 'is_current')
    list_filter = ('is_current', 'start_date')
    search_fields = ('job_title', 'company_name', 'user__email')

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('level', 'institution', 'user', 'start_date', 'end_date')
    list_filter = ('level', 'start_date')
    search_fields = ('institution', 'user__email', 'degree')
