import json
import datetime
from openai import OpenAI
from django.conf import settings

class AIService:
    @staticmethod
    def analyze_cv(cv_text):
        """
        Analyzes CV text using OpenAI and returns a structured JSON response.
        """
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            return None
            
        client = OpenAI(api_key=api_key)
        
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
            "improvement_suggestions": ["specifically", "list", "how", "to", "improve"]
        }}
        
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
