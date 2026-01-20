import json
import datetime
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
    def generate_cover_letter(user, job):
        """
        Generates a professional, tailored cover letter using OpenAI.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return "API Key not configured."
            
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
        1. Tone: Professional, confident, and enthusiastic.
        2. Format: Use a strict formal business letter layout:
           - [TOP LEFT] Your Name, Email, Phone
           - [NEXT LINE] Today's Date
           - [NEXT LINE] Hiring Manager, Job Company, Job Location
           - [NEXT LINE] Salutation (e.g., Dear Hiring Manager,)
        3. Content: Focus on matching the candidate's strongest skills and experiences with the specific requirements of the job.
        4. Avoid AI-sounding clichés. Use natural, direct language.
        5. Keep it concise (approx 350 words).
        6. Return ONLY the final text of the cover letter.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o", # Using gpt-4o for better quality
                messages=[
                    {"role": "system", "content": "You are a professional cover letter writer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in cover letter generation: {str(e)}")
            return f"Error generating cover letter: {str(e)}"

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
