import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIJobs.settings')
django.setup()
from jobs.models import JobListing, JobRequirement

try:
    job = JobListing.objects.get(id=1)
    job.title = "Senior Software Engineer (Python/Django)"
    job.company = "Nexus AI Technologies"
    job.location = "Nairobi, Kenya (Hybrid)"
    job.experience_required_years = 4
    job.description = """Nexus AI Technologies is a leading innovator in the African tech ecosystem, dedicated to building cutting-edge solutions for the logistics and fintech sectors. We are looking for a highly skilled Senior Software Engineer with a deep passion for Python and modern web technologies to join our core engineering team.

As a Senior Engineer, you will play a pivotal role in designing and implementing scalable backend systems, mentoring junior developers, and contributing to our architectural decisions. You will work closely with product managers and cross-functional teams to deliver high-quality software that impacts thousands of users across the continent.

Responsibilities:
- Architect and develop robust, scalable backend services using Python and Django.
- Design and maintain efficient database schemas and optimize query performance.
- Build responsive and interactive user interfaces with React.
- Implement security best practices and ensure data protection across all platforms.
- Mentor junior and mid-level developers through code reviews and technical guidance.
- Collaborate with DevOps to streamline our CI/CD pipelines and cloud deployments.
"""
    job.save()

    # Update requirements
    JobRequirement.objects.filter(job=job).delete()

    mandatory_reqs = [
        "4+ years of professional experience in backend development using Python.",
        "Expert-level knowledge of the Django web framework.",
        "Strong proficiency in modern JavaScript, CSS, and React for frontend integration.",
        "Experience with RESTful API design and implementation.",
        "Solid understanding of relational databases (PostgreSQL/MySQL)."
    ]

    optional_reqs = [
        "Experience with AWS EC2 deployment and infrastructure management.",
        "Knowledge of containerization technologies like Docker and Kubernetes."
    ]

    for req in mandatory_reqs:
        JobRequirement.objects.create(job=job, description=req, is_mandatory=True)

    for req in optional_reqs:
        JobRequirement.objects.create(job=job, description=req, is_mandatory=False)

    print("Job 1 updated successfully.")
except JobListing.DoesNotExist:
    print("Error: Job with ID 1 does not exist.")
except Exception as e:
    print(f"Error: {e}")
