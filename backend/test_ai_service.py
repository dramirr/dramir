"""
Test Script for AI Service
Usage: python backend/test_ai_service.py <path_to_resume.pdf>
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from services.ai_service import ai_service
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_ai_service(resume_path: str):
    """
    Test AI service with a sample resume
    
    Args:
        resume_path: Path to resume file
    """
    print("=" * 80)
    print("🧪 Testing AI Service")
    print("=" * 80)
    
    # Check file exists
    if not os.path.exists(resume_path):
        print(f"❌ File not found: {resume_path}")
        return
    
    print(f"📂 File: {resume_path}")
    print(f"📏 Size: {os.path.getsize(resume_path)} bytes")
    
    # Build test prompt
    test_prompt = """Extract the following information from this resume:

{
  "full_name": "Full name of candidate",
  "age": number or null,
  "phone": "Mobile phone (09...)" or null,
  "email": "Email address" or null,
  "education_level": "Bachelors/Masters/etc" or null,
  "work_experience_years": number or null,
  "last_job_title": "Most recent job" or null,
  "summary": "Brief summary"
}

Return ONLY valid JSON, no markdown.
"""
    
    print("\n📝 Prompt:")
    print(test_prompt[:200] + "...")
    
    try:
        print("\n⏳ Calling AI service...")
        response = ai_service.analyze_resume(resume_path, test_prompt)
        
        print("\n✅ Success!")
        print("=" * 80)
        print("📄 AI Response:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        
        # Try to parse as JSON
        import json
        try:
            # Remove markdown if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response.replace('```json', '').replace('```', '').strip()
            elif clean_response.startswith('```'):
                clean_response = clean_response.replace('```', '').strip()
            
            data = json.loads(clean_response)
            print("\n✅ Valid JSON!")
            print("\nExtracted fields:")
            for key, value in data.items():
                print(f"  - {key}: {value}")
                
        except json.JSONDecodeError as e:
            print(f"\n⚠️ Response is not valid JSON: {str(e)}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def test_text_generation():
    """Test simple text generation"""
    print("\n" + "=" * 80)
    print("🧪 Testing Text Generation")
    print("=" * 80)
    
    test_prompt = "Say 'Hello, TalentRadar!' in a friendly way."
    
    try:
        print("⏳ Calling AI service...")
        response = ai_service.generate_text(test_prompt, max_tokens=100)
        
        print("\n✅ Success!")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Main test function"""
    config = get_config()
    config.init_app()
    
    print("🔧 Configuration:")
    print(f"  - Model: {config.AI_MODEL}")
    print(f"  - Base URL: {config.LIARA_BASE_URL}")
    print(f"  - API Key: {'✅ Set' if os.getenv('LIARA_API_KEY') else '❌ Not set'}")
    
    if not os.getenv('LIARA_API_KEY'):
        print("\n❌ LIARA_API_KEY not found in environment!")
        print("Please set it in .env file")
        return
    
    # Test text generation first
    test_text_generation()
    
    # Test resume analysis if file provided
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
        test_ai_service(resume_path)
    else:
        print("\n" + "=" * 80)
        print("ℹ️ To test resume analysis:")
        print(f"   python {sys.argv[0]} <path_to_resume.pdf>")
        print("=" * 80)


if __name__ == '__main__':
    main()