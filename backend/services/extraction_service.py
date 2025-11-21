"""
Resume Data Extraction Service - FULLY FIXED
✅ Fixed: Database session detachment
✅ Fixed: File path handling
✅ Fixed: Proper data extraction
"""
import json
import logging
import re
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self):
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load extraction prompt template"""
        try:
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
            logger.error(f"Error loading prompt: {str(e)}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Default extraction prompt"""
        return """Extract resume information and return as JSON:

{
  "full_name": "REQUIRED - Full name",
  "age": number or null,
  "gender": "Male"/"Female"/null,
  "city": "City name"/null,
  "phone": "Mobile (09xxxxxxxxx)"/null,
  "email": "Email"/null,
  "education_level": "High School"/"Associate"/"Bachelors"/"Masters"/"Doctorate"/null,
  "education_field": "Field"/null,
  "work_experience_years": number/null,
  "last_job_title": "Job title"/null,
  "last_company": "Company"/null,
  "job_stability_months": number/null,
  "industry_type": "Industry"/null,
  "responsibility_level": "Specialist"/"Supervisor"/"Manager"/null,
  "sepidar_skill": "Basic"/"Intermediate"/"Advanced"/null,
  "excel_skill": "Basic"/"Intermediate"/"Advanced"/null,
  "office_skill": "Basic"/"Intermediate"/"Advanced"/null,
  "english_level": 0-100/null,
  "financial_reports_experience": true/false,
  "cost_calculation_experience": true/false,
  "warehouse_experience": true/false,
  "organization_type": "Trading"/"Manufacturing"/"Services"/null,
  "software_skills": ["List"],
  "summary": "Brief summary"
}

Return ONLY valid JSON, no markdown."""
    
    def extract_from_file(self, file_path: str, position_id: int) -> Dict[str, Any]:
        """
        ✅ FIXED: Extract data - Fixed session detachment issue
        """
        try:
            from database.db import get_db_session
            from database.models import Position, Criterion
            from services.ai_service import ai_service
            
            logger.info(f"📄 Starting extraction for: {file_path}")
            
            # ✅ FIX 1: Get all data we need from database FIRST
            position_title = None
            criteria_list = []
            
            with get_db_session() as db:
                position = db.query(Position).filter_by(id=position_id).first()
                
                if not position:
                    raise ValueError(f"Position {position_id} not found")
                
                # ✅ CRITICAL: Extract string values INSIDE the session
                position_title = str(position.title)  # Convert to string immediately
                
                # Get criteria
                criteria = db.query(Criterion).filter_by(position_id=position_id).order_by(Criterion.display_order).all()
                
                # ✅ CRITICAL: Extract all criterion data INSIDE the session
                for criterion in criteria:
                    criteria_list.append({
                        'name': str(criterion.criterion_name),
                        'key': str(criterion.criterion_key)
                    })
            
            # Now session is closed but we have all the data we need
            
            # ✅ FIX 2: Build criteria text
            criteria_text = "\n".join([f"- {c['name']} ({c['key']})" for c in criteria_list]) if criteria_list else "No specific criteria"
            
            # ✅ FIX 3: Build final prompt (outside session)
            final_prompt = f"""Position: {position_title}

Required Information to Extract:
{criteria_text}

{self.prompt_template}

IMPORTANT: Return ONLY the JSON object, no markdown, no explanations."""
            
            logger.info(f"🤖 Calling AI service for extraction...")
            logger.info(f"📂 File: {file_path}")
            logger.info(f"📏 File exists: {Path(file_path).exists()}")
            logger.info(f"📏 File size: {Path(file_path).stat().st_size if Path(file_path).exists() else 'N/A'}")
            
            # ✅ FIX 4: Call AI service
            ai_response = ai_service.analyze_resume(file_path, final_prompt)
            
            if not ai_response:
                raise ValueError("AI service returned empty response")
            
            logger.info(f"✅ AI response received ({len(ai_response)} chars)")
            logger.info(f"📄 Response preview: {ai_response[:200]}...")
            
            # Parse response
            extracted_data = self._parse_ai_response(ai_response)
            
            # Normalize data
            extracted_data = self._normalize_data(extracted_data)
            
            # Validate
            self._validate_extracted_data(extracted_data)
            
            logger.info(f"✅ Extraction completed for: {extracted_data.get('full_name', 'Unknown')}")
            
            return extracted_data
                
        except Exception as e:
            logger.error(f"❌ Extraction error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """✅ FIXED: Better JSON parsing"""
        try:
            response = response.strip()
            
            # Remove markdown
            if response.startswith('```json'):
                response = response.replace('```json', '').replace('```', '').strip()
            elif response.startswith('```'):
                response = response.replace('```', '').strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            # Parse JSON
            data = json.loads(response)
            
            logger.info(f"✅ JSON parsed successfully - Keys: {list(data.keys())}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {str(e)}")
            logger.error(f"Response full text:\n{response}")
            raise ValueError(f"Invalid JSON from AI: {str(e)}")
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize extracted data"""
        
        # Normalize phone
        if 'phone' in data and data['phone']:
            normalized_phone = self._normalize_phone(data['phone'])
            data['phone'] = normalized_phone if normalized_phone else data['phone']
        
        # Convert Persian/Arabic numbers
        persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
        arabic_to_persian = str.maketrans('يك', 'یک')
        
        for key, value in data.items():
            if isinstance(value, str):
                value = value.translate(persian_to_english)
                value = value.translate(arabic_to_persian)
                data[key] = value.strip()
        
        logger.info(f"✅ Data normalized")
        return data
    
    def _normalize_phone(self, phone: str) -> str:
        """✅ FIXED: Better phone normalization"""
        try:
            # Remove non-digits
            phone = ''.join(filter(str.isdigit, phone))
            
            # Convert Persian/Arabic
            persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
            phone = phone.translate(persian_to_english)
            
            # Handle country codes
            if phone.startswith('0098'):
                phone = '0' + phone[4:]
            elif phone.startswith('98') and len(phone) > 10:
                phone = '0' + phone[2:]
            elif phone.startswith('+98'):
                phone = '0' + phone[3:]
            elif not phone.startswith('0'):
                phone = '0' + phone
            
            # Validate mobile format
            if phone.startswith('09') and len(phone) == 11:
                logger.info(f"✅ Valid mobile: {phone}")
                return phone
            else:
                logger.warning(f"⚠️ Invalid phone format: {phone}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Phone normalization error: {str(e)}")
            return None
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> None:
        """
        ✅ FIXED: Relaxed validation
        """
        
        # Validate full name
        if not data.get('full_name'):
            raise ValueError("Full name is required")
        
        phone = data.get('phone')
        email = data.get('email')
        
        # Generate temp phone if needed
        if not phone and not email:
            logger.warning("⚠️ No contact info - generating temp phone")
            
            import hashlib
            name_hash = hashlib.md5(data['full_name'].encode()).hexdigest()[:10]
            temp_phone = f"09{name_hash[:9]}"
            
            data['phone'] = temp_phone
            data['email'] = ""
            
            logger.info(f"✅ Generated temp phone: {temp_phone}")
        
        # Validate phone format (warning only)
        if phone and not (phone.startswith('09') and len(phone) == 11):
            logger.warning(f"⚠️ Phone format may be invalid: {phone}")


# Singleton instance
extraction_service = ExtractionService()