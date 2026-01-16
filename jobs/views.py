from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import JobListing, JobCategory, Application, JobRequirement, Company
from .forms import ApplicationForm, JobListingForm, JobRequirementForm, CompanyForm
from .services import EmailService
from .utils import DocumentGenerator
from home.ai_service import AIService
from django.contrib.auth.decorators import user_passes_test

def job_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    jobs = JobListing.objects.all().order_by('-posted_at')

    # Filter for Attachment role
    if request.user.is_authenticated and request.user.role == 'Attachment':
        jobs = jobs.filter(terms='Attachment')
    
    # Filter by preferences if no category is selected and user is authenticated
    if not category_id and not query and request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.preferred_categories.exists():
            jobs = jobs.filter(category__in=profile.preferred_categories.all())

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(company__icontains=query) | 
            Q(description__icontains=query)
        )
        
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
    
    context = {
        'jobs': jobs,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
        'personal_complete': personal_complete,
        'documents_complete': documents_complete,
        'preferences_complete': preferences_complete,
        'show_profile_nudge_modal': show_profile_nudge_modal,
    }
    return render(request, 'jobs/job_list.html', context)

@login_required
def apply_via_email(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    
    if not job.employer_email:
        messages.error(request, "This job does not support email applications.")
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
            application.status = 'Applied'
            
            # If AI text was provided, generate document based on chosen format
            if form.cleaned_data.get('cover_letter_text'):
                text_content = form.cleaned_data.get('cover_letter_text')
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
                messages.success(request, f"Application sent successfully! ({message})")
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
        
    context = {
        'job': job,
        'user_application': user_application,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
def application_list(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_at')
    return render(request, 'jobs/application_list.html', {'applications': applications})

@login_required
def application_detail(request, pk):
    application = get_object_or_404(Application, pk=pk, user=request.user)
    return render(request, 'jobs/application_detail.html', {'application': application})

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@user_passes_test(is_admin)
def admin_create_job(request):
    if request.method == 'POST':
        job_form = JobListingForm(request.POST)
        if job_form.is_valid():
            job = job_form.save()
            
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
        company_id = request.GET.get('company')
        initial = {}
        if company_id:
            try:
                company = Company.objects.get(pk=company_id)
                initial['company_profile'] = company
                initial['company'] = company.name
            except Company.DoesNotExist:
                pass
        job_form = JobListingForm(initial=initial)
        
    return render(request, 'jobs/admin_create_job.html', {
        'job_form': job_form,
    })

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
