"""
Resume Parser Service
Extracts education, experience, and skills from resume files
Supports: PDF, DOCX, TXT
"""

import os
import re
from typing import Dict, Optional, Tuple
from pathlib import Path


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from resume file based on file type.
    Supports: PDF, DOCX, TXT
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    file_ext = Path(file_path).suffix.lower()

    # ── TXT files ──────────────────────────────────────────────────
    if file_ext == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT: {e}")
            return ""

    # ── PDF files ──────────────────────────────────────────────────
    elif file_ext == '.pdf':
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except ImportError:
            print("pdfplumber not installed. Install with: pip install pdfplumber")
            return ""
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    # ── DOCX files ─────────────────────────────────────────────────
    elif file_ext in ['.docx', '.doc']:
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            print("python-docx not installed. Install with: pip install python-docx")
            return ""
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""

    else:
        raise ValueError(f"Unsupported file format: {file_ext}")


def extract_education(text: str) -> str:
    """
    Extract education section from resume text.
    Looks for common education keywords.
    """
    lines = text.split('\n')
    education_lines = []
    in_education = False
    
    for i, line in enumerate(lines):
        lower_line = line.lower()
        
        # Start education section
        if any(keyword in lower_line for keyword in ['education', 'academic', 'degree', 'university', 'college', 'bachelor', 'master', 'phd']):
            in_education = True
            continue
        
        # End education section
        if in_education and any(keyword in lower_line for keyword in ['experience', 'skills', 'projects', 'certifications', 'summary']):
            in_education = False
            break
        
        # Collect education lines
        if in_education and line.strip():
            education_lines.append(line.strip())
    
    return '\n'.join(education_lines[:10]) if education_lines else "No education information found"


def extract_experience(text: str) -> str:
    """
    Extract experience/work history from resume text.
    """
    lines = text.split('\n')
    experience_lines = []
    in_experience = False
    
    for i, line in enumerate(lines):
        lower_line = line.lower()
        
        # Start experience section
        if any(keyword in lower_line for keyword in ['experience', 'work history', 'professional experience', 'employment']):
            in_experience = True
            continue
        
        # End experience section
        if in_experience and any(keyword in lower_line for keyword in ['education', 'skills', 'projects', 'certifications', 'summary']):
            in_experience = False
            break
        
        # Collect experience lines
        if in_experience and line.strip():
            experience_lines.append(line.strip())
    
    return '\n'.join(experience_lines[:15]) if experience_lines else "No experience information found"


def extract_skills(text: str) -> str:
    """
    Extract skills from resume text.
    Looks for skills section and common skill keywords.
    """
    lines = text.split('\n')
    skills_lines = []
    in_skills = False
    
    for i, line in enumerate(lines):
        lower_line = line.lower()
        
        # Start skills section
        if 'skills' in lower_line or 'technical skills' in lower_line or 'competencies' in lower_line:
            in_skills = True
            continue
        
        # End skills section
        if in_skills and any(keyword in lower_line for keyword in ['experience', 'education', 'projects', 'certifications', 'summary']):
            in_skills = False
            break
        
        # Collect skills lines
        if in_skills and line.strip() and len(line.strip()) > 2:
            skills_lines.append(line.strip())
    
    # If no dedicated skills section, extract common technical keywords
    if not skills_lines:
        tech_keywords = [
            'python', 'javascript', 'java', 'c++', 'sql', 'react', 'angular', 'vue', 'node', 'django',
            'flask', 'fastapi', 'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'git', 'linux', 'windows',
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'kafka', 'rest', 'graphql'
        ]
        found_skills = []
        for keyword in tech_keywords:
            if keyword in text.lower():
                found_skills.append(keyword.title())
        return ', '.join(found_skills) if found_skills else "No specific skills identified"
    
    return ', '.join(skills_lines[:10])


def parse_resume(file_path: str) -> Dict[str, str]:
    """
    Parse resume file and extract education, experience, and skills.
    
    Returns:
        {
            "education": "...",
            "experience": "...",
            "skills": "...",
            "raw_text": "..."
        }
    """
    try:
        # Extract text from file
        raw_text = extract_text_from_file(file_path)
        
        if not raw_text or not raw_text.strip():
            return {
                "education": "Could not extract resume text",
                "experience": "Could not extract resume text",
                "skills": "Could not extract resume text",
                "raw_text": ""
            }
        
        # Parse sections
        education = extract_education(raw_text)
        experience = extract_experience(raw_text)
        skills = extract_skills(raw_text)
        
        return {
            "education": education,
            "experience": experience,
            "skills": skills,
            "raw_text": raw_text[:500]  # First 500 chars
        }
    
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return {
            "education": f"Error parsing resume: {str(e)}",
            "experience": "",
            "skills": "",
            "raw_text": ""
        }


# ── Quick test ─────────────────────────────────────────────────
if __name__ == "__main__":
    # Test with a sample file
    test_file = "uploads/sample_resume.pdf"
    if os.path.exists(test_file):
        result = parse_resume(test_file)
        print("Education:", result['education'])
        print("\nExperience:", result['experience'])
        print("\nSkills:", result['skills'])
    else:
        print(f"Test file not found: {test_file}")