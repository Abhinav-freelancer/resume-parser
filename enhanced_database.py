import json
import os
import asyncio
import aiofiles
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class EnhancedDatabaseManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "app_data.json")
        self.backup_dir = os.path.join(data_dir, "backups")

        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

        # In-memory data store
        self.data = {
            "candidates": [],
            "jobs": [],
            "interviews": [],
            "match_scores": {},
            "next_id": 1
        }

    async def initialize(self):
        """Initialize database and load existing data"""
        try:
            if os.path.exists(self.data_file):
                await self._load_data()
                logger.info("Database initialized with existing data")

                # Check if jobs array is empty and seed sample jobs if needed
                if not self.data.get("jobs"):
                    logger.info("No jobs found in database, seeding sample jobs...")
                    await self._seed_sample_jobs()
            else:
                # Add default sample jobs for testing
                await self._seed_sample_jobs()
                logger.info("Database initialized with empty data and sample jobs")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise

    async def _seed_sample_jobs(self):
        """Seed sample jobs into the database"""
        try:
            self.data["jobs"] = [
                {
                    "id": self.get_next_id(),
                    "title": "Senior Software Engineer",
                    "description": "Develop and maintain scalable web applications using modern JavaScript frameworks and cloud technologies.",
                    "skills": ["JavaScript", "React", "Node.js", "AWS", "Docker"],
                    "experience_level": "Senior",
                    "department": "Engineering",
                    "location": "San Francisco, CA",
                    "status": "Active",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": self.get_next_id(),
                    "title": "Data Scientist",
                    "description": "Build predictive models and analyze large datasets to drive business insights.",
                    "skills": ["Python", "Machine Learning", "TensorFlow", "SQL", "Statistics"],
                    "experience_level": "Mid-level",
                    "department": "Data Science",
                    "location": "New York, NY",
                    "status": "Active",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": self.get_next_id(),
                    "title": "DevOps Engineer",
                    "description": "Manage CI/CD pipelines and cloud infrastructure to ensure reliable deployments.",
                    "skills": ["AWS", "Kubernetes", "Docker", "Jenkins", "Linux"],
                    "experience_level": "Mid-level",
                    "department": "Operations",
                    "location": "Remote",
                    "status": "Active",
                    "created_at": datetime.now().isoformat()
                }
            ]
            await self._save_data()
            logger.info("Sample jobs seeded successfully")
        except Exception as e:
            logger.error(f"Error seeding sample jobs: {str(e)}")
            raise

    async def close(self):
        """Close database and save data"""
        try:
            await self._save_data()
            logger.info("Database closed successfully")
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")

    async def _load_data(self):
        """Load data from file"""
        try:
            async with aiofiles.open(self.data_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                loaded_data = json.loads(content)
                self.data.update(loaded_data)
                logger.info(f"Loaded data: {len(self.data['candidates'])} candidates, {len(self.data['jobs'])} jobs")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise

    async def _save_data(self):
        """Save data to file with backup"""
        try:
            # Create backup before saving
            if os.path.exists(self.data_file):
                await self._create_backup()

            # Save current data
            async with aiofiles.open(self.data_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.data, indent=2, ensure_ascii=False))

            logger.info("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            raise

    async def _create_backup(self):
        """Create backup of current data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.json")

            async with aiofiles.open(self.data_file, 'r', encoding='utf-8') as source:
                content = await source.read()

            async with aiofiles.open(backup_file, 'w', encoding='utf-8') as backup:
                await backup.write(content)

            # Keep only last 10 backups
            await self._cleanup_old_backups()

            logger.info(f"Backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")

    async def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent 10"""
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".json"):
                    filepath = os.path.join(self.backup_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    backup_files.append((filepath, mtime))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            for filepath, _ in backup_files[10:]:
                os.remove(filepath)
                logger.info(f"Removed old backup: {filepath}")

        except Exception as e:
            logger.error(f"Error cleaning up backups: {str(e)}")

    async def save_all_data(self, data: Dict[str, Any]):
        """Save all application data"""
        try:
            self.data.update(data)
            await self._save_data()
            logger.info("All data saved successfully")
        except Exception as e:
            logger.error(f"Error saving all data: {str(e)}")
            raise

    async def load_all_data(self) -> Dict[str, Any]:
        """Load all application data"""
        try:
            await self._load_data()
            return self.data.copy()
        except Exception as e:
            logger.error(f"Error loading all data: {str(e)}")
            return self.data.copy()

    # Candidate operations
    async def save_candidate(self, candidate: Dict[str, Any]):
        """Save candidate data"""
        try:
            # Find existing candidate or create new one
            existing_index = None
            for i, c in enumerate(self.data["candidates"]):
                if c["id"] == candidate["id"]:
                    existing_index = i
                    break

            if existing_index is not None:
                self.data["candidates"][existing_index] = candidate
                logger.info(f"Updated candidate: {candidate['id']}")
            else:
                self.data["candidates"].append(candidate)
                logger.info(f"Added new candidate: {candidate['id']}")

            await self._save_data()
        except Exception as e:
            logger.error(f"Error saving candidate: {str(e)}")
            raise

    async def get_candidate(self, candidate_id: int) -> Optional[Dict[str, Any]]:
        """Get candidate by ID"""
        try:
            for candidate in self.data["candidates"]:
                if candidate["id"] == candidate_id:
                    return candidate.copy()
            return None
        except Exception as e:
            logger.error(f"Error getting candidate {candidate_id}: {str(e)}")
            return None

    async def get_candidates(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get candidates with optional filters"""
        try:
            candidates = self.data["candidates"].copy()

            if filters:
                if "status" in filters:
                    candidates = [c for c in candidates if c.get("status") == filters["status"]]

                if "job_id" in filters:
                    job_id = filters["job_id"]
                    candidates = [c for c in candidates if job_id in c.get("applied_jobs", [])]

                if "skills" in filters and filters["skills"]:
                    candidates = [c for c in candidates if any(
                        skill in c.get("skills", []) for skill in filters["skills"]
                    )]

            return candidates
        except Exception as e:
            logger.error(f"Error getting candidates: {str(e)}")
            return []

    async def delete_candidate(self, candidate_id: int) -> bool:
        """Delete candidate by ID"""
        try:
            for i, candidate in enumerate(self.data["candidates"]):
                if candidate["id"] == candidate_id:
                    del self.data["candidates"][i]
                    await self._save_data()
                    logger.info(f"Deleted candidate: {candidate_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting candidate {candidate_id}: {str(e)}")
            return False

    # Job operations
    async def save_job(self, job: Dict[str, Any]):
        """Save job data"""
        try:
            existing_index = None
            for i, j in enumerate(self.data["jobs"]):
                if j["id"] == job["id"]:
                    existing_index = i
                    break

            if existing_index is not None:
                self.data["jobs"][existing_index] = job
                logger.info(f"Updated job: {job['id']}")
            else:
                self.data["jobs"].append(job)
                logger.info(f"Added new job: {job['id']}")

            await self._save_data()
        except Exception as e:
            logger.error(f"Error saving job: {str(e)}")
            raise

    async def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        try:
            for job in self.data["jobs"]:
                if job["id"] == job_id:
                    return job.copy()
            return None
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            return None

    async def get_jobs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get jobs with optional filters"""
        try:
            jobs = self.data["jobs"].copy()

            if filters:
                if "status" in filters:
                    jobs = [j for j in jobs if j.get("status") == filters["status"]]

                if "department" in filters:
                    jobs = [j for j in jobs if j.get("department", "").lower().startswith(
                        filters["department"].lower()
                    )]

            return jobs
        except Exception as e:
            logger.error(f"Error getting jobs: {str(e)}")
            return []

    async def delete_job(self, job_id: int) -> bool:
        """Delete job by ID"""
        try:
            for i, job in enumerate(self.data["jobs"]):
                if job["id"] == job_id:
                    del self.data["jobs"][i]
                    await self._save_data()
                    logger.info(f"Deleted job: {job_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            return False

    # Interview operations
    async def save_interview(self, interview: Dict[str, Any]):
        """Save interview data"""
        try:
            existing_index = None
            for i, iv in enumerate(self.data["interviews"]):
                if iv["id"] == interview["id"]:
                    existing_index = i
                    break

            if existing_index is not None:
                self.data["interviews"][existing_index] = interview
                logger.info(f"Updated interview: {interview['id']}")
            else:
                self.data["interviews"].append(interview)
                logger.info(f"Added new interview: {interview['id']}")

            await self._save_data()
        except Exception as e:
            logger.error(f"Error saving interview: {str(e)}")
            raise

    async def get_interview(self, interview_id: int) -> Optional[Dict[str, Any]]:
        """Get interview by ID"""
        try:
            for interview in self.data["interviews"]:
                if interview["id"] == interview_id:
                    return interview.copy()
            return None
        except Exception as e:
            logger.error(f"Error getting interview {interview_id}: {str(e)}")
            return None

    async def get_interviews(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get interviews with optional filters"""
        try:
            interviews = self.data["interviews"].copy()

            if filters:
                if "candidate_id" in filters:
                    interviews = [iv for iv in interviews if iv.get("candidate_id") == filters["candidate_id"]]

                if "job_id" in filters:
                    interviews = [iv for iv in interviews if iv.get("job_id") == filters["job_id"]]

                if "interviewer" in filters:
                    interviews = [iv for iv in interviews if iv.get("interviewer") == filters["interviewer"]]

                if "status" in filters:
                    interviews = [iv for iv in interviews if iv.get("status") == filters["status"]]

                if "date" in filters:
                    target_date = filters["date"]
                    interviews = [iv for iv in interviews if
                        datetime.fromisoformat(iv.get("datetime", "")).date().isoformat() == target_date]

            return interviews
        except Exception as e:
            logger.error(f"Error getting interviews: {str(e)}")
            return []

    async def delete_interview(self, interview_id: int) -> bool:
        """Delete interview by ID"""
        try:
            for i, interview in enumerate(self.data["interviews"]):
                if interview["id"] == interview_id:
                    del self.data["interviews"][i]
                    await self._save_data()
                    logger.info(f"Deleted interview: {interview_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting interview {interview_id}: {str(e)}")
            return False

    # Match scores operations
    async def save_match_score(self, candidate_id: int, job_id: int, score: float, details: Dict[str, Any]):
        """Save match score between candidate and job"""
        try:
            key = f"{candidate_id}_{job_id}"
            self.data["match_scores"][key] = {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "score": score,
                "details": details,
                "calculated_date": datetime.now().isoformat()
            }
            await self._save_data()
            logger.info(f"Saved match score: {key} = {score}")
        except Exception as e:
            logger.error(f"Error saving match score: {str(e)}")
            raise

    async def get_match_score(self, candidate_id: int, job_id: int) -> Optional[Dict[str, Any]]:
        """Get match score between candidate and job"""
        try:
            key = f"{candidate_id}_{job_id}"
            return self.data["match_scores"].get(key)
        except Exception as e:
            logger.error(f"Error getting match score: {str(e)}")
            return None

    # Utility methods
    def get_next_id(self) -> int:
        """Get next available ID"""
        next_id = self.data["next_id"]
        self.data["next_id"] += 1
        return next_id

    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "total_candidates": len(self.data["candidates"]),
                "total_jobs": len(self.data["jobs"]),
                "total_interviews": len(self.data["interviews"]),
                "total_match_scores": len(self.data["match_scores"]),
                "last_backup": None,
                "data_size": len(json.dumps(self.data))
            }

            # Get last backup time
            if os.path.exists(self.backup_dir):
                backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith("backup_")]
                if backup_files:
                    latest_backup = max(backup_files, key=lambda x: os.path.getmtime(
                        os.path.join(self.backup_dir, x)))
                    stats["last_backup"] = datetime.fromtimestamp(
                        os.path.getmtime(os.path.join(self.backup_dir, latest_backup))
                    ).isoformat()

            return stats
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}

    async def export_data(self, export_path: str):
        """Export all data to a file"""
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "data": self.data.copy()
            }

            async with aiofiles.open(export_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(export_data, indent=2, ensure_ascii=False))

            logger.info(f"Data exported to: {export_path}")
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise

    async def import_data(self, import_path: str):
        """Import data from a file"""
        try:
            async with aiofiles.open(import_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                import_data = json.loads(content)

            if "data" in import_data:
                self.data.update(import_data["data"])
                await self._save_data()
                logger.info(f"Data imported from: {import_path}")
            else:
                raise ValueError("Invalid import file format")
        except Exception as e:
            logger.error(f"Error importing data: {str(e)}")
            raise
