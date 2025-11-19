"""
Resume Data Extraction Service - FIXED VERSION
✅ Fixed import issues for threading context
"""
import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self):
        self.prompt_template = self._load_prompt_template()
        self.config = None
    
    def _load_prompt_template(self) -> str:
        """Load extraction prompt template"""
        try:
            # Import config locally to avoid circular dependencies
            from backend.config import get_config
            config = get_config()
            
            prompt_file = config.PROMPTS_FOLDER / 'extraction_prompt.txt'
            
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Prompt file not found: {prompt_file}, using default")
                return self._get_default_prompt()
        except Exception as e:
            logger.error(f"Error loading prompt template: {str(e)}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default extraction prompt"""
        return """You are an expert ATS (Applicant Tracking System) that analyzes resumes.

Extract the following information from the resume and return it as valid JSON:

{
  "full_name": "Full name of candidate",
  "age": age as number or null,
  "gender": "Male" or "Female" or null,
  "city": "City name" or null,
  "phone": "Mobile phone number (11 digits starting with 09)" or null,
  "email": "Email address" or null,
  "education_level": "High School" or "Associate" or "Bachelors" or "Masters" or "Doctorate" or null,
  "education_field": "Field of study" or null,
  "work_experience_years": total years of experience as number or null,
  "last_job_title": "Most recent job title" or null,
  "last_company": "Most recent company" or null,
  "job_stability_months": months at last job as number or null,
  "industry_type": "Industry/sector" or null,
  "responsibility_level": "Specialist" or "Supervisor" or "Manager" or null,
  "sepidar_skill": "Basic" or "Intermediate" or "Advanced" or null,
  "excel_skill": "Basic" or "Intermediate" or "Advanced" or null,
  "office_skill": "Basic" or "Intermediate" or "Advanced" or null,
  "english_level": percentage (0-100) or null,
  "financial_reports_experience": true or false,
  "cost_calculation_experience": true or false,
  "warehouse_experience": true or false,
  "organization_type": "Trading" or "Manufacturing" or "Services" or null,
  "software_skills": ["List of software/tools"],
  "summary": "Brief 2-3 sentence summary of the resume"
}

CRITICAL RULES:
1. full_name is REQUIRED - never return null
2. phone MUST be a mobile number (11 digits starting with 09)
3. Convert Persian/Arabic numbers to English (۱۲۳ → 123)
4. Only extract information present in the resume
5. Return ONLY valid JSON, no additional text
6. Use exact skill level names: "Basic", "Intermediate", "Advanced"

Respond with ONLY the JSON object, nothing else."""
    
    def extract_from_file(self, file_path: str, position_id: int) -> Dict[str, Any]:
        """
        Extract data from resume file
        
        Args:
            file_path: Path to resume file
            position_id: Position ID for context
            
        Returns:
            Dictionary of extracted data
        """
        try:
            # Import database components locally for thread safety
            from database.db import get_db_session
            from database.models import Position
            
            # Import AI service locally
            from services.ai_service import ai_service
            
            with get_db_session() as db:
                position = db.query(Position).filter_by(id=position_id).first()
                
                if not position:
                    raise ValueError(f"Position {position_id} not found")
                
                criteria_list = []
                for criterion in position.criteria:
                    criteria_list.append(f"- {criterion.criterion_name} ({criterion.criterion_key})")
                
                criteria_text = "\n".join(criteria_list)
                
                prompt = f"""Position: {position.title}

Required Information to Extract:
{criteria_text}

{self.prompt_template}"""
                
                logger.info(f"Extracting data from: {file_path}")
                
                # Use AI service to analyze resume
                ai_response = ai_service.analyze_resume(file_path, prompt)
                
                # Parse AI response
                extracted_data = self._parse_ai_response(ai_response)
                
                # Normalize data
                extracted_data = self._normalize_data(extracted_data)
                
                # Validate data
                self._validate_extracted_data(extracted_data)
                
                logger.info(f"Data extracted successfully for: {extracted_data.get('full_name', 'Unknown')}")
                
                return extracted_data
                
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response to JSON"""
        try:
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            # Parse JSON
            data = json.loads(response)
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            logger.error(f"Response: {response[:500]}")
            raise ValueError(f"Invalid JSON response from AI: {str(e)}")
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize extracted data"""
        
        # Normalize phone number
        if 'phone' in data and data['phone']:
            data['phone'] = self._normalize_phone(data['phone'])
        
        # Convert Persian/Arabic numbers to English
        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        arabic_to_persian = str.maketrans('يك', 'یک')
        
        for key, value in data.items():
            if isinstance(value, str):
                value = value.translate(persian_to_english)
                value = value.translate(arabic_to_persian)
                data[key] = value.strip()
        
        return data
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number"""
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle country code
        if phone.startswith('98'):
            phone = '0' + phone[2:]
        elif phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif not phone.startswith('0'):
            phone = '0' + phone
        
        return phone
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> None:
        """Validate extracted data"""
        
        # Validate full name is present
        if not data.get('full_name'):
            raise ValueError("Full name is required but was not extracted")
        
        phone = data.get('phone')
        email = data.get('email')
        
        # At least one contact method required
        if not phone and not email:
            raise ValueError("Either phone or email must be provided")
        
        # Validate phone format if present
        if phone:
            if not (phone.startswith('09') and len(phone) == 11):
                logger.warning(f"Invalid phone format: {phone}")


# Create singleton instance
extraction_service = ExtractionService()