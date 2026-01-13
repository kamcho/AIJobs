import os
import json
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
