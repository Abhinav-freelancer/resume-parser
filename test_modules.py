#!/usr/bin/env python3
"""
Test script to verify that all backend modules are working correctly
"""

import asyncio
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_resume_parser():
    """Test the enhanced resume parser"""
    try:
        from enhanced_resume_parser import EnhancedResumeParser

        logger.info("Testing EnhancedResumeParser...")

        parser = EnhancedResumeParser()

        # Test with sample text
        sample_resume_text = """
        John Doe
        Software Engineer
        Email: john.doe@email.com
        Phone: (555) 123-4567

        Skills: Python, JavaScript, React, Node.js, AWS, Docker

        Experience:
        Senior Software Engineer at Tech Corp (2020-Present)
        - Developed web applications using React and Node.js
        - Managed AWS infrastructure and Docker containers

        Education:
        Bachelor of Science in Computer Science
        University of Technology, 2018
        """

        # Create a temporary file for testing
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_resume_text)
            temp_file = f.name

        try:
            # Test parsing
            result = await parser.parse_resume(temp_file)
            logger.info(f"Resume parsing successful: {result.get('name', 'Unknown')}")

            # Verify key fields
            assert result['name'] == 'John Doe'
            assert 'Python' in result['skills']
            assert result['email'] == 'john.doe@email.com'

            logger.info("✓ EnhancedResumeParser test passed")
            return True

        finally:
            os.unlink(temp_file)

    except Exception as e:
        logger.error(f"✗ EnhancedResumeParser test failed: {str(e)}")
        return False

async def test_skill_matcher():
    """Test the enhanced skill matcher"""
    try:
        from enhanced_skill_matcher import EnhancedSkillMatcher

        logger.info("Testing EnhancedSkillMatcher...")

        matcher = EnhancedSkillMatcher()

        candidate_skills = ["Python", "JavaScript", "React", "AWS"]
        job_skills = ["Python", "JavaScript", "Node.js", "Docker"]

        result = matcher.calculate_enhanced_match(candidate_skills, job_skills)

        logger.info(f"Skill matching result: {result['score']}% match")

        # Verify result structure
        assert 'score' in result
        assert 'matched_skills' in result
        assert 'missing_skills' in result
        assert isinstance(result['score'], (int, float))

        logger.info("✓ EnhancedSkillMatcher test passed")
        return True

    except Exception as e:
        logger.error(f"✗ EnhancedSkillMatcher test failed: {str(e)}")
        return False

async def test_database():
    """Test the enhanced database manager"""
    try:
        from enhanced_database import EnhancedDatabaseManager

        logger.info("Testing EnhancedDatabaseManager...")

        db = EnhancedDatabaseManager()

        # Initialize database
        await db.initialize()

        # Test saving a candidate
        test_candidate = {
            "id": 999,
            "name": "Test Candidate",
            "email": "test@example.com",
            "skills": ["Python", "JavaScript"],
            "status": "Applied",
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat()
        }

        await db.save_candidate(test_candidate)

        # Test retrieving the candidate
        retrieved = await db.get_candidate(999)
        assert retrieved is not None
        assert retrieved['name'] == 'Test Candidate'

        logger.info("✓ EnhancedDatabaseManager test passed")
        return True

    except Exception as e:
        logger.error(f"✗ EnhancedDatabaseManager test failed: {str(e)}")
        return False

async def test_scheduler():
    """Test the enhanced interview scheduler"""
    try:
        from enhanced_scheduler import EnhancedInterviewScheduler

        logger.info("Testing EnhancedInterviewScheduler...")

        scheduler = EnhancedInterviewScheduler()

        # Test availability check (should work without Google API)
        test_datetime = (datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)).isoformat()
        available = await scheduler.check_availability(test_datetime, "John Smith")

        # Should return True (available) since no calendar service is connected
        assert isinstance(available, bool)

        logger.info("✓ EnhancedInterviewScheduler test passed")
        return True

    except Exception as e:
        logger.error(f"✗ EnhancedInterviewScheduler test failed: {str(e)}")
        return False

async def test_models():
    """Test the data models"""
    try:
        from models import Candidate, Job, Interview

        logger.info("Testing data models...")

        # Test creating model instances
        candidate = Candidate(
            id=1,
            name="Test User",
            email="test@example.com",
            skills=["Python"],
            created_date=datetime.now().isoformat(),
            updated_date=datetime.now().isoformat()
        )

        assert candidate.name == "Test User"
        assert candidate.email == "test@example.com"

        logger.info("✓ Data models test passed")
        return True

    except Exception as e:
        logger.error(f"✗ Data models test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting backend module tests...")

    tests = [
        ("Resume Parser", test_resume_parser),
        ("Skill Matcher", test_skill_matcher),
        ("Database Manager", test_database),
        ("Interview Scheduler", test_scheduler),
        ("Data Models", test_models)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} test...")
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {str(e)}")

    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Backend modules are ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
