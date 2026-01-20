import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIJobs.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("EMAIL CONFIGURATION STATUS")
print("=" * 60)
print(f"✓ EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"✓ EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"✓ EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"✓ EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"✓ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"✓ EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'Not set'}")
print(f"✓ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print("=" * 60)

if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    print("✅ SMTP is ACTIVE - Emails will be sent via support@tscswap.com")
else:
    print("⚠️  Console backend is active - Emails will only be printed to console")
print("=" * 60)
