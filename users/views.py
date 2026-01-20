from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import (
    SignupForm, LoginForm, ProfileUpdateForm, WorkExperienceForm, 
    EducationForm, MySkillForm, UserDocumentForm, JobPreferenceForm
)
from django.views.decorators.csrf import csrf_exempt
import json
from .mpesa_service import MpesaService
from .models import (
    PersonalProfile, MyUser, WorkExperience, Education, MySkill, 
    UserDocument, CVAnalysis, Subscription, MpesaTransaction,
    NotificationPreference, UserNotification
)
from home.services import TextExtractor
from home.ai_service import AIService
from jobs.models import JobCategory

from django.contrib.auth.backends import ModelBackend

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()

            # 🔑 REQUIRED when multiple auth backends exist
            user.backend = 'django.contrib.auth.backends.ModelBackend'

            login(request, user)

            messages.success(request, "Registration successful.")
            return redirect('dashboard')
        messages.error(request, "Unsuccessful registration. Invalid information.")
    else:
        form = SignupForm()

    return render(request, 'users/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {email}.")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('index')

@login_required
def profile_detail(request):
    profile = getattr(request.user, 'profile', None)
    return render(request, 'users/profile_detail.html', {'profile': profile})

@login_required
def profile_edit(request):
    try:
        profile = request.user.profile
    except PersonalProfile.DoesNotExist:
        profile = PersonalProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_detail')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'users/profile_edit.html', {'form': form, 'profile': profile})

@login_required
def job_preference_edit(request):
    try:
        profile = request.user.profile
    except PersonalProfile.DoesNotExist:
        profile = PersonalProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = JobPreferenceForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Job preferences updated successfully.")
            return redirect('profile_detail')
    else:
        form = JobPreferenceForm(instance=profile)
    
    return render(request, 'users/job_preference_edit.html', {'form': form, 'profile': profile})

@login_required
def experience_list(request):
    experiences = request.user.work_experiences.all().order_by('-start_date')
    return render(request, 'users/experience_list.html', {'experiences': experiences})

@login_required
def experience_add(request):
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.user = request.user
            experience.save()
            messages.success(request, "Work experience added successfully.")
            return redirect('experience_list')
    else:
        form = WorkExperienceForm()
    return render(request, 'users/experience_form.html', {'form': form, 'title': 'Add Work Experience'})

@login_required
def experience_edit(request, pk):
    experience = request.user.work_experiences.get(pk=pk)
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST, instance=experience)
        if form.is_valid():
            form.save()
            messages.success(request, "Work experience updated successfully.")
            return redirect('experience_list')
    else:
        form = WorkExperienceForm(instance=experience)
    return render(request, 'users/experience_form.html', {'form': form, 'title': 'Edit Work Experience', 'experience': experience})

@login_required
def experience_delete(request, pk):
    experience = request.user.work_experiences.get(pk=pk)
    if request.method == 'POST':
        experience.delete()
        messages.success(request, "Work experience deleted.")
        return redirect('experience_list')
    return render(request, 'users/experience_confirm_delete.html', {'experience': experience})

@login_required
def education_list(request):
    educations = request.user.educations.all().order_by('-start_date')
    return render(request, 'users/education_list.html', {'educations': educations})

@login_required
def education_add(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            education = form.save(commit=False)
            education.user = request.user
            education.save()
            messages.success(request, "Education entry added successfully.")
            return redirect('education_list')
    else:
        form = EducationForm()
    return render(request, 'users/education_form.html', {'form': form, 'title': 'Add Education'})

@login_required
def education_edit(request, pk):
    education = request.user.educations.get(pk=pk)
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=education)
        if form.is_valid():
            form.save()
            messages.success(request, "Education entry updated successfully.")
            return redirect('education_list')
    else:
        form = EducationForm(instance=education)
    return render(request, 'users/education_form.html', {'form': form, 'title': 'Edit Education', 'education': education})

