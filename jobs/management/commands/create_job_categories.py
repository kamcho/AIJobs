from django.core.management.base import BaseCommand

from jobs.models import JobCategory


class Command(BaseCommand):
    help = "Create default job categories for FindAJob.ai"

    JOB_CATEGORIES = {
        "Administration / Office Support": {
            "keywords": [
                "admin", "office assistant", "secretary", "clerical",
                "receptionist", "office support"
            ],
            "type": "white_collar"
        },
        "Agriculture / Agribusiness": {
            "keywords": [
                "agriculture", "agribusiness", "farm manager", "livestock",
                "horticulture", "agripreneur"
            ],
            "type": "mixed"
        },
        "Banking / Finance / Microfinance": {
            "keywords": [
                "banking", "credit officer", "loan officer",
                "microfinance", "relationship manager"
            ],
            "type": "white_collar"
        },
        "Construction / Built Environment": {
            "keywords": [
                "construction", "quantity surveyor", "site engineer",
                "foreman", "architect"
            ],
            "type": "mixed"
        },
        "Customer Service / Call Center": {
            "keywords": [
                "customer service", "call center", "contact center",
                "customer support"
            ],
            "type": "white_collar"
        },
        "Data / AI / Business Analysis": {
            "keywords": [
                "data analyst", "data scientist", "machine learning",
                "business analyst", "ai engineer"
            ],
            "type": "white_collar"
        },
        "Driving / Logistics / Fleet": {
            "keywords": [
                "driver", "chauffeur", "delivery rider",
                "logistics assistant", "fleet supervisor"
            ],
            "type": "blue_collar"
        },
        "Education / Teaching / Training": {
            "keywords": [
                "teacher", "lecturer", "tutor",
                "trainer", "education officer"
            ],
            "type": "white_collar"
        },
        "Engineering (Civil / Electrical / Mechanical)": {
            "keywords": [
                "civil engineer", "electrical engineer",
                "mechanical engineer", "technician"
            ],
            "type": "mixed"
        },
        "Finance / Accounting / Audit": {
            "keywords": [
                "accountant", "auditor", "finance officer",
                "bookkeeper", "cpa"
            ],
            "type": "white_collar"
        },
        "Graduate / Entry-Level": {
            "keywords": [
                "graduate trainee", "internship",
                "entry level", "fresh graduate"
            ],
            "type": "white_collar"
        },
        "Healthcare / Medical": {
            "keywords": [
                "doctor", "nurse", "clinical officer",
                "pharmacist", "medical officer"
            ],
            "type": "mixed"
        },
        "Hospitality / Hotel / Restaurant": {
            "keywords": [
                "chef", "waiter", "housekeeping",
                "hotel", "front office"
            ],
            "type": "blue_collar"
        },
        "Human Resources / Recruitment": {
            "keywords": [
                "hr officer", "human resources",
                "recruiter", "talent acquisition"
            ],
            "type": "white_collar"
        },
        "ICT / Software / Computer Science": {
            "keywords": [
                "software developer", "web developer",
                "system administrator", "it support"
            ],
            "type": "white_collar"
        },
        "Legal / Compliance": {
            "keywords": [
                "advocate", "legal officer",
                "compliance", "paralegal"
            ],
            "type": "white_collar"
        },
        "Logistics / Supply Chain / Procurement": {
            "keywords": [
                "procurement officer", "supply chain",
                "logistics officer", "storekeeper"
            ],
            "type": "mixed"
        },
        "Manufacturing / Production": {
            "keywords": [
                "factory worker", "machine operator",
                "production supervisor"
            ],
            "type": "blue_collar"
        },
        "Marketing / Sales / Digital Marketing": {
            "keywords": [
                "sales executive", "marketing officer",
                "digital marketing", "brand manager"
            ],
            "type": "white_collar"
        },
        "Media / Communications / PR": {
            "keywords": [
                "journalist", "communications officer",
                "public relations", "content creator"
            ],
            "type": "white_collar"
        },
        "NGO / Non-Profit / Development": {
            "keywords": [
                "ngo", "program officer",
                "project officer", "development sector"
            ],
            "type": "white_collar"
        },
        "Project Management / M&E": {
            "keywords": [
                "project manager", "monitoring and evaluation",
                "m&e officer", "program manager"
            ],
            "type": "white_collar"
        },
        "Real Estate / Property Management": {
            "keywords": [
                "property manager", "estate agent",
                "real estate", "facilities manager"
            ],
            "type": "white_collar"
        },
        "Security / Safety / HSE": {
            "keywords": [
                "security guard", "hse officer",
                "safety officer", "risk management"
            ],
            "type": "mixed"
        },
        "Tourism / Travel / Tours": {
            "keywords": [
                "tour guide", "travel consultant",
                "tourism officer"
            ],
            "type": "blue_collar"
        }
    }

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for name, data in self.JOB_CATEGORIES.items():
            category, created = JobCategory.objects.update_or_create(
                name=name,
                defaults={
                    "keywords": data["keywords"],
                    "category_type": data["type"]
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))
            else:
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated category: {name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_count} new categories created, {updated_count} categories updated."
            )
        )

