  
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import pandas as pd
import io

from utils.resume_parser import ResumeParser
from utils.skill_extractor import SkillExtractor
from utils.matcher import JobMatcher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Initialize components
resume_parser = ResumeParser()
skill_extractor = SkillExtractor()
job_matcher = JobMatcher()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('database/candidates.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            location TEXT,
            experience_years INTEGER,
            skills TEXT,
            education TEXT,
            resume_path TEXT,
            uploaded_at TIMESTAMP,
            raw_text TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            description TEXT,
            required_skills TEXT,
            required_experience INTEGER,
            education_requirements TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            job_id INTEGER,
            overall_score REAL,
            skill_score REAL,
            experience_score REAL,
            education_score REAL,
            semantic_score REAL,
            matched_skills TEXT,
            missing_skills TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id),
            FOREIGN KEY (job_id) REFERENCES job_descriptions (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        # Ensure upload directory exists
        resume_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')
        os.makedirs(resume_dir, exist_ok=True)
        
        file_path = os.path.join(resume_dir, filename)
        file.save(file_path)
        
        try:
            # Parse resume
            file_extension = filename.rsplit('.', 1)[1].lower()
            parsed_data = resume_parser.parse_resume(file_path, file_extension)
            
            # Extract skills
            skills = skill_extractor.extract_all_skills(parsed_data['raw_text'])
            parsed_data['skills'] = skills
            
            # Save to database
            conn = sqlite3.connect('database/candidates.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO candidates 
                (name, email, phone, location, experience_years, skills, education, resume_path, uploaded_at, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form.get('name', 'Unknown'),
                parsed_data['contact_info'].get('email'),
                parsed_data['contact_info'].get('phone'),
                parsed_data['contact_info'].get('location'),
                parsed_data['experience_years'],
                json.dumps(skills),
                json.dumps(parsed_data['education']),
                file_path,
                datetime.now(),
                parsed_data['raw_text']
            ))
            
            candidate_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'candidate_id': candidate_id,
                'parsed_data': {
                    'contact_info': parsed_data['contact_info'],
                    'experience_years': parsed_data['experience_years'],
                    'skills': skills,
                    'education': parsed_data['education']
                }
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing resume: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/upload_job_description', methods=['POST'])
def upload_job_description():
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database/candidates.db')
        cursor = conn.cursor()
        
        # Extract skills from job description
        jd_skills = skill_extractor.extract_all_skills(data['description'])
        all_jd_skills = []
        for category_skills in jd_skills.values():
            all_jd_skills.extend(category_skills)
        
        cursor.execute('''
            INSERT INTO job_descriptions 
            (title, company, description, required_skills, required_experience, education_requirements, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data['company'],
            data['description'],
            json.dumps(all_jd_skills),
            data.get('required_experience', 0),
            json.dumps(data.get('education_requirements', [])),
            datetime.now()
        ))
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'extracted_skills': all_jd_skills
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing job description: {str(e)}'}), 500

@app.route('/match_candidates/<int:job_id>')
def match_candidates(job_id):
    try:
        conn = sqlite3.connect(os.path.join('database', 'candidates.db'))
        cursor = conn.cursor()
        
        # Get job description
        cursor.execute('SELECT * FROM job_descriptions WHERE id = ?', (job_id,))
        job_data = cursor.fetchone()
        
        if not job_data:
            return jsonify({'error': 'Job description not found'}), 404
        
        # Convert job tuple to dictionary (FIXED)
        job_dict = {
            'id': job_data[0],
            'title': job_data[1],
            'company': job_data[2],
            'description': job_data[3],
            'required_skills': json.loads(job_data[4]) if job_data[4] else [],
            'required_experience': job_data[5],
            'education_requirements': json.loads(job_data[6]) if job_data[6] else []
        }
        
        # Get all candidates
        cursor.execute('SELECT * FROM candidates')
        candidates = cursor.fetchall()
        
        matched_candidates = []
        
        for candidate in candidates:
            # Convert candidate tuple to dictionary (FIXED)
            candidate_dict = {
                'id': candidate[0],
                'name': candidate[1],
                'email': candidate[2],
                'phone': candidate[3],
                'location': candidate[4],
                'experience_years': candidate[5],
                'skills': json.loads(candidate[6]) if candidate[6] else {},
                'education': json.loads(candidate[7]) if candidate[7] else [],
                'raw_text': candidate[10] if len(candidate) > 10 else ''
            }
            
            # Calculate match score
            match_result = job_matcher.calculate_overall_match(candidate_dict, job_dict)
            
            # Save match result to database
            cursor.execute('''
                INSERT INTO matches 
                (candidate_id, job_id, overall_score, skill_score, experience_score, education_score, 
                semantic_score, matched_skills, missing_skills, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                candidate[0],  # Use index instead of key
                job_id,
                match_result['overall_score'],
                match_result['skill_match']['score'] * 100,
                match_result['experience_score'],
                match_result['education_score'],
                match_result['semantic_score'],
                json.dumps(match_result['skill_match']['matched_skills']),
                json.dumps(match_result['skill_match']['missing_skills']),
                datetime.now()
            ))
            
            matched_candidates.append({
                'candidate': candidate_dict,
                'match_result': match_result
            })
        
        # Sort by overall score
        matched_candidates.sort(key=lambda x: x['match_result']['overall_score'], reverse=True)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'job': job_dict,
            'matches': matched_candidates
        })
        
    except Exception as e:
        return jsonify({'error': f'Error matching candidates: {str(e)}'}), 500
    
@app.route('/dashboard')
def dashboard():
    try:
        conn = sqlite3.connect(os.path.join('database', 'candidates.db'))
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM candidates')
        total_candidates = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM job_descriptions')
        total_jobs = cursor.fetchone()[0]
        
        # Get recent matches
        cursor.execute('''
            SELECT m.*, c.name, c.email, j.title, j.company
            FROM matches m
            JOIN candidates c ON m.candidate_id = c.id
            JOIN job_descriptions j ON m.job_id = j.id
            ORDER BY m.created_at DESC
            LIMIT 10
        ''')
        recent_matches = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', 
                             total_candidates=total_candidates,
                             total_jobs=total_jobs,
                             recent_matches=recent_matches)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard.html', 
                             total_candidates=0,
                             total_jobs=0,
                             recent_matches=[],
                             error=str(e))

@app.route('/download_results/<int:job_id>')
def download_results(job_id):
    try:
        conn = sqlite3.connect('database/candidates.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.name, c.email, c.phone, c.location, c.experience_years,
                   m.overall_score, m.skill_score, m.experience_score, m.education_score
            FROM matches m
            JOIN candidates c ON m.candidate_id = c.id
            WHERE m.job_id = ?
            ORDER BY m.overall_score DESC
        ''', (job_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        # Create DataFrame
        df = pd.DataFrame(results, columns=[
            'Name', 'Email', 'Phone', 'Location', 'Experience Years',
            'Overall Score', 'Skill Score', 'Experience Score', 'Education Score'
        ])
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Create a BytesIO object for sending file
        mem = io.BytesIO()
        mem.write(output.getvalue().encode())
        mem.seek(0)
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=f'matching_results_job_{job_id}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error generating CSV: {str(e)}'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads/resumes', exist_ok=True)
    os.makedirs('uploads/job_descriptions', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    
    # Initialize database
    init_db()
    
    app.run(debug=True)