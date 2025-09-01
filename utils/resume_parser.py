  
import pdfplumber
from docx import Document
import re
import spacy
from typing import Dict, List, Any

class ResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF resume"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """Extract text from DOCX resume"""
        text = ""
        try:
            doc = Document(docx_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract email, phone, and location"""
        contact_info = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['email'] = emails[0] if emails else None
        
        # Phone extraction
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        contact_info['phone'] = phones[0] if phones else None
        
        # Location extraction (basic)
        doc = self.nlp(text)
        locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
        contact_info['location'] = locations[0] if locations else None
        
        return contact_info
    
    def extract_experience_years(self, text: str) -> int:
        """Extract years of experience"""
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?experience',
        ]
        
        years = []
        for pattern in experience_patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(match) for match in matches])
        
        return max(years) if years else 0
    
    def extract_education(self, text: str) -> List[str]:
        """Extract education details"""
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'diploma',
            'btech', 'mtech', 'bsc', 'msc', 'ba', 'ma', 'mba',
            'engineering', 'computer science', 'information technology'
        ]
        
        education = []
        lines = text.lower().split('\n')
        
        for line in lines:
            for keyword in education_keywords:
                if keyword in line:
                    education.append(line.strip())
                    break
        
        return list(set(education))  # Remove duplicates
    
    def parse_resume(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Main parsing function"""
        if file_type.lower() == 'pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_type.lower() == 'docx':
            text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file type")
        
        contact_info = self.extract_contact_info(text)
        experience_years = self.extract_experience_years(text)
        education = self.extract_education(text)
        
        return {
            'raw_text': text,
            'contact_info': contact_info,
            'experience_years': experience_years,
            'education': education
        }