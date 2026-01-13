from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import JobListing, JobCategory

def job_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    jobs = JobListing.objects.all().order_by('-posted_at')
    
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
    
    context = {
        'jobs': jobs,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None,
    }
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    context = {
        'job': job,
    }
    return render(request, 'jobs/job_detail.html', context)
