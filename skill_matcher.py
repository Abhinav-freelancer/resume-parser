import re
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from dataclasses import dataclass
import spacy
from sentence_transformers import SentenceTransformer, util


@dataclass
class MatchResult:
    """Data structure for matching results"""
    candidate_id: str
    job_id: str
    overall_score: float
    skill_match_score: float
    text_similarity_score: float
    matched_skills: Dict[str, float]
    missing_skills: List[str]
    recommendation: str


class SkillMatchingMLModel:
    """
    Core ML Model for Resume-Job Skill Matching
    Integrates with API data for automated candidate screening
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        # Load NLP model
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            print(f"Warning: {spacy_model} not found. Install with: python -m spacy download {spacy_model}")
            self.nlp = None

        # TF-IDF kept (optional, not used for similarity now but can reuse later)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )

        # Semantic embeddings model (Sentence-BERT)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Skill synonyms for better matching
        self.skill_synonyms = {
            'python': ['python', 'python programming', 'python dev', 'python development'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs', 'node js'],
            'java': ['java', 'java programming', 'java development'],
            'machine learning': ['ml', 'machine learning', 'artificial intelligence', 'ai', 'deep learning'],
            'data science': ['data science', 'data analysis', 'data analytics', 'statistics'],
            'sql': ['sql', 'mysql', 'postgresql', 'sqlite', 'database'],
            'aws': ['aws', 'amazon web services', 'cloud computing', 'ec2', 's3'],
            'docker': ['docker', 'containerization', 'containers'],
            'kubernetes': ['kubernetes', 'k8s', 'container orchestration'],
            'react': ['react', 'reactjs', 'react.js'],
            'angular': ['angular', 'angularjs'],
            'django': ['django', 'django framework'],
            'flask': ['flask', 'flask framework'],
            'git': ['git', 'version control', 'github', 'gitlab']
        }

        # Common technical skills dictionary
        self.technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'scala', 'kotlin'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'
            ],
            'data_science': [
                'machine learning', 'data science', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'
            ]
        }

    def extract_skills_from_text(self, text: str) -> List[str]:
        """
        Extract skills from text using NLP and pattern matching
        """
        if not text:
            return []

        text_lower = text.lower()
        extracted_skills = set()

        # Extract using technical skills dictionary
        for category, skills in self.technical_skills.items():
            for skill in skills:
                if skill in text_lower:
                    extracted_skills.add(skill)

        # Use spaCy for additional entity extraction if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT'] and len(ent.text) < 30:
                    skill_candidate = ent.text.lower()
                    for category, skills in self.technical_skills.items():
                        if skill_candidate in skills or any(skill_candidate in skill for skill in skills):
                            extracted_skills.add(skill_candidate)

        # Pattern-based extraction for common formats
        patterns = [
            r'\b(?:expertise|experience|skilled|proficient)\s+(?:in|with)\s+([^.!?]+)',
            r'\b(?:technologies|tools|languages):\s*([^.!?]+)',
            r'\b(?:programming|coding)\s+(?:languages?|skills?):\s*([^.!?]+)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skills_text = match.group(1)
                skill_parts = re.split(r'[,;|&\n]+', skills_text)
                for part in skill_parts:
                    part = part.strip()
                    if len(part) > 2 and len(part) < 30:
                        extracted_skills.add(part)

        return list(extracted_skills)

    def normalize_skills(self, skills: List[str]) -> List[str]:
        """
        Normalize skills using synonym dictionary
        """
        normalized = set()

        for skill in skills:
            skill_lower = skill.lower().strip()
            found_match = False

            for main_skill, synonyms in self.skill_synonyms.items():
                if skill_lower in [s.lower() for s in synonyms]:
                    normalized.add(main_skill)
                    found_match = True
                    break

            if not found_match:
                cleaned_skill = re.sub(r'[^\w\s+#.-]', '', skill_lower)
                if len(cleaned_skill) > 2:
                    normalized.add(cleaned_skill)

        return list(normalized)

    def calculate_skill_similarity(self, candidate_skills: List[str], job_skills: List[str]) -> Tuple[float, Dict[str, float]]:
        """
        Calculate similarity between candidate skills and job requirements
        """
        if not candidate_skills or not job_skills:
            return 0.0, {}

        candidate_norm = self.normalize_skills(candidate_skills)
        job_norm = self.normalize_skills(job_skills)

        if not candidate_norm or not job_norm:
            return 0.0, {}

        skill_matches = {}
        total_score = 0

        for job_skill in job_norm:
            best_match = 0
            for candidate_skill in candidate_norm:
                if job_skill == candidate_skill:
                    score = 1.0
                else:
                    job_words = set(job_skill.split())
                    cand_words = set(candidate_skill.split())
                    if job_words and cand_words:
                        intersection = len(job_words.intersection(cand_words))
                        union = len(job_words.union(cand_words))
                        score = intersection / union if union > 0 else 0
                    else:
                        score = 0
                best_match = max(best_match, score)

            skill_matches[job_skill] = best_match
            total_score += best_match

        overall_skill_score = total_score / len(job_norm) if job_norm else 0
        return overall_skill_score, skill_matches

    def calculate_text_similarity(self, resume_text: str, job_description: str) -> float:
        """
        Calculate semantic similarity using Sentence-BERT embeddings
        """
        if not resume_text or not job_description:
            return 0.0
        try:
            emb_resume = self.embedding_model.encode(resume_text, convert_to_tensor=True)
            emb_job = self.embedding_model.encode(job_description, convert_to_tensor=True)
            return float(util.cos_sim(emb_resume, emb_job).item())
        except Exception as e:
            print(f"Error calculating semantic similarity: {e}")
            return 0.0

    def predict_match(self, resume_text: str, job_description: str,
                      job_required_skills: List[str], candidate_id: str = "unknown",
                      job_id: str = "unknown") -> MatchResult:
        """
        Main prediction method - returns match score and recommendation
        """
        candidate_skills = self.extract_skills_from_text(resume_text)
        skill_score, skill_matches = self.calculate_skill_similarity(candidate_skills, job_required_skills)
        text_similarity = self.calculate_text_similarity(resume_text, job_description)

        overall_score = 0.7 * skill_score + 0.3 * text_similarity

        candidate_norm = self.normalize_skills(candidate_skills)
        job_norm = self.normalize_skills(job_required_skills)
        missing_skills = [skill for skill in job_norm if skill not in candidate_norm]

        if overall_score >= 0.8:
            recommendation = "Highly Recommended"
        elif overall_score >= 0.6:
            recommendation = "Recommended"
        elif overall_score >= 0.4:
            recommendation = "Consider with Interview"
        else:
            recommendation = "Not Recommended"

        return MatchResult(
            candidate_id=candidate_id,
            job_id=job_id,
            overall_score=round(overall_score, 3),
            skill_match_score=round(skill_score, 3),
            text_similarity_score=round(text_similarity, 3),
            matched_skills=skill_matches,
            missing_skills=missing_skills,
            recommendation=recommendation
        )

    def batch_predict(self, candidates_data: List[Dict], job_data: Dict) -> List[MatchResult]:
        results = []
        for candidate in candidates_data:
            result = self.predict_match(
                resume_text=candidate.get("resume_text", ""),
                job_description=job_data.get("description", ""),
                job_required_skills=job_data.get("required_skills", []),
                candidate_id=candidate.get("id", "unknown"),
                job_id=job_data.get("id", "unknown")
            )
            results.append(result)
        results.sort(key=lambda x: x.overall_score, reverse=True)
        return results

    def get_top_candidates(self, results: List[MatchResult], top_n: int = 10) -> List[Dict]:
        top_results = results[:top_n]
        formatted_results = []
        for result in top_results:
            formatted_results.append({
                "candidate_id": result.candidate_id,
                "job_id": result.job_id,
                "overall_score": result.overall_score,
                "skill_match_score": result.skill_match_score,
                "text_similarity_score": result.text_similarity_score,
                "recommendation": result.recommendation,
                "matched_skills": result.matched_skills,
                "missing_skills": result.missing_skills
            })
        return formatted_results


def run_match(resume_text: str, job_description: str, job_required_skills: list):
    """
    Run skill-job matching for a single resume and job.
    """
    # Initialize the ML model
    model = SkillMatchingMLModel()

    # Get prediction
    result = model.predict_match(
        resume_text=resume_text,
        job_description=job_description,
        job_required_skills=job_required_skills,
        candidate_id="candidate_001",
        job_id="job_001"
    )

    # Print results
    print("\n===== MATCHING RESULT =====")
    print(f"Overall Score: {result.overall_score}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Skill Match Score: {result.skill_match_score}")
    print(f"Text Similarity Score: {result.text_similarity_score}")
    print(f"Matched Skills: {result.matched_skills}")
    print(f"Missing Skills: {result.missing_skills}")

    return result


# Usage Example
if __name__ == "__main__":
    # Example usage with parameters
    resume = """
    John Doe
    Software Engineer with 5 years of experience in Python, Django, and AWS.
    Skilled in machine learning, data science, and SQL databases.
    Experience with Docker, Kubernetes, and cloud computing.
    """

    job_description = """
    Looking for a Senior Python Developer with expertise in Django framework.
    Must have experience with AWS cloud services and Docker containerization.
    Knowledge of machine learning and SQL is required.
    """

    required_skills = ["python", "django", "aws", "docker", "machine learning", "sql"]

    run_match(resume, job_description, required_skills)
