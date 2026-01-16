from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import PersonalProfile, MySkill, UserDocument
from .models import AIChatMessage
from jobs.models import Application, JobListing

def index(request):
    return render(request, 'home/index.html')


def privacy_policy(request):
    return render(request, 'home/privacy_policy.html')

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
    preferences_complete = False
    if profile and profile.preferred_categories.exists():
        preferences_complete = True
        recommended_jobs = JobListing.objects.filter(
            category__in=profile.preferred_categories.all()
        ).exclude(applications__user=user).order_by('-posted_at')[:4]

    # Completion logic
    personal_complete = (
        profile is not None
        and bool(getattr(profile, "full_name", ""))
        and bool(getattr(profile, "phone_primary", ""))
    )
    documents_complete = cv_documents.exists()

    steps = [
        personal_complete,      # Personal Info
        educations.exists(),    # Education
        work_experiences.exists(),  # Work Experience
        skills.exists(),        # Skills
        documents_complete,     # Documents (CV present)
        preferences_complete,   # Job Preferences
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
        'personal_complete': personal_complete,
        'documents_complete': documents_complete,
        'preferences_complete': preferences_complete,
        'show_profile_nudge_modal': (
            not personal_complete or not documents_complete or not preferences_complete
        ),
    }
    return render(request, 'home/dashboard.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .ai_service import AIService

@csrf_exempt
def ai_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message')
            if not message:
                return JsonResponse({'error': 'Message required'}, status=400)
            
            # Save user message
            if request.user.is_authenticated:
                AIChatMessage.objects.create(user=request.user, role='user', content=message)
                
            response = AIService.chat(request.user, message)
            
            # Save assistant response
            if request.user.is_authenticated:
                AIChatMessage.objects.create(user=request.user, role='assistant', content=response)
                
            return JsonResponse({'response': response})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def chat_history(request):
    messages = AIChatMessage.objects.filter(user=request.user).order_by('timestamp')[:50]
    history = [
        {'role': msg.role, 'content': msg.content}
        for msg in messages
    ]
    return JsonResponse({'history': history})
