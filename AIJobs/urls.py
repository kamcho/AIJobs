"""
URL configuration for AIJobs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from users import views as users_views
from home.sitemaps import StaticViewSitemap, JobListingSitemap, CompanySitemap, JobCategorySitemap

sitemaps = {
    'static': StaticViewSitemap,
    'jobs': JobListingSitemap,
    'companies': CompanySitemap,
    'categories': JobCategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('auth/', include('users.urls')),
    path('mpesa/callback/', users_views.mpesa_callback, name='mpesa_callback'),
    path('accounts/', include('allauth.urls')),
    path('jobs/', include('jobs.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
