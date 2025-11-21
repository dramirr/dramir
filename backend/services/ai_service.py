"""
AI Service for Resume Analysis
FIXED FOR LIARA API - Based on working app.py example
"""
import requests
import os
import logging
import json
import base64
from typing import Dict, Any

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
        ✅ FIXED: Analyze resume using Liara API with proper file upload
        Based on working app.py example
        
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
            
            # ✅ Read and encode file to base64 (like in working app.py)
            with open(file_path, 'rb') as file:
                file_content = file.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
            
            logger.info(f"📄 File encoded to base64 ({len(base64_content)} chars)")
            
            # ✅ Build request URL
            url = f"{self.base_url}/chat/completions"
            
            # ✅ Build headers (exactly like working app.py)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # ✅ Build messages with document type (like working app.py)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": base64_content
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # ✅ Build payload (exactly like working app.py)
            payload = {
                "model": config.AI_MODEL,
                "max_tokens": config.AI_MAX_TOKENS,
                "temperature": config.AI_TEMPERATURE,
                "messages": messages
            }
            
            logger.info(f"🤖 Calling Liara API: {url}")
            logger.info(f"📊 Model: {config.AI_MODEL}")
            logger.info(f"📄 Document size: {len(base64_content)} base64 chars")
            
            # ✅ Make request (exactly like working app.py)
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            # ✅ FIXED: Better error handling
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ API Error Response: {error_text}")
                
                try:
                    error_data = response.json()
                    # ✅ FIXED: Handle both dict and string error formats
                    if isinstance(error_data, dict):
                        if 'error' in error_data:
                            if isinstance(error_data['error'], dict):
                                error_msg = error_data['error'].get('message', error_text)
                            else:
                                error_msg = str(error_data['error'])
                        elif 'message' in error_data:
                            error_msg = error_data['message']
                        else:
                            error_msg = error_text
                    else:
                        error_msg = str(error_data)
                except (json.JSONDecodeError, ValueError):
                    error_msg = error_text
                
                raise ValueError(f"API Error ({response.status_code}): {error_msg}")
            
            # ✅ Parse response (like working app.py)
            result_data = response.json()
            
            # Check if response has expected structure
            if 'choices' not in result_data:
                logger.error(f"Unexpected response structure: {result_data}")
                raise ValueError("Invalid API response structure")
            
            if not result_data['choices']:
                raise ValueError("Empty choices in API response")
            
            # Extract content
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
            
            logger.info(f"🤖 Calling Liara API for text generation")
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ API Error: {error_text}")
                
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_msg = error_data.get('message', error_data.get('error', error_text))
                    else:
                        error_msg = str(error_data)
                except:
                    error_msg = error_text
                
                raise ValueError(f"API error: {response.status_code} - {error_msg}")
            
            result_data = response.json()
            
            if 'choices' not in result_data or not result_data['choices']:
                raise ValueError("Invalid API response structure")
            
            return result_data['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"Text generation error: {str(e)}")
            raise


# Singleton instance
ai_service = AIService()