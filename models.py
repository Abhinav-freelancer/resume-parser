from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class Candidate(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    education: Optional[str] = None
    work_history: List[Dict[str, Any]] = []
    status: str = "Applied"
    applied_jobs: List[int] = []
    match_scores: List[Dict[str, Any]] = []
    resume_file_path: Optional[str] = None
    original_filename: Optional[str] = None
    created_date: str
    updated_date: str
    confidence_scores: Dict[str, float] = {}
    raw_text: str = ""
    location: Optional[str] = None
    salary_expectation: Optional[str] = None

class Job(BaseModel):
    id: int
    title: str
    description: str
    skills: List[str] = []
    experience_level: str
    status: str = "Active"
    created_date: str
    department: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    applications_count: int = 0

class Interview(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    candidate_name: str
    job_title: str
    interviewer: str
    datetime: str
    interview_type: str
    status: str = "Scheduled"
    duration: int = 60
    location: str = "Virtual"
    meeting_link: str
    notes: str = ""
    created_date: str
    created_by: str = "System"

class MatchResult(BaseModel):
    score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_match: bool
    details: Dict[str, Any]

class ResumeParseResult(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    education: Optional[str] = None
    work_history: List[Dict[str, Any]] = []
    raw_text: str = ""
    confidence_scores: Dict[str, float] = {}
    location: Optional[str] = None
    salary_expectation: Optional[str] = None

class CalendarEvent(BaseModel):
    summary: str
    description: str
    start_datetime: str
    end_datetime: str
    attendees: List[str]
    location: str = "Virtual"
    meeting_link: Optional[str] = None

class EmailTemplate(BaseModel):
    subject: str
    body: str
    recipient: EmailStr
    sender: EmailStr
    template_type: str  # 'interview_invite', 'status_update', 'offer_letter'

class BiasDetectionResult(BaseModel):
    biased_words: List[str]
    bias_score: float
    recommendations: List[str]
    flagged_sections: List[Dict[str, Any]]
