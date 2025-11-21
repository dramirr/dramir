"""
AI Service for Resume Analysis
FIXED FOR LIARA API - Using multipart/form-data with files
"""
import requests
import os
import logging
from typing import Dict, Any
import json

from backend.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class AIService:
    def __init__(self):
        self.api_key = None
        self.base_url = None
        self._init_client()
    
    def _init_client(self):
        """Initialize AI client"""
        try:
            self.api_key = os.getenv('LIARA_API_KEY')
            self.base_url = config.LIARA_BASE_URL
            
            if not self.api_key:
                logger.warning("⚠️ No LIARA_API_KEY found in environment variables")
                return
            
            logger.info("✓ AI client initialized for Liara API")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {str(e)}")
    
    def analyze_resume(self, file_path: str, prompt: str) -> str:
        """
        ✅ Analyze resume using Liara API with file upload
        
        Args:
            file_path: Path to resume file
            prompt: Analysis prompt
            
        Returns:
            AI response text
        """
        if not self.api_key:
            raise ValueError("API key not configured. Please set LIARA_API_KEY in .env file")
        
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            logger.info(f"📂 File: {filename} ({file_size} bytes)")
            
            # Build request URL
            url = f"{self.base_url}/chat/completions"
            
            # ✅ CRITICAL: Use headers WITHOUT Content-Type (requests will set it automatically for multipart)
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # ✅ Open file and prepare multipart form data
            with open(file_path, 'rb') as file:
                # Build the messages structure
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "file",
                                "file": {
                                    "filename": filename
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
                
                # ✅ Prepare data payload
                data = {
                    'model': config.AI_MODEL,
                    'max_tokens': str(config.AI_MAX_TOKENS),
                    'temperature': str(config.AI_TEMPERATURE),
                    'messages': json.dumps(messages)
                }
                
                # ✅ Prepare files payload (key name might be 'file' or 'files')
                files = {
                    'file': (filename, file, 'application/pdf')
                }
                
                logger.info(f"🤖 Calling Liara API: {url}")
                logger.info(f"📊 Model: {config.AI_MODEL}")
                logger.info(f"📄 Uploading file: {filename}")
                
                # ✅ Make request with files
                response = requests.post(
                    url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=120
                )
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ API Error Response: {response.text}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', response.text)
                    raise ValueError(f"API Error ({response.status_code}): {error_msg}")
                except json.JSONDecodeError:
                    raise ValueError(f"API Error ({response.status_code}): {response.text}")
            
            # Parse response
            result_data = response.json()
            
            # Check if response has expected structure
            if 'choices' not in result_data:
                logger.error(f"Unexpected response structure: {result_data}")
                raise ValueError("Invalid API response structure")
            
            result = result_data['choices'][0]['message']['content']
            
            logger.info(f"✅ Success! Response length: {len(result)} characters")
            logger.info(f"📄 Preview: {result[:200]}...")
            
            # Log token usage if available
            if 'usage' in result_data:
                usage = result_data['usage']
                logger.info(f"🔢 Tokens - Input: {usage.get('prompt_tokens', 0)}, Output: {usage.get('completion_tokens', 0)}, Total: {usage.get('total_tokens', 0)}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("❌ Request timeout")
            raise ValueError("API request timed out. The file may be too large or the service is slow.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {str(e)}")
            raise ValueError(f"Failed to connect to API: {str(e)}")
            
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate text without file
        
        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if not self.api_key:
            raise ValueError("API key not configured")
        
        try:
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            payload = {
                "model": config.AI_MODEL,
                "max_tokens": max_tokens,
                "temperature": config.AI_TEMPERATURE,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                raise ValueError(f"API error: {response.status_code} - {response.text}")
            
            result_data = response.json()
            return result_data['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"Text generation error: {str(e)}")
            raise


ai_service = AIService()