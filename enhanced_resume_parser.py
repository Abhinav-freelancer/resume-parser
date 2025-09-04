import re
import spacy
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class EnhancedResumeParser:
    def __init__(self):
        try:
            # Load spaCy model for NLP processing
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Installing...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # Define skill taxonomy
        self.skill_taxonomy = {
            "programming_languages": [
                "Python", "Java", "JavaScript", "C++", "C#", "Ruby", "PHP", "Go", "Rust",
                "TypeScript", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl"
            ],
            "web_technologies": [
                "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express.js",
                "Django", "Flask", "Spring Boot", "ASP.NET", "Laravel", "Ruby on Rails"
            ],
            "databases": [
                "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "DynamoDB",
                "Oracle", "SQL Server", "SQLite", "Elasticsearch"
            ],
            "cloud_platforms": [
                "AWS", "Azure", "Google Cloud", "Heroku", "DigitalOcean", "Linode"
            ],
            "devops_tools": [
                "Docker", "Kubernetes", "Jenkins", "GitLab CI", "Travis CI", "CircleCI",
                "Terraform", "Ansible", "Puppet", "Chef"
            ],
            "version_control": [
                "Git", "SVN", "Mercurial"
            ],
            "soft_skills": [
                "Communication", "Leadership", "Problem Solving", "Teamwork", "Agile",
                "Scrum", "Project Management", "Time Management"
            ]
        }

        # Flatten skills for easier matching
        self.all_skills = []
        for category in self.skill_taxonomy.values():
            self.all_skills.extend(category)

    async def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Parse resume from file path and extract structured information"""
        try:
            # Extract text from file
            text = self._extract_text_from_file(file_path)

            if not text:
                return self._create_empty_result()

            # Parse different sections
            parsed_data = {
                "name": self._extract_name(text),
                "email": self._extract_email(text),
                "phone": self._extract_phone(text),
                "skills": self._extract_skills(text),
                "experience": self._extract_experience(text),
                "education": self._extract_education(text),
                "work_history": self._extract_work_history(text),
                "raw_text": text,
                "confidence_scores": self._calculate_confidence_scores(text),
                "location": self._extract_location(text),
                "salary_expectation": self._extract_salary_expectation(text)
            }

            logger.info(f"Successfully parsed resume: {parsed_data.get('name', 'Unknown')}")
            return parsed_data

        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            return self._create_empty_result()

    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file"""
        try:
            if file_path.lower().endswith('.pdf'):
                return self._extract_pdf_text(file_path)
            elif file_path.lower().endswith(('.docx', '.doc')):
                return self._extract_docx_text(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            return ""

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            logger.warning("PyPDF2 not installed. PDF parsing unavailable.")
            return ""
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            logger.warning("python-docx not installed. DOCX parsing unavailable.")
            return ""
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return ""

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume text"""
        # Look for name patterns at the beginning of the document
        lines = text.split('\n')[:10]  # Check first 10 lines

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip common headers
            if any(header in line.upper() for header in ['RESUME', 'CV', 'CURRICULUM VITAE']):
                continue

            # Look for name-like patterns (2-3 words, capitalized)
            words = line.split()
            if 1 <= len(words) <= 3:
                # Check if words look like names (capitalized, not all caps)
                if all(word[0].isupper() for word in words if word):
                    # Avoid common job titles or sections
                    if not any(title in line.upper() for title in
                             ['SOFTWARE ENGINEER', 'DEVELOPER', 'MANAGER', 'DIRECTOR', 'SENIOR']):
                        return line

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from resume text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0].lower() if matches else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume text"""
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{10,11}'
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]

        return None

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        found_skills = []
        text_lower = text.lower()

        for skill in self.all_skills:
            skill_lower = skill.lower()
            if skill_lower in text_lower:
                # Check for word boundaries to avoid partial matches
                if re.search(r'\b' + re.escape(skill_lower) + r'\b', text_lower):
                    found_skills.append(skill)

        return list(set(found_skills))  # Remove duplicates

    def _extract_experience(self, text: str) -> Optional[str]:
        """Extract years of experience"""
        exp_patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience:?\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s+(?:of\s+)?experience'
        ]

        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)}+ years"

        # Try to infer from work history
        work_history = self._extract_work_history(text)
        if work_history:
            # Calculate approximate experience from work history
            current_year = datetime.now().year
            start_years = []

            for job in work_history:
                if 'start_date' in job:
                    # Extract year from date string
                    year_match = re.search(r'\b(19|20)\d{2}\b', job['start_date'])
                    if year_match:
                        start_years.append(int(year_match.group(0)))

            if start_years:
                earliest_year = min(start_years)
                experience_years = current_year - earliest_year
                if experience_years > 0:
                    return f"{experience_years}+ years"

        return None

    def _extract_education(self, text: str) -> Optional[str]:
        """Extract education information"""
        education_keywords = ['education', 'degree', 'university', 'college', 'school', 'bachelor', 'master', 'phd']

        # Find education section
        lines = text.split('\n')
        education_section = []
        in_education = False

        for line in lines:
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in education_keywords):
                in_education = True
                education_section.append(line)
            elif in_education and line.strip():
                # Continue collecting education info until next major section
                if any(section in line_lower for section in ['experience', 'work', 'skills', 'projects']):
                    break
                education_section.append(line)
            elif in_education and not line.strip():
                # Stop at empty line after education section
                if education_section:
                    break

        if education_section:
            return ' '.join(education_section[:3])  # Take first 3 lines

        return None

    def _extract_work_history(self, text: str) -> List[Dict[str, Any]]:
        """Extract work history from resume"""
        work_history = []
        lines = text.split('\n')

        # Look for work/experience section
        experience_keywords = ['experience', 'work history', 'professional experience', 'employment']

        in_experience = False
        current_job = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # Check if we're entering experience section
            if any(keyword in line_lower for keyword in experience_keywords):
                in_experience = True
                continue

            if in_experience:
                # Look for job title patterns
                if re.match(r'^[A-Z][^|]*\|', line):  # Company | Title format
                    if current_job:
                        work_history.append(current_job)
                    parts = line.split('|')
                    current_job = {
                        'company': parts[0].strip(),
                        'title': parts[1].strip() if len(parts) > 1 else '',
                        'description': []
                    }
                elif re.match(r'^[A-Z][^,]*,\s*[A-Z]', line):  # Title, Company format
                    if current_job:
                        work_history.append(current_job)
                    parts = line.split(',')
                    current_job = {
                        'title': parts[0].strip(),
                        'company': parts[1].strip() if len(parts) > 1 else '',
                        'description': []
                    }
                elif current_job and line.startswith('•'):
                    # Bullet point description
                    current_job['description'].append(line[1:].strip())
                elif current_job and len(line) > 20:
                    # Continuation of description
                    if 'description' not in current_job:
                        current_job['description'] = []
                    current_job['description'].append(line)

        # Add the last job
        if current_job:
            work_history.append(current_job)

        return work_history[:5]  # Limit to 5 most recent jobs

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location information"""
        location_patterns = [
            r'Location:?\s*([A-Za-z\s,]+)',
            r'([A-Za-z\s]+,\s*[A-Z]{2})',
            r'([A-Za-z\s]+,\s*California|New York|Texas|Florida)'
        ]

        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_salary_expectation(self, text: str) -> Optional[str]:
        """Extract salary expectation"""
        salary_patterns = [
            r'Salary:?\s*\$?([\d,]+(?:\.\d+)?(?:k?|K?))',
            r'Expected Salary:?\s*\$?([\d,]+(?:\.\d+)?(?:k?|K?))',
            r'Compensation:?\s*\$?([\d,]+(?:\.\d+)?(?:k?|K?))'
        ]

        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _calculate_confidence_scores(self, text: str) -> Dict[str, float]:
        """Calculate confidence scores for extracted information"""
        scores = {}

        # Name confidence
        if self._extract_name(text):
            scores['name'] = 0.9
        else:
            scores['name'] = 0.1

        # Email confidence
        if self._extract_email(text):
            scores['email'] = 0.95
        else:
            scores['email'] = 0.0

        # Phone confidence
        if self._extract_phone(text):
            scores['phone'] = 0.85
        else:
            scores['phone'] = 0.0

        # Skills confidence based on number found
        skills = self._extract_skills(text)
        if skills:
            scores['skills'] = min(0.9, len(skills) / 10)  # Max confidence at 10 skills
        else:
            scores['skills'] = 0.0

        # Overall confidence
        scores['overall'] = sum(scores.values()) / len(scores)

        return scores

    def _create_empty_result(self) -> Dict[str, Any]:
        """Create empty result structure"""
        return {
            "name": None,
            "email": None,
            "phone": None,
            "skills": [],
            "experience": None,
            "education": None,
            "work_history": [],
            "raw_text": "",
            "confidence_scores": {"overall": 0.0},
            "location": None,
            "salary_expectation": None
        }
