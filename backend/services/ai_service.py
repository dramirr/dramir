"""
AI Service for Resume Analysis
✅ FIXED: Correct Liara API format according to their documentation
✅ FIXED: File upload using proper 'file' type with data URL
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
    
    def _file_to_data_url(self, file_path: str) -> str:
        """
        ✅ Convert file to Data URL format (like in working app.py)
        
        Args:
            file_path: Path to file
            
        Returns:
            Data URL string: "data:mime/type;base64,..."
        """
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
        
        with open(file_path, 'rb') as f:
            base64_data = base64.b64encode(f.read()).decode('utf-8')
        
        return f"data:{mime_type};base64,{base64_data}"
    
    def analyze_resume(self, file_path: str, prompt: str) -> str:
        """
        ✅ FIXED: Analyze resume using CORRECT Liara API format
        Based on working app.py + Liara expert guidance
        
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
            
            logger.info("=" * 80)
            logger.info("🤖 Calling Liara AI Service")
            logger.info(f"📂 File: {filename} ({file_size} bytes)")
            
            # ✅ Convert file to Data URL
            logger.info("📄 Converting file to Data URL...")
            file_data_url = self._file_to_data_url(file_path)
            logger.info(f"✅ File encoded ({len(file_data_url)} chars)")
            
            # ✅ Build request URL
            url = f"{self.base_url}/chat/completions"
            
            # ✅ Build headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            # ✅ CRITICAL: Use CORRECT format according to Liara experts
            # Format: { "type": "file", "file": { "filename": "...", "file_data": "..." } }
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",  # ✅ Changed from "document" to "file"
                            "file": {        # ✅ Changed from "source" to "file"
                                "filename": filename,
                                "file_data": file_data_url  # ✅ Data URL format
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # ✅ Build payload
            payload = {
                "model": config.AI_MODEL,
                "max_tokens": config.AI_MAX_TOKENS,
                "temperature": config.AI_TEMPERATURE,
                "messages": messages
            }
            
            logger.info(f"🔗 API URL: {url}")
            logger.info(f"📊 Model: {config.AI_MODEL}")
            logger.info(f"📝 Prompt length: {len(prompt)} chars")
            logger.info(f"📎 File data length: {len(file_data_url)} chars")
            
            # ✅ Make request
            logger.info("⏳ Sending request to Liara API...")
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            logger.info(f"📥 Response status: {response.status_code}")
            
            # ✅ Handle errors
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"❌ API Error Response: {error_text}")
                
                try:
                    error_data = response.json()
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
            
            # ✅ Parse response
            result_data = response.json()
            
            # Check structure
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
                logger.info(f"🔢 Tokens - Input: {usage.get('prompt_tokens', 0)}, "
                          f"Output: {usage.get('completion_tokens', 0)}, "
                          f"Total: {usage.get('total_tokens', 0)}")
            
            logger.info("=" * 80)
            
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