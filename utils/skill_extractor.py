import spacy
import re
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SkillExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            print("Warning: spaCy English model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Initialize TF-IDF for semantic similarity (alternative to sentence-transformers)
        self.tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Comprehensive skill database
        self.tech_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go',
                'rust', 'kotlin', 'swift', 'ruby', 'php', 'scala', 'r', 'matlab',
                'c', 'perl', 'dart', 'elixir', 'haskell', 'clojure'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express',
                'flask', 'django', 'spring', 'asp.net', 'laravel', 'fastapi',
                'bootstrap', 'tailwind', 'jquery', 'webpack', 'babel', 'sass',
                'less', 'typescript', 'next.js', 'nuxt.js', 'svelte'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'sqlite', 'oracle', 'cassandra', 'dynamodb', 'mariadb',
                'couchdb', 'neo4j', 'influxdb', 'firebase', 'supabase'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'gitlab', 'github actions', 'circleci', 'travis ci',
                'heroku', 'vercel', 'netlify', 'digitalocean', 'linode'
            ],
            'ai_ml': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch',
                'scikit-learn', 'pandas', 'numpy', 'opencv', 'nlp', 
                'computer vision', 'keras', 'xgboost', 'lightgbm', 'catboost',
                'neural networks', 'cnn', 'rnn', 'lstm', 'transformer', 'bert'
            ],
            'tools': [
                'git', 'jira', 'confluence', 'postman', 'swagger', 'figma',
                'adobe', 'photoshop', 'illustrator', 'sketch', 'vscode',
                'intellij', 'eclipse', 'sublime', 'vim', 'emacs'
            ],
            'mobile_development': [
                'android', 'ios', 'flutter', 'react native', 'xamarin',
                'ionic', 'cordova', 'swift', 'objective-c', 'kotlin'
            ],
            'data_science': [
                'data analysis', 'data visualization', 'statistics', 'tableau',
                'power bi', 'matplotlib', 'seaborn', 'plotly', 'jupyter',
                'r studio', 'spss', 'sas', 'hadoop', 'spark'
            ]
        }
        
        # Flatten all skills for easy searching
        self.all_skills = []
        for category in self.tech_skills.values():
            self.all_skills.extend(category)
    
    def extract_skills_keyword_matching(self, text: str) -> List[str]:
        """Extract skills using keyword matching with fuzzy matching"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.all_skills:
            # Exact match with word boundaries
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                found_skills.append(skill)
            # Fuzzy match for compound skills
            elif ' ' in skill:
                skill_words = skill.lower().split()
                if all(word in text_lower for word in skill_words):
                    found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_skills_ner(self, text: str) -> List[str]:
        """Extract skills using Named Entity Recognition"""
        doc = self.nlp(text)
        
        # Look for organizations and products (often tech companies/tools)
        tech_entities = []
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "GPE"]:
                ent_lower = ent.text.lower()
                # Check if entity matches our skill list
                for skill in self.all_skills:
                    if skill.lower() in ent_lower or ent_lower in skill.lower():
                        tech_entities.append(skill)
                        break
        
        return list(set(tech_entities))
    
    def extract_skills_context(self, text: str) -> List[str]:
        """Extract skills using context analysis"""
        skill_context_keywords = [
            'experience in', 'skilled in', 'proficient in', 'expertise in',
            'worked with', 'familiar with', 'knowledge of', 'using',
            'technologies:', 'skills:', 'tools:', 'frameworks:',
            'programming languages:', 'databases:', 'platforms:'
        ]
        
        contextual_skills = []
        sentences = re.split(r'[.!?\n]', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(keyword in sentence_lower for keyword in skill_context_keywords):
                # Extract potential skills from this sentence
                for skill in self.all_skills:
                    if skill.lower() in sentence_lower:
                        contextual_skills.append(skill)
        
        return list(set(contextual_skills))
    
    def extract_skills_section_based(self, text: str) -> List[str]:
        """Extract skills from dedicated skills sections"""
        section_skills = []
        
        # Look for common skill section headers
        skill_section_patterns = [
            r'(?:technical\s+)?skills?:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'technologies?:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'programming\s+languages?:?\s*([^\n]+(?:\n[^\n]+)*)',
            r'tools?:?\s*([^\n]+(?:\n[^\n]+)*)'
        ]
        
        for pattern in skill_section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                section_text = match.group(1).lower()
                # Extract skills from this section
                for skill in self.all_skills:
                    if skill.lower() in section_text:
                        section_skills.append(skill)
        
        return list(set(section_skills))
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using TF-IDF (alternative to sentence-transformers)"""
        try:
            # Prepare documents
            documents = [text1, text2]
            
            # Fit and transform documents
            tfidf_matrix = self.tfidf.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            print(f"Error in semantic similarity calculation: {e}")
            return 0.0
    
    def extract_all_skills(self, text: str) -> Dict[str, List[str]]:
        """Combine all skill extraction methods"""
        # Apply different extraction methods
        keyword_skills = self.extract_skills_keyword_matching(text)
        ner_skills = self.extract_skills_ner(text)
        context_skills = self.extract_skills_context(text)
        section_skills = self.extract_skills_section_based(text)
        
        # Combine and deduplicate
        all_extracted_skills = list(set(
            keyword_skills + ner_skills + context_skills + section_skills
        ))
        
        # Categorize skills
        categorized_skills = {category: [] for category in self.tech_skills.keys()}
        categorized_skills['other'] = []
        
        for skill in all_extracted_skills:
            categorized = False
            for category, skills_list in self.tech_skills.items():
                if skill.lower() in [s.lower() for s in skills_list]:
                    categorized_skills[category].append(skill)
                    categorized = True
                    break
            
            if not categorized:
                categorized_skills['other'].append(skill)
        
        return categorized_skills
    
    def get_skill_suggestions(self, extracted_skills: List[str], job_requirements: List[str]) -> List[str]:
        """Suggest additional skills based on job requirements"""
        missing_skills = []
        
        extracted_lower = [skill.lower() for skill in extracted_skills]
        
        for req_skill in job_requirements:
            if req_skill.lower() not in extracted_lower:
                missing_skills.append(req_skill)
        
        return missing_skills
    
    def calculate_skill_coverage(self, candidate_skills: List[str], job_requirements: List[str]) -> float:
        """Calculate what percentage of job requirements are covered by candidate skills"""
        if not job_requirements:
            return 1.0
        
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        matched_count = 0
        
        for req_skill in job_requirements:
            if req_skill.lower() in candidate_skills_lower:
                matched_count += 1
        
        return matched_count / len(job_requirements)