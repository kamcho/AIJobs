from django.core.management.base import BaseCommand

from jobs.models import JobCategory


class Command(BaseCommand):
    help = "Create default job categories for FindAJob.ai"

    CATEGORIES = [
        "Administration / Secretarial",
        "Agriculture / Agro-Allied",
        "Art / Crafts / Languages",
        "Aviation / Airline",
        "Banking",
        "Building and Construction",
        "Bursary and Scholarships",
        "Catering / Confectionery",
        "Consultancy",
        "Customer Care",
        "Data, Business Analysis and AI",
        "Driving",
        "Education / Teaching",
        "Engineering / Technical",
        "Expatriate",
        "Finance / Accounting / Audit",
        "General",
        "Graduate Jobs",
        "Hospitality / Hotel / Restaurant",
        "Human Resources / HR",
        "ICT / Computer",
        "Insurance",
        "Internships / Volunteering",
        "Janitorial Services",
        "Law / Legal",
        "Logistics",
        "Manufacturing",
        "Maritime",
        "Media / Advertising / Branding",
        "Medical / Healthcare",
        "NGO / Non-Profit",
        "Oil and Gas / Energy",
        "Pharmaceutical",
        "Procurement / Store-keeping / Supply Chain",
        "Product Management",
        "Project Management",
        "Real Estate",
        "Research",
        "RFP / RFQ / EOI",
        "Safety and Environment / HSE",
        "Sales / Marketing / Retail / Business Development",
        "Science",
        "Security / Intelligence",
        "Travels & Tours",
    ]

    def handle(self, *args, **options):
        created_count = 0
        for name in self.CATEGORIES:
            category, created = JobCategory.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created category: {name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Category already exists: {name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_count} new categories created, {len(self.CATEGORIES) - created_count} already existed."
            )
        )

