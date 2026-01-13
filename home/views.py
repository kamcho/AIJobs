from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import PersonalProfile, MySkill, UserDocument
from jobs.models import Application, JobListing

def index(request):
    return render(request, 'home/index.html')

@login_required
def dashboard(request):
    user = request.user
    
    # Simple profile retrieval, in real app might use get_or_create or a signal
    profile = getattr(user, 'profile', None)
    skills = user.skills.all()
    applications = user.applications.all().order_by('-applied_at')
    certifications = user.documents.filter(document_type__name__icontains='Cert')
    cv_documents = user.documents.filter(document_type__name__icontains='CV')
    latest_cv = cv_documents.order_by('-uploaded_at').first()
    cv_score = latest_cv.ai_score if latest_cv else None
    
    all_documents = user.documents.all()
    work_experiences = user.work_experiences.all().order_by('-start_date')
    educations = user.educations.all().order_by('-start_date')
    
    # Recommendation logic
    recommended_jobs = JobListing.objects.none()
    if profile and profile.preferred_categories.exists():
        recommended_jobs = JobListing.objects.filter(
            category__in=profile.preferred_categories.all()
        ).exclude(applications__user=user).order_by('-posted_at')[:4]

    # Calculate completion percentage
    steps = [
        profile is not None and bool(profile.full_name), # Personal Info
        educations.exists(), # Education
        work_experiences.exists(), # Work Experience
        skills.exists(), # Skills
        all_documents.exists(), # Documents (CV or Certs)
    ]
    completion_percentage = int((sum(steps) / len(steps)) * 100) if steps else 0

    context = {
        'profile': profile,
        'skills': skills,
        'applications': applications,
        'certifications': certifications,
        'cv_documents': cv_documents,
        'latest_cv': latest_cv,
        'cv_score': cv_score,
        'all_documents': all_documents,
        'work_experiences': work_experiences,
        'educations': educations,
        'completion_percentage': completion_percentage,
        'recommended_jobs': recommended_jobs,
    }
    return render(request, 'home/dashboard.html', context)