@login_required
def education_delete(request, pk):
    education = request.user.educations.get(pk=pk)
    if request.method == 'POST':
        education.delete()
        messages.success(request, "Education entry deleted.")
        return redirect('education_list')
    return render(request, 'users/education_confirm_delete.html', {'education': education})

@login_required
def skill_list(request):
    skills = request.user.skills.all()
    return render(request, 'users/skill_list.html', {'skills': skills})

@login_required
def skill_add(request):
    if request.method == 'POST':
        form = MySkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.user = request.user
            skill.save()
            messages.success(request, "Skill added successfully.")
            return redirect('skill_list')
    else:
        form = MySkillForm()
    return render(request, 'users/skill_form.html', {'form': form, 'title': 'Add Skill'})

@login_required
def skill_edit(request, pk):
    skill = request.user.skills.get(pk=pk)
    if request.method == 'POST':
        form = MySkillForm(request.POST, instance=skill)
        if form.is_valid():
            form.save()
            messages.success(request, "Skill updated successfully.")
            return redirect('skill_list')
    else:
        form = MySkillForm(instance=skill)
    return render(request, 'users/skill_form.html', {'form': form, 'title': 'Edit Skill', 'skill': skill})

@login_required
def skill_delete(request, pk):
    skill = request.user.skills.get(pk=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request, "Skill removed.")
        return redirect('skill_list')
    return render(request, 'users/skill_confirm_delete.html', {'skill': skill})

@login_required
def document_list(request):
    documents = request.user.documents.all()
    return render(request, 'users/document_list.html', {'documents': documents})

@login_required
def document_add(request):
    if request.method == 'POST':
        form = UserDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc_type = form.cleaned_data.get('document_type')
            
            # Enforce one CV per user
            if doc_type and doc_type.name == 'CV':
                request.user.documents.filter(document_type__name='CV').delete()
                
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save() # Save first to get the file path
            
            # Extract text
            try:
                extracted_text = TextExtractor.extract_text(doc.file.path)
                doc.extracted_content = extracted_text
                
                # AI Analysis for CVs
                if doc.document_type.name == 'CV':
                    # Get categories to suggest from
                    categories = JobCategory.objects.all().values('name', 'keywords')
                    categories_data = list(categories)
                    
                    analysis_data = AIService.analyze_cv(extracted_text, categories_data)
                    if analysis_data:
                        # Save total score to UserDocument
                        doc.ai_score = analysis_data.get('total_score', 0)
                        doc.save()
                        
                        # Create CVAnalysis record
                        CVAnalysis.objects.create(
                            user_document=doc,
                            total_score=analysis_data.get('total_score', 0),
                            professionalism_score=analysis_data.get('professionalism_score', 0),
                            relevance_score=analysis_data.get('relevance_score', 0),
                            experience_score=analysis_data.get('experience_score', 0),
                            education_score=analysis_data.get('education_score', 0),
                            missing_sections="\n".join(analysis_data.get('missing_sections', [])),
                            improvement_suggestions="\n".join(analysis_data.get('improvement_suggestions', [])),
                            raw_json_response=analysis_data
                        )
                        
                        # Automate Job Preferences
                        suggested_category_names = analysis_data.get('suggested_categories', [])
                        if suggested_category_names:
                            matched_categories = JobCategory.objects.filter(name__in=suggested_category_names)
                            if matched_categories.exists():
                                profile, created = PersonalProfile.objects.get_or_create(user=request.user)
                                profile.preferred_categories.add(*matched_categories)
                                messages.info(request, f"Updated your job preferences based on your CV: {', '.join([c.name for c in matched_categories])}")

                        messages.success(request, f"CV uploaded and analyzed! Score: {doc.ai_score}/100")
                    else:
                        messages.warning(request, "CV uploaded and text extracted, but detailed AI analysis failed.")
                else:
                    messages.success(request, "Document uploaded and text extracted successfully.")
                
                doc.save()
            except Exception as e:
                messages.warning(request, f"Document uploaded, but processing failed: {str(e)}")
            
            return redirect('document_detail', pk=doc.pk)
    else:
        form = UserDocumentForm()
    return render(request, 'users/document_form.html', {'form': form})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(UserDocument, pk=pk, user=request.user)
    return render(request, 'users/document_detail.html', {'document': document})

