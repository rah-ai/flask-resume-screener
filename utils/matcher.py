from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Tuple
import re

class JobMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True,
            strip_accents='unicode'
        )
        
        # Skill importance weights (higher = more important)
        self.skill_weights = {
            'programming_languages': 1.0,
            'ai_ml': 0.9,
            'web_technologies': 0.8,
            'databases': 0.7,
            'cloud_platforms': 0.6,
            'tools': 0.5,
            'mobile_development': 0.8,
            'data_science': 0.9
        }
    
    def normalize_skill_name(self, skill: str) -> str:
        """Normalize skill names for better matching"""
        skill = skill.lower().strip()
        
        # Common abbreviations and variations
        skill_mapping = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'dl': 'deep learning',
            'cv': 'computer vision',
            'nlp': 'natural language processing',
            'aws': 'amazon web services',
            'gcp': 'google cloud platform',
            'k8s': 'kubernetes',
            'tf': 'tensorflow',
            'sklearn': 'scikit-learn',
            'cv2': 'opencv',
            'pd': 'pandas',
            'np': 'numpy'
        }
        
        return skill_mapping.get(skill, skill)
    
    def calculate_skill_match(self, resume_skills: List[str], jd_skills: List[str]) -> Dict:
        """Calculate skill-based matching score with advanced matching"""
        if not jd_skills:
            return {'score': 0, 'matched_skills': [], 'missing_skills': [], 'partial_matches': []}
        
        # Normalize skills
        resume_skills_norm = [self.normalize_skill_name(skill) for skill in resume_skills]
        jd_skills_norm = [self.normalize_skill_name(skill) for skill in jd_skills]
        
        matched_skills = []
        partial_matches = []
        
        for jd_skill in jd_skills_norm:
            exact_match = False
            
            # Exact match
            for resume_skill in resume_skills_norm:
                if jd_skill == resume_skill:
                    matched_skills.append(jd_skill)
                    exact_match = True
                    break
            
            # Partial match (for compound skills)
            if not exact_match:
                for resume_skill in resume_skills_norm:
                    # Check if skills contain each other or share common words
                    if (jd_skill in resume_skill or resume_skill in jd_skill or
                        self._calculate_word_overlap(jd_skill, resume_skill) > 0.5):
                        partial_matches.append({'jd_skill': jd_skill, 'resume_skill': resume_skill})
                        break
        
        # Calculate missing skills
        missing_skills = [skill for skill in jd_skills_norm 
                         if skill not in matched_skills and 
                         not any(match['jd_skill'] == skill for match in partial_matches)]
        
        # Calculate score with weights for exact and partial matches
        exact_score = len(matched_skills) / len(jd_skills_norm) if jd_skills_norm else 0
        partial_score = (len(partial_matches) * 0.5) / len(jd_skills_norm) if jd_skills_norm else 0
        total_score = min(1.0, exact_score + partial_score)  # Cap at 1.0
        
        return {
            'score': total_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'partial_matches': partial_matches,
            'exact_matches': len(matched_skills),
            'total_required': len(jd_skills_norm)
        }
    
    def _calculate_word_overlap(self, skill1: str, skill2: str) -> float:
        """Calculate word overlap between two skills"""
        words1 = set(skill1.split())
        words2 = set(skill2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def calculate_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate semantic similarity using TF-IDF"""
        try:
            # Clean and prepare texts
            resume_clean = self._clean_text(resume_text)
            jd_clean = self._clean_text(jd_text)
            
            if not resume_clean or not jd_clean:
                return 0.0
            
            # Create TF-IDF vectors
            documents = [resume_clean, jd_clean]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
            
        except Exception as e:
            print(f"Error in semantic similarity: {e}")
            return 0.0
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better semantic analysis"""
        if not text:
            return ""
        
        # Remove special characters but keep spaces
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Convert to lowercase
        cleaned = cleaned.lower().strip()
        
        return cleaned
    
    def calculate_experience_match(self, resume_exp: int, required_exp: int) -> float:
        """Calculate experience matching score with flexibility"""
        if required_exp == 0:
            return 1.0
        
        if resume_exp >= required_exp:
            # Bonus for exceeding requirements (but cap at 1.0)
            bonus = min(0.1, (resume_exp - required_exp) * 0.02)
            return min(1.0, 1.0 + bonus)
        elif resume_exp >= required_exp * 0.8:  # 80% of required experience
            return 0.9
        elif resume_exp >= required_exp * 0.6:  # 60% of required experience
            return 0.7
        elif resume_exp >= required_exp * 0.4:  # 40% of required experience
            return 0.5
        else:
            return max(0.2, resume_exp / required_exp)  # Minimum 20% for any experience
    
    def calculate_education_match(self, resume_education: List[str], jd_requirements: List[str]) -> float:
        """Calculate education matching score with degree level consideration"""
        if not jd_requirements:
            return 1.0
        
        if not resume_education:
            return 0.3  # Some credit for experience over education
        
        resume_edu_text = ' '.join(resume_education).lower()
        
        # Define education hierarchy
        education_levels = {
            'phd': 5, 'doctorate': 5, 'doctoral': 5,
            'master': 4, 'mba': 4, 'ms': 4, 'ma': 4, 'mtech': 4,
            'bachelor': 3, 'ba': 3, 'bs': 3, 'btech': 3, 'be': 3,
            'associate': 2, 'diploma': 2,
            'certificate': 1, 'certification': 1
        }
        
        # Find highest education level in resume
        resume_level = 0
        for edu_item in resume_education:
            edu_lower = edu_item.lower()
            for level_key, level_value in education_levels.items():
                if level_key in edu_lower:
                    resume_level = max(resume_level, level_value)
        
        # Calculate match score
        matches = 0
        total_requirements = len(jd_requirements)
        
        for requirement in jd_requirements:
            req_lower = requirement.lower()
            
            # Direct keyword match
            if any(keyword in resume_edu_text for keyword in req_lower.split()):
                matches += 1
            # Level-based matching
            else:
                required_level = 0
                for level_key, level_value in education_levels.items():
                    if level_key in req_lower:
                        required_level = max(required_level, level_value)
                
                if resume_level >= required_level and required_level > 0:
                    matches += 0.8  # Partial credit for meeting level requirement
        
        return min(1.0, matches / total_requirements) if total_requirements > 0 else 1.0
    
    def calculate_overall_match(self, resume_data: Dict, job_data: Dict) -> Dict:
        """Calculate comprehensive matching score with detailed breakdown"""
        # Extract skills from both resume and JD
        resume_skills = []
        if 'skills' in resume_data:
            for category, category_skills in resume_data['skills'].items():
                if isinstance(category_skills, list):
                    resume_skills.extend(category_skills)
        
        jd_skills = job_data.get('required_skills', [])
        
        # Calculate individual scores
        skill_match = self.calculate_skill_match(resume_skills, jd_skills)
        semantic_score = self.calculate_semantic_similarity(
            resume_data.get('raw_text', ''), 
            job_data.get('description', '')
        )
        experience_score = self.calculate_experience_match(
            resume_data.get('experience_years', 0),
            job_data.get('required_experience', 0)
        )
        education_score = self.calculate_education_match(
            resume_data.get('education', []),
            job_data.get('education_requirements', [])
        )
        
        # Dynamic weights based on job requirements
        weights = self._calculate_dynamic_weights(job_data)
        
        # Calculate weighted overall score
        overall_score = (
            skill_match['score'] * weights['skills'] +
            semantic_score * weights['semantic'] +
            experience_score * weights['experience'] +
            education_score * weights['education']
        )
        
        # Bonus for skill diversity (if candidate has more skills than required)
        diversity_bonus = min(0.05, len(resume_skills) / max(len(jd_skills), 1) - 1) if len(resume_skills) > len(jd_skills) else 0
        overall_score = min(1.0, overall_score + diversity_bonus)
        
        return {
            'overall_score': round(overall_score * 100, 2),  # Convert to percentage
            'skill_match': skill_match,
            'semantic_score': round(semantic_score * 100, 2),
            'experience_score': round(experience_score * 100, 2),
            'education_score': round(education_score * 100, 2),
            'diversity_bonus': round(diversity_bonus * 100, 2),
            'breakdown': weights,
            'detailed_analysis': {
                'total_resume_skills': len(resume_skills),
                'required_skills': len(jd_skills),
                'exact_skill_matches': skill_match.get('exact_matches', 0),
                'partial_skill_matches': len(skill_match.get('partial_matches', [])),
                'skill_coverage_percentage': round(skill_match['score'] * 100, 1)
            }
        }
    
    def _calculate_dynamic_weights(self, job_data: Dict) -> Dict:
        """Calculate dynamic weights based on job requirements"""
        base_weights = {
            'skills': 0.4,
            'semantic': 0.3,
            'experience': 0.2,
            'education': 0.1
        }
        
        # Adjust weights based on job characteristics
        jd_text = job_data.get('description', '').lower()
        required_exp = job_data.get('required_experience', 0)
        
        # If it's a senior position, increase experience weight
        if required_exp > 5 or any(keyword in jd_text for keyword in ['senior', 'lead', 'principal', 'architect']):
            base_weights['experience'] += 0.1
            base_weights['skills'] -= 0.05
            base_weights['semantic'] -= 0.05
        
        # If it's an entry-level position, decrease experience weight
        elif required_exp <= 2 or any(keyword in jd_text for keyword in ['junior', 'entry', 'graduate', 'intern']):
            base_weights['experience'] -= 0.1
            base_weights['skills'] += 0.05
            base_weights['education'] += 0.05
        
        # If education is heavily emphasized, increase education weight
        if any(keyword in jd_text for keyword in ['degree required', 'masters preferred', 'phd', 'academic']):
            base_weights['education'] += 0.1
            base_weights['semantic'] -= 0.1
        
        return base_weights
    
    def generate_match_explanation(self, match_result: Dict) -> str:
        """Generate human-readable explanation of the match"""
        score = match_result['overall_score']
        skill_match = match_result['skill_match']
        
        if score >= 80:
            explanation = "Excellent match! "
        elif score >= 60:
            explanation = "Good match with some areas for development. "
        else:
            explanation = "Fair match with significant skill gaps. "
        
        explanation += f"The candidate matches {skill_match['exact_matches']} out of {skill_match['total_required']} required skills exactly"
        
        if skill_match.get('partial_matches'):
            explanation += f" and has partial matches for {len(skill_match['partial_matches'])} additional skills"
        
        explanation += "."
        
        return explanation