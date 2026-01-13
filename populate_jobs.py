import os
import django
import datetime
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIJobs.settings')
django.setup()

from jobs.models import JobCategory, JobListing, JobRequirement

def populate():
    print("Populating database with realistic job listings...")

    # Define Categories
    categories_data = [
        "Software Engineering", "Data Science", "Product Management", 
        "Design", "Digital Marketing", "Sales", "Finance", "Customer Success", "Operations"
    ]
    
    categories = {}
    for cat_name in categories_data:
        cat, created = JobCategory.objects.get_or_create(name=cat_name)
        categories[cat_name] = cat
        if created:
            print(f"Created category: {cat_name}")

    # Define Job Listings
    jobs_data = [
        {
            "title": "Senior Frontend Developer",
            "company": "TechFlow Systems",
            "category": "Software Engineering",
            "location": "Remote / New York, NY",
            "description": "We are seeking a Senior Frontend Developer with expertise in React and modern CSS to lead our dashboard experience. You will work closely with designers and backend engineers to build high-performance user interfaces.",
            "url": "https://techflow.io/careers/senior-frontend",
            "education_level_required": "University",
            "experience_required_years": 5,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=30),
            "requirements": [
                "Expert knowledge of React, Redux, and TypeScript",
                "Strong CSS skills (Sass, Tailwind, or CSS-in-JS)",
                "Experience with testing frameworks like Jest or Playwright",
                "Proven track record of delivering scalable web applications"
            ]
        },
        {
            "title": "Machine Learning Engineer",
            "company": "AI Labs Global",
            "category": "Data Science",
            "location": "San Francisco, CA",
            "description": "Join our R&D team to build and deploy large-scale NLP models. You will be responsible for the end-to-end lifecycle of ML models, from data preparation to production monitoring.",
            "url": "https://ailabs.global/jobs/ml-engineer",
            "education_level_required": "University",
            "experience_required_years": 3,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=45),
            "requirements": [
                "Proficiency in Python and PyTorch/TensorFlow",
                "Experience with LLMs and Transformers",
                "Solid understanding of software engineering best practices",
                "Master's or PhD in CS or related field preferred"
            ]
        },
        {
            "title": "Technical Product Manager",
            "company": "RetailGiant",
            "category": "Product Management",
            "location": "Seattle, WA",
            "description": "Drive the roadmap for our next-generation e-commerce platform. You will translate complex business needs into technical requirements and lead cross-functional delivery teams.",
            "url": "https://retailgiant.com/careers/tpm-seattle",
            "education_level_required": "University",
            "experience_required_years": 4,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=20),
            "requirements": [
                "4+ years of product management experience",
                "Background in computer science or engineering",
                "Excellent communication and stakeholder management skills",
                "Experience with Agile/Scrum methodologies"
            ]
        },
        {
            "title": "Lead UI/UX Designer",
            "company": "CreativeHub",
            "category": "Design",
            "location": "Austin, TX (On-site)",
            "description": "Help us redefine the creative tools for the next generation. You will lead the design strategy and mentor junior designers across branding and product interface projects.",
            "url": "https://creativehub.design/jobs/lead-designer",
            "education_level_required": "College",
            "experience_required_years": 6,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=60),
            "requirements": [
                "Professional portfolio demonstrating product design expertise",
                "Mastery of Figma, Adobe Creative Cloud, and prototyping tools",
                "Strategic thinker with a user-centric approach",
                "Leadership experience in a creative team environment"
            ]
        },
        {
            "title": "Backend Software Engineer (Go)",
            "company": "RapidPay",
            "category": "Software Engineering",
            "location": "London, UK / Remote",
            "description": "Build high-throughput payment processing systems using Go and Kubernetes. Our platforms handle millions of transactions daily with millisecond latency requirements.",
            "url": "https://rapidpay.dev/careers/go-backend",
            "education_level_required": "University",
            "experience_required_years": 3,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=25),
            "requirements": [
                "Proficiency in Go or C++",
                "Experience with distributed systems and microservices",
                "Knowledge of PostgreSQL and Redis",
                "Familiarity with cloud-native technologies (Docker, K8s)"
            ]
        },
        {
            "title": "Customer Success Manager",
            "company": "SaaSly",
            "category": "Customer Success",
            "location": "Boston, MA",
            "description": "Help our Enterprise clients maximize their ROI with our platform. You will be the primary point of contact for key accounts, ensuring long-term satisfaction and adoption.",
            "url": "https://saasly.co/jobs/csm-boston",
            "education_level_required": "University",
            "experience_required_years": 2,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=35),
            "requirements": [
                "Experience in B2B Customer Success or Account Management",
                "Exceptional empathy and problem-solving abilities",
                "Ability to learn technical products quickly",
                "Data-driven approach to customer health monitoring"
            ]
        },
        {
            "title": "Data Analyst (Marketing)",
            "company": "TrendSetters",
            "category": "Digital Marketing",
            "location": "Los Angeles, CA",
            "description": "Analyze marketing campaign performance and provide actionable insights to our growth team. You will build dashboards and run A/B test analysis to drive data-driven culture.",
            "url": "https://trendsetters.la/jobs/marketing-analyst",
            "education_level_required": "University",
            "experience_required_years": 2,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=40),
            "requirements": [
                "Strong SQL skills and proficiency in Tableau/Mode/Looker",
                "Understanding of digital marketing metrics (CAC, LTV, ROAS)",
                "Experience with Python or R for data manipulation",
                "Clear communication of statistical findings to non-technical audiences"
            ]
        },
        {
            "title": "DevOps / Infrastructure Engineer",
            "company": "CloudScale",
            "category": "Operations",
            "location": "Denver, CO / Remote",
            "description": "Own our cloud infrastructure and CI/CD pipelines. We are transitioning to a multi-cloud strategy and need an expert to help automate our scaling and security protocols.",
            "url": "https://cloudscale.net/careers/devops",
            "education_level_required": "None",
            "experience_required_years": 4,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=50),
            "requirements": [
                "Deep experience with AWS, Azure, or GCP",
                "Infrastructure as Code mastery (Terraform or CloudFormation)",
                "Strong Linux sysadmin skills",
                "Experience with incident response and monitoring (Datadog/Prometheus)"
            ]
        },
        {
            "title": "Enterprise Sales Executive",
            "company": "SecureSphere",
            "category": "Sales",
            "location": "Chicago, IL",
            "description": "Sell our cutting-edge cybersecurity solutions to Fortune 500 companies. You will lead the full sales cycle from prospecting to closing high-value contracts.",
            "url": "https://securesphere.com/jobs/enterprise-sales",
            "education_level_required": "University",
            "experience_required_years": 7,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=15),
            "requirements": [
                "Proven track record of exceeding sales quotas in SaaS",
                "Deep network within the IT security space",
                "Experience managing long and complex sales cycles",
                "Consultative sales approach"
            ]
        },
        {
            "title": "Financial Controller",
            "company": "HealthFirst",
            "category": "Finance",
            "location": "Atlanta, GA",
            "description": "Lead our finance department through a high-growth phase. You will oversee all accounting operations, financial reporting, and compliance activities.",
            "url": "https://healthfirst.com/jobs/financial-controller",
            "education_level_required": "University",
            "experience_required_years": 8,
            "expiry_date": timezone.now().date() + datetime.timedelta(days=28),
            "requirements": [
                "CPA certification required",
                "8+ years of accounting and finance leadership",
                "Experience with ERP implementation (NetSuite/Oracle)",
                "Strong leadership and team development skills"
            ]
        }
    ]

    for job_item in jobs_data:
        requirements = job_item.pop('requirements')
        cat_name = job_item.pop('category')
        job_item['category'] = categories[cat_name]
        
        job, created = JobListing.objects.get_or_create(
            title=job_item['title'],
            company=job_item['company'],
            defaults=job_item
        )
        
        if created:
            print(f"Created job: {job.title} at {job.company}")
            for req_desc in requirements:
                JobRequirement.objects.create(
                    job=job,
                    description=req_desc,
                    is_mandatory=True
                )
    
    print("\nDatabase population complete!")

if __name__ == '__main__':
    populate()
