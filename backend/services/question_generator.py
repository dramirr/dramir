"""
Interview Question Generator Service
"""
import json
import logging
from typing import Dict, Any, List
from pathlib import Path

from backend.services.ai_service import ai_service
from backend.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class QuestionGenerator:
    def __init__(self):
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load question generation prompt template"""
        prompt_file = config.PROMPTS_FOLDER / 'questions_prompt.txt'
        
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Prompt file not found: {prompt_file}, using default")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default question generation prompt"""
        return """Generate 3 customized interview questions based on the candidate's profile and position requirements.

Return ONLY a valid JSON array with this format:
[
  {
    "question_text": "Interview question here?",
    "category": "technical" or "behavioral" or "situational"
  }
]

Guidelines:
- Question 1: Technical - Based on required skills and experience
- Question 2: Behavioral - Based on past work experience
- Question 3: Situational - Based on role responsibilities

Make questions specific to the candidate's background and the position."""
    
    def generate_questions(
        self,
        extracted_data: Dict[str, Any],
        position_data: Dict[str, Any],
        score_details: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions
        
        Args:
            extracted_data: Candidate data extracted from resume
            position_data: Position information
            score_details: Scoring results
            
        Returns:
            List of generated questions
        """
        try:
            strengths = [
                s['criterion_name'] 
                for s in score_details 
                if s.get('awarded_points', 0) / max(s.get('max_points', 1), 1) >= 0.8
            ]
            
            weaknesses = [
                s['criterion_name']
                for s in score_details
                if s.get('awarded_points', 0) / max(s.get('max_points', 1), 1) < 0.5
            ]
            
            prompt = f"""{self.prompt_template}

POSITION: {position_data.get('title', 'Not specified')}

CANDIDATE PROFILE:
- Name: {extracted_data.get('full_name', 'Unknown')}
- Experience: {extracted_data.get('work_experience_years', 'N/A')} years
- Last Role: {extracted_data.get('last_job_title', 'N/A')}
- Education: {extracted_data.get('education_level', 'N/A')} in {extracted_data.get('education_field', 'N/A')}
- Key Skills: {', '.join(extracted_data.get('software_skills', []))}

STRENGTHS:
{', '.join(strengths) if strengths else 'None identified'}

AREAS FOR IMPROVEMENT:
{', '.join(weaknesses) if weaknesses else 'None identified'}

Generate 3 targeted interview questions that:
1. Probe their technical skills relevant to the position
2. Assess their behavioral fit based on experience
3. Test how they'd handle key job responsibilities

Return ONLY the JSON array, nothing else."""
            
            logger.info(f"Generating interview questions for: {extracted_data.get('full_name', 'Unknown')}")
            
            ai_response = ai_service.generate_text(prompt, max_tokens=1500)
            
            questions = self._parse_questions(ai_response)
            
            if len(questions) != 3:
                logger.warning(f"Expected 3 questions, got {len(questions)}. Generating default questions.")
                questions = self._get_default_questions(extracted_data, position_data)
            
            logger.info(f"Generated {len(questions)} interview questions")
            
            return questions
            
        except Exception as e:
            logger.error(f"Question generation error: {str(e)}")
            return self._get_default_questions(extracted_data, position_data)
    
    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response to questions list"""
        try:
            response = response.strip()
            
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            questions = json.loads(response)
            
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse questions: {str(e)}")
            raise
    
    def _get_default_questions(
        self,
        extracted_data: Dict[str, Any],
        position_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get default questions if generation fails"""
        position_title = position_data.get('title', 'this position')
        years_exp = extracted_data.get('work_experience_years', 'your')
        
        return [
            {
                "question_text": f"Can you describe your most significant accomplishment in your {years_exp} years of professional experience?",
                "category": "behavioral"
            },
            {
                "question_text": f"What specific skills and experiences make you a good fit for the {position_title} role?",
                "category": "technical"
            },
            {
                "question_text": f"How would you approach a situation where you need to learn a new system or tool quickly to meet a deadline?",
                "category": "situational"
            }
        ]


question_generator = QuestionGenerator()