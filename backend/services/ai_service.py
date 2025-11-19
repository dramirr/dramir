"""
AI Service for Resume Analysis
FIXED VERSION - Reads API key from .env instead of database
"""
from openai import OpenAI
import base64
import os
import logging
from typing import Dict, Any

from backend.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class AIService:
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize AI client with API key from environment variables"""
        try:
            # ✅ FIXED: Read directly from environment variable
            api_key = os.getenv('LIARA_API_KEY')
            
            if not api_key:
                logger.warning("No LIARA_API_KEY found in environment variables")
                logger.warning("Please add LIARA_API_KEY to your .env file")
                return
            
            # Initialize OpenAI client with Liara endpoint
            self.client = OpenAI(
                base_url=config.LIARA_BASE_URL,
                api_key=api_key
            )
            logger.info("✓ AI client initialized successfully with Liara API")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def analyze_resume(self, file_path: str, prompt: str) -> str:
        """
        Analyze resume file with AI
        
        Args:
            file_path: Path to resume file
            prompt: Analysis prompt
            
        Returns:
            AI response text
        """
        if not self.client:
            raise ValueError("AI client not initialized. Please configure LIARA_API_KEY in .env file.")
        
        try:
            with open(file_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode()
            
            ext = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.doc': 'application/msword',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png'
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')
            
            logger.info(f"Analyzing file: {os.path.basename(file_path)} ({mime_type})")
            
            response = self.client.chat.completions.create(
                model=config.AI_MODEL,
                max_tokens=config.AI_MAX_TOKENS,
                temperature=config.AI_TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": file_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            result = response.choices[0].message.content
            
            logger.info(f"✓ AI analysis completed. Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate text using AI (without file)
        
        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self.client:
            raise ValueError("AI client not initialized. Please configure LIARA_API_KEY in .env file.")
        
        try:
            response = self.client.chat.completions.create(
                model=config.AI_MODEL,
                max_tokens=max_tokens,
                temperature=config.AI_TEMPERATURE,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Text generation error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise


ai_service = AIService()