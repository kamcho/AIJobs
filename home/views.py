from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from users.models import PersonalProfile, MySkill, UserDocument
from .models import AIChatMessage
from jobs.models import Application, JobListing
import json

def index(request):
    latest_jobs = JobListing.objects.filter(is_active=True).order_by('-posted_at')[:6]
    return render(request, 'home/index.html', {'latest_jobs': latest_jobs})


def privacy_policy(request):
    return render(request, 'home/privacy_policy.html')

def robots_txt(request):
    """Serve robots.txt file"""
    content = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /auth/
Disallow: /accounts/
Disallow: /mpesa/

Sitemap: {}/sitemap.xml
""".format(request.build_absolute_uri('/').rstrip('/'))
    return HttpResponse(content, content_type='text/plain')

@login_required
def dashboard(request):
    user = request.user
    
    if user.role == 'Employer':
        # Employer Dashboard Logic
        company = user.company
        my_jobs = JobListing.objects.filter(company_profile=company).order_by('-posted_at') if company else JobListing.objects.none()
        
        # Get applications for these jobs
        job_ids = my_jobs.values_list('id', flat=True)
        recent_applications = Application.objects.filter(job_id__in=job_ids).order_by('-applied_at')[:10]
        
        context = {
            'company': company,
            'my_jobs': my_jobs,
            'recent_applications': recent_applications,
            'total_jobs_count': my_jobs.count(),
            'total_applications_count': Application.objects.filter(job_id__in=job_ids).count(),
            'pending_review_count': Application.objects.filter(job_id__in=job_ids, status='Under Review').count(),
        }
        return render(request, 'home/employer_dashboard.html', context)

    # Job Seeker Dashboard Logic (Existing)
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
            is_active=True,
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

@csrf_exempt
def contact(request):
    if request.method == 'POST':
        try:
            # Handle both JSON and Form data if needed, but here it looks like a standard form or simple AJAX
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                name = data.get('name')
                email = data.get('email')
                phone = data.get('phone')
                message = data.get('message')
            else:
                name = request.POST.get('name')
                email = request.POST.get('email')
                phone = request.POST.get('phone')
                message = request.POST.get('message')

            if not all([name, email, phone, message]):
                return JsonResponse({'error': 'All fields are required'}, status=400)

            subject = f"Contact Form Submission from {name}"
            email_body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}"
            
            send_mail(
                subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                ['kevingitundu@gmail.com'],
                fail_silently=False,
            )
            return JsonResponse({'message': 'Message sent successfully!'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
