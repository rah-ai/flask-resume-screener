  
"""
Utils package for Flask Resume Screener

This package contains utility modules for:
- Resume parsing (resume_parser.py)
- Skill extraction (skill_extractor.py) 
- Job matching algorithms (matcher.py)
"""

# Import main classes for easy access
try:
    from .resume_parser import ResumeParser
    from .skill_extractor import SkillExtractor
    from .matcher import JobMatcher
    
    __all__ = ['ResumeParser', 'SkillExtractor', 'JobMatcher']
    
except ImportError as e:
    print(f"Warning: Could not import all utils modules: {e}")
    __all__ = []

# Version information
__version__ = '1.0.0'
__author__ = 'Rahul Makwana'
__email__ = 'rahul.mak2216@gmail.com'
__description__ = 'AI-powered resume screening and job matching utilities'

# Configuration constants
DEFAULT_SKILLS_DATABASE = {
    'programming_languages': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go',
        'rust', 'kotlin', 'swift', 'ruby', 'php', 'scala', 'r', 'matlab'
    ],
    'web_technologies': [
        'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express',
        'flask', 'django', 'spring', 'asp.net', 'laravel', 'fastapi'
    ],
    'databases': [
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
        'sqlite', 'oracle', 'cassandra', 'dynamodb'
    ],
    'cloud_platforms': [
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
        'jenkins', 'gitlab', 'github actions'
    ],
    'ai_ml': [
        'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'scikit-learn', 'pandas', 'numpy', 'opencv', 'nlp', 'computer vision'
    ]
}

# Scoring weights
DEFAULT_SCORING_WEIGHTS = {
    'skills': 0.4,
    'semantic': 0.3,
    'experience': 0.2,
    'education': 0.1
}

def get_version():
    """Return the current version of the utils package"""
    return __version__

def get_default_config():
    """Return default configuration for the screening system"""
    return {
        'skills_database': DEFAULT_SKILLS_DATABASE,
        'scoring_weights': DEFAULT_SCORING_WEIGHTS,
        'supported_file_types': ['pdf', 'docx'],
        'max_file_size_mb': 16,
        'min_match_threshold': 30.0
    }