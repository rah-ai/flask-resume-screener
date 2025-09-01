import os
import sys

def test_basic_setup():
    print("🧪 Testing Flask Resume Screener Setup...")
    print("=" * 50)
    
    # Test 1: Check file structure
    required_files = [
        'app.py',
        'utils/__init__.py',
        'utils/resume_parser.py', 
        'utils/skill_extractor.py',
        'utils/matcher.py',
        'templates/base.html',
        'templates/index.html',
        'templates/results.html',
        'templates/dashboard.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    print("📁 Checking file structure...")
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing {len(missing_files)} files. Create them first!")
        return False
    
    # Test 2: Check imports
    print("\n📦 Testing imports...")
    try:
        import flask
        print("✅ Flask")
    except ImportError:
        print("❌ Flask - Run: pip install Flask==2.3.3")
        return False
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy + English model")
    except (ImportError, IOError):
        print("❌ spaCy - Run: pip install spacy==3.7.2 && python -m spacy download en_core_web_sm")
        return False
    
    try:
        import sklearn
        print("✅ scikit-learn")
    except ImportError:
        print("❌ scikit-learn - Run: pip install scikit-learn==1.3.0")
        return False
    
    # Test 3: Test project imports
    try:
        from utils.resume_parser import ResumeParser
        from utils.skill_extractor import SkillExtractor
        from utils.matcher import JobMatcher
        print("✅ All project modules")
    except ImportError as e:
        print(f"❌ Project modules - Error: {e}")
        return False
    
    # Test 4: Test Flask app
    try:
        from app import app
        print("✅ Flask app")
    except ImportError as e:
        print(f"❌ Flask app - Error: {e}")
        return False
    
    print("\n🎉 All tests passed! Ready to run the app.")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Test with your resume!")
    
    return True

if __name__ == "__main__":
    test_basic_setup()