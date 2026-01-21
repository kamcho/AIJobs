import json
import datetime
from difflib import SequenceMatcher
from home.models import AIChatMessage
from openai import OpenAI
from django.conf import settings

class AIService:
    @staticmethod
    def analyze_cv(cv_text, categories_data=None):
        """
        Analyzes CV text using OpenAI and returns a structured JSON response.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        
        categories_prompt = ""
        if categories_data:
            categories_prompt = f"""
            Also, identify the most relevant job categories for this candidate from the following list:
            {json.dumps(categories_data)}
            Include these in the "suggested_categories" field of your JSON response.
            """

        prompt = f"""
        You are a professional technical recruiter. Analyze the following CV text and provide a detailed assessment.
        
        Return your response ONLY as a valid JSON object with the following structure:
        {{
            "total_score": 0-100,
            "professionalism_score": 0-20,
            "relevance_score": 0-40,
            "experience_score": 0-30,
            "education_score": 0-10,
            "missing_sections": ["list", "of", "missing", "crucial", "information"],
            "improvement_suggestions": ["specifically", "list", "how", "to", "improve"],
            "suggested_categories": ["Category Name 1", "Category Name 2"]
        }}
        
        {categories_prompt}
        
        Evaluation criteria (must sum to total_score):
        1. Professionalism and formatting (max 20)
        2. Relevance of skills for applicants roles (max 40)
        3. Clarity and impact of work experience (max 30)
        4. Education and certifications (max 10)
        
        CV TEXT:
        {cv_text}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that evaluates CVs and returns ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error in CV analysis: {str(e)}")
            return None

    @staticmethod
    def analyze_cover_letter(text):
        """
        Analyzes Cover Letter text using OpenAI and returns a structured JSON response.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        You are a professional HR manager. Analyze the following Cover Letter text and provide a detailed assessment.
        
        Return your response ONLY as a valid JSON object with the following structure:
        {{
            "total_score": 0-100,
            "professionalism_score": 0-20,
            "content_score": 0-40,
            "tone_score": 0-20,
            "impact_score": 0-20,
            "missing_elements": ["list", "of", "missing", "important", "parts"],
        }}
        
        Evaluation criteria (must sum to total_score):
        1. Professionalism and formatting (max 20)
        2. Content and alignment with industry standards (max 40)
        3. Tone and engagement (max 20)
        4. Overall impact and persuasiveness (max 20)
        
        COVER LETTER TEXT:
        {text}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional recruiting assistant that evaluates Cover Letters and returns ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"Error in cover letter analysis: {str(e)}")
            return None

    @staticmethod
    def generate_cover_letter(user, job):
        """
        Generates a professional, tailored cover letter using OpenAI and includes analysis scores.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        
        # Gather User Data
        profile = getattr(user, 'profile', None)
        experiences = user.work_experiences.all()
        educations = user.educations.all()
        skills = user.skills.all()
        
        user_info = f"Name: {profile.full_name if profile else user.email}\n"
        user_info += f"Email: {user.email}\n"
        if profile and profile.phone_primary:
            user_info += f"Phone: {profile.phone_primary}\n"
        
        # Current Date for the letter
        current_date = datetime.date.today().strftime("%B %d, %Y")
        user_info += f"Current Date: {current_date}\n"
            
        experience_summary = "\n".join([
            f"- {exp.job_title} at {exp.company_name} ({exp.start_date} to {exp.end_date or 'Present'}): {exp.description}"
            for exp in experiences
        ])
        
        education_summary = "\n".join([
            f"- {edu.degree} from {edu.institution} ({edu.level})"
            for edu in educations
        ])
        
        skills_summary = ", ".join([skill.name for skill in skills])
        
        # Gather Job Data
        job_info = f"Title: {job.title}\n"
        job_info += f"Company: {job.company}\n"
        job_info += f"Location: {job.location}\n"
        job_info += f"Description: {job.description[:1000]}...\n"
        job_info += "Requirements:\n" + "\n".join([f"- {req.description}" for req in job.requirements.all()])

        prompt = f"""
        You are a professional career coach and expert cover letter writer. 
        Your task is to write a highly professional, persuasive, and tailored cover letter for a job application.
        
        CANDIDATE INFORMATION:
        {user_info}
        
        WORK EXPERIENCE:
        {experience_summary}
        
        EDUCATION:
        {education_summary}
        
        SKILLS:
        {skills_summary}
        
        JOB LISTING:
        {job_info}
        
        INSTRUCTIONS:
        1. Write the Cover Letter:
           - Tone: Professional, confident, and enthusiastic.
           - Format: Strict formal business letter layout.
           - Content: Match strongest skills to job requirements.
           - Length: ~350 words.
           
        2. Analyze the Letter (Self-Evaluation):
           - Score the letter you just wrote based on these criteria:
             a. Professionalism (0-20)
             b. Content & Alignment (0-40)
             c. Tone & Engagement (0-20)
             d. Overall Impact (0-20)
           
        3. Return ONLY a JSON object with this structure:
        {{
            "content": "Full text of the cover letter...",
            "analysis": {{
                "total_score": 0-100,
                "professionalism_score": 0-20,
                "content_score": 0-40,
                "tone_score": 0-20,
                "impact_score": 0-20,
                "missing_elements": [],
                "improvement_suggestions": []
            }}
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer who outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500,
                response_format={ "type": "json_object" }
            )
            
            return json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"Error in cover letter generation: {str(e)}")
            return None

    @staticmethod
    def chat(user, message):
        """
        Handles general chat interactions for the AI assistant.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return "AI Service is currently unavailable."
            
        client = OpenAI(api_key=api_key)
        
        # Build context
        context_prompt = f"""
        You are 'FindAJob Assistant', a helpful AI assistant embedded in the FindAJob.ai platform.
        Current User: {user.email if user.is_authenticated else 'Guest'}
        Role: {getattr(user, 'role', 'Visitor') if user.is_authenticated else 'Visitor'}
        
        Your goal is to help users navigate the site, understand features (job search, CV analysis, cover letter generation), and provide career advice.
        Keep responses concise, helpful, and friendly.
        """
        
        # Build message chain
        messages = [{"role": "system", "content": context_prompt}]
        
        # Add history if user is authenticated
        if user.is_authenticated:
            past_messages = AIChatMessage.objects.filter(user=user).order_by('-timestamp')[:6]
            # Reverse because we fetched latest first, but OpenAI needs chronological
            for msg in reversed(past_messages):
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in chat: {str(e)}")
            return "I'm having trouble connecting right now. Please try again later."
    @staticmethod
    def match_categories(query, categories_data):
        """
        Matches a search query to a list of job categories using OpenAI.
        categories_data is a list of dicts: [{'name': '...', 'keywords': [...]}, ...]
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return []
            
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
        Given the following search query from a job seeker, identify the most relevant job categories from the provided list.
        A query might match multiple categories.
        
        Return your response ONLY as a JSON object with a key "matched_categories" containing a list of category names.
        {{
            "matched_categories": ["Category 1", "Category 2"]
        }}
        
        If no categories match, return {{"matched_categories": []}}.
        
        SEARCH QUERY: {query}
        
        AVAILABLE CATEGORIES:
        {json.dumps(categories_data)}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a job search assistant. You map queries to job categories and return ONLY a JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3, 
                max_tokens=500,
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            return data.get("matched_categories", [])
        except Exception as e:
            print(f"Error in category matching: {str(e)}")
            return []

    @staticmethod
    def _fuzzy_match_company(company_name, existing_companies, threshold=0.75):
        """
        Performs fuzzy matching to find similar company names.
        Returns list of tuples: (company_id, company_name, similarity_score)
        """
        matches = []
        company_name_lower = company_name.lower().strip()
        
        for company in existing_companies:
            existing_name_lower = company['name'].lower().strip()
            similarity = SequenceMatcher(None, company_name_lower, existing_name_lower).ratio()
            
            if similarity >= threshold:
                matches.append({
                    'id': company['id'],
                    'name': company['name'],
                    'similarity': round(similarity, 3)
                })
        
        # Sort by similarity (highest first)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches

    @staticmethod
    def create_job_listing(text, existing_companies=None, categories_data=None):
        """
        Parses job listing text using OpenAI and extracts Company and JobListing data.
        Uses function calling to structure the response.
        
        Args:
            text: The job listing text to parse
            existing_companies: List of dicts with {'id', 'name'} of existing companies
            categories_data: List of dicts with {'name', 'keywords'} of job categories
            
        Returns:
            Dict with 'company', 'job_listing', 'requirements', and 'similar_companies' (if any found)
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        
        # Prepare existing companies data for AI
        companies_list = existing_companies if existing_companies else []
        companies_names = [c['name'] for c in companies_list]
        
        # Prepare categories data
        categories_list = categories_data if categories_data else []
        category_names = [c['name'] for c in categories_list]
        
        # Define the function schema for OpenAI function calling
        functions = [
            {
                "name": "extract_job_listing_data",
                "description": "Extract company and job listing information from the provided text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "object",
                            "description": "Company information extracted from the text",
                            "properties": {
                                "name": {"type": "string", "description": "Company name"},
                                "description": {"type": "string", "description": "Company description"},
                                "website": {"type": "string", "description": "Company website URL"},
                                "location": {"type": "string", "description": "Company location/headquarters"},
                                "primary_phone": {"type": "string", "description": "Primary phone number"},
                                "secondary_phone": {"type": "string", "description": "Secondary phone number"},
                                "primary_email": {"type": "string", "description": "Primary email address"},
                                "secondary_email": {"type": "string", "description": "Secondary email address"},
                                "founded_in": {"type": "integer", "description": "Year company was founded (optional)"}
                            },
                            "required": ["name"]
                        },
                        "job_listing": {
                            "type": "object",
                            "description": "Job listing information",
                            "properties": {
                                "title": {"type": "string", "description": "Job title"},
                                "category": {"type": "string", "description": f"Job category name from: {', '.join(category_names) if category_names else 'any relevant category'}"},
                                "description": {"type": "string", "description": "Full job description"},
                                "location": {"type": "string", "description": "Job location"},
                                "url": {"type": "string", "description": "Application URL or job posting URL"},
                                "terms": {"type": "string", "description": "Job terms: Full Time, Part Time, Contract, Freelance, Internship, Attachment, or None", "enum": ["Full Time", "Part Time", "Contract", "Freelance", "Internship", "Attachment", "None"]},
                                "education_level_required": {"type": "string", "description": "Required education level", "enum": ["Primary", "Secondary", "College", "University", "None"]},
                                "experience_required_years": {"type": "integer", "description": "Years of experience required"},
                                "application_method": {"type": "string", "description": "How to apply", "enum": ["email", "website", "google_form", "other"]},
                                "employer_email": {"type": "string", "description": "Email for applications"},
                                "application_url": {"type": "string", "description": "Application URL"},
                                "application_instructions": {"type": "string", "description": "Special application instructions"},
                                "expiry_date": {"type": "string", "description": "Job expiry date in YYYY-MM-DD format"}
                            },
                            "required": ["title", "description", "location"]
                        },
                        "requirements": {
                            "type": "array",
                            "description": "List of job requirements",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string", "description": "Requirement description"},
                                    "is_mandatory": {"type": "boolean", "description": "Whether this requirement is mandatory"}
                                },
                                "required": ["description"]
                            }
                        }
                    },
                    "required": ["company", "job_listing", "requirements"]
                }
            }
        ]
        
        system_prompt = f"""You are a job listing parser. Extract structured information from job posting text.
        
Available job categories: {', '.join(category_names) if category_names else 'Any relevant category'}
Existing companies in database: {', '.join(companies_names) if companies_names else 'None'}

Extract all relevant information accurately. For company name, check if it matches any existing company name from the list provided.
If the company name is very similar to an existing one (e.g., 'Arrotech Company' vs 'Arrotech Solutions'), note this in your response.
"""
        
        user_prompt = f"""Parse the following job listing text and extract company information, job listing details, and requirements:

{text}
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                functions=functions,
                function_call={"name": "extract_job_listing_data"},
                temperature=0.3,
                max_tokens=2000
            )
            
            # Extract function call result
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "extract_job_listing_data":
                parsed_data = json.loads(function_call.arguments)
                
                # Perform fuzzy matching on company name
                company_name = parsed_data.get('company', {}).get('name', '')
                similar_companies = []
                if company_name and existing_companies:
                    similar_companies = AIService._fuzzy_match_company(company_name, existing_companies)
                
                parsed_data['similar_companies'] = similar_companies
                return parsed_data
            else:
                return None
                
        except Exception as e:
            print(f"Error in job listing creation: {str(e)}")
            return None
