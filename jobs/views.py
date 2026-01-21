from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q, Avg, Count, F
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import JobListing, JobCategory, Application, JobRequirement, Company, Wishlist
from .forms import ApplicationForm, JobListingForm, JobRequirementForm, CompanyForm, PublicApplicationForm
from .services import EmailService
from .utils import DocumentGenerator
from home.ai_service import AIService
from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
import json
import uuid
from django.contrib.auth import get_user_model
from users.models import UserDocument, DocumentType, CoverLetterAnalysis, PersonalProfile

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

    # Check for existing application
    has_applied = Application.objects.filter(user=request.user, job=job).exists()
        
    if request.method == 'POST':
        if has_applied:
            messages.error(request, "You have already applied for this job.")
            return redirect('job_detail', pk=pk)

        action = request.POST.get('action')
        form = ApplicationForm(request.POST, request.FILES, user=request.user)
        
        if action == 'generate_ai':
            generated_data = AIService.generate_cover_letter(request.user, job)
            
            # Handle potential None response
            if not generated_data:
                messages.error(request, "Failed to generate cover letter. Please try again.")
                return redirect('apply_via_email', pk=pk)

            # generated_data is now a dict: {'content': '...', 'analysis': {...}}
            generated_text = generated_data.get('content', '')
            analysis_data = generated_data.get('analysis', {})
            
            # Re-initialize form with generated text and current data
            form = ApplicationForm(user=request.user, initial={
                'cover_letter_text': generated_text,
                'cv_used': request.POST.get('cv_used')
            })
            
            # Check subscription for AI features
            has_active_subscription = False
            try:
                if hasattr(request.user, 'subscription'):
                    subscription = request.user.subscription
                    from django.utils import timezone
                    # Check if subscription is active and not expired
                    if subscription.is_active:
                        if subscription.expiry_date:
                            has_active_subscription = subscription.expiry_date > timezone.now()
                        else:
                            # If no expiry date, consider it active if is_active is True
                            has_active_subscription = True
            except Exception:
                pass

            # Pass data to template
            context = {
                'form': form, 
                'job': job,
                'generated_text': generated_text, # For read-only display or strict usage
                'analysis_data_json': json.dumps(analysis_data), # To store in hidden field
                'has_applied': has_applied,
                'has_active_subscription': has_active_subscription
            }
            messages.info(request, "AI Cover Letter generated! Review the preview below.")
            return render(request, 'jobs/email_application.html', context)

        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.job = job
            application.status = 'Under Review'
            
            # If AI text was used (checked via hidden fields or form data)
            # We use the text from the form (which matches generated if read-only)
            text_content = form.cleaned_data.get('cover_letter_text')
            uploaded_file = form.cleaned_data.get('cover_letter_file')
            analysis_json = request.POST.get('analysis_data_json')

            if text_content:
                # 1. Create UserDocument
                # Ensure DocumentType exists
                doc_type, _ = DocumentType.objects.get_or_create(name='Cover Letter')
                
                # Create file content
                file_format = form.cleaned_data.get('file_format', 'pdf')
                filename = f"cover_letter_{request.user.id}_{job.id}.{file_format}"
                doc_content = DocumentGenerator.get_document_content(text_content, file_format)
                
                user_doc = UserDocument.objects.create(
                    user=request.user,
                    document_type=doc_type,
                    extracted_content=text_content
                )
                user_doc.file.save(filename, ContentFile(doc_content))
                
                # 2. Save Analysis if available
                if analysis_json:
                    try:
                        data = json.loads(analysis_json)
                        CoverLetterAnalysis.objects.create(
                            user_document=user_doc,
                            total_score=data.get('total_score', 0),
                            professionalism_score=data.get('professionalism_score', 0),
                            content_score=data.get('content_score', 0),
                            tone_score=data.get('tone_score', 0),
                            impact_score=data.get('impact_score', 0),
                            missing_elements=json.dumps(data.get('missing_elements', [])),
                            raw_json_response=data
                        )
                    except json.JSONDecodeError:
                        pass # Handle invalid JSON gracefully
                
                # 3. Link to Application
                application.cover_letter_text = text_content
                application.cover_letter_document = user_doc
                # Also save the file to the application's own field for redundancy/legacy support
                application.cover_letter.save(filename, ContentFile(doc_content), save=False)
            
            elif uploaded_file:
                 # Handle Manual Upload
                 application.cover_letter = uploaded_file
                 
                 # Create a UserDocument for consistency (without extract/analysis for now)
                 doc_type, _ = DocumentType.objects.get_or_create(name='Cover Letter')
                 user_doc = UserDocument.objects.create(
                    user=request.user,
                    document_type=doc_type,
                    file=uploaded_file
                 )
                 application.cover_letter_document = user_doc

            application.save()
            
            # Send Email
            success, message = EmailService.send_application_email(
                user=request.user,
                job=job,
                cover_letter_file=application.cover_letter,
                cv_file_path=application.cv_used.file.path if application.cv_used else None
            )
            
            if success:
                if "sent to your email" in message.lower() or "forwarded to your email" in message.lower():
                    messages.info(request, f"📧 {message}")
                else:
                    messages.success(request, f"✅ Application sent successfully! {message}")
            else:
                messages.warning(request, f"Application logged, but email failed: {message}")
                
            return redirect('job_detail', pk=pk)
    else:
        form = ApplicationForm(user=request.user)
        
        # Check subscription status for GET request
        has_active_subscription = False
        try:
            if hasattr(request.user, 'subscription'):
                subscription = request.user.subscription
                from django.utils import timezone
                # Check if subscription is active and not expired
                if subscription.is_active:
                    if subscription.expiry_date:
                        has_active_subscription = subscription.expiry_date > timezone.now()
                    else:
                        # If no expiry date, consider it active if is_active is True
                        has_active_subscription = True
        except Exception:
            pass
        
    return render(request, 'jobs/email_application.html', {
        'form': form, 
        'job': job, 
        'has_applied': has_applied,
        'has_active_subscription': has_active_subscription
    })

