from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q, Avg, Count, F
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import JobListing, JobCategory, Application, JobRequirement, Company, Wishlist
from .forms import ApplicationForm, JobListingForm, JobRequirementForm, CompanyForm
from .services import EmailService
from .utils import DocumentGenerator
from home.ai_service import AIService
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction

def job_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    jobs = JobListing.objects.filter(is_active=True).order_by('-posted_at')

    # Filter for Attachment role
    if request.user.is_authenticated and request.user.role == 'Attachment':
        jobs = jobs.filter(terms='Attachment')
    
    # Filter by preferences if no category is selected and user is authenticated
    if not category_id and not query and request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.preferred_categories.exists():
            preferred_jobs = jobs.filter(category__in=profile.preferred_categories.all())
            if preferred_jobs.exists():
                jobs = preferred_jobs
            # No else: if empty, we keep the original 'jobs' which has all listings

    if query:
        # 1. AI-Powered Category Matching
        # Prepare categories data for AI
        categories_data = list(JobCategory.objects.values('name', 'keywords'))
        ai_matched_category_names = AIService.match_categories(query, categories_data)
        
        # 2. Build Search Filter
        search_filter = Q(
            Q(title__icontains=query) | 
            Q(company__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(category__name__in=ai_matched_category_names)
        )
        
        # 3. Keyword-based matching as fallback/complement
        search_words = [w.strip() for w in query.split() if len(w.strip()) > 2]
        for word in search_words:
            search_filter |= Q(category__keywords__icontains=word)
            
        jobs = jobs.filter(search_filter).distinct()
        
    if category_id:
        try:
            jobs = jobs.filter(category_id=category_id)
        except (ValueError, TypeError):
            pass

    categories = JobCategory.objects.all().order_by('name')

    # Profile nudge state for logged-in users
    personal_complete = False
    documents_complete = False
    preferences_complete = False
    show_profile_nudge_modal = False

    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        from users.models import UserDocument  # local import to avoid cycles at top

        if profile is not None:
            personal_complete = bool(getattr(profile, "full_name", "")) and bool(
                getattr(profile, "phone_primary", "")
            )
            preferences_complete = profile.preferred_categories.exists()

        cv_documents = UserDocument.objects.filter(
            user=request.user, document_type__name__icontains='CV'
        )
        documents_complete = cv_documents.exists()

        show_profile_nudge_modal = (
            not personal_complete or not documents_complete or not preferences_complete
        )

    user_wishlisted_ids = []
    if request.user.is_authenticated:
        user_wishlisted_ids = list(Wishlist.objects.filter(user=request.user).values_list('job_id', flat=True))
    
    context = {
        'jobs': jobs,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'personal_complete': personal_complete,
        'documents_complete': documents_complete,
        'preferences_complete': preferences_complete,
        'show_profile_nudge_modal': show_profile_nudge_modal,
        'user_wishlisted_ids': user_wishlisted_ids,
    }
    return render(request, 'jobs/job_list.html', context)

@login_required
def apply_via_email(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    
    # Check if a target exists for the application method
    target_exists = (
        (job.application_method == 'email' and job.employer_email) or
        (job.application_method in ['website', 'google_form'] and (job.application_url or job.url)) or
        (job.application_method == 'other')
    )
    
    if not target_exists:
        messages.error(request, "This job listing is missing application details. Please contact support.")
        return redirect('job_detail', pk=pk)
        
    if request.method == 'POST':
        action = request.POST.get('action')
        form = ApplicationForm(request.POST, request.FILES, user=request.user)
        
        if action == 'generate_ai':
            generated_text = AIService.generate_cover_letter(request.user, job)
            # Re-initialize form with generated text and current data (like cv_used)
            form = ApplicationForm(user=request.user, initial={
                'cover_letter_text': generated_text,
                'cv_used': request.POST.get('cv_used')
            })
            messages.info(request, "AI Cover Letter generated! You can review and edit it below.")
            return render(request, 'jobs/email_application.html', {'form': form, 'job': job})

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.job = job
            application.status = 'Under Review'
            
            # If AI text was provided, generate document based on chosen format
            if form.cleaned_data.get('cover_letter_text'):
                text_content = form.cleaned_data.get('cover_letter_text')
                application.cover_letter_text = text_content
                file_format = form.cleaned_data.get('file_format', 'pdf')
                filename = f"cover_letter_{request.user.id}_{job.id}.{file_format}"
                
                doc_content = DocumentGenerator.get_document_content(text_content, file_format)
                application.cover_letter.save(filename, ContentFile(doc_content), save=False)
                
            application.save()
            
            # Send Email
            success, message = EmailService.send_application_email(
                user=request.user,
                job=job,
                cover_letter_file=application.cover_letter,
                cv_file_path=application.cv_used.file.path if application.cv_used else None
            )
            
            if success:
                # Check if message indicates materials sent to user's email
                if "sent to your email" in message.lower() or "forwarded to your email" in message.lower():
                    messages.info(request, f"📧 {message}")
                else:
                    messages.success(request, f"✅ Application sent successfully! {message}")
            else:
                messages.warning(request, f"Application logged, but email failed: {message}")
                
            return redirect('job_detail', pk=pk)
    else:
        form = ApplicationForm(user=request.user)
        
    return render(request, 'jobs/email_application.html', {'form': form, 'job': job})

def job_detail(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    user_application = None
    if request.user.is_authenticated:
        user_application = Application.objects.filter(user=request.user, job=job).first()
        
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, job=job).exists()
        
    context = {
        'job': job,
        'user_application': user_application,
        'is_wishlisted': is_wishlisted,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
def application_list(request):
    if request.user.role == 'Employer' and request.user.company:
        # Employers see applications for their company's jobs
        applications = Application.objects.filter(job__company_profile=request.user.company).order_by('-applied_at')
    elif request.user.role == 'Admin':
        applications = Application.objects.all().order_by('-applied_at')
    else:
        # Job seekers see their own applications
        applications = Application.objects.filter(user=request.user).order_by('-applied_at')
    return render(request, 'jobs/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    # Base query for basic security
    if request.user.role == 'Admin':
        application = get_object_or_404(Application, pk=pk)
    elif request.user.role == 'Employer' and request.user.company:
        # Allow if the application is for a job in the employer's company
        application = get_object_or_404(Application, pk=pk, job__company_profile=request.user.company)
    else:
        # Normal user only sees their own
        application = get_object_or_404(Application, pk=pk, user=request.user)
        
    return render(request, 'jobs/application_detail.html', {'application': application})

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@login_required
def job_add(request):
    # Check if user is either Admin or Employer
    if not (request.user.role == 'Admin' or request.user.role == 'Employer'):
        messages.error(request, "You do not have permission to post jobs.")
        return redirect('dashboard')
    
    # If Employer, check if they have an assigned company
    if request.user.role == 'Employer' and not request.user.company:
        messages.warning(request, "Your account is not linked to a company. Please contact an admin.")
        return redirect('dashboard')

    if request.method == 'POST':
        job_form = JobListingForm(request.POST)
        if job_form.is_valid():
            with transaction.atomic():
                job = job_form.save(commit=False)
                
                # Auto-assign company for Employers
                if request.user.role == 'Employer':
                    job.company_profile = request.user.company
                    job.company = request.user.company.name
                
                job.save()
                
                # Handle Requirements
                req_descriptions = request.POST.getlist('requirement_description')
                req_mandatory = request.POST.getlist('requirement_mandatory')
                
                for i in range(len(req_descriptions)):
                    desc = req_descriptions[i].strip()
                    if desc:
                        is_mandatory = True if str(i) in req_mandatory else False
                        JobRequirement.objects.create(
                            job=job,
                            description=desc,
                            is_mandatory=is_mandatory
                        )
                
                messages.success(request, f"Job Listing '{job.title}' created successfully!")
                return redirect('job_detail', pk=job.pk)
    else:
        # Pre-fill for employers or via GET param for admins
        initial = {}
        if request.user.role == 'Employer' and request.user.company:
            initial['company_profile'] = request.user.company
            initial['company'] = request.user.company.name
        else:
            company_id = request.GET.get('company')
            if company_id:
                try:
                    company = Company.objects.get(pk=company_id)
                    initial['company_profile'] = company
                    initial['company'] = company.name
                except Company.DoesNotExist:
                    pass
                    
        job_form = JobListingForm(initial=initial)
        
    return render(request, 'jobs/job_add.html', {
        'job_form': job_form,
        'role': request.user.role
    })

@user_passes_test(is_admin)
def admin_create_job(request):
    return redirect('job_add')

@user_passes_test(is_admin)
def admin_edit_job(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    if request.method == 'POST':
        job_form = JobListingForm(request.POST, instance=job)
        if job_form.is_valid():
            job = job_form.save()
            
            # Update Requirements: Remove existing and create new ones
            job.requirements.all().delete()
            
            req_descriptions = request.POST.getlist('requirement_description')
            req_mandatory = request.POST.getlist('requirement_mandatory')
            
            for i in range(len(req_descriptions)):
                desc = req_descriptions[i].strip()
                if desc:
                    is_mandatory = True if str(i) in req_mandatory else False
                    JobRequirement.objects.create(
                        job=job,
                        description=desc,
                        is_mandatory=is_mandatory
                    )
            
            messages.success(request, f"Job Listing '{job.title}' updated successfully!")
            return redirect('job_detail', pk=job.pk)
    else:
        job_form = JobListingForm(instance=job)
        
    return render(request, 'jobs/admin_edit_job.html', {
        'job_form': job_form,
        'job': job,
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'Company "{company.name}" created successfully!')
            return redirect('company_detail', pk=company.pk)
    else:
        form = CompanyForm()
    
    return render(request, 'jobs/company_form.html', {
        'form': form,
        'title': 'Add New Company'
    })


def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    jobs = company.jobs.all().order_by('-posted_at')
    context = {
        'company': company,
        'jobs': jobs,
    }
    return render(request, 'jobs/company_detail.html', context)
@login_required
def wishlist_list(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('job', 'job__company_profile').order_by('-created_at')
    return render(request, 'jobs/wishlist_list.html', {'wishlist_items': wishlist_items})

@login_required
def toggle_wishlist(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    wishlist_item = Wishlist.objects.filter(user=request.user, job=job).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.info(request, f'Removed "{job.title}" from your saved jobs.')
    else:
        Wishlist.objects.create(user=request.user, job=job)
        messages.success(request, f'Saved "{job.title}" to your wishlist.')
    
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('job_detail', pk=pk)
@login_required
def job_analytics(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    
    # Permission check: Only job owner (Employer) or Admin
    if request.user.role != 'Admin' and (request.user.role != 'Employer' or job.company_profile != request.user.company):
        messages.error(request, "Access denied. You can only view analytics for your company's jobs.")
        return redirect('dashboard')
    
    all_applications = job.applications.all()
    
    # Metrics (calculated on all applications)
    total_applicants = all_applications.count()
    
    # Filtering for the table
    applications = job.applications.select_related('user', 'user__profile', 'cv_used')
    
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    if search_query:
        applications = applications.filter(
            Q(user__email__icontains=search_query) |
            Q(user__profile__full_name__icontains=search_query)
        )
    
    if status_filter:
        applications = applications.filter(status=status_filter)

    applications = applications.order_by(F('cv_used__ai_score').desc(nulls_last=True), '-applied_at')
    
    # AI Score Metrics
    avg_ai_score = all_applications.aggregate(avg=Avg('cv_used__ai_score'))['avg'] or 0
    
    # Prepare status distribution with percentages
    stats = []
    status_choices = ['Under Review', 'Shortlisted', 'Interviewing', 'Offer', 'Rejected']
    for status in status_choices:
        count = all_applications.filter(status=status).count()
        pct = (count / total_applicants * 100) if total_applicants > 0 else 0
        
        color = 'var(--primary)'
        if status == 'Interviewing': color = '#f59e0b'
        elif status == 'Shortlisted': color = '#8b5cf6'
        elif status == 'Offer': color = 'var(--success)'
        elif status == 'Rejected': color = '#ef4444'
        
        stats.append({
            'label': status,
            'count': count,
            'pct': pct,
            'color': color,
            'css_class': status.lower()
        })
    
    context = {
        'job': job,
        'applications': applications,
        'total_applicants': total_applicants,
        'avg_ai_score': round(avg_ai_score, 1),
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': status_choices,
    }
    return render(request, 'jobs/job_analytics.html', context)

@login_required
def update_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    
    # Permission check: Only job owner (Employer) or Admin
    if request.user.role != 'Admin' and (request.user.role != 'Employer' or application.job.company_profile != request.user.company):
        messages.error(request, "Access denied. You can only update statuses for your company's jobs.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.save()
            messages.success(request, f"Status updated to {new_status} for {application.user.email}")
        else:
            messages.error(request, "Invalid status selected.")
            
    referer = request.META.get('HTTP_REFERER')
    if referer:
        if 'analytics' in referer and '#applicant-pool' not in referer:
            referer += '#applicant-pool'
        return redirect(referer)
    return redirect(reverse('job_analytics', kwargs={'pk': application.job.pk}) + '#applicant-pool')

@login_required
def toggle_job_status(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    
    # Permission check: Only job owner (Employer) or Admin
    if request.user.role != 'Admin' and (request.user.role != 'Employer' or job.company_profile != request.user.company):
        messages.error(request, "Access denied. You can only update your own job statuses.")
        return redirect('dashboard')
    
    job.is_active = not job.is_active
    job.save()
    
    status_text = "Reopened" if job.is_active else "Closed"
    messages.success(request, f"Job '{job.title}' has been {status_text}.")
    
    return redirect('job_analytics', pk=job.pk)

@login_required
def bulk_update_application_status(request):
    if request.method == 'POST':
        application_ids = request.POST.getlist('application_ids')
        new_status = request.POST.get('status')
        job_pk = request.POST.get('job_pk')
        
        if not application_ids or not new_status:
            messages.error(request, "Please select applications and a status.")
            if job_pk:
                return redirect('job_analytics', pk=job_pk)
            return redirect('dashboard')
            
        if new_status not in dict(Application.STATUS_CHOICES):
            messages.error(request, "Invalid status selected.")
            if job_pk:
                return redirect('job_analytics', pk=job_pk)
            return redirect('dashboard')

        # Filter applications to ensure user has permission
        # Admin can update any. Employer can only update for their company.
        if request.user.role == 'Admin':
            applications = Application.objects.filter(pk__in=application_ids)
        elif request.user.role == 'Employer' and request.user.company:
            applications = Application.objects.filter(
                pk__in=application_ids, 
                job__company_profile=request.user.company
            )
        else:
            messages.error(request, "Permission denied.")
            return redirect('dashboard')
            
        count = applications.update(status=new_status)
        messages.success(request, f"Successfully updated status to '{new_status}' for {count} applications.")
        
        if job_pk:
            return redirect(reverse('job_analytics', kwargs={'pk': job_pk}) + '#applicant-pool')
            
    return redirect('dashboard')
