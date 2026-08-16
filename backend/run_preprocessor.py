"""
Simple script to run the OSM preprocessor from the backend directory.
Run this from the backend directory: python run_preprocessor.py
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.routing.preprocessor import main

if __name__ == '__main__':
    main()
