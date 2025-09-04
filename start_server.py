#!/usr/bin/env python3
"""
Startup script for the AI Recruitment Agent backend
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import spacy
        logger.info("Core dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            logger.error("Failed to install dependencies")
            return False

def download_spacy_model():
    """Download spaCy language model if not present"""
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model is available")
        except OSError:
            logger.info("Downloading spaCy model...")
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            logger.info("spaCy model downloaded successfully")
    except Exception as e:
        logger.error(f"Error with spaCy model: {e}")

def create_directories():
    """Create necessary directories"""
    directories = ["uploads", "data", "data/backups"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def start_server():
    """Start the FastAPI server"""
    try:
        logger.info("Starting AI Recruitment Agent server...")
        import uvicorn
        from enhanced_main import app

        logger.info("Server starting on http://localhost:8000")
        logger.info("API documentation available at http://localhost:8000/docs")

        uvicorn.run(
            "enhanced_main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    logger.info("AI Recruitment Agent - Starting up...")

    # Check and install dependencies
    if not check_dependencies():
        sys.exit(1)

    # Download spaCy model
    download_spacy_model()

    # Create necessary directories
    create_directories()

    # Start the server
    start_server()

if __name__ == "__main__":
    main()
