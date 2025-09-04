import re
from typing import List, Dict, Any, Tuple
import logging
from collections import Counter
import math

logger = logging.getLogger(__name__)

class EnhancedSkillMatcher:
    def __init__(self):
        # Define skill categories and their importance weights
        self.skill_weights = {
            "programming_languages": 1.0,
            "web_technologies": 0.9,
            "databases": 0.8,
            "cloud_platforms": 0.9,
            "devops_tools": 0.8,
            "version_control": 0.6,
            "soft_skills": 0.7
        }

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

        # Experience level mappings
        self.experience_levels = {
            "Entry": 0,
            "Junior": 1,
            "Mid-Level": 2,
            "Senior": 3,
            "Lead": 4,
            "Principal": 5
        }

    def calculate_enhanced_match(self, candidate_skills: List[str], job_skills: List[str],
                               candidate_experience: str = None, job_experience_level: str = None) -> Dict[str, Any]:
        """Calculate enhanced skill match with detailed analysis"""
        try:
            # Basic skill matching
            matched_skills, missing_skills = self._find_skill_matches(candidate_skills, job_skills)

            # Calculate base score
            base_score = self._calculate_base_score(matched_skills, job_skills)

            # Experience matching
            experience_score = self._calculate_experience_score(candidate_experience, job_experience_level)

            # Skill category analysis
            category_analysis = self._analyze_skill_categories(candidate_skills, job_skills)

            # Overall score with weights
            overall_score = self._calculate_overall_score(base_score, experience_score, category_analysis)

            # Generate explainability details
            details = {
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "skill_match_ratio": len(matched_skills) / len(job_skills) if job_skills else 0,
                "category_breakdown": category_analysis,
                "experience_match": experience_score > 0.7,
                "recommendations": self._generate_recommendations(missing_skills, category_analysis)
            }

            result = {
                "score": round(overall_score, 2),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "details": details
            }

            logger.info(f"Enhanced match calculated: {result['score']}% match")
            return result

        except Exception as e:
            logger.error(f"Error calculating enhanced match: {str(e)}")
            return {
                "score": 0.0,
                "matched_skills": [],
                "missing_skills": job_skills,
                "details": {"error": str(e)}
            }

    def _find_skill_matches(self, candidate_skills: List[str], job_skills: List[str]) -> Tuple[List[str], List[str]]:
        """Find matching and missing skills"""
        candidate_skills_lower = [skill.lower() for skill in candidate_skills]
        job_skills_lower = [skill.lower() for skill in job_skills]

        matched_skills = []
        missing_skills = []

        for job_skill in job_skills:
            job_skill_lower = job_skill.lower()
            found_match = False

            for candidate_skill in candidate_skills:
                candidate_skill_lower = candidate_skill.lower()

                # Exact match
                if job_skill_lower == candidate_skill_lower:
                    matched_skills.append(job_skill)
                    found_match = True
                    break

                # Partial match (contains)
                if job_skill_lower in candidate_skill_lower or candidate_skill_lower in job_skill_lower:
                    matched_skills.append(job_skill)
                    found_match = True
                    break

            if not found_match:
                missing_skills.append(job_skill)

        return matched_skills, missing_skills

    def _calculate_base_score(self, matched_skills: List[str], job_skills: List[str]) -> float:
        """Calculate base matching score"""
        if not job_skills:
            return 0.0

        match_ratio = len(matched_skills) / len(job_skills)

        # Apply diminishing returns for over-matching
        if match_ratio > 1.0:
            match_ratio = 1.0 + math.log(match_ratio) * 0.1

        return min(match_ratio * 100, 100)

    def _calculate_experience_score(self, candidate_experience: str = None, job_experience_level: str = None) -> float:
        """Calculate experience matching score"""
        if not candidate_experience or not job_experience_level:
            return 0.5  # Neutral score when information is missing

        # Extract years from candidate experience
        candidate_years = self._extract_years_from_experience(candidate_experience)
        job_level_years = self._get_years_for_experience_level(job_experience_level)

        if candidate_years is None:
            return 0.3  # Low confidence when experience can't be parsed

        # Calculate experience match
        if candidate_years >= job_level_years:
            # Overqualified - good match but may indicate mismatch
            if candidate_years > job_level_years + 3:
                return 0.8  # Slightly reduced for being too experienced
            else:
                return 0.95  # Good match
        else:
            # Underqualified
            experience_gap = job_level_years - candidate_years
            if experience_gap <= 1:
                return 0.7  # Close match
            elif experience_gap <= 3:
                return 0.4  # Moderate gap
            else:
                return 0.1  # Large gap

    def _extract_years_from_experience(self, experience_str: str) -> int:
        """Extract number of years from experience string"""
        if not experience_str:
            return None

        # Look for patterns like "5 years", "3+ years", "2-3 years"
        patterns = [
            r'(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?',
            r'experience:?\s*(\d+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, experience_str, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _get_years_for_experience_level(self, level: str) -> int:
        """Get typical years of experience for a level"""
        level_mapping = {
            "Entry": 0,
            "Junior": 1,
            "Mid-Level": 3,
            "Senior": 5,
            "Lead": 7,
            "Principal": 10
        }

        return level_mapping.get(level, 3)  # Default to mid-level

    def _analyze_skill_categories(self, candidate_skills: List[str], job_skills: List[str]) -> Dict[str, Any]:
        """Analyze skill matching by categories"""
        analysis = {}

        for category, skills in self.skill_taxonomy.items():
            job_category_skills = [skill for skill in job_skills if skill in skills]
            candidate_category_skills = [skill for skill in candidate_skills if skill in skills]

            if job_category_skills:
                matched = len(set(job_category_skills) & set(candidate_category_skills))
                total_job = len(job_category_skills)

                analysis[category] = {
                    "matched": matched,
                    "required": total_job,
                    "coverage": matched / total_job if total_job > 0 else 0,
                    "weight": self.skill_weights.get(category, 0.5)
                }

        return analysis

    def _calculate_overall_score(self, base_score: float, experience_score: float,
                               category_analysis: Dict[str, Any]) -> float:
        """Calculate overall score with weighted components"""
        # Base skill matching (40% weight)
        skill_weight = 0.4

        # Experience matching (30% weight)
        experience_weight = 0.3

        # Category analysis (30% weight)
        category_weight = 0.3

        # Calculate category score
        if category_analysis:
            category_scores = []
            total_weight = 0

            for category_data in category_analysis.values():
                category_score = category_data["coverage"] * category_data["weight"]
                category_scores.append(category_score)
                total_weight += category_data["weight"]

            category_score = sum(category_scores) / total_weight if total_weight > 0 else 0
        else:
            category_score = 0.5

        # Combine scores
        overall_score = (
            base_score * skill_weight +
            experience_score * 100 * experience_weight +
            category_score * 100 * category_weight
        )

        return min(overall_score, 100)

    def _generate_recommendations(self, missing_skills: List[str],
                                category_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for skill improvement"""
        recommendations = []

        # Recommend missing critical skills
        if missing_skills:
            critical_missing = missing_skills[:3]  # Top 3 missing skills
            recommendations.append(f"Consider learning: {', '.join(critical_missing)}")

        # Analyze weak categories
        weak_categories = []
        for category, data in category_analysis.items():
            if data["coverage"] < 0.5:
                weak_categories.append(category.replace("_", " ").title())

        if weak_categories:
            recommendations.append(f"Strengthen skills in: {', '.join(weak_categories)}")

        # Experience recommendations
        if not recommendations:
            recommendations.append("Your skills profile looks strong! Consider gaining more experience in your field.")

        return recommendations

    def rank_candidates(self, candidates: List[Dict[str, Any]], job_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank candidates for a job based on matching criteria"""
        ranked_candidates = []

        for candidate in candidates:
            match_result = self.calculate_enhanced_match(
                candidate.get("skills", []),
                job_requirements.get("skills", []),
                candidate.get("experience"),
                job_requirements.get("experience_level")
            )

            candidate_with_score = {
                **candidate,
                "match_score": match_result["score"],
                "match_details": match_result["details"]
            }

            ranked_candidates.append(candidate_with_score)

        # Sort by match score (descending)
        ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)

        return ranked_candidates

    def get_fairness_score(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate fairness score by removing potentially biased information"""
        # Remove or anonymize potentially biased attributes
        fair_data = candidate_data.copy()

        # Remove personal identifiers that might introduce bias
        biased_fields = ["name", "gender", "age", "ethnicity", "location"]
        for field in biased_fields:
            if field in fair_data:
                fair_data[field] = "[REDACTED]"

        # Calculate fairness metrics
        fairness_score = {
            "overall_fairness": 0.8,  # Placeholder - would need more sophisticated analysis
            "bias_indicators": [],
            "recommendations": [
                "Personal identifiers removed from ranking input",
                "Focus on skills and experience for fair evaluation"
            ]
        }

        return fairness_score