@login_required
def document_delete(request, pk):
    doc = request.user.documents.get(pk=pk)
    if request.method == 'POST':
        doc.delete()
        messages.success(request, "Document deleted.")
        return redirect('document_list')
    return render(request, 'users/document_confirm_delete.html', {'document': doc})

@login_required
def subscription_page(request):
    subscription = getattr(request.user, 'subscription', None)
    pricing = {
        'Basic': 200,
        'Pro': 500,
        'Ultimate': 1500
    }
    
    if request.method == 'POST':
        tier = request.POST.get('tier')
        phone_number = request.POST.get('phone_number')
        
        if tier in pricing:
            amount = pricing[tier]
            if not phone_number:
                messages.error(request, "Please provide a valid phone number for M-Pesa payment.")
            else:
                success, message = MpesaService.initiate_stk_push(request.user, phone_number, amount, tier)
                if success:
                    messages.success(request, message)
                else:
                    messages.error(request, message)
            return redirect('subscription_page')
            
    return render(request, 'users/subscription.html', {
        'subscription': subscription,
        'tiers': Subscription.TIER_CHOICES
    })

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        merchant_request_id = stk_callback.get('MerchantRequestID')
        result_desc = stk_callback.get('ResultDesc')
        
        try:
            transaction = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
            transaction.result_code = result_code
            transaction.result_description = result_desc
            
            if result_code == 0:
                # Payment Successful
                transaction.status = 'Success'
                # Extract details from CallbackMetadata
                items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        transaction.mpesa_receipt_number = item.get('Value')
                
                # Update/Create Subscription
                from django.utils import timezone
                from datetime import timedelta
                
                sub, created = Subscription.objects.get_or_create(user=transaction.user)
                sub.tier = transaction.subscription_tier
                sub.is_active = True
                sub.start_date = timezone.now()
                sub.expiry_date = timezone.now() + timedelta(days=90) # 3 months
                sub.save()
            else:
                transaction.status = 'Failed'
                
            transaction.save()
            return render(request, 'users/callback_success.html', status=200) # Simple response for Safaricom
        except MpesaTransaction.DoesNotExist:
            return render(request, 'users/callback_error.html', status=404)
            
    return render(request, 'users/callback_error.html', status=405)

@login_required
def payment_history(request):
    transactions = request.user.mpesa_transactions.all().order_by('-created_at')
@login_required
def update_role(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        valid_roles = [c[0] for c in MyUser.ROLE_CHOICES if c[0] not in ['Admin', 'None']]
        
        if role in valid_roles:
            request.user.role = role
            request.user.save()
            messages.success(request, f"Role updated to {role}.")
            return redirect(request.META.get('HTTP_REFERER', 'index'))
        else:
            messages.error(request, "Invalid role selected.")
            
    return redirect('index')

@login_required
def notifications_list(request):
    notifications = request.user.notifications.all()
    return render(request, 'users/notifications.html', {'notifications': notifications})

@login_required
@csrf_exempt # Using CSRF token in fetch, but exempt for simplicity if needed, better to handle in JS
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(UserNotification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
@csrf_exempt
def toggle_notification_preference(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pref_type = data.get('type') # 'email' or 'whatsapp'
            enabled = data.get('enabled', True)
            
            prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
            
            if pref_type == 'email':
                prefs.email_enabled = enabled
            elif pref_type == 'whatsapp':
                prefs.whatsapp_enabled = enabled
                
            prefs.save()
            return JsonResponse({'status': 'success', 'pref': pref_type, 'enabled': enabled})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
@login_required
def get_latest_notifications(request):
    notifications = request.user.notifications.all()[:5]
    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'job_url': reverse('job_detail', args=[n.job.id]) if n.job else '#'
        })
    return JsonResponse({'notifications': data, 'unread_count': request.user.notifications.filter(is_read=False).count()})
