import os
import django
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIJobs.settings')
django.setup()

from jobs.models import JobListing, JobCategory, JobRequirement

def create_test_jobs():
    # 1. Ensure categories exist
    categories_names = ['Technology', 'Healthcare', 'Finance', 'Education', 'Marketing']
    categories = {}
    for name in categories_names:
        cat, _ = JobCategory.objects.get_or_create(name=name)
        categories[name] = cat

    # 2. Define job data
    jobs_data = [
        {
            'title': 'Senior Python Developer',
            'category': categories['Technology'],
            'company': 'Techflow Solutions',
            'description': 'We are looking for a Senior Python Developer to join our backend team. You will be responsible for building scalable APIs and integrating AI models.',
            'location': 'Nairobi, Kenya',
            'url': 'https://techflow.example.com/jobs/1',
            'employer_email': 'annitah932@gmail.com',
            'education_level_required': 'University',
            'experience_required_years': 5,
            'requirements': ['Strong proficiency in Python and Django', 'Experience with PostgreSQL', 'Knowledge of AWS or GCP']
        },
        {
            'title': 'Registered Nurse',
            'category': categories['Healthcare'],
            'company': 'City General Hospital',
            'description': 'Seeking a compassionate Registered Nurse for our busy ER department. Must be able to work in shifts and handle high-pressure situations.',
            'location': 'Mombasa, Kenya',
            'url': 'https://cityhospital.example.com/jobs/nurse',
            'employer_email': 'annitah932@gmail.com',
            'education_level_required': 'University',
            'experience_required_years': 2,
            'requirements': ['Valid nursing license', 'Emergency room experience preferred', 'Strong communication skills']
        },
        {
            'title': 'Financial Analyst',
            'category': categories['Finance'],
            'company': 'Capital Edge Investments',
            'description': 'Join our investment team to analyze market trends and provide data-driven insights for our portfolio management.',
            'location': 'Nairobi, Kenya',
            'url': 'https://capedge.example.com/careers/analyst',
            'employer_email': 'annitah932@gmail.com',
            'education_level_required': 'University',
            'experience_required_years': 3,
            'requirements': ['Degree in Finance or Economics', 'Proficiency in Excel and modeling', 'CFA candidate preferred']
        },
        {
            'title': 'High School Mathematics Teacher',
            'category': categories['Education'],
            'company': 'Greenwood Academy',
            'description': 'We are looking for a dedicated Math Teacher for our senior classes. Help students master complex mathematical concepts and prepare for exams.',
            'location': 'Nakuru, Kenya',
            'url': 'https://greenwood.example.com/jobs/math',
            'employer_email': 'annitah932@gmail.com',
            'education_level_required': 'University',
            'experience_required_years': 2,
            'requirements': ['TSC Registration', 'Minimum of 2 years teaching experience', 'Experience with integrated technology in classroom']
        },
        {
            'title': 'Digital Marketing Specialist',
            'category': categories['Marketing'],
            'company': 'Vibrant Media Group',
            'description': 'Lead our digital marketing campaigns across SEO, SEM, and Social Media. Drive growth and engagement for our diverse client base.',
            'location': 'Nairobi, Kenya',
            'url': 'https://vibrant.example.com/join-us/marketing',
            'employer_email': 'annitah932@gmail.com',
            'education_level_required': 'College',
            'experience_required_years': 3,
            'requirements': ['Proven experience with Google Ads and Meta Ads', 'Strong understanding of SEO principles', 'Content creation and copy-writing skills']
        }
    ]

    # 3. Create jobs and requirements
    for data in jobs_data:
        requirements = data.pop('requirements')
        job = JobListing.objects.create(
            **data,
            expiry_date=datetime.date.today() + datetime.timedelta(days=30)
        )
        for req_desc in requirements:
            JobRequirement.objects.create(job=job, description=req_desc)
        print(f"Created Job: {job.title}")

if __name__ == "__main__":
    create_test_jobs()
