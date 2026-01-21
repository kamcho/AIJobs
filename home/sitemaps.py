from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from jobs.models import JobListing, Company, JobCategory

class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'daily'

    def items(self):
        # Return list of URL names for static pages
        return ['index', 'job_list', 'privacy_policy']

    def location(self, item):
        return reverse(item)

class JobListingSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return JobListing.objects.filter(is_active=True).order_by('-posted_at')

    def location(self, obj):
        return reverse('job_detail', args=[obj.pk])

    def lastmod(self, obj):
        return obj.posted_at

class CompanySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Company.objects.all()

    def location(self, obj):
        return reverse('company_detail', args=[obj.pk])

    def lastmod(self, obj):
        return obj.created_at

class JobCategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return JobCategory.objects.all()

    def location(self, obj):
        # Categories are typically shown in job_list with filters, but we can point to job list
        return reverse('job_list')