from django.contrib.auth import login

def public_job_application(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    
    if request.method == 'POST':
        form = PublicApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            full_name = form.cleaned_data['full_name']
            phone = form.cleaned_data['phone']
            cv_file = form.cleaned_data['cv_file']
            cl_text = form.cleaned_data.get('cover_letter_text')
            cl_file = form.cleaned_data.get('cover_letter_file')
            
            User = get_user_model()
            user = User.objects.filter(email=email).first()
            
            is_new_user = False
            if not user:
                # Create user with phone number as password
                user = User.objects.create_user(email=email, password=phone, role='Job Seeker')
                is_new_user = True
            
            # Create/Update Profile
            profile, created = PersonalProfile.objects.get_or_create(user=user)
            if not profile.full_name:
                profile.full_name = full_name
            if not profile.phone_primary:
                profile.phone_primary = phone
            profile.save()
            
            # --- CV handling ---
            cv_doc_type, _ = DocumentType.objects.get_or_create(name='CV')
            
            # Extract text from CV for analysis
            cv_text = DocumentGenerator.extract_text_from_file(cv_file)
            
            cv_doc = UserDocument.objects.create(
                user=user,
                document_type=cv_doc_type,
                file=cv_file,
                extracted_content=cv_text
            )
            
            # Trigger AI Analysis for CV if text exists
            if cv_text:
                cv_analysis_result = AIService.analyze_cv(cv_text)
                if cv_analysis_result:
                    try:
                        from users.models import CVAnalysis
                        CVAnalysis.objects.create(
                            user_document=cv_doc,
                            total_score=cv_analysis_result.get('total_score', 0),
                            professionalism_score=cv_analysis_result.get('professionalism_score', 0),
                            relevance_score=cv_analysis_result.get('relevance_score', 0),
                            experience_score=cv_analysis_result.get('experience_score', 0),
                            education_score=cv_analysis_result.get('education_score', 0),
                            missing_sections=json.dumps(cv_analysis_result.get('missing_sections', [])),
                            improvement_suggestions=json.dumps(cv_analysis_result.get('improvement_suggestions', [])),
                            raw_json_response=cv_analysis_result
                        )
                    except Exception as e:
                        print(f"Failed to save CV Analysis: {e}")

            # --- Application Creation ---
            application = Application.objects.create(
                user=user,
                job=job,
                status='Under Review',
                cv_used=cv_doc
            )
            
            # --- Cover Letter Handling ---
            cl_doc_type, _ = DocumentType.objects.get_or_create(name='Cover Letter')
            cl_doc = None
            cl_analysis_text = ""
            
            if cl_text:
                application.cover_letter_text = cl_text
                cl_analysis_text = cl_text
                
                cl_doc = UserDocument.objects.create(
                    user=user,
                    document_type=cl_doc_type,
                    extracted_content=cl_text
                )
                # Save generated file
                filename = f"public_cl_{user.id}_{job.id}.pdf"
                content = DocumentGenerator.get_document_content(cl_text, 'pdf')
                cl_doc.file.save(filename, ContentFile(content))
                
                application.cover_letter_document = cl_doc
                application.cover_letter = cl_doc.file 
                application.save()
                
            elif cl_file:
                application.cover_letter = cl_file
                cl_analysis_text = DocumentGenerator.extract_text_from_file(cl_file)
                
                cl_doc = UserDocument.objects.create(
                    user=user,
                    document_type=cl_doc_type,
                    file=cl_file,
                    extracted_content=cl_analysis_text
                )
                application.cover_letter_document = cl_doc
                application.save()
                
            # Trigger AI Analysis for Cover Letter
            if cl_analysis_text and cl_doc:
                cl_analysis_result = AIService.analyze_cover_letter(cl_analysis_text)
                if cl_analysis_result:
                    try:
                        CoverLetterAnalysis.objects.create(
                            user_document=cl_doc,
                            total_score=cl_analysis_result.get('total_score', 0),
                            professionalism_score=cl_analysis_result.get('professionalism_score', 0),
                            content_score=cl_analysis_result.get('content_score', 0),
                            tone_score=cl_analysis_result.get('tone_score', 0),
                            impact_score=cl_analysis_result.get('impact_score', 0),
                            missing_elements=json.dumps(cl_analysis_result.get('missing_elements', [])),
                            raw_json_response=cl_analysis_result
                        )
                    except Exception as e:
                        print(f"Failed to save CL Analysis: {e}")

            # --- Final Redirection Logic ---
            if is_new_user:
                # Login the user and redirect to applications
                login(request, user, backend='django.contrib.auth.backends.ModelBackend') # Force login
                messages.success(request, f"Application submitted! Account created. Your password is your phone number: {phone}")
                return redirect('application_list')
            else:
                # Redirect to login with message
                # We can't auto-login existing user for security without password
                messages.success(request, "Application submitted successfully! Please log in to view its status.")
                return redirect('account_login')

    else:
        form = PublicApplicationForm()
        
    return render(request, 'jobs/public_application.html', {'form': form, 'job': job})

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
    # Optimized query to fetch user, profile, cv, and cover letter analysis
    applications = job.applications.select_related(
        'user', 
        'user__profile', 
        'cv_used', 
        'cover_letter_document',
        'cover_letter_document__cl_analysis'
    )
    
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    cv_min = request.GET.get('cv_min', '')
    cl_min = request.GET.get('cl_min', '')
    
    if search_query:
        applications = applications.filter(
            Q(user__email__icontains=search_query) |
            Q(user__profile__full_name__icontains=search_query)
        )
    
    if status_filter:
        applications = applications.filter(status=status_filter)

    # Score Filtering
    if cv_min:
        try:
            cv_min_val = int(cv_min)
            applications = applications.filter(cv_used__ai_score__gte=cv_min_val)
        except (ValueError, TypeError):
            pass

    if cl_min:
        try:
            cl_min_val = int(cl_min)
            applications = applications.filter(cover_letter_document__cl_analysis__total_score__gte=cl_min_val)
        except (ValueError, TypeError):
            pass

    applications = applications.order_by(F('cv_used__ai_score').desc(nulls_last=True), '-applied_at')
    
    # AI Score Metrics
    avg_ai_score = all_applications.aggregate(avg=Avg('cv_used__ai_score'))['avg'] or 0
    
    # Cover Letter Score Metrics
    # We need to compute this manually or via simpler aggregation if possible
    # Note: 'cover_letter_document__cl_analysis__total_score' might span tables, so using aggregate with valid relation traversal
    avg_cl_score = all_applications.filter(cover_letter_document__cl_analysis__isnull=False).aggregate(
        avg=Avg('cover_letter_document__cl_analysis__total_score')
    )['avg'] or 0
    
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
        'avg_cl_score': round(avg_cl_score, 1),
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'cv_min': cv_min,
        'cl_min': cl_min,
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

@login_required
def add_jobs_ai(request):
    """
    AI-powered job listing creation page.
    GET: Shows textarea form
    POST with action='process': Processes text and shows preview
    POST with action='confirm': Creates the job listing and company
    """
    # Check if user has permission (Admin or Employer)
    if not (request.user.role == 'Admin' or request.user.role == 'Employer'):
        messages.error(request, "You do not have permission to post jobs.")
        return redirect('dashboard')
    
    # If Employer, check if they have an assigned company (but allow AI creation for new companies)
    # We'll handle company assignment later
    
    if request.method == 'POST':
        action = request.POST.get('action', 'process')
        
        if action == 'process':
            # Process the text input
            text = request.POST.get('text', '').strip()
            if not text:
                messages.error(request, "Please provide job listing text.")
                return render(request, 'jobs/add_jobs_ai.html', {
                    'text': text
                })
            
            # Get all existing companies for fuzzy matching
            existing_companies = list(Company.objects.values('id', 'name'))
            
            # Get all job categories
            categories_data = list(JobCategory.objects.values('name', 'keywords'))
            
            # Call AI service to parse the text
            parsed_data = AIService.create_job_listing(text, existing_companies, categories_data)
            
            if not parsed_data:
                messages.error(request, "Failed to parse job listing. Please try again or check your OpenAI API key.")
                return render(request, 'jobs/add_jobs_ai.html', {
                    'text': text
                })
            
            # Store parsed data in session for confirmation step
            request.session['ai_job_parsed_data'] = parsed_data
            request.session['ai_job_original_text'] = text
            
            # Prepare context for preview
            company_data = parsed_data.get('company', {})
            job_data = parsed_data.get('job_listing', {})
            requirements = parsed_data.get('requirements', [])
            similar_companies = parsed_data.get('similar_companies', [])
            
            # Get full company objects for similar companies with similarity scores
            similar_company_list = []
            if similar_companies:
                company_ids = [c['id'] for c in similar_companies]
                company_objects = Company.objects.filter(id__in=company_ids)
                company_dict = {c.id: c for c in company_objects}
                # Create list with company objects and similarity scores
                for similar_comp in similar_companies:
                    comp_id = similar_comp['id']
                    if comp_id in company_dict:
                        similar_company_list.append({
                            'company': company_dict[comp_id],
                            'similarity': round(similar_comp['similarity'] * 100, 1)  # Convert to percentage
                        })
            
            # Get category object if category name was provided
            category_obj = None
            if job_data.get('category'):
                try:
                    category_obj = JobCategory.objects.get(name=job_data['category'])
                except JobCategory.DoesNotExist:
                    # Try to find by similar name
                    categories = JobCategory.objects.all()
                    for cat in categories:
                        if job_data['category'].lower() in cat.name.lower() or cat.name.lower() in job_data['category'].lower():
                            category_obj = cat
                            break
            
            context = {
                'company_data': company_data,
                'job_data': job_data,
                'requirements': requirements,
                'similar_companies': similar_company_list,
                'category': category_obj,
                'preview_mode': True,
            }
            
            return render(request, 'jobs/add_jobs_ai_preview.html', context)
        
        elif action == 'confirm':
            # Create the job listing and company
            parsed_data = request.session.get('ai_job_parsed_data')
            if not parsed_data:
                messages.error(request, "Session expired. Please try again.")
                return redirect('add_jobs_ai')
            
            company_data = parsed_data.get('company', {})
            job_data = parsed_data.get('job_listing', {})
            requirements = parsed_data.get('requirements', [])
            
            # Determine company to use
            selected_company_id = request.POST.get('selected_company_id')
            create_new_company = request.POST.get('create_new_company') == 'yes'
            
            try:
                with transaction.atomic():
                    # Handle company
                    if create_new_company or not selected_company_id:
                        # Create new company
                        company, created = Company.objects.get_or_create(
                            name=company_data.get('name', ''),
                            defaults={
                                'description': company_data.get('description', ''),
                                'website': company_data.get('website', ''),
                                'location': company_data.get('location', ''),
                                'primary_phone': company_data.get('primary_phone', ''),
                                'secondary_phone': company_data.get('secondary_phone', ''),
                                'primary_email': company_data.get('primary_email', ''),
                                'secondary_email': company_data.get('secondary_email', ''),
                                'founded_in': company_data.get('founded_in'),
                            }
                        )
                        if not created:
                            # Update existing company if name matches exactly
                            company.description = company_data.get('description', company.description) or company.description
                            company.website = company_data.get('website', company.website) or company.website
                            company.location = company_data.get('location', company.location) or company.location
                            company.save()
                    else:
                        # Use existing company
                        company = get_object_or_404(Company, id=selected_company_id)
                    
                    # Get or create category
                    category_name = job_data.get('category', '')
                    if category_name:
                        category, _ = JobCategory.objects.get_or_create(name=category_name)
                    else:
                        messages.warning(request, "No category specified. Using default.")
                        category = JobCategory.objects.first()
                        if not category:
                            messages.error(request, "No job categories exist. Please create categories first.")
                            return redirect('add_jobs_ai')
                    
                    # Create job listing
                    expiry_date = None
                    if job_data.get('expiry_date'):
                        try:
                            from datetime import datetime
                            expiry_date = datetime.strptime(job_data['expiry_date'], '%Y-%m-%d').date()
                        except:
                            pass
                    
                    job = JobListing.objects.create(
                        title=job_data.get('title', ''),
                        category=category,
                        company=company.name,
                        company_profile=company,
                        description=job_data.get('description', ''),
                        location=job_data.get('location', ''),
                        url=job_data.get('url') or job_data.get('application_url') or 'https://example.com',
                        terms=job_data.get('terms', 'Full Time'),
                        education_level_required=job_data.get('education_level_required', 'None'),
                        experience_required_years=job_data.get('experience_required_years'),
                        application_method=job_data.get('application_method', 'website'),
                        employer_email=job_data.get('employer_email', ''),
                        application_url=job_data.get('application_url', ''),
                        application_instructions=job_data.get('application_instructions', ''),
                        expiry_date=expiry_date,
                    )
                    
                    # Create requirements
                    for req in requirements:
                        JobRequirement.objects.create(
                            job=job,
                            description=req.get('description', ''),
                            is_mandatory=req.get('is_mandatory', True)
                        )
                    
                    # Clear session data
                    request.session.pop('ai_job_parsed_data', None)
                    request.session.pop('ai_job_original_text', None)
                    
                    messages.success(request, f"Job listing '{job.title}' created successfully!")
                    return redirect('job_detail', pk=job.pk)
                    
            except Exception as e:
                messages.error(request, f"Error creating job listing: {str(e)}")
                return redirect('add_jobs_ai')
    
    # GET request - show form
    original_text = request.session.get('ai_job_original_text', '')
    return render(request, 'jobs/add_jobs_ai.html', {
        'text': original_text
    })
